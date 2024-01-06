# This file is part of Jeedom.
#
# Jeedom is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jeedom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jeedom. If not, see <http://www.gnu.org/licenses/>.

import logging
import shutil
import sys
import os
import time
import traceback
import signal
import json
import argparse
from urllib.parse import urljoin

try:
    from jeedom.jeedom import *
except ImportError:
    print("[DAEMON][IMPORT] Error: importing module jeedom.jeedom")
    sys.exit(1)

# Import pour PyChromeCast

import hashlib
try:    
    from google.oauth2 import service_account
    import google.cloud.texttospeech as tts
    import pychromecast
    from pychromecast import quick_play
except ImportError:
    print("[DAEMON][IMPORT] Error: importing module TTS")
    sys.exit(1)

# ***** GLOBALS VAR *****

KNOWN_DEVICES = {}
NOWPLAYING_DEVICES = {}
GCAST_DEVICES = {}

TTS_CACHEFOLDER = 'data/cache'
TTS_CACHEFOLDERWEB = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), TTS_CACHEFOLDER))
TTS_CACHEFOLDERTMP = os.path.join('/tmp/jeedom/', 'ttscast_cache')
TTS_WEBSRVCACHE = ''
TTS_WEBSRVMEDIA = ''

GCLOUDAPIKEY = ''

MEDIA_FOLDER = 'data/media'
MEDIA_FULLPATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), MEDIA_FOLDER))

CONFIG_FOLDER = 'core/config'
CONFIG_FULLPATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), CONFIG_FOLDER))

# ***** END GLOBALS VAR *****


def read_socket():
    global JEEDOM_SOCKET_MESSAGE
    if not JEEDOM_SOCKET_MESSAGE.empty():
        logging.debug("[DAEMON][READ-SOCKET] Message received in socket JEEDOM_SOCKET_MESSAGE")
        message = json.loads(JEEDOM_SOCKET_MESSAGE.get().decode('utf-8'))
        if message['apikey'] != _apikey:
            logging.error("[DAEMON][READ-SOCKET] Invalid apikey from socket :: %s", message)
            return
        try:
            # TODO ***** Gestion des messages reçus de Jeedom *****
            if message['cmd'] == 'purgettscache':
                logging.debug('[DAEMON][SOCKET-READ] Purge TTS Cache')
                if 'days' in message:
                    purgeCache(message['days'])
                else:
                    purgeCache()
            elif message['cmd'] == 'playtesttts':
                logging.debug('[DAEMON][SOCKET-READ] Generate And Play Test TTS')
                if all(keys in message for keys in ('ttsText', 'ttsGoogleName', 'ttsVoiceName')):
                    logging.debug('[DAEMON][SOCKET-READ] Test TTS :: %s', message['ttsText'] + ' | ' + message['ttsGoogleName'] + ' | ' + message['ttsVoiceName'])
                    generateTestTTS(message['ttsText'], message['ttsGoogleName'], message['ttsVoiceName'])
                else:
                    logging.debug('[DAEMON][SOCKET-READ] Test TTS :: Il manque des données pour traiter la commande.')
        except Exception as e:
            logging.error('[DAEMON][READ-SOCKET] Send command to daemon error :: %s', e)


def listen(cycle=0.3):
    jeedom_socket.open()
    try:
        while 1:
            time.sleep(cycle)
            read_socket()
    except KeyboardInterrupt:
        shutdown()

# ----------------------------------------------------------------------------


def generateTestTTS(ttsText, ttsGoogleName, ttsVoiceName):
    logging.debug('[DAEMON][TestTTS] Check des répertoires')
    cachePath = TTS_CACHEFOLDERWEB
    symLinkPath = TTS_CACHEFOLDERTMP
    ttsSrvWeb = TTS_WEBSRVCACHE
    
    try:
        os.stat(symLinkPath)
    except Exception:
        os.mkdir(symLinkPath)
    try:
        os.stat(cachePath)
    except Exception:
        os.symlink(symLinkPath, cachePath)
    
    logging.debug('[DAEMON][TestTTS] Import de la clé API :: ' + GCLOUDAPIKEY)
    if GCLOUDAPIKEY != 'noKey':
        credentials = service_account.Credentials.from_service_account_file(os.path.join(CONFIG_FULLPATH, GCLOUDAPIKEY))

        logging.debug('[DAEMON][TestTTS] Test et génération du fichier TTS (mp3)')
        raw_filename = ttsText + "|" + ttsVoiceName
        filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
        filepath = os.path.join(symLinkPath, filename)
        
        logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
        
        if not os.path.isfile(filepath):
            language_code = "-".join(ttsVoiceName.split("-")[:2])
            text_input = tts.SynthesisInput(text=ttsText)
            voice_params = tts.VoiceSelectionParams(language_code=language_code, name=ttsVoiceName)
            audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3, effects_profile_id=['small-bluetooth-speaker-class-device'])

            client = tts.TextToSpeechClient(credentials=credentials)
            response = client.synthesize_speech(input=text_input, voice=voice_params, audio_config=audio_config)

            with open(filepath, "wb") as out:
                out.write(response.audio_content)
                logging.debug('[DAEMON][TestTTS] Fichier TTS généré :: %s', filepath)
        else:
            logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
        
        urlFileToPlay = urljoin(ttsSrvWeb, filename)
        logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
        res = castToGoogleHome(urlFileToPlay, ttsGoogleName)
        logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
    else:
        logging.error('[DAEMON][TestTTS] Clé API invalide :: ' + GCLOUDAPIKEY)

def castToGoogleHome(urltoplay, googleName):
    if googleName != '':
        logging.debug('[DAEMON][Cast] Diffusion sur le Google Home :: %s', googleName)
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[googleName])
        if not chromecasts:
            logging.debug('[DAEMON][Cast] Aucun Chromecast avec ce nom :: %s', googleName)
            return False        
        cast = list(chromecasts)[0]
        cast.wait()
          
        logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
        
        app_name = "default_media_receiver"
        app_data = {"media_id": urltoplay, "media_type": "audio/mp3"}
        quick_play.quick_play(cast, app_name, app_data)
        
        logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', cast.media_controller.status)
        
        while cast.media_controller.status.player_state == 'PLAYING':
            time.sleep(1)
            logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', cast.media_controller.status)
        
        cast.quit_app()
        browser.stop_discovery()
        return True
    else:
        logging.debug('[DAEMON][Cast] Diffusion impossible (GoogleHome absent)')
        return False


def purgeCache(nbDays='0'):
    if nbDays == '0':  # clean entire directory including containing folder
        logging.debug('[DAEMON][PURGE-CACHE] nbDays is 0.')
        try:
            if os.path.exists(TTS_CACHEFOLDERTMP):
                shutil.rmtree(TTS_CACHEFOLDERTMP)
        except Exception as e:
            logging.warning('[DAEMON][PURGE-CACHE] Error while cleaning cache entirely (nbDays = 0) :: %s', e)
            pass
    else:  # clean only files older than X days
        now = time.time()
        path = TTS_CACHEFOLDERTMP
        try:
            for f in os.listdir(path):
                logging.debug("[DAEMON][PURGE-CACHE] Age for " + f + " is " + str(
                    int((now - (os.stat(os.path.join(path, f)).st_mtime)) / 86400)) + " days")
                if os.stat(os.path.join(path, f)).st_mtime < (now - (int(nbDays) * 86400)):
                    os.remove(os.path.join(path, f))
                    logging.debug("[DAEMON][PURG-CACHE] File Removed " + f +
                                  " due to expiration (" + nbDays + " days)")
        except Exception as e:
            logging.warning('[DAEMON][PURGE-CACHE] Error while cleaning cache based on file age :: %s', e)
            pass

# ----------------------------------------------------------------------------


def handler(signum=None, frame=None):
    logging.debug("Signal %i caught, exiting...", int(signum))
    shutdown()


def shutdown():
    logging.debug("Shutdown")
    logging.debug("Removing PID file %s", _pidfile)
    try:
        os.remove(_pidfile)
    except Exception:
        pass
    try:
        jeedom_socket.close()
    except Exception:
        pass
    logging.debug("Exit 0")
    sys.stdout.flush()
    os._exit(0)

# ----------------------------------------------------------------------------

# ***** PROGRAMME PRINCIPAL *****


_log_level = "error"
_socket_port = 55999
_socket_host = 'localhost'
_pidfile = '/tmp/ttscastd.pid'
_apikey = ''
_callback = ''
_cycle = 0.3

parser = argparse.ArgumentParser(description='TTSCast Daemon for Jeedom plugin')
parser.add_argument("--loglevel", help="Log Level for the daemon", type=str)
parser.add_argument("--callback", help="Callback", type=str)
parser.add_argument("--apikey", help="ApiKey", type=str)
parser.add_argument("--gcloudapikey", help="Google Cloud TTS ApiKey", type=str)
parser.add_argument("--cycle", help="Cycle to send event", type=str)
parser.add_argument("--ttsweb", help="Jeedom Web Server", type=str)
parser.add_argument("--pid", help="Pid file", type=str)
parser.add_argument("--socketport", help="Port for TTSCast server", type=str)

args = parser.parse_args()
if args.loglevel:
    _log_level = args.loglevel
if args.callback:
    _callback = args.callback
if args.apikey:
    _apikey = args.apikey
if args.gcloudapikey:
    GCLOUDAPIKEY = args.gcloudapikey
if args.pid:
    _pidfile = args.pid
if args.cycle:
    _cycle = float(args.cycle)
if args.socketport:
    _socket_port = int(args.socketport)
if args.ttsweb:
    TTS_WEBSRVCACHE = urljoin(args.ttsweb, 'plugins/ttscast/data/cache/')
    TTS_WEBSRVMEDIA = urljoin(args.ttsweb, 'plugins/ttscast/data/media/')

jeedom_utils.set_log_level(_log_level)

logging.info('[DAEMON][MAIN] Start ttscastd')
logging.info('[DAEMON][MAIN] Log level: %s', _log_level)
logging.info('[DAEMON][MAIN] Socket port: %s', _socket_port)
logging.info('[DAEMON][MAIN] Socket host: %s', _socket_host)
logging.info('[DAEMON][MAIN] Cycle: %s', _cycle)
logging.info('[DAEMON][MAIN] PID file: %s', _pidfile)
logging.info('[DAEMON][MAIN] ApiKey: %s', "***************")
logging.info('[DAEMON][MAIN] Google Cloud ApiKey: %s', GCLOUDAPIKEY)
logging.info('[DAEMON][MAIN] CallBack: %s', _callback)
logging.info('[DAEMON][MAIN] Jeedom WebSrvCache: %s', TTS_WEBSRVCACHE)
logging.info('[DAEMON][MAIN] Jeedom WebSrvMedia: %s', TTS_WEBSRVMEDIA)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

try:
    jeedom_utils.write_pid(str(_pidfile))
    jeedom_socket = jeedom_socket(port=_socket_port, address=_socket_host)
    listen(_cycle)
except Exception as e:
    logging.error('[DAEMON][MAIN] Fatal error: %s', e)
    logging.info(traceback.format_exc())
    shutdown()
