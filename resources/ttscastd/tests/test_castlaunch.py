""" Lancement d'une lecture (castQuickPlay : délai borné, lecture suivie si elle a démarré malgré l'absence de réponse), type du média
et récepteur de la commande Media. Faux appareils et faux serveur : aucun appareil ni réseau réel.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

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
    status = pytypes.SimpleNamespace(content_id=contentId, player_state=playerState)
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

    def play(self, options, url=URL, launch=None):
        cast = fakeCast()
        with mock.patch.object(Functions, 'castQuickPlay', side_effect=launch) as castQuickPlay, \
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

    def test_displayedMetadataWithoutUrl(self):
        """ Écran de l'équipement : titre tiré du nom du fichier, jamais l'URL (jeton ou identifiants possibles) """
        url = 'http://user:secret@nas/Musique/Mon%20morceau.mp3?token=abc'
        metadata = self.play(None, url=url)[1].call_args.args[2]['metadata']
        self.assertEqual((metadata['title'], metadata['subtitle'], metadata['artist']), ('Mon morceau', 'TTSCast Media', 'TTSCast Media'))
        self.assertNotIn('secret', str(metadata))
        self.assertNotIn('token', str(metadata))

    def test_titleWithoutFileName(self):
        self.assertEqual(Functions.mediaTitle('http://serveur/'), 'TTSCast Media')
        self.assertEqual(Functions.mediaTitle('http://serveur'), 'TTSCast Media')
        self.assertEqual(Functions.mediaTitle('http://serveur/flux/direct'), 'direct')

    def test_launchFailedRestoresVolume(self):
        """ Lecture non démarrée : déjà signalée par castQuickPlay, pas d'erreur en plus ; volume rétabli, commande en échec """
        with self.assertNoLogs(level='ERROR'):
            result, _, cast = self.play('"volume": 30', launch=ttscastd.CastLaunchFailed('pas de réponse'))
        self.assertFalse(result)
        self.assertEqual(cast.set_volume.call_args_list, [mock.call(volume=0.3), mock.call(volume=0.4)])


if __name__ == '__main__':
    unittest.main()
