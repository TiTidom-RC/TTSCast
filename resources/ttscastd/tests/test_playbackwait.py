""" Attente de fin de lecture (waitPlaybackEnd) et validation des options wait / force de la file d'attente.
Horloge simulée et faux contrôleur média : aucune attente réelle, aucun appareil.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import threading
import types as pytypes
import unittest
from unittest import mock
from uuid import uuid4

import ttscastd
import waitqueue
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

    def run(self, sessionBefore=None, mediaUrl=URL, contentBefore=None):
        return Functions.waitPlaybackEnd(self.cast, sessionBefore, self.start, '[TEST]', mediaUrl=mediaUrl, contentBefore=contentBefore,
                                         clock=self.clock, sleep=self.sleep)


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
        """ Échec de chargement (code 102) : fin immédiate, warning avec le code expliqué et le fichier du cache, signalement à Jeedom """
        def fail(sc):
            myConfig.loadFailures[str(sc.cast.uuid)] = (sc.now, 102)
        sc = Scenario([(1, fail)])
        cacheUrl = 'http://jeedom/plugins/ttscast/core/php/ttscast.audio.proxy.php?type=tts&file=6f47f866.mp3'
        with self.assertLogs(level='WARNING') as logs:
            self.assertEqual(sc.run(mediaUrl=cacheUrl), 'error')
        self.assertLess(sc.elapsed(), 2)
        self.assertIn('MEDIA_DECODE (fichier audio illisible ou corrompu), code 102 (fichier : 6f47f866.mp3)', logs.output[0])
        sent = [value for key, value in ttscastd.Comm.sendToJeedom.sent if key == 'immediate']
        self.assertEqual(sent, [{'playbackError': {'uuid': str(sc.cast.uuid), 'device': 'Enceinte de test', 'code': 102,
                                                   'codeName': 'MEDIA_DECODE', 'source': 'tts', 'file': '6f47f866.mp3'}}])

    def test_loadFailedUnknownCodeAndStream(self):
        """ Code absent de la table : « code N » ; flux Gemini : pas de fichier désigné (tube temporaire) """
        def fail(sc):
            myConfig.loadFailures[str(sc.cast.uuid)] = (sc.now, 123)
        sc = Scenario([(1, fail)])
        with self.assertLogs(level='WARNING') as logs:
            self.assertEqual(sc.run(mediaUrl='http://jeedom/proxy.php?type=stream&file=pipe123&rate=24000'), 'error')
        self.assertIn('code 123 ::', logs.output[0])
        self.assertNotIn('fichier', logs.output[0])
        error = ttscastd.Comm.sendToJeedom.sent[-1][1]['playbackError']
        self.assertEqual((error['codeName'], error['source'], error['file']), ('', 'stream', ''))

    def test_loadFailedBeforeRequestIgnored(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (3, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        myConfig.loadFailures[str(sc.cast.uuid)] = (sc.start - 50, 102)
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
        """ Même TTS rejoué depuis le cache, même identifiant de session : l'état restant n'est pas pris pour une fin,
        la nouvelle lecture est reconnue dès qu'elle joue """
        sc = Scenario([
            (0, state(media_session_id=7, player_state='IDLE', idle_reason='FINISHED', content_id=URL)),
            (1, state(player_state='PLAYING', idle_reason=None)),
            (5, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        self.assertEqual(sc.run(sessionBefore=7, contentBefore=URL), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 5, delta=0.2)

    def test_sameSessionIdAfterOtherApp(self):
        """ Radio dans une autre application en session 1, TTS très court relancé lui aussi en session 1 (renumérotation au
        lancement de l'application) : reconnu par son URL, fin vue sans état PLAYING observé """
        radio = 'http://radio/flux'
        sc = Scenario([
            (0, state(media_session_id=1, player_state='PLAYING', content_id=radio)),
            (1, state(media_session_id=1, player_state='BUFFERING', content_id=URL)),
            (1.5, state(player_state='IDLE', idle_reason='FINISHED')),
        ])
        self.assertEqual(sc.run(sessionBefore=1, contentBefore=radio), 'finished')
        self.assertLess(sc.elapsed(), 2)

    def test_sameSessionIdAfterOtherAppIdleFirst(self):
        """ Même cas, premier état reçu IDLE sans raison (chargement) : notre lecture est reconnue dès cet état """
        radio = 'http://radio/flux'
        sc = Scenario([
            (0, state(media_session_id=1, player_state='PLAYING', content_id=radio)),
            (1, state(media_session_id=1, player_state='IDLE', content_id=URL)),
            (2, state(player_state='IDLE', idle_reason='FINISHED')),
        ])
        self.assertEqual(sc.run(sessionBefore=1, contentBefore=radio), 'finished')
        self.assertLess(sc.elapsed(), 3)

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

    def test_parseBoolOption(self):
        for value, expected in ((True, True), (False, False), (1, True), (0, False), ('true', True), (' TRUE ', True),
                                ('false', False), ('0', False), ('non', False), ('no', False), (' Off ', False), ('', False), (None, False)):
            with self.subTest(value=value):
                self.assertEqual(Functions.parseBoolOption(value), expected)

    def _register(self, options):
        uuid = uuid4()
        myConfig.NETCAST_DEVICES[uuid] = pytypes.SimpleNamespace(uuid=uuid, name='Enceinte de test')
        return uuid, Functions.socketRegisterQueue(str(uuid), options, 1234, 'TEST')

    def test_invalidWaitQueuedAsAuto(self):
        uuid, (registered, ticket) = self._register('"wait": -1')
        self.assertTrue(registered)
        self.assertEqual((ticket.kind, ticket.number), ('auto', 0))
        queue = myConfig.deviceQueues[str(uuid)]
        self.assertEqual(queue.blocksByPid, {})
        Functions.waitQueueExit(ticket)
        self.assertEqual(queue.serving, 1)

    def test_forceFalseText(self):
        _, (registered, ticket) = self._register('"force": "false"')
        self.assertTrue(registered)
        self.assertEqual((ticket.kind, ticket.number), ('auto', 0))

    def test_validWaitOpensBlock(self):
        uuid, (registered, ticket) = self._register('"wait": 2')
        self.assertTrue(registered)
        self.assertEqual((ticket.kind, ticket.waitValue, ticket.number), ('wait', 2, 0))
        self.assertEqual(myConfig.deviceQueues[str(uuid)].blocksByPid, {1234: 0})

    def test_unknownDeviceNotRegistered(self):
        with self.assertLogs(level='WARNING'):
            self.assertEqual(Functions.socketRegisterQueue(str(uuid4()), '', 1234, 'TEST'), (False, None))


class CommandLoopTest(unittest.TestCase):
    """ Boucle des commandes (eventsFromJeedom) : un message invalide est écarté, la boucle continue """
    def setUp(self):
        helpers.resetDaemonState()
        self.addCleanup(setattr, myConfig, 'IS_ENDING', False)

    def test_invalidMessagesDoNotStopLoop(self):
        handled = []
        socketQueue = ttscastd.JEEDOM_SOCKET_MESSAGE
        with mock.patch.object(Functions, 'purgeCache', side_effect=lambda *a: handled.append(True)), \
                mock.patch.object(myConfig, 'apiKey', 'cle-de-test'), self.assertLogs(level='ERROR') as logs:
            for raw in (b'{"cmd": "action"}', b'[1, 2]', b'{"apikey": "cle-de-test"}', b'pas du json',
                        b'{"cmd": "purgettscache", "apikey": "cle-de-test"}'):
                socketQueue.put(raw)
            loop = threading.Thread(target=ttscastd.Loops.eventsFromJeedom, args=(0.05,), daemon=True)
            loop.start()
            self.assertTrue(helpers.waitUntil(lambda: handled))
            myConfig.IS_ENDING = True
            loop.join(2)
        self.assertFalse(loop.is_alive())
        self.assertEqual(len(logs.output), 4)


class ForceCutTest(unittest.TestCase):
    """ force : la boucle des commandes ne fait que prendre le ticket ; la diffusion en cours est coupée par le thread de la notification """
    def setUp(self):
        helpers.resetDaemonState()
        myConfig.deviceQueues = {}

    def addPlayingCast(self, quitApp=None):
        uuid = uuid4()
        cast = pytypes.SimpleNamespace(uuid=uuid, name='Enceinte de test', status=pytypes.SimpleNamespace(app_id='CC1AD845'))
        cast.quit_app = mock.Mock(side_effect=quitApp or (lambda: setattr(cast.status, 'app_id', None)))
        myConfig.NETCAST_DEVICES[uuid] = cast
        return uuid, cast

    def test_registrationDoesNotWaitForDevice(self):
        uuid, cast = self.addPlayingCast()
        registered, ticket = Functions.socketRegisterQueue(str(uuid), '"force": true', 1234, 'TEST')
        self.assertTrue(registered)
        self.assertEqual(ticket.kind, 'force')
        cast.quit_app.assert_not_called()
        self.assertTrue(myConfig.deviceQueues[str(uuid)].isActive(), 'file gelée dès l\'enregistrement')

    def test_forceCutQuitsCurrentApp(self):
        uuid, cast = self.addPlayingCast()
        Functions.forceCut(str(uuid))
        cast.quit_app.assert_called_once()

    def test_forceCutFailureLoggedAndNotRaised(self):
        uuid, cast = self.addPlayingCast(quitApp=ConnectionError('enceinte injoignable'))
        with self.assertLogs(level='WARNING') as logs:
            Functions.forceCut(str(uuid))
        self.assertIn('diffusion en cours non coupée', logs.output[0])

    def test_cutAtTurnOnly(self):
        """ La coupure est faite au tour de la notification : un force qui échoue avant (moteur refusé) ne coupe rien ;
        controllerActions coupe à son tour ; les tickets sont libérés à la sortie """
        uuid, _ = self.addPlayingCast()
        with mock.patch.object(Functions, 'forceCut') as forceCut, mock.patch.object(myConfig, 'geminiTTSEnabled', False), \
                mock.patch.object(myConfig, 'geminiTTSDefault', False), self.assertLogs(level='ERROR'):
            args = Functions.socketRegisterQueue(str(uuid), '"force": true', 1234, 'TTS')
            self.assertFalse(ttscastd.TTSCast.getTTS('Bonjour', str(uuid), 'voix', 'voix', 'Achird', 'fr-FR', 'gcloudtts', 'piper', '1.0', '0',
                                                      '"engine": "geminitts", "force": true', 0, *args))
            forceCut.assert_not_called()
        self.assertFalse(myConfig.deviceQueues[str(uuid)].isActive(), 'ticket libéré')
        with mock.patch.object(Functions, 'forceCut') as forceCut:
            args = Functions.socketRegisterQueue(str(uuid), '"force": true', 1234, 'media')
            self.assertTrue(Functions.controllerActions(str(uuid), 'aucune', '', '"force": true', *args))
            forceCut.assert_called_once_with(str(uuid))
        self.assertFalse(myConfig.deviceQueues[str(uuid)].isActive(), 'ticket libéré')


class GeminiStreamNoReaderTest(unittest.TestCase):
    """ Flux Gemini sans lecteur sur le tube : erreur, sauf si la notification a été abandonnée par la file (debug) """
    def runWithoutReader(self, ticket):
        clock = iter(range(0, 100))
        with mock.patch.object(ttscastd.os, 'O_NONBLOCK', 0, create=True), \
                mock.patch.object(ttscastd.os, 'open', side_effect=OSError(ttscastd.errno.ENXIO, 'pas de lecteur')), \
                mock.patch.object(ttscastd.time, 'time', side_effect=lambda: next(clock) * 5.0), \
                mock.patch.object(ttscastd.time, 'sleep'):
            return ttscastd.TTSCast.geminiTTSStream(iter([]), b'\x00\x00', 24000, 1, '/tmp/tube-absent', queueTicket=ticket)

    def test_errorWhenNotificationActive(self):
        ticket = waitqueue.DeviceQueue('enceinte-test', myConfig).register('auto', 'TTS')
        with self.assertLogs(level='ERROR'):
            self.assertIsNone(self.runWithoutReader(ticket))

    def test_debugWhenNotificationAbandoned(self):
        ticket = waitqueue.DeviceQueue('enceinte-test', myConfig).register('auto', 'TTS')
        ticket.state = waitqueue.ORPHANED
        with self.assertNoLogs(level='ERROR'):
            self.assertIsNone(self.runWithoutReader(ticket))


class DashCastForceDisplayTest(unittest.TestCase):
    """ DashCast : « force_display » force l'affichage de la page ; « force » est la priorité de la file, comme pour les autres commandes """
    def setUp(self):
        helpers.resetDaemonState()
        myConfig.deviceQueues = {}

    def display(self, options):
        player = mock.Mock()
        cast = mock.Mock(status=pytypes.SimpleNamespace(app_id=None))
        with mock.patch.object(ttscastd.dashcast, 'DashCastController', return_value=player), \
                mock.patch.object(Functions, 'trackPluginSession'), mock.patch.object(ttscastd.time, 'sleep'):
            self.assertTrue(Functions.controllerDashCast(cast, str(uuid4()), 'https://exemple.fr', options))
        return player.load_url.call_args.kwargs['force']

    def ticketKind(self, options):
        uuid = uuid4()
        myConfig.NETCAST_DEVICES[uuid] = pytypes.SimpleNamespace(uuid=uuid, name='Nest Hub de test')
        return Functions.socketRegisterQueue(str(uuid), options, 1234, 'dashcast')[1].kind

    def test_forceDisplayOnly(self):
        self.assertTrue(self.display('"force_display": true'))
        self.assertEqual(self.ticketKind('"force_display": true'), 'auto')

    def test_forceIsQueuePriorityOnly(self):
        self.assertFalse(self.display('"force": true'))
        self.assertEqual(self.ticketKind('"force": true'), 'force')

    def test_bothOptions(self):
        self.assertTrue(self.display('"force": true, "force_display": true'))
        self.assertEqual(self.ticketKind('"force": true, "force_display": true'), 'force')

    def test_noOption(self):
        self.assertFalse(self.display(None))
        self.assertFalse(self.display('"force_display": "false"'))

    def test_quitAppTextOption(self):
        """ Option booléenne écrite en texte : "false" vaut faux """
        for options, expected in (('"quit_app": "false"', False), ('"quit_app": true', True)):
            cast = mock.Mock(status=pytypes.SimpleNamespace(app_id=None))
            with self.subTest(options=options), mock.patch.object(ttscastd.dashcast, 'DashCastController', return_value=mock.Mock()), \
                    mock.patch.object(Functions, 'trackPluginSession'), mock.patch.object(ttscastd.time, 'sleep'):
                Functions.controllerDashCast(cast, str(uuid4()), 'https://exemple.fr', options)
                self.assertEqual(cast.quit_app.called, expected)

    def test_orphanedCommandNotLaunched(self):
        """ Commande déclarée bloquée par la file pendant son lancement : la page n'est pas chargée """
        queue = waitqueue.DeviceQueue('enceinte-test', myConfig)
        ticket = queue.register('auto', 'dashcast')
        self.assertTrue(queue.hold(ticket))
        self.addCleanup(waitqueue._setCurrent, None)
        ticket.state = waitqueue.ORPHANED
        player = mock.Mock()
        with mock.patch.object(ttscastd.dashcast, 'DashCastController', return_value=player), mock.patch.object(ttscastd.time, 'sleep'):
            self.assertFalse(Functions.controllerDashCast(mock.Mock(status=pytypes.SimpleNamespace(app_id=None)), str(uuid4()),
                                                         'https://exemple.fr', '"force_display": true'))
        player.load_url.assert_not_called()


class PlaybackWithQueueTest(unittest.TestCase):
    """ waitPlaybackEnd avec la notification de la file d'attente du thread courant """
    def setUp(self):
        helpers.resetDaemonState()
        self.saved = (myConfig.cmdWaitTimeout, myConfig.playbackStatusRefresh)
        myConfig.cmdWaitTimeout = TIMEOUT
        myConfig.playbackStatusRefresh = REFRESH
        self.queue = waitqueue.DeviceQueue('enceinte-test', myConfig)
        self.ticket = self.queue.register('auto', 'TTS')
        self.assertTrue(self.queue.hold(self.ticket))
        self.addCleanup(self.queue.release, self.ticket)

    def tearDown(self):
        myConfig.cmdWaitTimeout, myConfig.playbackStatusRefresh = self.saved

    def test_orphanedStopsFollowing(self):
        def orphan(sc):
            self.ticket.state = waitqueue.ORPHANED
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (3, orphan),
        ], playingResponder)
        self.assertEqual(sc.run(), 'orphaned')
        self.assertLess(sc.elapsed(), 4)

    def test_progressPushesQueueDeadline(self):
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING')),
            (300, state(player_state='IDLE', idle_reason='FINISHED')),
        ], playingResponder)
        self.assertEqual(sc.run(), 'finished')
        self.assertEqual(self.ticket.phase, 'lecture')
        self.assertGreater(self.ticket.deadline, sc.start + 290)

    def streamEnd(self, audioSeconds):
        """ Fin de l'envoi d'un flux live de audioSeconds secondes d'audio (comme geminiTTSStream) """
        def action(sc):
            self.ticket.streamAudioSeconds = audioSeconds
            self.ticket.streamEndedAt = sc.now
        return action

    def test_liveStreamLongerThanTimeoutNotCut(self):
        """ Flux de 90 s envoyé en 30 s (génération plus rapide que la lecture) : lu jusqu'au bout """
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING', stream_type='LIVE')),
            (30, self.streamEnd(90)),
            (90.5, state(player_state='IDLE', idle_reason='FINISHED')),
        ], lambda sc: sc.mc.apply(current_time=0.0))
        self.assertEqual(sc.run(), 'finished')
        self.assertAlmostEqual(sc.elapsed(), 90.5, delta=0.2)

    def test_liveStreamStuckAfterAudio(self):
        """ Flux de 40 s entièrement lu, mais l'enceinte reste en lecture : arrêt au bout du délai après la fin de l'audio """
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING', stream_type='LIVE')),
            (20, self.streamEnd(40)),
        ], lambda sc: sc.mc.apply(current_time=0.0))
        with self.assertLogs(level='WARNING') as logs:
            self.assertEqual(sc.run(), 'stalled')
        self.assertAlmostEqual(sc.elapsed(), 0.5 + 40 + TIMEOUT, delta=0.3)
        self.assertIn('après la fin de l\'audio (40s)', logs.output[0])

    def test_liveStreamLateStreamEnd(self):
        """ Génération plus lente que la lecture (enceinte en lecture pendant les creux) : pas d'arrêt avant le délai après la fin de l'envoi """
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING', stream_type='LIVE')),
            (60, self.streamEnd(10)),
        ], lambda sc: sc.mc.apply(current_time=0.0))
        with self.assertLogs(level='WARNING'):
            self.assertEqual(sc.run(), 'stalled')
        self.assertAlmostEqual(sc.elapsed(), 60 + TIMEOUT, delta=0.3)

    def test_liveStreamPauseNotCounted(self):
        """ Pause pendant un flux : le temps en pause ne compte pas dans le temps de lecture """
        sc = Scenario([
            (0.5, state(media_session_id=7, player_state='PLAYING', stream_type='LIVE')),
            (10, state(player_state='PAUSED')),
            (10 + TIMEOUT - 2, state(player_state='PLAYING')),
            (20, self.streamEnd(40)),
        ], lambda sc: sc.mc.apply(current_time=0.0))
        with self.assertLogs(level='WARNING'):
            self.assertEqual(sc.run(), 'stalled')
        self.assertAlmostEqual(sc.elapsed(), 0.5 + 40 + TIMEOUT + (TIMEOUT - 2), delta=0.3)


if __name__ == '__main__':
    unittest.main()
