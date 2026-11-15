""" Nouvelles tentatives des appels Gemini (callGeminiWithRetry) : erreurs relancées ou non, délais, délai indiqué par Gemini,
temps restant. Horloge simulée : aucune attente réelle, aucun appel à Gemini.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import unittest
from unittest import mock

import httpx2
from google.genai import errors as genaiErrors
from google.genai import types

import ttscastd

TTSCast = ttscastd.TTSCast


class FakeClock:
    def __init__(self):
        self.now, self.sleeps = 0.0, []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def apiError(code, retryDelay=None):
    body = {'error': {'code': code, 'message': 'x', 'status': 'S'}}
    if retryDelay:
        body['error']['details'] = [{'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': retryDelay}]
    return genaiErrors.APIError(code, body)


class GeminiRetryTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        patches = [mock.patch.object(ttscastd, 'time', self.clock)]
        retrySettings = {'geminiRetryAttempts': 3, 'geminiRetryDelays': (1, 2), 'geminiRetryMinRemaining': 5,
                         'geminiRetryHttpCodes': (429, 500, 502, 503, 504)}
        patches += [mock.patch.object(ttscastd.myConfig, name, value) for name, value in retrySettings.items()]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_(self, outcomes, budget=30, callCost=0.5):
        """ outcomes : exceptions levées ou valeurs renvoyées successivement. Retourne (résultat ou exception, délais transmis) """
        timeouts, sequence = [], list(outcomes)

        def call(timeoutMs):
            timeouts.append(timeoutMs)
            self.clock.now += callCost
            item = sequence.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item
        try:
            return TTSCast.callGeminiWithRetry('[TEST]', budget, call), timeouts
        except BaseException as error:  # noqa: BLE001 — l'erreur relevée fait partie du résultat attendu
            return error, timeouts

    def testDirectSuccess(self):
        result, timeouts = self.run_(['ok'])
        self.assertEqual((result, timeouts, self.clock.sleeps), ('ok', [30000], []))

    def testRetriesOnServerErrorsThenSucceeds(self):
        result, timeouts = self.run_([apiError(503), apiError(503), 'ok'])
        self.assertEqual(result, 'ok')
        self.assertEqual(self.clock.sleeps, [1, 2])
        self.assertEqual(len(timeouts), 3)
        self.assertLess(timeouts[1], 30000, 'délai restant transmis à la tentative suivante')

    def testClientErrorIsNotRetried(self):
        result, _ = self.run_([apiError(400)])
        self.assertIsInstance(result, genaiErrors.APIError)
        self.assertEqual(result.code, 400)
        self.assertEqual(self.clock.sleeps, [])

    def testErrorRaisedAfterTheLastAttempt(self):
        result, _ = self.run_([apiError(503)] * 3)
        self.assertIsInstance(result, genaiErrors.APIError)
        self.assertEqual(self.clock.sleeps, [1, 2])

    def testGeminiRetryDelayLongerThanTheBudget(self):
        with self.assertLogs(level='DEBUG') as logs:
            result, _ = self.run_([apiError(429, '37s')])
        self.assertIsInstance(result, genaiErrors.APIError)
        self.assertEqual(self.clock.sleeps, [])
        self.assertTrue(any('attendre 37s' in line for line in logs.output))
        self.assertTrue(any('quota' in line for line in logs.output))

    def testGeminiRetryDelayIsUsed(self):
        result, _ = self.run_([apiError(429, '2s'), 'ok'])
        self.assertEqual(result, 'ok')
        self.assertEqual(self.clock.sleeps, [2.0])

    def testConnectionErrorIsRetried(self):
        result, _ = self.run_([httpx2.ConnectError('dns'), 'ok'])
        self.assertEqual(result, 'ok')
        self.assertEqual(self.clock.sleeps, [1])

    def testTimeoutIsNotRetried(self):
        result, _ = self.run_([httpx2.ReadTimeout('lent')])
        self.assertIsInstance(result, httpx2.ReadTimeout)
        self.assertEqual(self.clock.sleeps, [])

    def testNoRetryWhenTooLittleTimeRemains(self):
        result, _ = self.run_([apiError(503), 'ok'], budget=6)
        self.assertIsInstance(result, genaiErrors.APIError)
        self.assertEqual(self.clock.sleeps, [])

    def testConfigCopiedWithTimeout(self):
        config = TTSCast.geminiConfigWithTimeout(types.GenerateContentConfig(temperature=0.3), 12345)
        self.assertEqual(config.http_options.timeout, 12345)
        self.assertEqual(config.temperature, 0.3)

    FAILED_PRECONDITION = genaiErrors.APIError(400, {'error': {'code': 400, 'message': 'x', 'status': 'FAILED_PRECONDITION'}})

    def adviceFor(self, authMode, error):
        with mock.patch.object(ttscastd.myConfig, 'aiAuthMode', authMode):
            return TTSCast.geminiErrorAdvice(error)

    def testErrorAdviceApiKey(self):
        for code, expected in ((401, 'identifiants Gemini refusés'), (402, 'crédit Gemini épuisé'),
                               (403, 'accès Gemini refusé : vérifiez la clé et la facturation')):
            with self.subTest(code=code):
                self.assertTrue(self.adviceFor('apikey', apiError(code)).startswith(' — ' + expected))
        self.assertIn('facturation Gemini à activer', self.adviceFor('apikey', self.FAILED_PRECONDITION))
        self.assertEqual(self.adviceFor('apikey', apiError(404)), '')  # modèle introuvable : rien à corriger par l'utilisateur

    def testErrorAdviceOauth2(self):
        for code, expected in ((401, 'identifiants Gemini refusés'), (403, 'accès Gemini refusé : vérifiez dans la console Google Cloud'),
                               (404, 'projet Gemini introuvable : vérifiez l\'ID du projet')):
            with self.subTest(code=code):
                self.assertTrue(self.adviceFor('oauth2', apiError(code)).startswith(' — ' + expected))
        self.assertEqual(self.adviceFor('oauth2', apiError(402)), '')
        self.assertEqual(self.adviceFor('oauth2', self.FAILED_PRECONDITION), '')

    def testNoAdviceForPassingOrPluginErrors(self):
        for authMode in ('apikey', 'oauth2'):
            for code in (400, 429, 500, 503, 504):
                with self.subTest(authMode=authMode, code=code):
                    self.assertEqual(self.adviceFor(authMode, apiError(code)), '')
            self.assertEqual(self.adviceFor(authMode, ValueError('x')), '')

    def testCreditDepletedNotRetried(self):
        result, timeouts = self.run_([apiError(402), 'ok'])
        self.assertIsInstance(result, genaiErrors.APIError)
        self.assertEqual(len(timeouts), 1)

    def testRetryDelayAbsent(self):
        self.assertIsNone(TTSCast.geminiRetryDelay(apiError(503)))
        self.assertIsNone(TTSCast.geminiRetryDelay(ValueError()))


class GeminiApiVersionTest(unittest.TestCase):
    """ Mode clé API : clients créés en v1beta (google-genai utilise v1 par défaut, sans sortie audio pour Gemini TTS) """
    def setUp(self):
        settings = {'aiAuthMode': 'apikey', 'aiApiKey': 'cle-de-test', 'gCloudApiKey': 'noKey', 'aiProjectID': 'noProjectID',
                    'aiModel': 'gemini-3.5-flash-lite', 'geminiTTSModel': 'gemini-3.8-flash-lite-tts'}
        for name, value in settings.items():
            patcher = mock.patch.object(ttscastd.myConfig, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        clientPatcher = mock.patch.object(ttscastd.genai, 'Client', side_effect=RuntimeError('appel non effectué en test'))
        self.client = clientPatcher.start()
        self.addCleanup(clientPatcher.stop)

    def assertClientVersion(self):
        self.client.assert_called_once()
        self.assertEqual(self.client.call_args.kwargs['http_options'].api_version, 'v1beta')

    def testGenAI(self):
        with self.assertLogs(level='ERROR'):
            self.assertIsNone(TTSCast.genAI('Bonjour'))
        self.assertClientVersion()

    def testGeminiTTS(self):
        with self.assertLogs(level='ERROR'):
            self.assertIsNone(TTSCast.geminiTTS('Bonjour', 'Achird'))
        self.assertClientVersion()


if __name__ == '__main__':
    unittest.main()
