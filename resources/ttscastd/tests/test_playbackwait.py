""" Attente de fin de lecture (waitPlaybackEnd) et validation des options wait / force de la file d'attente.
Horloge simulée et faux contrôleur média : aucune attente réelle, aucun appareil.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import types as pytypes
import unittest
from uuid import uuid4

import ttscastd
from tests import helpers

Functions = ttscastd.Functions
myConfig = ttscastd.myConfig

TIMEOUT = 20
REFRESH = 5
URL = 'http://jeedom/cache/tts.mp3'


class FakeMediaController:
    """ État média modifiable ; chaque modification ou réponse à update_status renouvelle last_updated, comme pychromecast """
    def __init__(self):
        self.status = pytypes.SimpleNamespace(
            media_session_id=None, player_state='UNKNOWN', idle_reason=None, current_time=0.0,
            last_updated=None, stream_type='BUFFERED', content_id=None,
        )
        self.updateCount = 0
        self.responder = None  # appelé sans argument à chaque update_status : simule la réponse de l'enceinte

    def apply(self, **changes):
        for key, value in changes.items():
            setattr(self.status, key, value)
        self.updateCount += 1
        self.status.last_updated = self.updateCount

    def reset(self):
        """ Coupure du canal média : pychromecast remplace l'état par un état vierge """
        self.status = pytypes.SimpleNamespace(
            media_session_id=None, player_state='UNKNOWN', idle_reason=None, current_time=0.0,
            last_updated=None, stream_type='BUFFERED', content_id=None,
        )

    def update_status(self):
        if self.responder is not None:
            self.responder()


class Scenario:
    """ Horloge simulée + événements datés (secondes depuis le début) appliqués au faux contrôleur """
    def __init__(self, events=(), responder=None, start=1000.0):
        self.start = start
        self.now = start
        self.events = sorted(events, key=lambda e: e[0])
        self.mc = FakeMediaController()
        self.mc.responder = (lambda: responder(self)) if responder else None
        self.cast = pytypes.SimpleNamespace(uuid=uuid4(), name='Enceinte de test', media_controller=self.mc)
        self._applyDue()

    def elapsed(self):
        return self.now - self.start

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self._applyDue()
        if self.elapsed() > 3600:
            raise AssertionError('attente de fin de lecture sans fin')

    def _applyDue(self):
        while self.events and self.events[0][0] <= self.elapsed() + 1e-9:
            _, action = self.events.pop(0)
            action(self)

    def run(self, sessionBefore=None, mediaUrl=URL):
        return Functions.waitPlaybackEnd(self.cast, sessionBefore, self.start, '[TEST]', mediaUrl=mediaUrl, clock=self.clock, sleep=self.sleep)


def state(**changes):
    return lambda sc: sc.mc.apply(**changes)


def playingResponder(sc):
    """ Enceinte qui lit normalement : position = temps écoulé depuis le début """
    sc.mc.apply(current_time=sc.elapsed())


class WaitPlaybackEndTest(unittest.TestCase):
    def setUp(self):
        helpers.resetDaemonState()
        self.saved = (myConfig.cmdWaitTimeout, myConfig.playbackStatusRefresh)
        myConfig.cmdWaitTimeout = TIMEOUT
        myConfig.playbackStatusRefresh = REFRESH

    def tearDown(self):
        myConfig.cmdWaitTimeout, myConfig.playbackStatusRefresh = self.saved

    def test_normalEnd(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='BUFFERING', content_id=URL)),
            (1, state(player_state='PLAYING')),
            (4, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        self.assertEqual(sc.run(), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 4, delta=0.2)

    def test_playingNeverSeen(self):
        """ Clip très court : l'état PLAYING n'est jamais observé, la fin est quand même reconnue """
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='BUFFERING')),
            (1, state(player_state='IDLE', idle_reason='FINISHED')),
        ])
        self.assertEqual(sc.run(), 'finished')
        self.assertLess(sc.elapsed(), 2)

    def test_loadFailed(self):
        def fail(sc):
            myConfig.loadFailures[str(sc.cast.uuid)] = sc.now
        sc = Scenario([(1, fail)])
        self.assertEqual(sc.run(), 'error')
        self.assertLess(sc.elapsed(), 2)

    def test_loadFailedBeforeRequestIgnored(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (3, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        myConfig.loadFailures[str(sc.cast.uuid)] = sc.start - 50
        self.assertEqual(sc.run(), 'finished')

    def test_idleError(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='BUFFERING')),
            (2, state(player_state='IDLE', idle_reason='ERROR')),
        ])
        self.assertEqual(sc.run(), 'error')

    def test_neverStarted(self):
        sc = Scenario()
        self.assertEqual(sc.run(), 'notStarted')
        self.assertAlmostEqual(sc.elapsed(), TIMEOUT, delta=0.2)

    def test_stuckBuffering(self):
        sc = Scenario([(0.5, state(media_session_id=7, player_state='BUFFERING'))])
        self.assertEqual(sc.run(), 'notStarted')
        self.assertAlmostEqual(sc.elapsed(), TIMEOUT, delta=0.2)

    def test_pauseThenResume(self):
        """ Pause plus courte que le délai : la lecture reprend et va à son terme, même au-delà du délai total """
        def responder(sc):
            if sc.mc.status.player_state == 'PLAYING':
                sc.mc.apply(current_time=sc.elapsed())
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (5, state(player_state='PAUSED')),
            (5 + TIMEOUT - 2, state(player_state='PLAYING')),
            (60, state(player_state='IDLE', idle_reason='FINISHED')),
        ], responder)
        self.assertEqual(sc.run(), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 60, delta=0.2)

    def test_pauseTooLong(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (5, state(player_state='PAUSED')),
        ])
        self.assertEqual(sc.run(), 'stalled')
        self.assertLess(sc.elapsed(), 5 + TIMEOUT + REFRESH + 1)

    def test_frozenPosition(self):
        """ L'enceinte répond toujours PLAYING mais la position n'avance plus """
        def responder(sc):
            sc.mc.apply(current_time=min(sc.elapsed(), 8.0))
        sc = Scenario([(0.5, state(media_session_id=7, player_state='PLAYING'))], responder)
        self.assertEqual(sc.run(), 'stalled')
        self.assertLess(sc.elapsed(), 8 + TIMEOUT + REFRESH + 1)

    def test_noMoreAnswers(self):
        """ L'enceinte ne répond plus aux demandes d'état, sans coupure de la connexion """
        sc = Scenario([(0.5, state(media_session_id=7, player_state='PLAYING'))])
        self.assertEqual(sc.run(), 'stalled')

    def test_longPlaybackNeverCut(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (600, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        self.assertEqual(sc.run(), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 600, delta=0.2)

    def test_liveStreamConstantPosition(self):
        """ Flux LIVE (Gemini en streaming) : position non significative, l'enceinte qui répond en lecture suffit """
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING', stream_type='LIVE')),
            (120, state(player_state='IDLE', idle_reason='FINISHED')),
        ], lambda sc: sc.mc.apply(current_time=0.0))
        self.assertEqual(sc.run(), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 120, delta=0.2)

    def test_interruptedBySessionReset(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (3, lambda sc: sc.mc.reset()),
        ], playingResponder)
        self.assertEqual(sc.run(), 'interrupted')
        self.assertLess(sc.elapsed(), 4)

    def test_replacedByOtherSession(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (3, state(media_session_id=8, player_state='PLAYING', content_id='http://autre/media')),
        ], playingResponder)
        self.assertEqual(sc.run(), 'replaced')

    def test_replacedIdleInterrupted(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (3, state(player_state='IDLE', idle_reason='INTERRUPTED')),
        ], playingResponder)
        self.assertEqual(sc.run(), 'replaced')

    def test_previousMediaStateIgnored(self):
        """ État restant d'une radio (session 3) : ni sa lecture ni son arrêt ne sont pris pour les nôtres """
        sc = Scenario([
            (0, state(media_session_id=3, player_state='PLAYING', content_id='http://radio/flux')),
            (0.5, state(player_state='IDLE', idle_reason='INTERRUPTED')),
            (1, state(media_session_id=4, player_state='BUFFERING', content_id=URL, idle_reason=None)),
            (2, state(player_state='PLAYING')),
            (6, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        self.assertEqual(sc.run(sessionBefore=3), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 6, delta=0.2)

    def test_sameSessionIdOurUrl(self):
        """ Identifiant de session inchangé : la lecture de notre URL est quand même reconnue """
        sc = Scenario([
            (0, state(media_session_id=7, player_state='IDLE', idle_reason='FINISHED', content_id=URL)),
            (1, state(player_state='PLAYING', idle_reason=None)),
            (5, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        self.assertEqual(sc.run(sessionBefore=7), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 5, delta=0.2)

    def test_statusRefreshedDuringPlayback(self):
        requests = []

        def responder(sc):
            requests.append(sc.elapsed())
            playingResponder(sc)
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (30, state(player_state='IDLE', idle_reason='FINISHED')),
        ], responder)
        sc.run()
        self.assertIn(len(requests), (30 // REFRESH - 1, 30 // REFRESH))


class QueueOptionsTest(unittest.TestCase):
    def setUp(self):
        helpers.resetDaemonState()
        myConfig.deviceQueues = {}

    def test_parseWaitOption(self):
        for value, expected in ((None, None), (0, 0), (2, 2), ('3', 3), (1.7, 1), (True, 1),
                                (-1, None), ('-2', None), ('un', None), ('1.5', None), ([], None), (float('inf'), None)):
            with self.subTest(value=value):
                self.assertEqual(Functions.parseWaitOption(value), expected)

    def test_parseForceOption(self):
        for value, expected in ((True, True), (False, False), (1, True), (0, False), ('true', True), (' TRUE ', True),
                                ('false', False), ('0', False), ('non', False), ('', False), (None, False)):
            with self.subTest(value=value):
                self.assertEqual(Functions.parseForceOption(value), expected)

    def _register(self, options):
        uuid = uuid4()
        myConfig.NETCAST_DEVICES[uuid] = pytypes.SimpleNamespace(uuid=uuid, name='Enceinte de test')
        return uuid, Functions.socketRegisterQueue(str(uuid), options, 1234, 'TEST')

    def test_invalidWaitQueuedAsAuto(self):
        uuid, (registered, targetUUID, ticket, cmdWait, cmdForce) = self._register('"wait": -1')
        self.assertTrue(registered)
        self.assertEqual((ticket, cmdWait, cmdForce), (0, None, False))
        entry = myConfig.deviceQueues[str(uuid)]
        self.assertEqual(entry['blocksByTicket'], {})
        Functions.waitQueueExit(targetUUID, ticket, cmdWait, cmdForce, 'TEST')
        self.assertEqual(entry['serving'], 1)

    def test_forceFalseText(self):
        _, (registered, _, ticket, _, cmdForce) = self._register('"force": "false"')
        self.assertTrue(registered)
        self.assertFalse(cmdForce)
        self.assertEqual(ticket, 0)

    def test_validWaitOpensBlock(self):
        uuid, (registered, _, ticket, cmdWait, _) = self._register('"wait": 2')
        self.assertTrue(registered)
        self.assertEqual((ticket, cmdWait), (0, 2))
        self.assertEqual(myConfig.deviceQueues[str(uuid)]['blocksByTicket'][0]['bitmask'], 4)


if __name__ == '__main__':
    unittest.main()
