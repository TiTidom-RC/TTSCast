""" Logs du démon : filtres de logs configurables (PatternRemapFilter), masquage des secrets (SecretMaskFilter),
exceptions non interceptées journalisées via logging (secrets masqués).
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import io
import logging
import threading
import unittest

import ttscastd

RULES = [
    {'pattern': 'Failed to connect to service', 'level': 'DEBUG', 'enabled': True},
    {'pattern': 'Cannot ping', 'level': 'DROP', 'enabled': True},
    {'pattern': 'Plugin Version', 'level': 'DEBUG', 'enabled': True},
    {'pattern': 'Heartbeat', 'level': 'WARNING', 'enabled': True},
    {'pattern': 'Error reading', 'level': 'WARNING', 'enabled': True},
    {'pattern': 'disabled rule', 'level': 'DROP', 'enabled': False},
]
SECRET = 'a0195cxTOCFQ7DS4E85YFYgJjF06yJRMldD1cIfQ9WPR6el2jqyPThIqI1Fijq3B'
MASK = 'sEcReT'


class LoggingTestCase(unittest.TestCase):
    """ Configuration de logs du démon (basicConfig : seuil porté par le logger, handler sans niveau), sortie capturée """

    def configure(self, daemonLevel, castLevel, *filters):
        self.stream = io.StringIO()
        root = logging.getLogger()
        previous = (root.handlers[:], root.level, logging.getLogger('pychromecast').level)
        self.addCleanup(self.restore, previous)
        logging.basicConfig(level=daemonLevel, format='[%(levelname)s] %(message)s', stream=self.stream, force=True)
        logging.getLogger('pychromecast').setLevel(castLevel)
        for handler in root.handlers:
            for logFilter in filters:
                handler.addFilter(logFilter)

    @staticmethod
    def restore(previous):
        handlers, level, castLevel = previous
        root = logging.getLogger()
        root.handlers = handlers
        root.setLevel(level)
        logging.getLogger('pychromecast').setLevel(castLevel)

    def lines(self):
        return self.stream.getvalue().splitlines()


class PatternRemapFilterTest(LoggingTestCase):
    def emitAll(self):
        library = logging.getLogger('pychromecast.socket_client')
        library.error('Failed to connect to service X')
        library.error('Cannot ping until reconnected')
        library.info('Heartbeat timeout')
        library.error('Error reading from socket')
        logging.info('[DAEMON][MAIN] Plugin Version: 1.13.0')
        logging.error('[DAEMON] disabled rule stays')
        return self.lines()

    def testDaemonInInfo(self):
        self.configure(logging.INFO, logging.WARNING, ttscastd.PatternRemapFilter(RULES))
        lines = self.emitAll()
        self.assertFalse(any('Failed to connect' in line for line in lines), 'ERROR abaissé en DEBUG : masqué')
        self.assertFalse(any('Plugin Version' in line for line in lines), 'INFO abaissé en DEBUG : masqué')
        self.assertFalse(any('Cannot ping' in line for line in lines), '--- : supprimé')
        self.assertIn('[WARNING] Error reading from socket', lines)
        self.assertFalse(any('Heartbeat' in line for line in lines), 'un filtre ne fait pas apparaître un message sous le seuil')
        self.assertIn('[ERROR] [DAEMON] disabled rule stays', lines)

    def testDaemonInDebug(self):
        self.configure(logging.DEBUG, logging.DEBUG, ttscastd.PatternRemapFilter(RULES))
        lines = self.emitAll()
        self.assertIn('[DEBUG] Failed to connect to service X', lines)
        self.assertIn('[DEBUG] [DAEMON][MAIN] Plugin Version: 1.13.0', lines)
        self.assertIn('[WARNING] Heartbeat timeout', lines)
        self.assertFalse(any('Cannot ping' in line for line in lines))

    def testLibraryMessagesFollowTheDaemonLevelByDefault(self):
        self.configure(logging.ERROR, logging.NOTSET, ttscastd.PatternRemapFilter(RULES))  # niveau Chromecast = identique au démon
        self.assertFalse(any('Error reading' in line for line in self.emitAll()), 'ERROR abaissé en WARNING sous un démon en error : masqué')


class SecretMaskTest(LoggingTestCase):
    def testSecretIsMaskedEverywhere(self):
        self.configure(logging.DEBUG, logging.DEBUG, ttscastd.SecretMaskFilter([SECRET, 'noKey', ''], MASK))
        logging.getLogger('urllib3').debug('GET /jeettscast.php?apikey=%s', SECRET)
        logging.info('[DAEMON] noKey reste lisible')
        output = self.stream.getvalue()
        self.assertNotIn(SECRET, output)
        self.assertIn('apikey=' + MASK, output)
        self.assertIn('noKey reste lisible', output, 'valeurs courtes ou par défaut ignorées (mots ordinaires)')


class UncaughtExceptionTest(LoggingTestCase):
    def setUp(self):
        self.configure(logging.DEBUG, logging.DEBUG, ttscastd.SecretMaskFilter([SECRET], MASK))

    @staticmethod
    def boom():
        raise ConnectionError('Max retries exceeded with url: /jeettscast.php?apikey=' + SECRET)

    def testThreadException(self):
        previousHook = threading.excepthook
        threading.excepthook = ttscastd.logUncaughtThreadException
        try:
            thread = threading.Thread(target=self.boom, name='TestThread')
            thread.start()
            thread.join()
        finally:
            threading.excepthook = previousHook
        output = self.stream.getvalue()
        self.assertIn('[ERROR] [DAEMON] Exception non interceptée dans le thread TestThread', output)
        self.assertIn('apikey=' + MASK, output)
        self.assertNotIn(SECRET, output)

    def testMainThreadException(self):
        try:
            self.boom()
        except ConnectionError as error:
            ttscastd.logUncaughtException(type(error), error, error.__traceback__)
        output = self.stream.getvalue()
        self.assertIn('[CRITICAL] [DAEMON] Exception non interceptée', output)
        self.assertIn('apikey=' + MASK, output)
        self.assertNotIn(SECRET, output)


if __name__ == '__main__':
    unittest.main()
