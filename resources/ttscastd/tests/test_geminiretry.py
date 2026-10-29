""" Nouvelles tentatives des appels Gemini (callGeminiWithRetry) : erreurs relancées ou non, délais, délai indiqué par Gemini,
temps restant. Horloge simulée : aucune attente réelle, aucun appel à Gemini.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import unittest
from unittest import mock

import httpx
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
        result, _ = self.run_([httpx.ConnectError('dns'), 'ok'])
        self.assertEqual(result, 'ok')
        self.assertEqual(self.clock.sleeps, [1])

    def testTimeoutIsNotRetried(self):
        result, _ = self.run_([httpx.ReadTimeout('lent')])
        self.assertIsInstance(result, httpx.ReadTimeout)
        self.assertEqual(self.clock.sleeps, [])

    def testNoRetryWhenTooLittleTimeRemains(self):
        result, _ = self.run_([apiError(503), 'ok'], budget=6)
        self.assertIsInstance(result, genaiErrors.APIError)
        self.assertEqual(self.clock.sleeps, [])

    def testConfigCopiedWithTimeout(self):
        config = TTSCast.geminiConfigWithTimeout(types.GenerateContentConfig(temperature=0.3), 12345)
        self.assertEqual(config.http_options.timeout, 12345)
        self.assertEqual(config.temperature, 0.3)

    def testRetryDelayAbsent(self):
        self.assertIsNone(TTSCast.geminiRetryDelay(apiError(503)))
        self.assertIsNone(TTSCast.geminiRetryDelay(ValueError()))


if __name__ == '__main__':
    unittest.main()
