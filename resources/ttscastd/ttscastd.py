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
import resource
import shutil
import sys
import os
import time
import hashlib
import traceback
import signal
import json
import argparse
import threading
import datetime
import requests

from urllib.parse import urljoin, quote
from uuid import UUID

# Import pour Jeedom
try:
    from jeedom.jeedom import *
    # from jeedom.jeedom import jeedom_socket, jeedom_utils, jeedom_com, JEEDOM_SOCKET_MESSAGE
except ImportError as e:
    print("[DAEMON][IMPORT] Error: importing module jeedom.jeedom ::", e)
    sys.exit(1)

# Import pour Google Cloud TTS
try:
    from google.oauth2 import service_account
    import google.cloud.texttospeech as googleCloudTTS
except ImportError as e:
    print("[DAEMON][IMPORT] Error: importing module Google Cloud TTS ::", e)
    sys.exit(1)

# Import pour PyChromeCast
try:
    import zeroconf
    import pychromecast
    from pychromecast import quick_play
    from pychromecast.controllers.media import MediaStatusListener
    from pychromecast.controllers.receiver import CastStatusListener
    from pychromecast.controllers import dashcast
except ImportError as e:
    print("[DAEMON][IMPORT] Error: importing module PyChromecast ::", e)
    sys.exit(1)

# Import gTTS (Google Translate TTS)
try:
    from gtts import gTTS
except ImportError as e: 
    print("[DAEMON][IMPORT] Error: importing module gTTS ::", e)
    sys.exit(1)

# Import pyDub (Audio changing)
# try:
#     from pydub import AudioSegment
# except ImportError as e: 
#     print("[DAEMON][IMPORT] Error: importing module gTTS ::", e)
#     sys.exit(1)

# Import Config
try:
    from utils import Comm, Config
except ImportError as e:
    print("[DAEMON][IMPORT] Error: importing module config ::", e)
    sys.exit(1)

class Loops:
    # *** Boucle events from Jeedom ***
    def eventsFromJeedom(cycle=0.5):
        global JEEDOM_SOCKET_MESSAGE
        while not Config.IS_ENDING:    
            if not JEEDOM_SOCKET_MESSAGE.empty():
                logging.debug("[DAEMON][SOCKET] Message received in socket JEEDOM_SOCKET_MESSAGE")
                
                message = json.loads(JEEDOM_SOCKET_MESSAGE.get().decode('utf-8'))
                
                if message['apikey'] != Config.apiKey:
                    logging.error("[DAEMON][SOCKET] Invalid apikey from socket :: %s", message['apikey'])
                    return
                
                try:
                    # TODO ***** Gestion des messages reçus de Jeedom *****
                    if message['cmd'] == 'action':
                        # Gestion des actions
                        logging.debug('[DAEMON][SOCKET] Action')
                        
                        if 'cmd_action' in message:
                            
                            if (message['cmd_action'] == 'volumeset' and all(keys in message for keys in ('value', 'googleUUID'))):
                                logging.debug('[DAEMON][SOCKET] Action :: VolumeSet = %s @ %s', message['value'], message['googleUUID'])
                                Functions.mediaActions(message['googleUUID'], message['value'], message['cmd_action'])
                            
                            elif (message['cmd_action'] in ('volumeup', 'volumedown', 'media_pause', 'media_play', 'media_stop', 'media_next', 'media_quit', 'media_rewind', 'media_previous', 'mute_on', 'mute_off') and 'googleUUID' in message):
                                logging.debug('[DAEMON][SOCKET] Action :: %s @ %s', message['cmd_action'], message['googleUUID'])
                                Functions.mediaActions(message['googleUUID'], '', message['cmd_action'])
                                
                            elif (message['cmd_action'] in ('youtube', 'dashcast', 'radios')):
                                logging.debug('[DAEMON][SOCKET] Media :: %s @ %s', message['cmd_action'], message['googleUUID'])
                                Functions.controllerActions(message['googleUUID'], message['cmd_action'], message['value'], _options=message['options'])
                                
                    elif message['cmd'] == 'purgettscache':
                        logging.debug('[DAEMON][SOCKET] Purge TTS Cache')
                        
                        if 'days' in message:
                            Functions.purgeCache(message['days'])
                        
                        else:
                            Functions.purgeCache()
                            
                    elif message['cmd'] == "addcast":
                        
                        if all(keys in message for keys in ('uuid', 'host', 'friendly_name')):
                            _uuid = UUID(message['uuid'])
                            
                            if message['host'] not in Config.KNOWN_HOSTS:
                                Config.KNOWN_HOSTS.append(message['host'])
                                logging.debug('[DAEMON][SOCKET] Add Cast to KNOWN Devices :: %s', str(Config.KNOWN_HOSTS))
                            
                            if message['friendly_name'] not in Config.GCAST_NAMES: 
                                Config.GCAST_NAMES.append(message['friendly_name'])
                                logging.debug('[DAEMON][SOCKET] Add Cast to GCAST Names :: %s', str(Config.GCAST_NAMES))
                            
                            if _uuid not in Config.GCAST_UUID:
                                Config.GCAST_UUID.append(_uuid)
                                logging.debug('[DAEMON][SOCKET] Add Cast to GCAST UUID :: %s', str(Config.GCAST_UUID))
                                myCast.castListeners(uuid=str(_uuid))
                                
                    elif message['cmd'] == "removecast":
                        if all(keys in message for keys in ('uuid', 'host', 'friendly_name')):
                            _uuid = UUID(message['uuid'])
                            
                            if message['host'] in Config.KNOWN_HOSTS:
                                Config.KNOWN_HOSTS.remove(message['host'])
                                logging.debug('[DAEMON][SOCKET] Remove Cast from KNOWN Devices :: %s', str(Config.KNOWN_HOSTS))
                            
                            if message['friendly_name'] in Config.GCAST_NAMES: 
                                Config.GCAST_NAMES.remove(message['friendly_name'])
                                logging.debug('[DAEMON][SOCKET] Remove Cast from GCAST Names :: %s', str(Config.GCAST_NAMES))
                            
                            if _uuid in Config.GCAST_UUID:
                                Config.GCAST_UUID.remove(_uuid)
                                logging.debug('[DAEMON][SOCKET] Remove Cast from GCAST UUID :: %s', str(Config.GCAST_UUID))
                                myCast.castRemove(uuid=str(_uuid))
                            
                    elif message['cmd'] == 'playtesttts':
                        logging.debug('[DAEMON][SOCKET] Generate And Play Test TTS')
                        
                        if all(keys in message for keys in ('ttsText', 'ttsGoogleName', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed', 'ttsRSSSpeed', 'ttsRSSVoiceName')):
                            logging.debug('[DAEMON][SOCKET] Test TTS :: %s', message['ttsText'] + ' | ' + message['ttsGoogleName'] + ' | ' + message['ttsVoiceName'] + ' | ' + message['ttsLang'] + ' | ' + message['ttsEngine'] + ' | ' + message['ttsSpeed'] + ' | ' + message['ttsRSSVoiceName'] + ' | ' + message['ttsRSSSpeed'])
                            TTSCast.generateTestTTS(message['ttsText'], message['ttsGoogleName'], message['ttsVoiceName'], message['ttsRSSVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'], message['ttsRSSSpeed'])
                        
                        else:
                            logging.debug('[DAEMON][SOCKET] Test TTS :: Il manque des données pour traiter la commande.')
                            
                    elif message['cmd'] == 'playtts':
                        logging.debug('[DAEMON][SOCKET] Generate And Play TTS')
                        
                        if all(keys in message for keys in ('ttsText', 'ttsGoogleUUID', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed', 'ttsOptions', 'ttsRSSSpeed', 'ttsRSSVoiceName')):
                            logging.debug('[DAEMON][SOCKET] TTS :: %s', str(message))
                            TTSCast.getTTS(message['ttsText'], message['ttsGoogleUUID'], message['ttsVoiceName'], message['ttsRSSVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'], message['ttsRSSSpeed'], message['ttsOptions'])
                        
                        else:
                            logging.debug('[DAEMON][SOCKET] TTS :: Il manque des données pour traiter la commande.')
                            
                    elif message['cmd'] == "scanOn":
                        logging.debug('[DAEMON][SOCKET] ScanState = scanOn')
                        
                        Config.ScanMode = True
                        Config.ScanModeStart = int(time.time())
                        Comm.sendToJeedom.send_change_immediate({'scanState': 'scanOn'})
                        
                    elif message['cmd'] == "scanOff":
                        logging.debug('[DAEMON][SOCKET] ScanState = scanOff')
                        
                        Config.ScanMode = False
                        Comm.sendToJeedom.send_change_immediate({'scanState': 'scanOff'})
                        
                except Exception as e:
                    logging.error('[DAEMON][SOCKET] Send command to daemon error :: %s', e)
                    logging.debug(traceback.format_exc())
            time.sleep(cycle)
        
    # *** Boucle principale infinie (daemon) ***
    def mainLoop(cycle=2):
        jeedom_socket.open()
        logging.info('[DAEMON][MAINLOOP] Starting MainLoop')
        
        # *** Thread pour les Event venant de Jeedom ***
        threading.Thread(target=Loops.eventsFromJeedom, args=(Config.cycleEvent,)).start()
        
        try:
            # Thread pour le browser (pychromecast)
            Config.NETCAST_ZCONF = zeroconf.Zeroconf()
            Config.NETCAST_BROWSER = pychromecast.get_chromecasts(tries=3, retry_wait=10, timeout=60, blocking=False, callback=myCast.castCallBack, zeroconf_instance=Config.NETCAST_ZCONF, known_hosts=Config.KNOWN_HOSTS)

            logging.info('[DAEMON][MAINLOOP][NETCAST] Listening for Chromecast events...')

            # Informer Jeedom que le démon est démarré
            Comm.sendToJeedom.send_change_immediate({'daemonStarted': '1'})

            while not Config.IS_ENDING:
                try:
                    # *** Actions de la MainLoop ***
                    currentTime = int(time.time())
                    
                    # Arrêt du ScanMode au bout de 60 secondes
                    if (Config.ScanMode and (Config.ScanModeStart + Config.ScanModeTimeOut) <= currentTime):
                        Config.ScanMode = False
                        logging.info('[DAEMON][MAINLOOP] ScanMode END')
                        Comm.sendToJeedom.send_change_immediate({'scanState': 'scanOff'})
                    # Heartbeat du démon
                    if ((Config.HeartbeatLastTime + Config.HeartbeatFrequency) <= currentTime):
                        logging.info('[DAEMON][MAINLOOP] Heartbeat = 1')
                        Comm.sendToJeedom.send_change_immediate({'heartbeat': '1'})
                        Config.HeartbeatLastTime = currentTime
                        Functions.getResourcesUsage()
                    # Scan New Chromecast
                    if not Config.ScanPending:
                        if Config.ScanMode and (Config.ScanLastTime < Config.ScanModeStart):
                            threading.Thread(target=Functions.scanChromeCast, args=('ScanMode',)).start()
                        elif (Config.ScanLastTime + Config.ScanSchedule <= currentTime):
                            logging.debug('[DAEMON][SCANNER][SCHEDULE][CALL] GCAST Names :: %s', str(Config.GCAST_NAMES))
                            threading.Thread(target=Functions.scanChromeCast, args=('ScheduleMode',)).start()
                    else:
                        logging.debug('[DAEMON][MAINLOOP] ScanMode : SCAN PENDING ! ')
                    # Pause Cycle
                    time.sleep(cycle)
                except Exception as e:
                    logging.error('[DAEMON][MAINLOOP] Exception on MainLoop :: %s', e)
                    logging.debug(traceback.format_exc())    
                    shutdown()
        except KeyboardInterrupt:
            logging.error('[DAEMON][MAINLOOP] KeyboardInterrupt on MainLoop, Shutdown.')
            shutdown()
                    
class TTSCast:
    """ Class TTS Cast """
    
    def jeedomTTS(ttsText, ttsLang):
        filecontent = None
        try:
            ttsParams = 'tts.php?apikey=' + Config.apiTTSKey + '&voice=' + ttsLang + '&path=1&text=' + quote(ttsText, safe='')
            ttsFullURI = urljoin(Config.ttsWebSrvJeeTTS, ttsParams)
            logging.debug('[DAEMON][JeedomTTS] ttsFullURI :: %s', ttsFullURI)
            
            response = requests.post(ttsFullURI, timeout=8, verify=False)
            filecontent = response.content
            
            if response.status_code != requests.codes.ok:
                filecontent = None
                logging.error('[DAEMON][JeedomTTS] Status Code Error :: %s', response.status_code)
            else:
                if len(response.content) < 254 and os.path.exists(response.content):
                    logging.debug('[DAEMON][JeedomTTS] Response is a FilePath. Downloading Content Now.')
                    fc = open(response.content, "rb")
                    filecontent = fc.read()
                    fc.close()
        except Exception as e:
            logging.error('[DAEMON][JeedomTTS] Error while retrieving TTS file :: %s', e)
            logging.debug(traceback.format_exc())
            filecontent = None
        return filecontent
    
    def voiceRSS(ttsText, ttsLang, ttsSpeed='0'):
        filecontent = None
        try:
            ttsLangCode = "-".join(ttsLang.split("-")[:2])
            ttsVoiceName = ttsLang.split("-")[2:][0]
            logging.debug('[DAEMON][TestTTS] LanguageCode / VoiceName :: %s / %s', ttsLangCode, ttsVoiceName)
            
            ttsHeaders = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            ttsParams = '?key=' + Config.apiRSSKey + '&hl=' + ttsLangCode + '&v=' + ttsVoiceName + '&r=' + ttsSpeed + '&c=MP3&f=16khz_8bit_mono&ssml=false&b64=false' + '&src=' + quote(ttsText, safe='')
            ttsFullURI = urljoin(Config.ttsVoiceRSSUrl, ttsParams)
            logging.debug('[DAEMON][VoiceRSS] ttsFullURI :: %s', ttsFullURI)
            
            response = requests.post(ttsFullURI, headers=ttsHeaders, timeout=30, verify=True)
            filecontent = response.content
            
            if response.status_code != requests.codes.ok:
                filecontent = None
                logging.error('[DAEMON][VoiceRSS] Status Code Error :: %s (%s)', response.status_code, response.reason)
            else:
                """ logging.debug('[DAEMON][VoiceRSS] Response is OK. Downloading Content Now.')
                fc = open(response.content, "rb")
                filecontent = fc.read()
                fc.close() """
        except Exception as e:
            logging.error('[DAEMON][VoiceRSS] Error while retrieving TTS file :: %s', e)
            logging.debug(traceback.format_exc())
            filecontent = None
        return filecontent
    
    def generateTestTTS(ttsText, ttsGoogleName, ttsVoiceName, ttsRSSVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0', ttsRSSSpeed='0'):
        logging.debug('[DAEMON][TestTTS] Param TTSEngine :: %s', ttsEngine)
        
        logging.debug('[DAEMON][TestTTS] Check des répertoires')
        cachePath = Config.ttsCacheFolderWeb
        symLinkPath = Config.ttsCacheFolderTmp
        ttsSrvWeb = Config.ttsWebSrvCache
        
        try:
            os.stat(symLinkPath)
        except Exception:
            os.mkdir(symLinkPath)
        try:
            os.stat(cachePath)
        except Exception:
            os.symlink(symLinkPath, cachePath)
        
        if ttsEngine == "gcloudtts":
            logging.debug('[DAEMON][TestTTS] TTSEngine = gcloudtts')
            logging.debug('[DAEMON][TestTTS] Import de la clé API :: *** ')
            if Config.gCloudApiKey != 'noKey':
                credentials = service_account.Credentials.from_service_account_file(os.path.join(Config.configFullPath, Config.gCloudApiKey))

                logging.debug('[DAEMON][TestTTS] Test et génération du fichier TTS (mp3)')
                raw_filename = ttsText + "|gCloudTTS|" + ttsVoiceName + "|" + ttsSpeed
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                
                logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    language_code = "-".join(ttsVoiceName.split("-")[:2])
                    logging.debug('[DAEMON][TestTTS] LanguageCode :: %s', language_code)
                    text_input = googleCloudTTS.SynthesisInput(text=ttsText)
                    voice_params = googleCloudTTS.VoiceSelectionParams(language_code=language_code, name=ttsVoiceName)
                    audio_config = googleCloudTTS.AudioConfig(audio_encoding=googleCloudTTS.AudioEncoding.MP3, effects_profile_id=['small-bluetooth-speaker-class-device'], speaking_rate=float(ttsSpeed))

                    client = googleCloudTTS.TextToSpeechClient(credentials=credentials)
                    response = client.synthesize_speech(input=text_input, voice=voice_params, audio_config=audio_config)

                    with open(filepath, "wb") as out:
                        out.write(response.audio_content)
                        logging.debug('[DAEMON][TestTTS] Fichier TTS généré :: %s', filepath)
                else:
                    logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                
                urlFileToPlay = urljoin(ttsSrvWeb, filename)
                logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                res = TTSCast.castToGoogleHome(urlFileToPlay, ttsGoogleName)
                logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            else:
                logging.warning('[DAEMON][TestTTS] Clé API (Google Cloud TTS) invalide :: ' + Config.gCloudApiKey)
        elif ttsEngine == "gtranslatetts":
            logging.debug('[DAEMON][TestTTS] TTSEngine = gtranslatetts')
            raw_filename = ttsText + "|gTTS|" + ttsLang
            filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
            filepath = os.path.join(symLinkPath, filename)
            logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
            
            if not os.path.isfile(filepath):
                langToTTS = ttsLang.split('-')[0]
                try:
                    client = gTTS(ttsText, lang=langToTTS)
                    client.save(filepath)
                except Exception as e:
                    if os.path.isfile(filepath):
                        try:
                            os.remove(filepath)
                        except OSError:
                            pass
                    logging.debug('[DAEMON][TestTTS] Google Translate API ERROR :: %s', e)
            else:
                logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            urlFileToPlay = urljoin(ttsSrvWeb, filename)
            logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
            
            res = TTSCast.castToGoogleHome(urlFileToPlay, ttsGoogleName)
            logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
        elif ttsEngine == "jeedomtts":
            logging.debug('[DAEMON][TestTTS] TTSEngine = jeedomtts')
            raw_filename = ttsText + "|JeedomTTS|" + ttsLang
            filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
            filepath = os.path.join(symLinkPath, filename)
            logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
            
            if not os.path.isfile(filepath):
                ttsfile = TTSCast.jeedomTTS(ttsText, ttsLang)
                if ttsfile is not None:
                    with open(filepath, 'wb') as f:
                        f.write(ttsfile)
                else:
                    logging.debug('[DAEMON][TestTTS] JeedomTTS Error :: Incorrect Output')
            else:
                logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            urlFileToPlay = urljoin(ttsSrvWeb, filename)
            logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
            
            res = TTSCast.castToGoogleHome(urlFileToPlay, ttsGoogleName)
            logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
        elif ttsEngine == "voicersstts":
            logging.debug('[DAEMON][TestTTS] TTSEngine = voicersstts')
            logging.debug('[DAEMON][TestTTS] Import de la clé API :: *** ')
            if Config.apiRSSKey != 'noKey':
                raw_filename = ttsText + "|VoiceRSSTTS|" + ttsRSSVoiceName + "|" + ttsRSSSpeed
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    
                    ttsfile = TTSCast.voiceRSS(ttsText, ttsRSSVoiceName, ttsRSSSpeed)
                    if ttsfile is not None:
                        with open(filepath, 'wb') as f:
                            f.write(ttsfile)
                    else:
                        logging.debug('[DAEMON][TestTTS] VoiceRSS Error :: Incorrect Output')
                else:
                    logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                
                urlFileToPlay = urljoin(ttsSrvWeb, filename)
                logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                
                res = TTSCast.castToGoogleHome(urlFileToPlay, ttsGoogleName)
                logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            else:
                logging.warning('[DAEMON][TestTTS] Clé API (Voice RSS) invalide :: ' + Config.apiRSSKey)
                
    def getTTS(ttsText, ttsGoogleUUID, ttsVoiceName, ttsRSSVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0', ttsRSSSpeed='0', ttsOptions=None):
        logging.debug('[DAEMON][TTS] Check des répertoires')
        cachePath = Config.ttsCacheFolderWeb
        symLinkPath = Config.ttsCacheFolderTmp
        ttsSrvWeb = Config.ttsWebSrvCache
        
        try:
            os.stat(symLinkPath)
        except Exception:
            os.mkdir(symLinkPath)
        try:
            os.stat(cachePath)
        except Exception:
            os.symlink(symLinkPath, cachePath)
        
        if not ttsOptions:
            ttsOptions = None
        _ttsVolume = None
        
        try:
            if (ttsOptions is not None):
                options_json = json.loads("{" + ttsOptions + "}")
                _ttsVolume = options_json['volume'] if 'volume' in options_json else None
                logging.debug('[DAEMON][TTS] Options :: %s', str(options_json))
        except ValueError as e:
            logging.debug('[DAEMON][TTS] Options mal formatées (Json KO) :: %s', e)
        
        if ttsEngine == "gcloudtts":
            logging.debug('[DAEMON][TTS] TTSEngine = gcloudtts')
            logging.debug('[DAEMON][TTS] Import de la clé API :: *** ')
            if Config.gCloudApiKey != 'noKey':
                credentials = service_account.Credentials.from_service_account_file(os.path.join(Config.configFullPath, Config.gCloudApiKey))

                logging.debug('[DAEMON][TTS] Génération du fichier TTS (mp3)')
                raw_filename = ttsText + "|gCloudTTS|" + ttsVoiceName + "|" + ttsSpeed
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                
                logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    language_code = "-".join(ttsVoiceName.split("-")[:2])
                    text_input = googleCloudTTS.SynthesisInput(text=ttsText)
                    voice_params = googleCloudTTS.VoiceSelectionParams(language_code=language_code, name=ttsVoiceName)
                    audio_config = googleCloudTTS.AudioConfig(audio_encoding=googleCloudTTS.AudioEncoding.MP3, effects_profile_id=['small-bluetooth-speaker-class-device'], speaking_rate=float(ttsSpeed))

                    client = googleCloudTTS.TextToSpeechClient(credentials=credentials)
                    response = client.synthesize_speech(input=text_input, voice=voice_params, audio_config=audio_config)

                    with open(filepath, "wb") as out:
                        out.write(response.audio_content)
                        logging.debug('[DAEMON][TTS] Fichier TTS généré :: %s', filepath)
                else:
                    logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                
                urlFileToPlay = urljoin(ttsSrvWeb, filename)
                logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume)
                logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            else:
                logging.warning('[DAEMON][TestTTS] Clé API invalide :: ' + Config.gCloudApiKey)
        elif ttsEngine == "gtranslatetts":
            logging.debug('[DAEMON][TTS] TTSEngine = gtranslatetts')
            raw_filename = ttsText + "|gTTS|" + ttsLang
            filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
            filepath = os.path.join(symLinkPath, filename)
            logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
            
            if not os.path.isfile(filepath):
                langToTTS = ttsLang.split('-')[0]
                try:
                    client = gTTS(ttsText, lang=langToTTS)
                    client.save(filepath)
                except Exception as e:
                    if os.path.isfile(filepath):
                        try:
                            os.remove(filepath)
                        except OSError:
                            pass
                    logging.debug('[DAEMON][TTS] Google Translate API ERROR :: %s', e)
            else:
                logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            urlFileToPlay = urljoin(ttsSrvWeb, filename)
            logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
            
            res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume)
            logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
        elif ttsEngine == "jeedomtts":
            logging.debug('[DAEMON][TTS] TTSEngine = jeedomtts')
            
            raw_filename = ttsText + "|JeedomTTS|" + ttsLang
            filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
            filepath = os.path.join(symLinkPath, filename)
            logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
            
            if not os.path.isfile(filepath):
                ttsfile = TTSCast.jeedomTTS(ttsText, ttsLang)
                if ttsfile is not None:
                    with open(filepath, 'wb') as f:
                        f.write(ttsfile)
                else:
                    logging.debug('[DAEMON][TTS] JeedomTTS Error :: Incorrect Output')
            else:
                logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            urlFileToPlay = urljoin(ttsSrvWeb, filename)
            logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
            
            res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume)
            logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
        elif ttsEngine == "voicersstts":
            logging.debug('[DAEMON][TTS] TTSEngine = voicersstts')
            logging.debug('[DAEMON][TTS] Import de la clé API :: *** ')
            if Config.apiRSSKey != 'noKey':
                raw_filename = ttsText + "|VoiceRSSTTS|" + ttsRSSVoiceName + "|" + ttsRSSSpeed
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    ttsfile = TTSCast.voiceRSS(ttsText, ttsRSSVoiceName, ttsRSSSpeed)
                    if ttsfile is not None:
                        with open(filepath, 'wb') as f:
                            f.write(ttsfile)
                    else:
                        logging.debug('[DAEMON][TTS] VoiceRSS Error :: Incorrect Output')
                else:
                    logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                
                urlFileToPlay = urljoin(ttsSrvWeb, filename)
                logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                
                res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume)
                logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            else:
                logging.warning('[DAEMON][TTS] Clé API (Voice RSS) invalide :: ' + Config.apiRSSKey)  

    def castToGoogleHome(urltoplay, googleName='', googleUUID='', volumeForPlay=None):
        if googleName != '':
            logging.debug('[DAEMON][Cast] Diffusion sur le Google Home :: %s', googleName)
            
            chromecasts = None
            cast = None
            try:
                chromecasts = [mycast for mycast in Config.NETCAST_DEVICES if str(mycast.name) == googleName]
                if not chromecasts:
                    logging.debug('[DAEMON][Cast] Aucun Chromecast avec ce nom :: %s', googleName)
                    return False
                cast = chromecasts[0]
                logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
            
                # Si DashCast alors sortir de l'appli avant sinon cela plante
                Functions.checkIfDashCast(cast)
            
                volumeBeforePlay = cast.status.volume_level
                if (volumeForPlay is not None):
                    logging.debug('[DAEMON][Cast] Volume avant lecture :: %s', str(volumeBeforePlay))
                    cast.set_volume(volume=volumeForPlay / 100)
                
                urlThumb = urljoin(Config.ttsWebSrvImages, "tts.png")
                logging.debug('[DAEMON][Cast] Thumb path :: %s', urlThumb)
                
                app_name = "default_media_receiver"
                app_data = {
                    "media_id": urltoplay, 
                    "media_type": "audio/mp3", 
                    "title": "[Jeedom] TTSCast", 
                    "thumb": urlThumb
                }
                quick_play.quick_play(cast, app_name, app_data)
                
                logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', str(cast.media_controller.status))
                
                while cast.media_controller.status.player_state == 'PLAYING':
                    time.sleep(1)
                    logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', str(cast.media_controller.status))
                
                cast.quit_app()
                if (volumeForPlay is not None):
                    cast.set_volume(volume=volumeBeforePlay)
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return True
            except Exception as e:
                logging.debug('[DAEMON][Cast] Exception (Chromecasts) :: %s', e)
                logging.debug(traceback.format_exc())
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return False
        elif googleUUID != '':
            logging.debug('[DAEMON][Cast] Diffusion sur le Google Home :: %s', googleUUID)
            
            chromecasts = None
            cast = None
            try:
                chromecasts = [mycast for mycast in Config.NETCAST_DEVICES if str(mycast.uuid) == googleUUID]
                if not chromecasts:
                    logging.debug('[DAEMON][Cast] Aucun Chromecast avec cet UUID nom :: %s', googleUUID)
                    return False
                cast = chromecasts[0]
                logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
                
                # Si DashCast alors sortir de l'appli avant sinon cela plante
                Functions.checkIfDashCast(cast)
                
                volumeBeforePlay = cast.status.volume_level
                if (volumeForPlay is not None):
                    logging.debug('[DAEMON][Cast] Volume avant lecture :: %s', str(volumeBeforePlay))
                    cast.set_volume(volume=volumeForPlay / 100)
            
                urlThumb = urljoin(Config.ttsWebSrvImages, "tts.png")
                logging.debug('[DAEMON][Cast] Thumb path :: %s', urlThumb)
            
                app_name = "default_media_receiver"
                app_data = {
                    "media_id": urltoplay, 
                    "media_type": "audio/mp3", 
                    "title": "[Jeedom] TTSCast", 
                    "thumb": urlThumb
                }
                quick_play.quick_play(cast, app_name, app_data)
            
                logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', str(cast.media_controller.status))
            
                while cast.media_controller.status.player_state == 'PLAYING':
                    time.sleep(1)
                    logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', str(cast.media_controller.status))
            
                cast.quit_app()
                if (volumeForPlay is not None):
                    cast.set_volume(volume=volumeBeforePlay)
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return True
            except Exception as e:
                logging.debug('[DAEMON][Cast] Exception (Chromecasts) :: %s', e)
                logging.debug(traceback.format_exc())
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return False
        else:
            logging.debug('[DAEMON][Cast] Diffusion impossible (GoogleHome + GoogleUUID manquants)')
            return False

class Functions:
    """ Class Functions """
    
    def checkIfDashCast(chromecast=None):
        if chromecast is not None and (not chromecast.is_idle or chromecast.status.app_id == '84912283'):  # DashCast = '84912283'
            logging.debug('[DAEMON][checkIfDashCast] QuitDashCastApp')
            chromecast.quit_app()
            t = 5
            while chromecast.status.app_id is not None and t > 0:
                time.sleep(0.1)
                t = t - 0.1
        time.sleep(0.5)
        return True
    
    def controllerActions(_googleUUID='UNKOWN', _controller='', _value='', _options=''):
        if _googleUUID != 'UNKOWN':
            chromecasts = None
            cast = None
            try:
                chromecasts = [mycast for mycast in Config.NETCAST_DEVICES if str(mycast.uuid) == _googleUUID]
                if not chromecasts:
                    logging.debug('[DAEMON][controllerActions] Aucun Chromecast avec cet UUID :: %s', _googleUUID)
                    return False
                cast = chromecasts[0]
                logging.debug('[DAEMON][controllerActions] Chromecast trouvé, lancement des actions')
                
                if (_controller == 'youtube'):
                    logging.debug('[DAEMON][controllerActions] YouTube Id @ UUID :: %s @ %s', _value, _googleUUID)
                    
                    # Si DashCast alors sortir de l'appli avant sinon cela plante
                    Functions.checkIfDashCast(cast)
                    
                    _playlist = None
                    _enqueue = False
                    _volume = None
                    
                    try:
                        options_json = json.loads("{" + _options + "}")
                        _playlist = options_json['playlist'] if 'playlist' in options_json else None
                        _enqueue = options_json['enqueue'] if 'enqueue' in options_json else False
                        _volume = options_json['volume'] if 'volume' in options_json else None
                        logging.debug('[DAEMON][controllerActions] YouTube :: Options :: %s', str(options_json))
                    except ValueError as e:
                        logging.debug('[DAEMON][controllerActions] YouTube :: Options mal formatées (Json KO) :: %s', e)
                    
                    volumeBeforePlay = cast.status.volume_level
                    if (_volume is not None):
                        logging.debug('[DAEMON][controllerActions] Volume avant lecture :: %s', str(volumeBeforePlay))
                        cast.set_volume(volume=_volume / 100)

                    app_name = "youtube"
                    app_data = {
                        "media_id": _value,
                        "playlist_id": _playlist,
                        "enqueue": _enqueue
                    }
                    quick_play.quick_play(cast, app_name, app_data)
                    logging.debug('[DAEMON][controllerActions] Youtube :: Diffusion lancée :: %s', str(cast.media_controller.status))
                    
                    # Libération de la mémoire
                    cast = None
                    chromecasts = None
                    return True
                
                elif (_controller == 'dashcast'):
                    logging.debug('[DAEMON][controllerActions] DashCast URL / Options @ UUID :: %s / %s @ %s', _value, _options, _googleUUID)
                    
                    player = dashcast.DashCastController()
                    cast.register_handler(player)
                    
                    _force = None
                    _reload_seconds = None
                    
                    try:
                        options_json = json.loads("{" + _options + "}")    
                        _force = options_json['force'] if 'force' in options_json else False
                        _reload_seconds = options_json['reload_seconds'] if 'reload_seconds' in options_json else None
                    except ValueError as e:
                        logging.debug('[DAEMON][controllerActions] DashCast :: Options mal formatées (Json KO) :: %s', e)
                    
                    if not cast.is_idle or ('quit_app' in options_json and options_json['quit_app']):
                        logging.debug('[DAEMON][controllerActions] DashCast :: QuitOtherApp')
                        cast.quit_app()
                        t = 5
                        while cast.status.app_id is not None and t > 0:
                            time.sleep(0.1)
                            t = t - 0.1                                       
                    time.sleep(1)
                    
                    logging.debug('[DAEMON][controllerActions] DashCast :: LoadUrl | Options :: %s | %s', _value, str(options_json))
                    player.load_url(url=_value, force=_force, reload_seconds=_reload_seconds)
                    time.sleep(2)
                    
                    cast.unregister_handler(player)
                    time.sleep(1)
                    
                    # Libération de la mémoire
                    player = None
                    cast = None
                    chromecasts = None
                    return True
                
                elif (_controller == 'radios'):
                    logging.debug('[DAEMON][controllerActions] Radio Streaming ID @ UUID :: %s @ %s', _value, _googleUUID)
                    
                    if _value == '':
                        cast.quit_app()
                        time.sleep(1)
                    else:
                        # Si DashCast alors sortir de l'appli avant sinon cela plante
                        Functions.checkIfDashCast(cast)
                        
                        if not os.path.isfile(Config.radiosFilePath):
                            logging.error('[DAEMON][controllerActions] Radios JSON GetFile ERROR :: %s @ %s', _value, _googleUUID)
                        else:    
                            f = open(Config.radiosFilePath, "r")
                            radiosArray = json.loads(f.read())
                            
                            if _value in radiosArray:
                                radio = radiosArray[_value]
                                if "NoLogo" in radio['image']:
                                    radioThumb = urljoin(Config.ttsWebSrvImages, "tts.png")
                                else:
                                    radioThumb = radio['image']
                                # logging.debug('[DAEMON][controllerActions] Radio Thumb path :: %s', urlThumb)
                                radioUrl = radio['location']
                                radioTitle = radio['title']
                                radioSubTitle = "[Jeedom] TTSCast Radio"
                                
                                app_name = "default_media_receiver"
                                # app_name = "bubbleupnp"
                                app_data = {
                                    "media_id": radioUrl,
                                    "media_type": "audio/mp3",
                                    "title": radioTitle,
                                    "thumb": radioThumb,
                                    "metadata": {
                                        "title": radioTitle,
                                        "subtitle": radioSubTitle,
                                        "images": [{"url": radioThumb}]
                                    },
                                    "stream_type": "LIVE"
                                }
                                quick_play.quick_play(cast, app_name, app_data)
                                # cast.media_controller.play_media(radioUrl, "audio/mp3")
                                logging.debug('[DAEMON][controllerActions] Diffusion Radio lancée :: %s', str(cast.media_controller.status))
                    
                    # Libération de la mémoire
                    cast = None
                    chromecasts = None
                    return True
                
            except Exception as e:
                logging.error('[DAEMON][mediaActions] Exception on mediaActions :: %s', e)
                logging.debug(traceback.format_exc())
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return False
    
    def mediaActions(_googleUUID='UNKOWN', _value='0', _mode=''):
        if _googleUUID != 'UNKOWN':
            chromecasts = None
            cast = None
            try:
                chromecasts = [mycast for mycast in Config.NETCAST_DEVICES if str(mycast.uuid) == _googleUUID]
                if not chromecasts:
                    logging.debug('[DAEMON][mediaActions] Aucun Chromecast avec cet UUID :: %s', _googleUUID)
                    return False
                cast = chromecasts[0]
                logging.debug('[DAEMON][mediaActions] Chromecast trouvé, lancement des actions')
                
                if (_mode in ('volumeset', 'volumeup', 'volumedown')):
                    castVolumeLevel = None
                    if (_mode == 'volumeset'):
                        castVolumeLevel = round(cast.set_volume(volume=float(_value) / 100) * 100)
                    elif (_mode == 'volumeup'):
                        castVolumeLevel = round(cast.volume_up(delta=0.05) * 100)
                    elif (_mode == 'volumedown'): 
                        castVolumeLevel = round(cast.volume_down(delta=0.05) * 100)
                    logging.debug('[DAEMON][mediaActions] Chromecast Volume @ UUID :: %s @ %s', str(castVolumeLevel), _googleUUID)
                elif (_mode == 'media_pause'):
                    cast.media_controller.pause()
                    logging.debug('[DAEMON][mediaActions] PAUSE :: %s', _googleUUID)
                elif (_mode == 'media_play'):
                    cast.media_controller.play()
                    logging.debug('[DAEMON][mediaActions] PLAY :: %s', _googleUUID)
                elif (_mode == 'media_stop'): 
                    cast.media_controller.stop()
                    logging.debug('[DAEMON][mediaActions] STOP :: %s', _googleUUID)
                elif (_mode == 'media_quit'): 
                    cast.quit_app()
                    logging.debug('[DAEMON][mediaActions] QUIT :: %s', _googleUUID)
                elif (_mode == 'media_next'): 
                    cast.media_controller.queue_next()
                    logging.debug('[DAEMON][mediaActions] NEXT :: %s', _googleUUID)
                elif (_mode == 'media_previous'): 
                    cast.media_controller.queue_prev()
                    logging.debug('[DAEMON][mediaActions] PREVIOUS :: %s', _googleUUID)
                elif (_mode == 'media_rewind'): 
                    cast.media_controller.rewind()
                    logging.debug('[DAEMON][mediaActions] REWIND :: %s', _googleUUID)
                elif (_mode == 'mute_on'): 
                    cast.set_volume_muted(True)
                    logging.debug('[DAEMON][mediaActions] MUTE ON :: %s', _googleUUID)
                elif (_mode == 'mute_off'): 
                    cast.set_volume_muted(False)
                    logging.debug('[DAEMON][mediaActions] MUTE OFF :: %s', _googleUUID)
                    
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return True
            except Exception as e:
                logging.error('[DAEMON][mediaActions] Exception on mediaActions :: %s', e)
                logging.debug(traceback.format_exc())
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return False
    
    def scanChromeCast(_mode='UNKOWN'):
        try:
            logging.debug('[DAEMON][SCANNER] Start Scanner :: %s', _mode)
            Config.ScanPending = True
            
            if (_mode == "ScanMode"):
                currentTime = int(time.time())
                currentTimeStr = datetime.datetime.fromtimestamp(currentTime).strftime("%d/%m/%Y - %H:%M:%S")
            
                # Thread pour le discovery (pychromecast)
                """ 
                browser = pychromecast.discovery.CastBrowser(myCast.MyCastListener(), Config.NETCAST_ZCONF, Config.KNOWN_HOSTS)
                browser.start_discovery()
                logging.info('[DAEMON][MAINLOOP][NETCAST] Listening for Chromecast events...') """
                
                logging.debug('[DAEMON][SCANNER] Devices découverts :: %s', len(Config.NETCAST_DEVICES))
                for device in Config.NETCAST_DEVICES:
                    logging.debug('[DAEMON][SCANNER] Device Chromecast :: %s (%s) @ %s:%s uuid: %s', device.cast_info.friendly_name, device.cast_info.model_name, device.cast_info.host, device.cast_info.port, device.uuid)
                    data = {
                        'friendly_name': device.cast_info.friendly_name,
                        'uuid': str(device.uuid),
                        'lastscan': currentTimeStr,
                        'model_name': device.cast_info.model_name,
                        'cast_type': device.cast_info.cast_type,
                        'manufacturer': device.cast_info.manufacturer,
                        'host': device.cast_info.host,
                        'port': device.cast_info.port,
                        'scanmode': 1
                    }
                    # Envoi vers Jeedom
                    Comm.sendToJeedom.add_changes('devices::' + data['uuid'], data)
            elif (_mode == "ScheduleMode"):
                # ScheduleMode
                currentTime = int(time.time())
                currentTimeStr = datetime.datetime.fromtimestamp(currentTime).strftime("%d/%m/%Y - %H:%M:%S")
                
                _gcast_names = Config.GCAST_NAMES.copy()
                
                logging.debug('[DAEMON][SCANNER][SCHEDULE] GCAST Names :: %s', str(_gcast_names))
                
                chromecasts = [mycast for mycast in Config.NETCAST_DEVICES if mycast.name in _gcast_names]
                logging.debug('[DAEMON][SCANNER][SCHEDULE] Nb NetCast vs JeeCast :: %s vs %s', len(Config.NETCAST_DEVICES), len(chromecasts))
                
                for cast in chromecasts: 
                    logging.debug('[DAEMON][SCANNER][SCHEDULE] Chromecast Name :: %s', cast.name)
                    try:
                        # time.sleep(0.3)
                        castVolumeLevel = int(cast.status.volume_level * 100)
                        castAppDisplayName = cast.status.display_name
                        
                        castIsStandBy = cast.status.is_stand_by
                        castIsMuted = cast.status.volume_muted
                        castAppId = cast.status.app_id
                        castStatusText = cast.status.status_text
                        
                        mediaLastUpdated = None
                        if (cast.media_controller.status.last_updated is not None):
                            last_updated = cast.media_controller.status.last_updated.replace(tzinfo=datetime.timezone.utc)
                            last_updated_local = last_updated.astimezone(tz=None)
                            mediaLastUpdated = last_updated_local.strftime("%d/%m/%Y - %H:%M:%S")
                        
                        mediaPlayerState = cast.media_controller.status.player_state
                        mediaTitle = cast.media_controller.status.title
                        mediaArtist = cast.media_controller.status.artist
                        mediaAlbumName = cast.media_controller.status.album_name
                        mediaContentType = cast.media_controller.status.content_type
                        mediaStreamType = cast.media_controller.status.stream_type
                        
                        data = {
                            'uuid': str(cast.uuid),
                            'lastschedule': currentTimeStr,
                            'lastschedulets': currentTime,
                            'volume_level': castVolumeLevel,
                            'display_name': castAppDisplayName,
                            'is_stand_by': castIsStandBy,
                            'volume_muted': castIsMuted,
                            'app_id': castAppId,
                            'status_text': castStatusText,
                            'player_state': mediaPlayerState,
                            'title': mediaTitle,
                            'artist': mediaArtist,
                            'album_name': mediaAlbumName,
                            'content_type': mediaContentType,
                            'stream_type': mediaStreamType,
                            'last_updated': mediaLastUpdated,
                            'schedule': 1,
                            'online': '1'
                        }

                        # Envoi vers Jeedom
                        Comm.sendToJeedom.add_changes('casts::' + data['uuid'], data)
                    except Exception as e:
                        logging.error('[DAEMON][SCANNER][SCHEDULE] Exception :: %s', e)
                        logging.debug(traceback.format_exc())
        except Exception as e:
            logging.error('[DAEMON][SCANNER] Exception on Scanner :: %s', e)
            logging.debug(traceback.format_exc())
            return False
        Config.ScanLastTime = int(time.time())
        Config.ScanPending = False
        return True
    
    def getResourcesUsage():
        if logging.getLogger().isEnabledFor(logging.INFO):
            resourcesUse = resource.getrusage(resource.RUSAGE_SELF)
            try:
                uTime = getattr(resourcesUse, 'ru_utime')
                sTime = getattr(resourcesUse, 'ru_stime')
                maxRSS = getattr(resourcesUse, 'ru_maxrss')
                totalTime = uTime + sTime
                currentTime = int(time.time())
                timeDiff = currentTime - Config.ResourcesLastTime
                timeDiffTotal = currentTime - Config.ResourcesFirstTime
                logging.info('[DAEMON][RESOURCES] Total CPU Time used : %.3fs (%.2f%%) | Last %i sec : %.3fs (%.2f%%) | Memory : %s Mo', totalTime, totalTime / timeDiffTotal * 100, timeDiff, totalTime - Config.ResourcesLastUsed, (totalTime - Config.ResourcesLastUsed) / timeDiff * 100, int(round(maxRSS / 1024)))
                Config.ResourcesLastUsed = totalTime
                Config.ResourcesLastTime = currentTime
            except Exception:
                pass
        
    def purgeCache(nbDays='0'):
        if nbDays == '0':  # clean entire directory including containing folder
            logging.debug('[DAEMON][PURGE-CACHE] nbDays is 0.')
            try:
                if os.path.exists(Config.ttsCacheFolderTmp):
                    shutil.rmtree(Config.ttsCacheFolderTmp)
            except Exception as e:
                logging.error('[DAEMON][PURGE-CACHE] Error while cleaning cache entirely (nbDays = 0) :: %s', e)
                logging.debug(traceback.format_exc())
                pass
        else:  # clean only files older than X days
            now = time.time()
            path = Config.ttsCacheFolderTmp
            try:
                for f in os.listdir(path):
                    logging.debug("[DAEMON][PURGE-CACHE] Age for " + f + " is " + str(
                        int((now - (os.stat(os.path.join(path, f)).st_mtime)) / 86400)) + " days")
                    if os.stat(os.path.join(path, f)).st_mtime < (now - (int(nbDays) * 86400)):
                        os.remove(os.path.join(path, f))
                        logging.debug("[DAEMON][PURG-CACHE] File Removed " + f + " due to expiration (" + nbDays + " days)")
            except Exception as e:
                logging.error('[DAEMON][PURGE-CACHE] Error while cleaning cache based on file age :: %s', e)
                logging.debug(traceback.format_exc())
                pass

class myCast:

    def castListeners(chromecast=None, uuid=''):
        """ Connect and Add Listener for Chromecast """
        if not chromecast:
            chromecasts = [cast for cast in Config.NETCAST_DEVICES if str(cast.uuid) == uuid]
            
            if not chromecasts:
                logging.debug('[DAEMON][NETCAST][CastListeners] Aucun Chromecast avec cet UUID :: %s', uuid)
                return False
            chromecast = chromecasts[0]
        
        logging.info('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Add Listeners', str(chromecast.name))
    
        if (uuid not in Config.LISTENER_CAST):
            Config.LISTENER_CAST[uuid] = myCast.MyCastStatusListener(chromecast.name, chromecast)
            chromecast.register_status_listener(Config.LISTENER_CAST[uuid])
        else:
            logging.debug('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Status Listener already active', str(chromecast.name))
            
        if (uuid not in Config.LISTENER_MEDIA):
            Config.LISTENER_MEDIA[uuid] = myCast.MyMediaStatusListener(chromecast.name, chromecast)
            chromecast.media_controller.register_status_listener(Config.LISTENER_MEDIA[uuid])
        else:
            logging.debug('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Media Listener already active', str(chromecast.name))
                       
    def castRemove(chromecast=None, uuid=''):
        """ Remove Listener and Connection for Chromecast """
        if not chromecast:
            chromecasts = [cast for cast in Config.NETCAST_DEVICES if str(cast.uuid) == uuid]
            
            if not chromecasts:
                logging.debug('[DAEMON][NETCAST][CastRemove] Aucun Chromecast avec cet UUID :: %s', uuid)
                return False
            chromecast = chromecasts[0]
    
        if (uuid in Config.LISTENER_CAST):
            chromecast.register_status_listener(None)
            del Config.LISTENER_CAST[uuid]
        else:
            logging.warning('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Status Listener already deleted', str(chromecast.name))
            
        if (uuid in Config.LISTENER_MEDIA):
            chromecast.media_controller.register_status_listener(None)
            del Config.LISTENER_MEDIA[uuid]
        else:
            logging.warning('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Media Listener already deleted', str(chromecast.name))
        
        logging.info('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Listeners Removed', str(chromecast.name))

        """ chromecast.disconnect()
        logging.info('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Disconnected', str(chromecast.name)) """

    def castCallBack(chromecast=None):
        """ Service CallBack de découverte des Google Cast """

        if chromecast is not None:
            if not any(mycast.uuid == chromecast.uuid for mycast in Config.NETCAST_DEVICES):
                Config.NETCAST_DEVICES.append(chromecast)
                logging.info('[DAEMON][NETCAST][CastCallBack] Chromecast with name :: %s :: Added to NETCAST_DEVICES', str(chromecast.name))
            else:
                logging.info('[DAEMON][NETCAST][CastCallBack] Chromecast with name :: %s :: Already in NETCAST_DEVICES', str(chromecast.name))
            logging.info('[DAEMON][NETCAST][CastCallBack] NETCAST_DEVICES Nb :: %s', len(Config.NETCAST_DEVICES))
            
            chromecast.wait(timeout=10)
            logging.info('[DAEMON][NETCAST][CastCallBack] Chromecast with name :: %s :: Connected', str(chromecast.name))
             
            if chromecast.uuid in Config.GCAST_UUID:
                uuid = str(chromecast.uuid)
                # myCast.castConnectAndListen(chromecast=chromecast, uuid=uuid)
                myCast.castListeners(uuid=uuid)
                
    class MyCastListener(pychromecast.discovery.AbstractCastListener):
        """Listener for discovering chromecasts."""

        def add_cast(self, uuid, _service):
            """Called when a new cast has beeen discovered."""
            # print(f"Found cast device '{Config.NETCAST_BROWSER.services[uuid].friendly_name}' with UUID {uuid}")
            logging.debug('[DAEMON][NETCAST][Add_Cast] Found Cast Device (Name/UUID) :: ' + Config.NETCAST_BROWSER.services[uuid].friendly_name + ' / ' + str(uuid))
            # TODO Action lorsqu'un GoogleCast est ajouté
            if Config.NETCAST_DEVICES is not None:
                chromecasts = [mycast for mycast in Config.NETCAST_DEVICES if mycast.uuid == uuid]
            else:
                chromecasts = None
            if not chromecasts:
                Config.NETCAST_DEVICES.append(pychromecast.get_chromecast_from_cast_info(Config.NETCAST_BROWSER.services[uuid], Config.NETCAST_ZCONF, 1, 10, 30))
                logging.debug('[DAEMON][NETCAST][Add_Cast] NETCAST_DEVICES Append :: ' + Config.NETCAST_BROWSER.services[uuid].friendly_name + ' / ' + str(uuid))
            else:
                logging.debug('[DAEMON][NETCAST][Add_Cast] NETCAST_DEVICES :: Device déjà présent')
            # TODO Config.NETCAST_DEVICES add device ?

        def remove_cast(self, uuid, _service, cast_info):
            """Called when a cast has beeen lost (MDNS info expired or host down)."""
            # print(f"Lost cast device '{cast_info.friendly_name}' with UUID {uuid}")
            logging.debug('[DAEMON][NETCAST][Remove_Cast] Lost Cast Device (Name/UUID) :: ' + cast_info.friendly_name + ' / ' + str(uuid))
            # TODO Action lorsqu'un GoogleCast est supprimé
            # TODO Config.NETCAST_DEVICES remove device + Listener ?

        def update_cast(self, uuid, _service):
            """Called when a cast has beeen updated (MDNS info renewed or changed)."""
            # print(f"Updated cast device '{Config.NETCAST_BROWSER.services[uuid].friendly_name}' with UUID {uuid}")
            logging.debug('[DAEMON][NETCAST][Update_Cast] Updated Cast Device (Name/UUID) :: ' + Config.NETCAST_BROWSER.services[uuid].friendly_name + ' / ' + str(uuid))
            # TODO Action lorsqu'un GoogleCast est mis à jour
            # TODO Est ce que cela remplace les autres listener notamment le média ? 

    class MyCastStatusListener(CastStatusListener):
        """Cast status listener"""

        def __init__(self, name, cast):
            self.name = name
            self.cast = cast

        def new_cast_status(self, status):
            logging.debug('[DAEMON][NETCAST][New_Cast_Status] ' + self.name + ' :: STATUS Chromecast change :: ' + str(status))
            try:
                castVolumeLevel = int(status.volume_level * 100)
                castAppDisplayName = status.display_name
            
                data = {
                    'uuid': str(self.cast.uuid),
                    'is_stand_by': status.is_stand_by,
                    'volume_level': castVolumeLevel,
                    'volume_muted': status.volume_muted,
                    'display_name': castAppDisplayName,
                    'app_id': status.app_id,
                    'status_text': status.status_text,
                    'realtime': 1,
                    'status_type': 'cast',
                    'online': '1'
                }

                # Envoi vers Jeedom
                Comm.sendToJeedom.add_changes('castsRT::' + data['uuid'], data)
            except Exception as e:
                logging.error('[DAEMON][NETCAST][New_Cast_Status] Exception :: %s', e)
                logging.debug(traceback.format_exc())
            
    class MyMediaStatusListener(MediaStatusListener):
        """Status media listener"""

        def __init__(self, name, cast):
            self.name = name
            self.cast = cast

        def new_media_status(self, status):
            logging.debug('[DAEMON][NETCAST][New_Media_Status] ' + self.name + ' :: STATUS Media change :: ' + str(status))
            try:
                mediaLastUpdated = None
                if (status.last_updated is not None):
                    last_updated = status.last_updated.replace(tzinfo=datetime.timezone.utc)
                    last_updated_local = last_updated.astimezone(tz=None)
                    mediaLastUpdated = last_updated_local.strftime("%d/%m/%Y - %H:%M:%S")
                
                data = {
                    'uuid': str(self.cast.uuid),
                    'player_state': status.player_state,
                    'title': status.title,
                    'artist': status.artist,
                    'album_name': status.album_name,
                    'content_type': status.content_type,
                    'stream_type': status.stream_type,
                    'last_updated': mediaLastUpdated,
                    'realtime': 1,
                    'status_type': 'media',
                    'online': '1'
                }

                # Envoi vers Jeedom
                Comm.sendToJeedom.add_changes('castsRT::' + data['uuid'], data)
                
            except Exception as e:
                logging.error('[DAEMON][NETCAST][New_Media_Status] Exception :: %s', e)
                logging.debug(traceback.format_exc())

        def load_media_failed(self, item, error_code):
            logging.error('[DAEMON][NETCAST][Load_Media_Failed] ' + self.name + ' :: LOAD Media FAILED for item :: ' + str(item) + ' with code :: ' + str(error_code))

# ----------------------------------------------------------------------------

def handler(signum=None, frame=None):
    logging.debug("[DAEMON] Signal %i caught, exiting...", int(signum))
    shutdown()

def shutdown():
    logging.info("[DAEMON] Shutdown :: Begin...")
    Config.IS_ENDING = True
    logging.info("[DAEMON] Shutdown :: Devices Disconnect :: Begin...")
    try:
        for chromecast in Config.NETCAST_DEVICES:
            chromecast.disconnect(timeout=5, blocking=False)
        logging.info("[DAEMON] Shutdown :: Devices Disconnect :: OK")
        Config.NETCAST_BROWSER.stop_discovery()
        logging.info("[DAEMON] Shutdown :: Browser Stop :: OK")
        Config.NETCAST_ZCONF.close()
        logging.info("[DAEMON] Shutdown :: ZeroConf Close :: OK")
    except Exception as e:
        # pass
        logging.error('[DAEMON] Exception on Shutdown :: %s', e)
        logging.debug(traceback.format_exc())
    logging.debug("[DAEMON] Removing PID file %s", Config.pidFile)
    try:
        os.remove(Config.pidFile)
    except Exception:
        pass
    try:
        jeedom_socket.close()
    except Exception:
        pass
    logging.info("[DAEMON] Shutdown :: Exit 0")
    sys.stdout.flush()
    os._exit(0)

# ----------------------------------------------------------------------------

# ***** PROGRAMME PRINCIPAL *****

parser = argparse.ArgumentParser(description='TTSCast Daemon for Jeedom plugin')
parser.add_argument("--loglevel", help="Log Level for the daemon", type=str)
parser.add_argument("--pluginversion", help="Plugin Version", type=str)
parser.add_argument("--callback", help="Callback", type=str)
parser.add_argument("--apikey", help="ApiKey", type=str)
parser.add_argument("--apittskey", help="ApiTTS Key", type=str)
parser.add_argument("--gcloudapikey", help="Google Cloud TTS ApiKey", type=str)
parser.add_argument("--voicerssapikey", help="Voice RSS ApiKey", type=str)
parser.add_argument("--cyclefactor", help="Cycle Factor", type=str)
parser.add_argument("--ttsweb", help="Jeedom Web Server", type=str)
parser.add_argument("--pid", help="Pid file", type=str)
parser.add_argument("--socketport", help="Port for TTSCast server", type=str)

args = parser.parse_args()
if args.loglevel:
    Config.logLevel = args.loglevel
if args.pluginversion:
    Config.pluginVersion = args.pluginversion
if args.callback:
    Config.callBack = args.callback
if args.apikey:
    Config.apiKey = args.apikey
if args.apikey:
    Config.apiTTSKey = args.apittskey
if args.gcloudapikey:
    Config.gCloudApiKey = args.gcloudapikey
if args.voicerssapikey:
    Config.apiRSSKey = args.voicerssapikey
if args.pid:
    Config.pidFile = args.pid
if args.cyclefactor:
    Config.cycleFactor = float(args.cyclefactor)
if args.socketport:
    Config.socketPort = int(args.socketport)
if args.ttsweb:
    Config.ttsWebSrvCache = urljoin(args.ttsweb, 'plugins/ttscast/data/cache/')
    Config.ttsWebSrvMedia = urljoin(args.ttsweb, 'plugins/ttscast/data/media/')
    Config.ttsWebSrvImages = urljoin(args.ttsweb, 'plugins/ttscast/data/images/')
    Config.ttsWebSrvJeeTTS = urljoin(args.ttsweb, 'core/api/')

jeedom_utils.set_log_level(Config.logLevel)

if (Config.cycleFactor == 0):
    Config.cycleFactor = 1
Config.cycleEvent = float(Config.cycleEvent * Config.cycleFactor)
Config.cycleMain = float(Config.cycleMain * Config.cycleFactor)

logging.info('[DAEMON][MAIN] Start ttscastd')
logging.info('[DAEMON][MAIN] Plugin Version: %s', Config.pluginVersion)
logging.info('[DAEMON][MAIN] Log level: %s', Config.logLevel)
logging.info('[DAEMON][MAIN] Socket port: %s', Config.socketPort)
logging.info('[DAEMON][MAIN] Socket host: %s', Config.socketHost)
logging.info('[DAEMON][MAIN] CycleFactor: %s', Config.cycleFactor)
# TODO ***** Ajouter le cycle pour les events cycleEvent *****
logging.info('[DAEMON][MAIN] PID file: %s', Config.pidFile)
logging.info('[DAEMON][MAIN] ApiKey: %s', "***")
logging.info('[DAEMON][MAIN] ApiTTSKey: %s', "***")
logging.info('[DAEMON][MAIN] Google Cloud ApiKey: %s', Config.gCloudApiKey)
logging.info('[DAEMON][MAIN] VoiceRSS ApiKey: %s', "***")
logging.info('[DAEMON][MAIN] CallBack: %s', Config.callBack)
logging.info('[DAEMON][MAIN] Jeedom WebSrvCache: %s', Config.ttsWebSrvCache)
logging.info('[DAEMON][MAIN] Jeedom WebSrvMedia: %s', Config.ttsWebSrvMedia)
logging.info('[DAEMON][MAIN] Jeedom WebSrvImages: %s', Config.ttsWebSrvImages)
logging.info('[DAEMON][MAIN] Jeedom WebSrvJeeTTS: %s', Config.ttsWebSrvJeeTTS)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

try:
    jeedom_utils.write_pid(str(Config.pidFile))
    Comm.sendToJeedom = jeedom_com(apikey=Config.apiKey, url=Config.callBack, cycle=Config.cycleEvent)
    if not Comm.sendToJeedom.test():
        logging.error('[DAEMON][JEEDOMCOM] sendToJeedom :: Network communication ERROR (Daemon to Jeedom)')
        shutdown()
    else:
        logging.info('[DAEMON][JEEDOMCOM] sendToJeedom :: Network communication OK (Daemon to Jeedom)')
    jeedom_socket = jeedom_socket(port=Config.socketPort, address=Config.socketHost)
    Loops.mainLoop(Config.cycleMain)
except Exception as e:
    logging.error('[DAEMON][MAIN] Fatal error: %s', e)
    logging.info(traceback.format_exc())
    shutdown()
