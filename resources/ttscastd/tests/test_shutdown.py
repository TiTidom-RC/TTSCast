""" Arrêt du démon : ordre des étapes (découverte, déconnexions, zeroconf), une étape en échec n'empêche pas les suivantes,
délai borné même avec un appareil en cours de reconnexion. Aucun appareil réel nécessaire.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import os
import time
import types as pytypes
import unittest
from unittest import mock

import ttscastd
from tests.helpers import newCast, resetDaemonState, stopAllConnections

myConfig = ttscastd.myConfig


class DaemonExit(Exception):
    """ Remplace os._exit : l'arrêt du démon termine le processus """


def fakeExit(code):
    raise DaemonExit(code)


class ShutdownTest(unittest.TestCase):
    def setUp(self):
        resetDaemonState()
        self.steps = []
        test = self

        class FailingBrowser:
            def stop_discovery(self):
                test.steps.append('browser')
                raise RuntimeError('échec simulé de stop_discovery')

        class Zeroconf:
            def close(self):
                test.steps.append('zeroconf')

        myConfig.NETCAST_BROWSER = FailingBrowser()
        myConfig.NETCAST_ZCONF = Zeroconf()
        myConfig.pidFile = os.path.join(os.path.dirname(__file__), '__inexistant__.pid')
        for name, value in (('os', pytypes.SimpleNamespace(remove=os.remove, _exit=fakeExit)), ('my_jeedom_socket', None)):
            patcher = mock.patch.object(ttscastd, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        stopAllConnections()

    def testShutdown(self):
        _, reconnecting = newCast('TV en veille')  # connexion qui échoue et attend avant de retenter
        _, neverConnected = newCast('Jamais connecté')
        reconnecting.start()
        time.sleep(0.5)
        start = time.monotonic()
        with self.assertLogs(level='INFO') as logs, self.assertRaises(DaemonExit):
            ttscastd.shutdown()
        duration = time.monotonic() - start

        self.assertEqual(self.steps, ['browser', 'zeroconf'], 'découverte arrêtée en premier, zeroconf fermé en dernier')
        self.assertTrue(any('Browser Stop :: Exception' in line for line in logs.output))
        self.assertTrue(any('ZeroConf Close :: OK' in line for line in logs.output), 'étape suivante exécutée malgré l\'échec')
        self.assertTrue(any('Devices Disconnect :: OK (1)' in line for line in logs.output), 'seul l\'appareil connecté est déconnecté')
        self.assertFalse(reconnecting.socket_client.is_alive())
        self.assertFalse(neverConnected.socket_client.is_alive())
        self.assertLess(duration, 7, 'délai borné')
        self.assertTrue(any('Exit 0' in line for line in logs.output))


if __name__ == '__main__':
    unittest.main()
