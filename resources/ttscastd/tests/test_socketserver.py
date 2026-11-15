""" Serveur socket du démon (jeedom_socket_server) : commandes déposées dans l'ordre d'envoi, connexion muette, message invalide,
commandes synchrones traitées sans retarder les suivantes, erreur imprévue. Vrai serveur sur un port libre de 127.0.0.1.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import json
import queue
import random
import socket
import threading
import time
import unittest
from unittest import mock

from jeedom import jeedom as jeedomLib
from tests import helpers

APIKEY = 'cle-de-test'


class SocketServerTest(unittest.TestCase):
    def setUp(self):
        while not jeedomLib.JEEDOM_SOCKET_MESSAGE.empty():
            jeedomLib.JEEDOM_SOCKET_MESSAGE.get_nowait()
        patches = [mock.patch.object(jeedomLib.jeedom_socket_handler, 'sync_command_handlers', {}),
                   mock.patch.object(jeedomLib.jeedom_socket_handler, 'expected_apikey', APIKEY)]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.server = jeedomLib.jeedom_socket_server(('127.0.0.1', 0), jeedomLib.jeedom_socket_handler)
        self.port = self.server.server_address[1]
        self.closed = []
        originalShutdown = self.server.shutdown_request

        def countedShutdown(request):
            self.closed.append(request)
            originalShutdown(request)
        self.server.shutdown_request = countedShutdown
        thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def send(self, payload):
        """ Comme sendToDaemon (PHP) : connexion, écriture, fermeture, sans attendre le démon """
        with socket.create_connection(('127.0.0.1', self.port)) as client:
            client.sendall(payload if isinstance(payload, bytes) else json.dumps(payload).encode('utf-8'))

    def sendSync(self, payload):
        """ Comme sendToDaemonSync (PHP) : écriture, fin d'envoi signalée, lecture de la réponse jusqu'à la fermeture """
        with socket.create_connection(('127.0.0.1', self.port)) as client:
            client.settimeout(5)
            client.sendall(json.dumps(payload).encode('utf-8'))
            client.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    return b''.join(chunks)
                chunks.append(chunk)

    def received(self, count, timeout=3):
        return [json.loads(jeedomLib.JEEDOM_SOCKET_MESSAGE.get(timeout=timeout)) for _ in range(count)]

    def assertNothingReceived(self):
        self.assertRaises(queue.Empty, jeedomLib.JEEDOM_SOCKET_MESSAGE.get, timeout=0.3)

    def test_orderOfSending(self):
        # Durée variable du traitement d'une connexion (logs filtrés et masqués sur une box) : un serveur à un thread par connexion
        # déposerait les messages dans le désordre
        with mock.patch.object(jeedomLib.logging, 'debug', side_effect=lambda *a, **k: time.sleep(random.random() * 0.003)):
            for n in range(50):
                self.send({'cmd': 'action', 'n': n, 'apikey': APIKEY})
            self.assertEqual([m['n'] for m in self.received(50)], list(range(50)))
        self.assertTrue(helpers.waitUntil(lambda: len(self.closed) == 50))
        self.assertEqual(len(set(map(id, self.closed))), 50, 'chaque connexion fermée une seule fois')

    def test_silentClientDelaysFollowingOnlyUntilTimeout(self):
        with mock.patch.object(jeedomLib.jeedom_socket_handler, 'timeout', 0.3), self.assertLogs(level='WARNING') as logs:
            silent = socket.create_connection(('127.0.0.1', self.port))
            self.addCleanup(silent.close)
            start = time.monotonic()
            self.send({'cmd': 'action', 'n': 1})
            self.assertEqual(self.received(1)[0]['n'], 1)
        self.assertLess(time.monotonic() - start, 2)
        self.assertTrue(any('Message non reçu' in line for line in logs.output))

    def test_invalidMessagesIgnored(self):
        with self.assertLogs(level='ERROR') as logs:
            self.send(b'pas du json')
            self.send(b'[1, 2]')
            self.send({'cmd': 'action', 'n': 3})
            self.assertEqual(self.received(1)[0]['n'], 3)
        self.assertEqual(len(logs.output), 2)
        self.assertNothingReceived()

    def test_syncCommandDoesNotDelayFollowing(self):
        release, calls = threading.Event(), []

        def slowHandler(message):
            calls.append(message['value'])
            release.wait(5)
            return {'result': message['value'].upper()}
        jeedomLib.jeedom_socket_handler.sync_command_handlers['aiReformat'] = slowHandler
        answers = []
        client = threading.Thread(target=lambda: answers.append(self.sendSync({'cmd': 'aiReformat', 'value': 'bonjour', 'apikey': APIKEY})))
        client.start()
        self.assertTrue(helpers.waitUntil(lambda: calls == ['bonjour']))
        self.send({'cmd': 'action', 'n': 1})
        self.assertEqual(self.received(1)[0]['n'], 1, 'message reçu pendant la commande synchrone')
        release.set()
        client.join(5)
        self.assertEqual(json.loads(answers[0]), {'result': 'BONJOUR'})
        self.assertTrue(helpers.waitUntil(lambda: len(self.closed) == 2))
        self.assertEqual(len(set(map(id, self.closed))), 2, 'chaque connexion fermée une seule fois')
        self.assertNothingReceived()

    def test_syncCommandInvalidApikey(self):
        handler = mock.Mock(return_value={'result': 'x'})
        jeedomLib.jeedom_socket_handler.sync_command_handlers['aiReformat'] = handler
        with self.assertLogs(level='ERROR'):
            self.assertEqual(self.sendSync({'cmd': 'aiReformat', 'apikey': 'mauvaise'}), b'')
        handler.assert_not_called()
        self.assertNothingReceived()

    def test_syncCommandError(self):
        jeedomLib.jeedom_socket_handler.sync_command_handlers['aiReformat'] = mock.Mock(side_effect=RuntimeError('panne'))
        with self.assertLogs(level='ERROR') as logs:
            self.assertEqual(self.sendSync({'cmd': 'aiReformat', 'apikey': APIKEY}), b'')
        self.assertTrue(any('panne' in line for line in logs.output))
        self.assertNothingReceived()

    def test_syncThreadNotStarted(self):
        jeedomLib.jeedom_socket_handler.sync_command_handlers['aiReformat'] = mock.Mock(return_value={})
        with mock.patch.object(jeedomLib, 'Thread', side_effect=RuntimeError('trop de threads')), self.assertLogs(level='ERROR'):
            self.assertEqual(self.sendSync({'cmd': 'aiReformat', 'apikey': APIKEY}), b'')
        self.send({'cmd': 'action', 'n': 1})
        self.assertEqual(self.received(1)[0]['n'], 1)

    def test_unexpectedErrorLoggedAndServerContinues(self):
        with mock.patch.object(jeedomLib.JEEDOM_SOCKET_MESSAGE, 'put', side_effect=RuntimeError('imprévu')), \
                self.assertLogs(level='ERROR') as logs:
            self.send({'cmd': 'action', 'n': 1})
            self.assertTrue(helpers.waitUntil(lambda: logs.output))
        self.assertIn('Erreur sur la connexion', logs.output[0])
        self.assertIn('imprévu', logs.output[0])
        self.send({'cmd': 'action', 'n': 2})
        self.assertEqual(self.received(1)[0]['n'], 2)



if __name__ == '__main__':
    unittest.main()
