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

try:
    from jeedom.jeedom import *
    # from jeedom.jeedom import jeedom_socket, jeedom_utils, jeedom_com, JEEDOM_SOCKET_MESSAGE
except ImportError:
    print("[DAEMON][IMPORT] Error: importing module jeedom.jeedom")
    sys.exit(1)

# Import pour PyChromeCast
try:    
    from google.oauth2 import service_account
    import google.cloud.texttospeech as googleCloudTTS
    import pychromecast
    from pychromecast import quick_play
    import zeroconf
except ImportError:
    print("[DAEMON][IMPORT] Error: importing module TTS")
    sys.exit(1)

# Import gTTS (Google Translate TTS)
try:
    from gtts import gTTS
except ImportError: 
    print("[DAEMON][IMPORT] Error: importing module gTTS")
    sys.exit(1)

# Import pyDub (Audio changing)
try:
    from pydub import AudioSegment
except ImportError: 
    print("[DAEMON][IMPORT] Error: importing module gTTS")
    sys.exit(1)


# Import Config
try:
    from utils import Utils, Config
except ImportError:
    print("[DAEMON][IMPORT] Error: importing module config")
    sys.exit(1)

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
                if message['cmd'] == 'purgettscache':
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
                elif message['cmd'] == "removecast":
                    if 'uuid' in message and message['host'] in Config.KNOWN_HOSTS:
                        Config.KNOWN_HOSTS.remove(message['host'])
                        logging.debug('[DAEMON][SOCKET] Remove Cast from KNOWN Devices :: %s', str(Config.KNOWN_HOSTS))
                elif message['cmd'] == 'playtesttts':
                    logging.debug('[DAEMON][SOCKET] Generate And Play Test TTS')
                    if all(keys in message for keys in ('ttsText', 'ttsGoogleName', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed')):
                        logging.debug('[DAEMON][SOCKET] Test TTS :: %s', message['ttsText'] + ' | ' + message['ttsGoogleName'] + ' | ' + message['ttsVoiceName'] + ' | ' + message['ttsLang'] + ' | ' + message['ttsEngine'] + ' | ' + message['ttsSpeed'])
                        gCloudTTS.generateTestTTS(message['ttsText'], message['ttsGoogleName'], message['ttsVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'])
                    else:
                        logging.debug('[DAEMON][SOCKET] Test TTS :: Il manque des données pour traiter la commande.')
                elif message['cmd'] == 'playtts':
                    logging.debug('[DAEMON][SOCKET] Generate And Play TTS')
                    if all(keys in message for keys in ('ttsText', 'ttsGoogleUUID', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed', 'ttsVolume')):
                        logging.debug('[DAEMON][SOCKET] TTS :: %s', message['ttsText'] + ' | ' + message['ttsGoogleUUID'] + ' | ' + message['ttsVoiceName'] + ' | ' + message['ttsLang'] + ' | ' + message['ttsEngine'] + ' | ' + message['ttsSpeed'] + ' | ' + message['ttsVolume'])
                        gCloudTTS.getTTS(message['ttsText'], message['ttsGoogleUUID'], message['ttsVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'], message['ttsVolume'])
                    else:
                        logging.debug('[DAEMON][SOCKET] TTS :: Il manque des données pour traiter la commande.')
                elif message['cmd'] == "scanOn":
                    logging.debug('[DAEMON][SOCKET] ScanState = scanOn')
                    Config.ScanMode = True
                    Config.ScanModeStart = int(time.time())
                    Utils.sendToJeedom.send_change_immediate({'scanState': 'scanOn'})
                elif message['cmd'] == "scanOff":
                    logging.debug('[DAEMON][SOCKET] ScanState = scanOff')
                    Config.ScanMode = False
                    Utils.sendToJeedom.send_change_immediate({'scanState': 'scanOff'})
                    
            except Exception as e:
                logging.error('[DAEMON][SOCKET] Send command to daemon error :: %s', e)
                logging.debug(traceback.format_exc())
        time.sleep(cycle)
        

# *** Boucle principale infinie (daemon) ***
def mainLoop(cycle=2):
    jeedom_socket.open()
    logging.info('[DAEMON][MAINLOOP] Starting MainLoop')
    # *** Thread pour les Event venant de Jeedom ***
    threading.Thread(target=eventsFromJeedom, args=(Config.cycleEvent,)).start()
    try:
        # Thread pour le browsermanager (pychromecast)
        # Config.NETCAST_BROWSERMANAGER = castBrowserManager()
        # Config.NETCAST_BROWSERMANAGER.start()
        
        Utils.sendToJeedom.send_change_immediate({'daemonStarted': '1'})
                
        while not Config.IS_ENDING:
            try:
                # *** Actions de la MainLoop ***
                currentTime = int(time.time())
                
                # Arrêt du ScanMode au bout de 60 secondes
                if (Config.ScanMode and (Config.ScanModeStart + Config.ScanModeTimeOut) <= currentTime):
                    Config.ScanMode = False
                    logging.info('[DAEMON][MAINLOOP] ScanMode END')
                    Utils.sendToJeedom.send_change_immediate({'scanState': 'scanOff'})
                # Heartbeat du démon
                if ((Config.HeartbeatLastTime + Config.HeartbeatFrequency) <= currentTime):
                    logging.debug('[DAEMON][MAINLOOP] Heartbeat = 1')
                    Utils.sendToJeedom.send_change_immediate({'heartbeat': '1'})
                    Config.HeartbeatLastTime = currentTime
                # Scan New Chromecast
                if not Config.ScanPending:
                    if Config.ScanMode and (Config.ScanLastTime < Config.ScanModeStart):
                        threading.Thread(target=scanChromeCast, args=('ScanMode',)).start()
                    elif (Config.ScanLastTime + Config.ScanSchedule <= currentTime):
                        threading.Thread(target=scanChromeCast, args=('ScheduleMode',)).start()
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

# ----------------------------------------------------------------------------

def scanChromeCast(_mode='UNKOWN'):
    try:
        logging.debug('[DAEMON][SCANNER] Start Scanner :: %s', _mode)
        Config.ScanPending = True
        
        if (_mode == "ScanMode"):
            currentTime = int(time.time())
            currentTimeStr = datetime.datetime.fromtimestamp(currentTime).strftime("%d/%m/%Y - %H:%M:%S")

            chromecasts, browser = pychromecast.discovery.discover_chromecasts(known_hosts=Config.KNOWN_HOSTS)
            browser.stop_discovery()
            
            logging.debug('[DAMEON][SCANNER] Devices découverts :: %s', len(chromecasts))
            for device in chromecasts: 
                logging.debug('[DAMEON][SCANNER] Device Chromecast :: %s (%s) @ %s:%s uuid: %s', device.friendly_name, device.model_name, device.host, device.port, device.uuid)
                data = {
                    'friendly_name': device.friendly_name,
                    'uuid': str(device.uuid),
                    'lastscan': currentTimeStr,
                    'model_name': device.model_name,
                    'cast_type': device.cast_type,
                    'manufacturer': device.manufacturer,
                    'host': device.host,
                    'port': device.port,
                    'scanmode': 1
                }
                # Envoi vers Jeedom
                Utils.sendToJeedom.add_changes('devices::' + data['uuid'], data)
        elif (_mode == "ScheduleMode"):
            # ScheduleMode
            currentTime = int(time.time())
            currentTimeStr = datetime.datetime.fromtimestamp(currentTime).strftime("%d/%m/%Y - %H:%M:%S")

            # chromecasts, browser = pychromecast.get_chromecasts(known_hosts=Config.KNOWN_HOSTS)
            # res = [sub['uuid'] for sub in Config.KNOWN_HOSTS]
            chromecasts, browser = pychromecast.get_listed_chromecasts(uuids=[Config.GCAST_UUID], known_hosts=Config.KNOWN_HOSTS)
            logging.debug('[DAMEON][SCANNER][SCHEDULE] GCAST UUID :: %s', str(Config.GCAST_UUID))
            logging.debug('[DAMEON][SCANNER][SCHEDULE] Nb Cast :: %s', len(chromecasts))
            for cast in chromecasts: 
                logging.debug('[DAMEON][SCANNER][SCHEDULE] Chromecast :: uuid: %s', cast.uuid)
                
                # Connexion au Chromecast
                cast.wait(timeout=10)
                castVolumeLevel = int(cast.status.volume_level * 100)
                cast.status
                data = {
                    'uuid': str(cast.uuid),
                    'lastschedule': currentTimeStr,
                    'volumelevel': castVolumeLevel,
                    'schedule': 1
                }
                # Déconnexion du Chromecast
                cast.disconnect(timeout=10, blocking=False)
                # Envoi vers Jeedom
                Utils.sendToJeedom.add_changes('casts::' + data['uuid'], data)
                
            browser.stop_discovery()
            Config.ScanLastTime = currentTime
            
    except Exception as e:
        logging.error('[DAEMON][SCANNER] Exception on Scanner :: %s', e)
        logging.debug(traceback.format_exc())
    
    Config.ScanLastTime = int(time.time())
    Config.ScanPending = False
                    
class gCloudTTS:
    """ Class Google TTS """
    
    def changeSpeedTTS(soundfile, speed):
        logging.debug('[DAEMON][TestTTS] ChangeSpeed File :: %s', soundfile)
    
    def generateTestTTS(ttsText, ttsGoogleName, ttsVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0'):
        logging.debug('[DAEMON][TestTTS] TTSEngine :: %s', ttsEngine)
        
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
                res = gCloudTTS.castToGoogleHome(urlFileToPlay, ttsGoogleName)
                logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            else:
                logging.warning('[DAEMON][TestTTS] Clé API invalide :: ' + Config.gCloudApiKey)
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
            
            res = gCloudTTS.castToGoogleHome(urlFileToPlay, ttsGoogleName)
            logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
        elif ttsEngine == "jeedomtts":
            logging.debug('[DAEMON][TestTTS] TTSEngine = jeedomtts')
            
            raw_filename = ttsText + "|JeedomTTS|" + ttsLang
            filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
            filepath = os.path.join(symLinkPath, filename)
            logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
            
            if not os.path.isfile(filepath):
                ttsfile = Functions.jeedomTTS(ttsText, ttsLang)
                if ttsfile is not None:
                    with open(filepath, 'wb') as f:
                        f.write(ttsfile)
                else:
                    logging.debug('[DAEMON][TestTTS] JeedomTTS Error :: Incorrect Output')
            else:
                logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            urlFileToPlay = urljoin(ttsSrvWeb, filename)
            logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
            
            res = gCloudTTS.castToGoogleHome(urlFileToPlay, ttsGoogleName)
            logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            
    def getTTS(ttsText, ttsGoogleUUID, ttsVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0', ttsVolume='30'):
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
                res = gCloudTTS.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=int(ttsVolume))
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
            
            res = gCloudTTS.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=int(ttsVolume))
            logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
        elif ttsEngine == "jeedomtts":
            logging.debug('[DAEMON][TTS] TTSEngine = jeedomtts')
            
            raw_filename = ttsText + "|JeedomTTS|" + ttsLang
            filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
            filepath = os.path.join(symLinkPath, filename)
            logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
            
            if not os.path.isfile(filepath):
                ttsfile = Functions.jeedomTTS(ttsText, ttsLang)
                if ttsfile is not None:
                    with open(filepath, 'wb') as f:
                        f.write(ttsfile)
                else:
                    logging.debug('[DAEMON][TTS] JeedomTTS Error :: Incorrect Output')
            else:
                logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            urlFileToPlay = urljoin(ttsSrvWeb, filename)
            logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
            
            res = gCloudTTS.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=int(ttsVolume))
            logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))

    def castToGoogleHome(urltoplay, googleName='', googleUUID='', volumeForPlay=30):
        if googleName != '':
            logging.debug('[DAEMON][Cast] Diffusion sur le Google Home :: %s', googleName)
            chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[googleName])
            if not chromecasts:
                logging.debug('[DAEMON][Cast] Aucun Chromecast avec ce nom :: %s', googleName)
                browser.stop_discovery()
                return False        
            cast = chromecasts[0]
            cast.wait(timeout=10)
            logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
            
            volumeBeforePlay = cast.status.volume_level
            logging.debug('[DAEMON][Cast] Volume avant lecture :: %s', volumeBeforePlay)
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
            
            logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', cast.media_controller.status)
            
            while cast.media_controller.status.player_state == 'PLAYING':
                time.sleep(1)
                logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', cast.media_controller.status)
            
            cast.quit_app()
            cast.set_volume(volume=volumeBeforePlay)
            cast.disconnect(timeout=10, blocking=False)
            browser.stop_discovery()
            return True
        elif googleUUID != '':
            logging.debug('[DAEMON][Cast] Diffusion sur le Google Home :: %s', googleUUID)
            uuid = UUID(googleUUID)
            chromecasts, browser = pychromecast.get_listed_chromecasts(uuids=[uuid])
            if not chromecasts:
                logging.debug('[DAEMON][Cast] Aucun Chromecast avec cet UUID :: %s', googleUUID)
                browser.stop_discovery()
                return False        
            cast = chromecasts[0]
            cast.wait(timeout=10)
            logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
            
            volumeBeforePlay = cast.status.volume_level
            logging.debug('[DAEMON][Cast] Volume avant lecture :: %s', volumeBeforePlay)
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
            
            logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', cast.media_controller.status)
            
            while cast.media_controller.status.player_state == 'PLAYING':
                time.sleep(1)
                logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', cast.media_controller.status)
            
            cast.quit_app()
            cast.set_volume(volume=volumeBeforePlay)
            cast.disconnect(timeout=10, blocking=False)
            browser.stop_discovery()
            return True
        else:
            logging.debug('[DAEMON][Cast] Diffusion impossible (GoogleHome + GoogleUUID manquants)')
            return False

class Functions:
    """ Class Functions """
    def purgeCache(nbDays='0'):
        if nbDays == '0':  # clean entire directory including containing folder
            logging.debug('[DAEMON][PURGE-CACHE] nbDays is 0.')
            try:
                if os.path.exists(Config.ttsCacheFolderTmp):
                    shutil.rmtree(Config.ttsCacheFolderTmp)
            except Exception as e:
                logging.error('[DAEMON][PURGE-CACHE] Error while cleaning cache entirely (nbDays = 0) :: %s', e)
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
                pass
    
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
            filecontent = None
        return filecontent
            
# ----------------------------------------------------------------------------

def handler(signum=None, frame=None):
    logging.debug("[DAEMON] Signal %i caught, exiting...", int(signum))
    shutdown()

def shutdown():
    logging.debug("[DAEMON] Shutdown")
    Config.IS_ENDING = True
    logging.debug("[DAEMON] Removing PID file %s", Config.pidFile)
    try:
        os.remove(Config.pidFile)
    except Exception:
        pass
    try:
        jeedom_socket.close()
    except Exception:
        pass
    logging.debug("[DAEMON] Exit 0")
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
logging.info('[DAEMON][MAIN] CallBack: %s', Config.callBack)
logging.info('[DAEMON][MAIN] Jeedom WebSrvCache: %s', Config.ttsWebSrvCache)
logging.info('[DAEMON][MAIN] Jeedom WebSrvMedia: %s', Config.ttsWebSrvMedia)
logging.info('[DAEMON][MAIN] Jeedom WebSrvImages: %s', Config.ttsWebSrvImages)
logging.info('[DAEMON][MAIN] Jeedom WebSrvJeeTTS: %s', Config.ttsWebSrvJeeTTS)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

try:
    jeedom_utils.write_pid(str(Config.pidFile))
    Utils.sendToJeedom = jeedom_com(apikey=Config.apiKey, url=Config.callBack, cycle=Config.cycleEvent)
    if not Utils.sendToJeedom.test():
        logging.error('[DAEMON][JEEDOMCOM] sendToJeedom :: Network communication ERROR (Daemon to Jeedom)')
        shutdown()
    else:
        logging.info('[DAEMON][JEEDOMCOM] sendToJeedom :: Network communication OK (Daemon to Jeedom)')
    jeedom_socket = jeedom_socket(port=Config.socketPort, address=Config.socketHost)
    mainLoop(Config.cycleMain)
except Exception as e:
    logging.error('[DAEMON][MAIN] Fatal error: %s', e)
    logging.info(traceback.format_exc())
    shutdown()
