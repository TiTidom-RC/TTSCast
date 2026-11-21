""" Lancement d'une lecture (castQuickPlay : délai borné, lecture suivie si elle a démarré malgré l'absence de réponse), type du média
et récepteur de la commande Media. Faux appareils et faux serveur : aucun appareil ni réseau réel.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import threading
import time
import types as pytypes
import unittest
from unittest import mock

import requests
from pychromecast.error import RequestFailed, RequestTimeout

import ttscastd
from tests import helpers

Functions = ttscastd.Functions
myConfig = ttscastd.myConfig
URL = 'http://jeedom/media/morceau.mp3'


def fakeCast(castType='audio', contentId=None, playerState='UNKNOWN'):
    status = pytypes.SimpleNamespace(content_id=contentId, player_state=playerState, media_session_id=None)
    cast = mock.Mock(status=pytypes.SimpleNamespace(volume_level=0.4), cast_info=pytypes.SimpleNamespace(cast_type=castType))
    cast.name = 'Enceinte de test'
    cast.media_controller.status = status
    return cast


def response(status=200, contentType=None):
    resp = mock.MagicMock(status_code=status, ok=200 <= status < 400, headers={} if contentType is None else {'Content-Type': contentType})
    resp.__enter__.return_value = resp
    return resp


class CastQuickPlayTest(unittest.TestCase):
    def setUp(self):
        helpers.resetDaemonState()

    def test_launchBoundedByCastLaunchTimeout(self):
        cast = fakeCast()
        with mock.patch.object(ttscastd.quick_play, 'quick_play') as quickPlay:
            Functions.castQuickPlay(cast, 'default_media_receiver', {'media_id': URL}, '[TEST]')
        quickPlay.assert_called_once_with(cast, 'default_media_receiver', {'media_id': URL}, timeout=myConfig.castLaunchTimeout)

    def test_timeoutButMediaPlaying(self):
        """ Pas de réponse dans le délai, mais l'enceinte lit le média : la lecture est suivie normalement """
        cast = fakeCast(contentId=URL, playerState='PLAYING')
        with mock.patch.object(ttscastd.quick_play, 'quick_play', side_effect=RequestTimeout('quick play', 15)), \
                self.assertLogs(level='INFO') as logs:
            Functions.castQuickPlay(cast, 'default_media_receiver', {'media_id': URL}, '[TEST]')
        self.assertIn('Pas de réponse', logs.output[0])
        self.assertIn('Lecture démarrée', logs.output[1])

    def test_timeoutAndNotStarted(self):
        cast = fakeCast(contentId='http://jeedom/autre.mp3', playerState='PLAYING')
        with mock.patch.object(ttscastd.quick_play, 'quick_play', side_effect=RequestTimeout('quick play', 15)), \
                self.assertLogs(level='WARNING') as logs, self.assertRaises(ttscastd.CastLaunchFailed):
            Functions.castQuickPlay(cast, 'default_media_receiver', {'media_id': URL}, '[TEST]')
        self.assertIn('Lecture non démarrée', logs.output[-1])

    def test_launchRefused(self):
        """ Lancement refusé par l'enceinte (ou connexion perdue) : rien n'a été envoyé, lecture non démarrée """
        cast = fakeCast()
        with mock.patch.object(ttscastd.quick_play, 'quick_play', side_effect=RequestFailed('quick play')), \
                self.assertLogs(level='WARNING') as logs, self.assertRaises(ttscastd.CastLaunchFailed):
            Functions.castQuickPlay(cast, 'default_media_receiver', {'media_id': URL}, '[TEST]')
        self.assertIn('refusé', logs.output[0])

    def test_idleMediaIsNotStarted(self):
        cast = fakeCast(contentId=URL, playerState='IDLE')
        self.assertFalse(Functions.mediaStarted(cast, URL))
        self.assertFalse(Functions.mediaStarted(fakeCast(contentId=None, playerState='PLAYING'), None))


class MediaMimeTypeTest(unittest.TestCase):
    def setUp(self):
        helpers.resetDaemonState()

    def mimeType(self, url, castType='audio', head=None, get=None):
        error = head if isinstance(head, Exception) else None
        with mock.patch.object(ttscastd.requests, 'head', side_effect=error, return_value=None if error else head) as headCall, \
                mock.patch.object(ttscastd.requests, 'get', return_value=get) as getCall:
            result = Functions.mediaMimeType(url, fakeCast(castType), '[TEST]')
        return result, headCall, getCall

    def test_knownExtensionWithoutRequest(self):
        result, head, _ = self.mimeType('http://jeedom/media/morceau.MP3?token=abc')
        self.assertEqual(result, 'audio/mpeg')
        head.assert_not_called()
        self.assertEqual(self.mimeType('http://jeedom/film.mp4')[0], 'video/mp4')
        self.assertEqual(self.mimeType('http://serveur/flux/index.m3u8')[0], 'application/x-mpegURL')

    def test_typeServedForUnknownExtension(self):
        """ URL sans extension de média (proxy .php, service) : type annoncé par le serveur, paramètres retirés """
        result, head, _ = self.mimeType('http://jeedom/plugins/ttscast/core/php/ttscast.audio.proxy.php?type=tts&file=a.mp3',
                                        head=response(contentType='Audio/MPEG; charset=binary'))
        self.assertEqual(result, 'audio/mpeg')
        self.assertTrue(head.call_args.kwargs['allow_redirects'])
        self.assertEqual(head.call_args.kwargs['timeout'], myConfig.mediaProbeTimeout)

    def test_getWhenHeadRefused(self):
        result, _, get = self.mimeType('http://serveur/video', head=response(405), get=response(contentType='video/webm'))
        self.assertEqual(result, 'video/webm')
        self.assertTrue(get.call_args.kwargs['stream'])

    def test_fallbackByDevice(self):
        """ Rien de fiable (serveur injoignable, réponse en erreur, type non média) : audio sur une enceinte ou un groupe, vidéo sur un écran """
        cases = (
            (requests.ConnectionError('injoignable'), 'audio', 'audio/mpeg'),
            (response(404, 'text/html'), 'group', 'audio/mpeg'),
            (response(contentType='application/octet-stream'), 'cast', 'video/mp4'),
            (response(contentType='text/html'), 'cast', 'video/mp4'),
        )
        for head, castType, expected in cases:
            with self.subTest(head=head, castType=castType), self.assertLogs(level='WARNING') as logs:
                self.assertEqual(self.mimeType('http://serveur/lecture', castType, head=head)[0], expected)
            self.assertIn('précisez l\'option type', logs.output[0])


class MediaReceiverTest(unittest.TestCase):
    """ Commande Media : récepteur Google Cast par défaut, BubbleUPnP avec l'option app ; type déduit ou imposé par l'option type """
    def setUp(self):
        helpers.resetDaemonState()

    def play(self, options, url=URL, launch=None, start='started'):
        cast = fakeCast()
        with mock.patch.object(Functions, 'castQuickPlay', side_effect=launch) as castQuickPlay, \
                mock.patch.object(Functions, 'confirmPlaybackStart', **({'side_effect': start} if isinstance(start, Exception) else {'return_value': start})), \
                mock.patch.object(Functions, 'checkIfDashCast'), mock.patch.object(Functions, 'getGroupSnapshot', return_value={}), \
                mock.patch.object(Functions, 'trackPluginSession'), mock.patch.object(myConfig, 'appDisableDing', False):
            result = Functions.controllerMedia(cast, 'uuid-test', url, options)
        return result, castQuickPlay, cast

    def launched(self, castQuickPlay):
        _, appName, appData, _ = castQuickPlay.call_args.args
        return appName, appData['media_type'], appData['metadata']['metadataType']

    def test_defaultReceiverAndDetectedType(self):
        result, castQuickPlay, _ = self.play(None)
        self.assertTrue(result)
        self.assertEqual(self.launched(castQuickPlay), ('default_media_receiver', 'audio/mpeg', 3))

    def test_bubbleUpnpOption(self):
        self.assertEqual(self.launched(self.play('"app": "BubbleUPnP"')[1])[0], 'bubbleupnp')

    def test_unknownAppOption(self):
        with self.assertLogs(level='WARNING') as logs:
            castQuickPlay = self.play('"app": "vlc"')[1]
        self.assertEqual(self.launched(castQuickPlay)[0], 'default_media_receiver')
        self.assertIn('Option app inconnue', logs.output[0])

    def test_typeOptionWins(self):
        castQuickPlay = self.play('"type": "video/mp4"')[1]
        self.assertEqual(self.launched(castQuickPlay)[1:], ('video/mp4', 1))

    def test_displayedMetadataLikeSounds(self):
        """ Écran de l'équipement, comme pour les sons : titre « TTSCast Media », nom du fichier en artiste et en sous-titre ; jamais
        l'URL (jeton ou identifiants possibles) """
        url = 'http://user:secret@nas/Musique/Mon%20morceau.mp3?token=abc'
        metadata = self.play(None, url=url)[1].call_args.args[2]['metadata']
        self.assertEqual((metadata['title'], metadata['subtitle'], metadata['artist'], metadata['albumName']),
                         ('TTSCast Media', 'Mon morceau.mp3', 'Mon morceau.mp3', 'Jeedom'))
        self.assertNotIn('secret', str(metadata))
        self.assertNotIn('token', str(metadata))

    def test_noFileNameNoArtist(self):
        metadata = self.play(None, url='http://serveur/flux/direct', launch=None)[1].call_args.args[2]['metadata']
        self.assertEqual(metadata['title'], 'TTSCast Media')
        self.assertNotIn('artist', metadata)
        self.assertNotIn('subtitle', metadata)

    def test_fileNameFromMediaFileOnly(self):
        """ Nom tiré d'un vrai fichier de média (chemin, sinon paramètre de l'URL) ; jamais un morceau d'URL """
        cases = (
            ('http://jeedom/plugins/ttscast/core/php/ttscast.audio.proxy.php?type=sounds&file=bigben1.mp3', 'bigben1.mp3'),
            ('http://nas/stream.php?id=12&path=%2FMusique%2FMon%20morceau.flac', 'Mon morceau.flac'),
            ('http://jeedom/plugins/ttscast/core/php/ttscast.audio.proxy.php?type=sounds', None),
            ('http://serveur/flux/direct', None),
            ('http://serveur/', None),
            ('http://serveur', None),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                self.assertEqual(Functions.mediaFileName(url), expected)

    def test_launchFailedRestoresVolume(self):
        """ Lecture non démarrée : déjà signalée par castQuickPlay, pas d'erreur en plus ; volume rétabli, commande en échec """
        with self.assertNoLogs(level='ERROR'):
            result, _, cast = self.play('"volume": 30', launch=ttscastd.CastLaunchFailed('pas de réponse'))
        self.assertFalse(result)
        self.assertEqual(cast.set_volume.call_args_list, [mock.call(volume=0.3), mock.call(volume=0.4)])


    def test_playbackFailedAfterLaunch(self):
        """ Échec juste après le lancement (signalé par confirmPlaybackStart) : volume rétabli, commande en échec, pas d'erreur en plus """
        with self.assertNoLogs(level='ERROR'):
            result, _, cast = self.play('"volume": 30', start=ttscastd.CastLaunchFailed('lecture en échec'))
        self.assertFalse(result)
        self.assertEqual(cast.set_volume.call_args_list, [mock.call(volume=0.3), mock.call(volume=0.4)])

    def test_unconfirmedStartIsNotAnError(self):
        with self.assertLogs(level='INFO') as logs:
            result = self.play(None, start='unconfirmed')[0]
        self.assertTrue(result)
        self.assertTrue(any('démarrage non confirmé' in line for line in logs.output))
        self.assertFalse(any('Diffusion Media lancée' in line for line in logs.output))


class FakeSessionEvent:
    """ Événement « session active » sur une horloge simulée : wait(secondes) fait avancer l'horloge et applique les actions datées,
    sans dépasser l'instant où la session devient active (réveil immédiat, comme threading.Event) """
    def __init__(self, test):
        self.test = test
        self.active = False

    def set(self):
        self.active = True

    def wait(self, seconds):
        end = self.test.now + seconds
        while not self.active and self.test.now < end - 1e-9:
            self.test.now = min(end, self.test.now + 0.01)
            for at in sorted(list(self.test.actions)):
                if self.test.now >= at - 1e-9:
                    self.test.actions.pop(at)()
        return self.active


class WaitMediaActiveTest(unittest.TestCase):
    """ Attente de la session média après le lancement : réveil immédiat dès la session active (comme block_until_active), ou arrêt
    dès un échec de chargement (LOAD_FAILED, sans session) postérieur à la demande ; au plus mediaActivationTimeout secondes """
    def setUp(self):
        helpers.resetDaemonState()
        self.now = 10.0
        self.actions = {}
        self.event = FakeSessionEvent(self)
        self.cast = pytypes.SimpleNamespace(uuid='uuid-test', media_controller=pytypes.SimpleNamespace(session_active_event=self.event))

    def wait(self):
        Functions.waitMediaActive(self.cast, 10.0, clock=lambda: self.now)
        return self.now - 10.0

    def test_realEventWakesUpAtOnce(self):
        """ Avec un vrai threading.Event : retour dès qu'un autre thread signale la session active """
        event = threading.Event()
        cast = pytypes.SimpleNamespace(uuid='uuid-test', media_controller=pytypes.SimpleNamespace(session_active_event=event))
        threading.Timer(0.05, event.set).start()
        startedAt = time.monotonic()
        Functions.waitMediaActive(cast, startedAt)
        self.assertLess(time.monotonic() - startedAt, 0.5)

    def test_sessionAlreadyActive(self):
        self.event.set()
        self.assertEqual(self.wait(), 0)

    def test_stopsWhenSessionBecomesActive(self):
        self.actions[11.03] = self.event.set
        self.assertAlmostEqual(self.wait(), 1.03, delta=0.011)

    def test_stopsOnLoadFailedWithoutSession(self):
        """ LOAD_FAILED : aucune session ne viendra, pas d'attente du délai complet """
        self.actions[10.3] = lambda: myConfig.loadFailures.__setitem__('uuid-test', (10.3, 102))
        self.assertAlmostEqual(self.wait(), 0.3, delta=0.11)

    def test_oldLoadFailedIgnored(self):
        myConfig.loadFailures['uuid-test'] = (5.0, 102)
        self.actions[12.0] = self.event.set
        self.assertAlmostEqual(self.wait(), 2.0, delta=0.11)

    def test_boundedByActivationTimeout(self):
        self.assertAlmostEqual(self.wait(), myConfig.mediaActivationTimeout, delta=0.11)


class ConfirmPlaybackStartTest(unittest.TestCase):
    """ Démarrage d'une lecture longue : arrêt au premier état qui tranche, au plus mediaStartCheckTimeout secondes """
    def setUp(self):
        self.comm = helpers.resetDaemonState()
        self.now = 0.0
        self.status = pytypes.SimpleNamespace(content_id='http://avant/autre.mp3', media_session_id=1, player_state='IDLE', idle_reason='FINISHED')
        self.cast = pytypes.SimpleNamespace(uuid='uuid-test', name='Enceinte de test', media_controller=pytypes.SimpleNamespace(status=self.status))
        self.events = {}

    def sleep(self, seconds):
        self.now += seconds
        for at in sorted(list(self.events)):
            if self.now >= at:
                self.events.pop(at)(self.status)

    def confirm(self, sessionBefore=1, contentBefore='http://avant/autre.mp3', source='media', name='morceau.mp3'):
        return Functions.confirmPlaybackStart(self.cast, URL, 0.0, sessionBefore, contentBefore, '[TEST]', source, name,
                                              clock=lambda: self.now, sleep=self.sleep)

    @staticmethod
    def state(**changes):
        return lambda status: status.__dict__.update(changes)

    def test_stopsAtFirstPlayingState(self):
        self.events[0.3] = self.state(content_id=URL, media_session_id=2, player_state='BUFFERING', idle_reason=None)
        self.assertEqual(self.confirm(), 'started')
        self.assertLess(self.now, 0.5)

    def test_veryShortFileAlreadyFinished(self):
        """ Fichier très court, déjà terminé quand la vérification commence : démarré, sans attendre le délai """
        self.status.__dict__.update(content_id=URL, media_session_id=2, player_state='IDLE', idle_reason='FINISHED')
        self.assertEqual(self.confirm(), 'started')
        self.assertEqual(self.now, 0.0)

    def test_previousPlaybackOfSameMediaIgnored(self):
        """ Même média rejoué : l'état final de la lecture précédente n'est pas pris pour la nouvelle """
        self.status.__dict__.update(content_id=URL, media_session_id=1, player_state='IDLE', idle_reason='FINISHED')
        self.events[0.5] = self.state(player_state='PLAYING', idle_reason=None)
        self.assertEqual(self.confirm(sessionBefore=1, contentBefore=URL), 'started')
        self.assertAlmostEqual(self.now, 0.5, delta=0.11)

    def test_errorWithoutCodeReported(self):
        self.events[0.2] = self.state(content_id=URL, media_session_id=2, player_state='IDLE', idle_reason='ERROR')
        with self.assertLogs(level='WARNING') as logs, self.assertRaises(ttscastd.CastLaunchFailed):
            self.confirm()
        self.assertIn('(fichier : morceau.mp3)', logs.output[0])
        self.assertEqual(self.comm.sent[-1][1]['playbackError']['source'], 'media')
        self.assertEqual(self.comm.sent[-1][1]['playbackError']['file'], 'morceau.mp3')

    def test_loadFailedWithCodeReported(self):
        myConfig.loadFailures['uuid-test'] = (0.1, 104)
        with self.assertLogs(level='WARNING') as logs, self.assertRaises(ttscastd.CastLaunchFailed):
            self.confirm(source='radios', name='FIP')
        self.assertIn('MEDIA_SRC_NOT_SUPPORTED', logs.output[0])
        self.assertIn('(radio : FIP)', logs.output[0])
        error = self.comm.sent[-1][1]['playbackError']
        self.assertEqual((error['code'], error['source'], error['file']), (104, 'radios', 'FIP'))

    def test_oldLoadFailureIgnored(self):
        myConfig.loadFailures['uuid-test'] = (-5.0, 102)
        self.events[0.2] = self.state(content_id=URL, media_session_id=2, player_state='PLAYING', idle_reason=None)
        self.assertEqual(self.confirm(), 'started')

    def test_noDecisiveStateIsUnconfirmed(self):
        """ Rien de décisif dans le délai : pas d'alerte (l'état réel est remonté par le suivi temps réel) """
        with self.assertNoLogs(level='WARNING'):
            self.assertEqual(self.confirm(), 'unconfirmed')
        self.assertAlmostEqual(self.now, myConfig.mediaStartCheckTimeout, delta=0.11)
        self.assertEqual(self.comm.sent, [])


if __name__ == '__main__':
    unittest.main()
