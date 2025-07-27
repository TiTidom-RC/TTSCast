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

from urllib.parse import urljoin, urlencode, urlparse
from uuid import UUID

# Import pour Jeedom
try:
    # from jeedom.jeedom import *
    from jeedom.jeedom import jeedom_socket, jeedom_utils, jeedom_com, JEEDOM_SOCKET_MESSAGE  # jeedom_serial
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
    from pychromecast.socket_client import ConnectionStatusListener
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

# Import GenAI (Gemini)
try:
    from google import genai
    from google.genai import types
    import markdown
    from bs4 import BeautifulSoup
except ImportError as e:
    print("[DAEMON][IMPORT] Error: importing modules for GenAI ::", e)
    sys.exit(1)

# Import Config
try:
    from utils import Comm, Config
except ImportError as e:
    print("[DAEMON][IMPORT] Error: importing module config ::", e)
    sys.exit(1)

class Loops:
    # *** Boucle events from Jeedom ***
    def eventsFromJeedom(cycle=0.5):
        # global JEEDOM_SOCKET_MESSAGE
        while not myConfig.IS_ENDING:    
            if not JEEDOM_SOCKET_MESSAGE.empty():
                logging.debug("[DAEMON][SOCKET] Message received in socket JEEDOM_SOCKET_MESSAGE")
                
                message = json.loads(JEEDOM_SOCKET_MESSAGE.get().decode('utf-8'))
                
                if message['apikey'] != myConfig.apiKey:
                    logging.error("[DAEMON][SOCKET] Invalid apikey from socket :: %s", message['apikey'])
                    return
                
                try:
                    # TODO ***** Gestion des messages reçus de Jeedom *****
                    if message['cmd'] == 'action':
                        # TODO ***** Gestion des actions
                        logging.debug('[DAEMON][SOCKET] Action')
                        
                        if 'cmd_action' in message:
                            
                            # Traitement des actions (inclus les CustomCmd)
                            if message['cmd_action'] == 'ttstest':
                                logging.debug('[DAEMON][SOCKET] Generate And Play Test TTS')

                                if all(keys in message for keys in ('ttsText', 'ttsGoogleName', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed', 'ttsRSSSpeed', 'ttsRSSVoiceName', 'ttsSSML', 'ttsAI')):
                                    logging.debug('[DAEMON][SOCKET] Test TTS :: %s', message['ttsText'] + ' | ' + message['ttsGoogleName'] + ' | ' + message['ttsVoiceName'] + ' | ' + message['ttsLang'] + ' | ' + message['ttsEngine'] + ' | ' + message['ttsSpeed'] + ' | ' + message['ttsRSSVoiceName'] + ' | ' + message['ttsRSSSpeed'] + ' | ' + message['ttsSSML'] + ' | ' + message['ttsAI'])
                                    threading.Thread(target=TTSCast.generateTestTTS, args=[message['ttsText'], message['ttsGoogleName'], message['ttsVoiceName'], message['ttsRSSVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'], message['ttsRSSSpeed'], message['ttsSSML'], message['ttsAI']]).start()
                                else:
                                    logging.debug('[DAEMON][SOCKET] Test TTS :: Il manque des données pour traiter la commande.')
                            
                            elif message['cmd_action'] == 'tts':
                                logging.debug('[DAEMON][SOCKET] Generate And Play TTS')
                        
                                if all(keys in message for keys in ('ttsText', 'ttsGoogleUUID', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed', 'ttsOptions', 'ttsRSSSpeed', 'ttsRSSVoiceName')):
                                    logging.debug('[DAEMON][SOCKET] TTS :: %s', str(message))                                    
                                    threading.Thread(target=TTSCast.getTTS, args=[message['ttsText'], message['ttsGoogleUUID'], message['ttsVoiceName'], message['ttsRSSVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'], message['ttsRSSSpeed'], message['ttsOptions']]).start()
                                else:
                                    logging.debug('[DAEMON][SOCKET] TTS :: Il manque des données pour traiter la commande.')
                                    
                            elif message['cmd_action'] == 'generatetts':
                                logging.debug('[DAEMON][SOCKET] Generate TTS as Jeedom Engine')
                                
                                if all(keys in message for keys in ('ttsText', 'ttsFile', 'ttsVoiceName', 'ttsLang', 'ttsEngine', 'ttsSpeed', 'ttsOptions', 'ttsRSSSpeed', 'ttsRSSVoiceName')):
                                    logging.debug('[DAEMON][SOCKET] GenerateTTS :: %s', str(message))
                                    threading.Thread(target=TTSCast.generateTTS, args=[message['ttsText'], message['ttsFile'], message['ttsVoiceName'], message['ttsRSSVoiceName'], message['ttsLang'], message['ttsEngine'], message['ttsSpeed'], message['ttsRSSSpeed'], message['ttsOptions']]).start()
                                else:
                                    logging.debug('[DAEMON][SOCKET] GenerateTTS :: Il manque des données pour traiter la commande.')
                            
                            elif (message['cmd_action'] == 'volumeset' and all(keys in message for keys in ('value', 'googleUUID'))):
                                logging.debug('[DAEMON][SOCKET] Action :: VolumeSet = %s @ %s', message['value'], message['googleUUID'])
                                threading.Thread(target=Functions.mediaActions, args=[message['googleUUID'], message['value'], message['cmd_action']]).start()
                            
                            elif (message['cmd_action'] in ('volumeup', 'volumedown', 'media_pause', 'media_play', 'media_stop', 'media_next', 'media_quit', 'media_rewind', 'media_previous', 'mute_on', 'mute_off') and 'googleUUID' in message):
                                logging.debug('[DAEMON][SOCKET] Action :: %s @ %s', message['cmd_action'], message['googleUUID'])
                                threading.Thread(target=Functions.mediaActions, args=[message['googleUUID'], '', message['cmd_action']]).start()
                                
                            elif (message['cmd_action'] in ('youtube', 'dashcast', 'radios', 'customradios', 'sounds', 'customsounds', 'media', 'start_app')):
                                logging.debug('[DAEMON][SOCKET] Media :: %s @ %s', message['cmd_action'], message['googleUUID'])
                                threading.Thread(target=Functions.controllerActions, args=[message['googleUUID'], message['cmd_action'], message['value'], message['options']]).start()
                                
                    elif message['cmd'] == 'purgettscache':
                        logging.debug('[DAEMON][SOCKET] Purge TTS Cache')
                        
                        if 'days' in message:
                            threading.Thread(target=Functions.purgeCache, args=[message['days']]).start()
                        
                        else:
                            threading.Thread(target=Functions.purgeCache).start()
                            
                    elif message['cmd'] == "addcast":
                        
                        if all(keys in message for keys in ('uuid', 'host', 'friendly_name')):
                            _uuid = UUID(message['uuid'])
                            
                            if message['host'] not in myConfig.KNOWN_HOSTS:
                                myConfig.KNOWN_HOSTS.append(message['host'])
                                logging.debug('[DAEMON][SOCKET] Add Cast to KNOWN Devices :: %s', str(myConfig.KNOWN_HOSTS))
                            
                            if message['friendly_name'] not in myConfig.GCAST_NAMES: 
                                myConfig.GCAST_NAMES.append(message['friendly_name'])
                                logging.debug('[DAEMON][SOCKET] Add Cast to GCAST Names :: %s', str(myConfig.GCAST_NAMES))
                            
                            if _uuid not in myConfig.GCAST_UUID:
                                myConfig.GCAST_UUID.append(_uuid)
                                logging.debug('[DAEMON][SOCKET] Add Cast to GCAST UUID :: %s', str(myConfig.GCAST_UUID))
                                myCast.castListeners(uuid=_uuid)
                            
                            if message['uuid'] not in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[message['uuid']] = 0
                                logging.debug('[DAEMON][SOCKET] Add Wait Queue for Device :: %s', message['uuid'])
                                
                    elif message['cmd'] == "removecast":
                        if all(keys in message for keys in ('uuid', 'host', 'friendly_name')):
                            _uuid = UUID(message['uuid'])
                            
                            if message['host'] in myConfig.KNOWN_HOSTS:
                                myConfig.KNOWN_HOSTS.remove(message['host'])
                                logging.debug('[DAEMON][SOCKET] Remove Cast from KNOWN Devices :: %s', str(myConfig.KNOWN_HOSTS))
                            
                            if message['friendly_name'] in myConfig.GCAST_NAMES: 
                                myConfig.GCAST_NAMES.remove(message['friendly_name'])
                                logging.debug('[DAEMON][SOCKET] Remove Cast from GCAST Names :: %s', str(myConfig.GCAST_NAMES))
                            
                            if _uuid in myConfig.GCAST_UUID:
                                myConfig.GCAST_UUID.remove(_uuid)
                                logging.debug('[DAEMON][SOCKET] Remove Cast from GCAST UUID :: %s', str(myConfig.GCAST_UUID))
                                myCast.castRemove(uuid=_uuid)
                            
                            if message['uuid'] in myConfig.cmdWaitQueue:
                                del myConfig.cmdWaitQueue[message['uuid']]
                                logging.debug('[DAEMON][SOCKET] Remove Wait Queue for Device :: %s', message['uuid'])
                            
                    elif message['cmd'] == "scanOn":
                        logging.debug('[DAEMON][SOCKET] ScanState = scanOn')
                        
                        myConfig.ScanMode = True
                        myConfig.ScanModeStart = int(time.time())
                        Comm.sendToJeedom.send_change_immediate({'scanState': 'scanOn'})
                        
                    elif message['cmd'] == "scanOff":
                        logging.debug('[DAEMON][SOCKET] ScanState = scanOff')
                        
                        myConfig.ScanMode = False
                        Comm.sendToJeedom.send_change_immediate({'scanState': 'scanOff'})
                        
                except Exception as e:
                    logging.error('[DAEMON][SOCKET] Send command to daemon error :: %s', e)
                    logging.debug(traceback.format_exc())
            time.sleep(cycle)
        
    # *** Boucle principale infinie (daemon) ***
    def mainLoop(cycle=2):
        my_jeedom_socket.open()
        logging.info('[DAEMON][MAINLOOP] Starting MainLoop')
        
        # *** Thread pour les Event venant de Jeedom ***
        threading.Thread(target=Loops.eventsFromJeedom, args=(myConfig.cycleEvent,)).start()
        
        try:
            # Thread pour le browser (pychromecast)
            myConfig.NETCAST_ZCONF = zeroconf.Zeroconf()
            myConfig.NETCAST_BROWSER = pychromecast.get_chromecasts(tries=None, retry_wait=5, timeout=30, blocking=False, callback=myCast.castCallBack, zeroconf_instance=myConfig.NETCAST_ZCONF, known_hosts=myConfig.KNOWN_HOSTS)

            logging.info('[DAEMON][MAINLOOP][NETCAST] Listening for Chromecast events...')

            # Informer Jeedom que le démon est démarré
            Comm.sendToJeedom.send_change_immediate({'daemonStarted': '1'})

            while not myConfig.IS_ENDING:
                try:
                    # *** Actions de la MainLoop ***
                    currentTime = int(time.time())
                    
                    # Arrêt du ScanMode au bout de 60 secondes
                    if (myConfig.ScanMode and (myConfig.ScanModeStart + myConfig.ScanModeTimeOut) <= currentTime):
                        myConfig.ScanMode = False
                        logging.info('[DAEMON][MAINLOOP] ScanMode END')
                        Comm.sendToJeedom.send_change_immediate({'scanState': 'scanOff'})
                    # Heartbeat du démon
                    if ((myConfig.HeartbeatLastTime + myConfig.HeartbeatFrequency) <= currentTime):
                        logging.info('[DAEMON][MAINLOOP] Heartbeat = 1')
                        Comm.sendToJeedom.send_change_immediate({'heartbeat': '1'})
                        myConfig.HeartbeatLastTime = currentTime
                        Functions.getResourcesUsage()
                    # Scan New Chromecast
                    if not myConfig.ScanPending:
                        if myConfig.ScanMode and (myConfig.ScanLastTime < myConfig.ScanModeStart):
                            threading.Thread(target=Functions.scanChromeCast, args=('ScanMode',)).start()
                        elif (myConfig.ScanLastTime + myConfig.ScanSchedule <= currentTime):
                            logging.debug('[DAEMON][SCANNER][SCHEDULE][CALL] GCAST Names :: %s', str(myConfig.GCAST_NAMES))
                            threading.Thread(target=Functions.scanChromeCast, args=('ScheduleMode',)).start()
                    else:
                        logging.debug('[DAEMON][MAINLOOP] ScanMode : SCAN PENDING !')
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
            # ttsParams = 'tts.php?apikey=' + myConfig.apiTTSKey + '&voice=' + ttsLang + '&path=1&text=' + quote(ttsText, safe='')
            # ttsFullURI = urljoin(myConfig.ttsWebSrvJeeTTS, ttsParams)
            ttsFullURI = urljoin(myConfig.ttsWebSrvJeeTTS, 'tts.php')
            logging.debug('[DAEMON][JeedomTTS] ttsFullURI :: %s', ttsFullURI)
            logging.debug('[DAEMON][JeedomTTS] ttsText Length :: %s', str(len(ttsText)))
            
            ttsHeaders = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            ttsParams = {
                'apikey': myConfig.apiTTSKey,
                'voice': ttsLang,
                'path': 1,
                'text': ttsText
            }
            
            response = requests.post(ttsFullURI, headers=ttsHeaders, data=urlencode(ttsParams), timeout=30, verify=False)
            filecontent = response.content
            
            # response = requests.post(ttsFullURI, timeout=30, verify=False)
            # filecontent = response.content
            
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
    
    def voiceRSS(ttsText, ttsLang, ttsSpeed='0', ttsSSML=False):
        filecontent = None
        try:
            ttsLangCode = "-".join(ttsLang.split("-")[:2])
            ttsVoiceName = ttsLang.split("-")[2:][0]
            ttsUseSSML = 'true' if ttsSSML else 'false'
            
            logging.debug('[DAEMON][VoiceRSS] LanguageCode / VoiceName :: %s / %s', ttsLangCode, ttsVoiceName)
            
            ttsHeaders = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            
            # TODO Formats disponibles pour VoiceRSS : 16khz_16bit_mono ? 22khz_8bit_mono ? 22khz_16bit_mono ? 24khz_8bit_mono ? 24khz_16bit_mono ? 32khz_8bit_mono ? 32khz_16bit_mono ? 44khz_8bit_mono ? 44khz_16bit_mono ? 48khz_8bit_mono ? 48khz_16bit_mono ?  
            ttsParams = {
                "key": myConfig.apiRSSKey,
                "hl": ttsLangCode,
                "v": ttsVoiceName,
                "src": ttsText,
                "r": ttsSpeed,
                "c": 'mp3',
                "f": '16khz_16bit_mono',
                "ssml": ttsUseSSML,
                "b64": 'false'
            }
            
            response = requests.post(myConfig.ttsVoiceRSSUrl, headers=ttsHeaders, data=urlencode(ttsParams), timeout=30, verify=True)
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
    
    def generateTestTTS(ttsText, ttsGoogleName, ttsVoiceName, ttsRSSVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0', ttsRSSSpeed='0', ttsSSML='0', ttsAI='0'):
        logging.debug('[DAEMON][TestTTS] Param TTSEngine :: %s', ttsEngine)
        
        logging.debug('[DAEMON][TestTTS] Check des répertoires')
        cachePath = myConfig.ttsCacheFolderWeb
        symLinkPath = myConfig.ttsCacheFolderTmp
        ttsSrvWeb = myConfig.ttsWebSrvCache
        
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
            if myConfig.gCloudApiKey != 'noKey':
                credentials = service_account.Credentials.from_service_account_file(os.path.join(myConfig.configFullPath, myConfig.gCloudApiKey))

                logging.debug('[DAEMON][TestTTS] Test et génération du fichier TTS (mp3)')
                raw_filename = ttsText + "|gCloudTTS|" + ttsVoiceName + "|" + ttsSpeed + "|" + ttsSSML
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                
                logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath) or ttsAI == '1':
                    language_code = "-".join(ttsVoiceName.split("-")[:2])
                    logging.debug('[DAEMON][TestTTS] LanguageCode :: %s', language_code)
                    if ttsSSML == '1':
                        logging.debug('[DAEMON][TestTTS] Génération du TTS avec SSML')
                        text_input = googleCloudTTS.SynthesisInput(ssml=ttsText)
                    elif ttsAI == '1':
                        ttsAIText = TTSCast.genAI(ttsText)
                        if ttsAIText is not None:
                            logging.debug('[DAEMON][TestTTS] Génération du TTS avec IA')
                            text_input = googleCloudTTS.SynthesisInput(text=ttsAIText)
                        else:
                            logging.error('[DAEMON][TestTTS] Erreur lors de la génération du TTS avec IA. Génération du TTS sans IA (Backup)')
                            text_input = googleCloudTTS.SynthesisInput(text=ttsText)
                    else:
                        logging.debug('[DAEMON][TestTTS] Génération du TTS')
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
                logging.warning('[DAEMON][TestTTS] Clé API (Google Cloud TTS) invalide :: ' + myConfig.gCloudApiKey)
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
                ttsResult = TTSCast.jeedomTTS(ttsText, ttsLang)
                if ttsResult is not None:
                    with open(filepath, 'wb') as f:
                        f.write(ttsResult)
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
            if myConfig.apiRSSKey != 'noKey':
                raw_filename = ttsText + "|VoiceRSSTTS|" + ttsRSSVoiceName + "|" + ttsRSSSpeed + "|" + ttsSSML
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                logging.debug('[DAEMON][TestTTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    ttsResult = TTSCast.voiceRSS(ttsText, ttsRSSVoiceName, ttsRSSSpeed, True if ttsSSML == '1' else False)
                    if ttsResult is not None:
                        with open(filepath, 'wb') as f:
                            f.write(ttsResult)
                    else:
                        logging.debug('[DAEMON][TestTTS] VoiceRSS Error :: Incorrect Output')
                else:
                    logging.debug('[DAEMON][TestTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                
                urlFileToPlay = urljoin(ttsSrvWeb, filename)
                logging.debug('[DAEMON][TestTTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                
                res = TTSCast.castToGoogleHome(urlFileToPlay, ttsGoogleName)
                logging.debug('[DAEMON][TestTTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            else:
                logging.warning('[DAEMON][TestTTS] Clé API (Voice RSS) invalide :: ' + myConfig.apiRSSKey)

    def generateTTS(ttsText, ttsFile, ttsVoiceName, ttsRSSVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0', ttsRSSSpeed='0', ttsOptions=None):
        try:
            if not ttsOptions:
                ttsOptions = None
            
            _useAI = False
            _aiCustomTone = None
            _aiCustomSysPrompt = None
            _aiCustomTemp = None
            _useSSML = False
            _silenceBefore = None
            
            try:
                if (ttsOptions is not None):
                    options_json = json.loads("{" + ttsOptions + "}")
                    
                    # AI
                    if myConfig.aiEnabled:
                        _useAI = options_json.get('genai', False)
                        _aiCustomTone = options_json.get('aitone', None)
                        _aiCustomSysPrompt = options_json.get('aisysprompt', myConfig.aiCustomSysPrompt if myConfig.aiUseCustomSysPrompt else None)
                        _aiCustomTemp = options_json.get('aitemp', None)
                    # SSML
                    _useSSML = options_json.get('ssml', False)
                    # Before
                    _silenceBefore = options_json.get('before', None)

                    if _silenceBefore is not None and _useSSML is False:
                        _useSSML = True
                        ttsText = "<speak><break time='" + str(_silenceBefore) + "' /><p>" + ttsText + "</p></speak>"
                        logging.debug('[DAEMON][GenerateTTS] Ajout de %s de silence avant le TTS :: %s', str(_silenceBefore), ttsText)
                    elif _silenceBefore is not None and _useSSML is True:
                        logging.error('[DAEMON][GenerateTTS] Les options "before" et "ssml" ne peuvent pas être utilisées dans la même commande.')
                        return False

                    # Custom Voice
                    _ttsVoiceCode = options_json.get('voice', None)
                    if _ttsVoiceCode is not None:
                        if ttsEngine == "gcloudtts":
                            ttsVoiceName = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (Google Cloud) :: %s', ttsVoiceName)
                        elif ttsEngine == "gtranslatetts":
                            ttsLang = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (Google Translate) :: %s', ttsLang)
                        elif ttsEngine == "voicersstts":
                            ttsRSSVoiceName = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (VoiceRSS) :: %s', ttsRSSVoiceName)
                            
                    logging.debug('[DAEMON][GenerateTTS] Options :: %s', str(options_json))
            except ValueError as e:
                logging.debug('[DAEMON][GenerateTTS] Options mal formatées (Json KO) :: %s', e)
            
            if ttsEngine == "gcloudtts":
                logging.debug('[DAEMON][GenerateTTS] TTSEngine = gcloudtts')
                logging.debug('[DAEMON][GenerateTTS] Import de la clé API :: *** ')
                if myConfig.gCloudApiKey != 'noKey':
                    gKey = os.path.join(myConfig.configFullPath, myConfig.gCloudApiKey)
                    if os.path.exists(gKey):
                        credentials = service_account.Credentials.from_service_account_file(gKey)
                    else:
                        logging.error('[DAEMON][GenerateTTS] Impossible de charger le fichier JSON (clé API : KO) :: %s', gKey)
                        return False

                    logging.debug('[DAEMON][GenerateTTS] Génération du fichier TTS (mp3)')
                    filepath = ttsFile
                    logging.debug('[DAEMON][GenerateTTS] Nom du fichier à générer :: %s', filepath)
                    
                    if not os.path.isfile(filepath) or _useAI:
                        language_code = "-".join(ttsVoiceName.split("-")[:2])
                        if _useSSML:
                            logging.debug('[DAEMON][GenerateTTS] Génération du TTS avec SSML')
                            text_input = googleCloudTTS.SynthesisInput(ssml=ttsText)
                        elif _useAI:
                            ttsAIText = TTSCast.genAI(ttsText, _aiCustomSysPrompt, _aiCustomTone, _aiCustomTemp)
                            if ttsAIText is not None:
                                logging.debug('[DAEMON][GenerateTTS] Génération du TTS avec IA')
                                text_input = googleCloudTTS.SynthesisInput(text=ttsAIText)
                            else:
                                logging.error('[DAEMON][GenerateTTS] Erreur lors de la génération du TTS avec IA. Génération du TTS sans IA (Backup)')
                                text_input = googleCloudTTS.SynthesisInput(text=ttsText)
                        else:
                            logging.debug('[DAEMON][GenerateTTS] Génération du TTS')
                            text_input = googleCloudTTS.SynthesisInput(text=ttsText)
                        voice_params = googleCloudTTS.VoiceSelectionParams(language_code=language_code, name=ttsVoiceName)
                        audio_config = googleCloudTTS.AudioConfig(audio_encoding=googleCloudTTS.AudioEncoding.MP3, effects_profile_id=['small-bluetooth-speaker-class-device'], speaking_rate=float(ttsSpeed))

                        client = googleCloudTTS.TextToSpeechClient(credentials=credentials)
                        response = client.synthesize_speech(input=text_input, voice=voice_params, audio_config=audio_config)

                        with open(filepath, "wb") as out:
                            out.write(response.audio_content)
                            logging.debug('[DAEMON][GenerateTTS] Fichier TTS généré :: %s', filepath)
                    else:
                        logging.debug('[DAEMON][GenerateTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                else:
                    logging.warning('[DAEMON][GenerateTTS] Clé API invalide :: ' + myConfig.gCloudApiKey)
            
            elif ttsEngine == "gtranslatetts":
                logging.debug('[DAEMON][GenerateTTS] TTSEngine = gtranslatetts')
                filepath = ttsFile
                logging.debug('[DAEMON][GenerateTTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    langToTTS = ttsLang.split('-')[0]
                    try:
                        client = gTTS(ttsText, lang=langToTTS)
                        client.save(filepath)
                        logging.debug('[DAEMON][GenerateTTS] Fichier TTS généré :: %s', filepath)
                    except Exception as e:
                        if os.path.isfile(filepath):
                            try:
                                os.remove(filepath)
                            except OSError:
                                pass
                        logging.debug('[DAEMON][GenerateTTS] Google Translate API ERROR :: %s', e)
                else:
                    logging.debug('[DAEMON][GenerateTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
            
            elif ttsEngine == "voicersstts":
                logging.debug('[DAEMON][GenerateTTS] TTSEngine = voicersstts')
                logging.debug('[DAEMON][GenerateTTS] Import de la clé API :: *** ')
                if myConfig.apiRSSKey != 'noKey':
                    filepath = ttsFile
                    logging.debug('[DAEMON][GenerateTTS] Nom du fichier à générer :: %s', filepath)
                    
                    if not os.path.isfile(filepath):
                        ttsResult = TTSCast.voiceRSS(ttsText, ttsRSSVoiceName, ttsRSSSpeed, _useSSML)
                        if ttsResult is not None:
                            with open(filepath, 'wb') as f:
                                f.write(ttsResult)
                            logging.debug('[DAEMON][GenerateTTS] Fichier TTS généré :: %s', filepath)
                        else:
                            logging.debug('[DAEMON][GenerateTTS] VoiceRSS Error :: Incorrect Output')
                    else:
                        logging.debug('[DAEMON][GenerateTTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                else:
                    logging.warning('[DAEMON][GenerateTTS] Clé API (Voice RSS) invalide :: ' + myConfig.apiRSSKey)  
                    
        except Exception as e:
            logging.error('[DAEMON][GenerateTTS] Exception on TTS :: %s', e)
            logging.debug(traceback.format_exc())
                
    def getTTS(ttsText, ttsGoogleUUID, ttsVoiceName, ttsRSSVoiceName, ttsLang, ttsEngine, ttsSpeed='1.0', ttsRSSSpeed='0', ttsOptions=None):
        try:
            logging.debug('[DAEMON][TTS] Check des répertoires')
            cachePath = myConfig.ttsCacheFolderWeb
            symLinkPath = myConfig.ttsCacheFolderTmp
            ttsSrvWeb = myConfig.ttsWebSrvCache
            
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
            _appDing = True
            _cmdWait = None
            _useAI = False
            _aiCustomTone = None
            _aiCustomSysPrompt = None
            _aiCustomTemp = None
            _useSSML = False
            _silenceBefore = None
            _cmdForce = False
            
            try:
                if (ttsOptions is not None):
                    options_json = json.loads("{" + ttsOptions + "}")
                    
                    # General Options
                    _ttsVolume = options_json.get('volume', None)
                    _appDing = options_json.get('ding', True)
                    _cmdWait = options_json.get('wait', None)

                    # AI
                    _useAI = options_json.get('genai', False)
                    _aiCustomTone = options_json.get('aitone', None)
                    _aiCustomSysPrompt = options_json.get('aisysprompt', myConfig.aiCustomSysPrompt if myConfig.aiUseCustomSysPrompt else None)
                    _aiCustomTemp = options_json.get('aitemp', None)
                    # SSML
                    _useSSML = options_json.get('ssml', False)
                    # Silent Before
                    _silenceBefore = options_json.get('before', None)

                    if _silenceBefore is not None and _useSSML is False:
                        _useSSML = True
                        ttsText = "<speak><break time='" + str(_silenceBefore) + "' /><p>" + ttsText + "</p></speak>"
                        logging.debug('[DAEMON][TTS] Ajout de %s de silence avant le TTS :: %s', str(_silenceBefore), ttsText)
                    elif _silenceBefore is not None and _useSSML is True:
                        logging.error('[DAEMON][TTS] Les options "before" et "ssml" ne peuvent pas être utilisées dans la même commande.')
                        return False
                    
                    # Force
                    _cmdForce = options_json.get('force', False)

                    # Custom Voice
                    _ttsVoiceCode = options_json.get('voice', None)

                    if _ttsVoiceCode is not None:
                        if ttsEngine == "gcloudtts":
                            ttsVoiceName = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (Google Cloud) :: %s', ttsVoiceName)
                        elif ttsEngine == "gtranslatetts":
                            ttsLang = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (Google Translate) :: %s', ttsLang)
                        elif ttsEngine == "voicersstts":
                            ttsRSSVoiceName = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (VoiceRSS) :: %s', ttsRSSVoiceName)
                        elif ttsEngine == "jeedomtts":
                            ttsLang = _ttsVoiceCode
                            logging.debug('[DAEMON][GenerateTTS] Voix Custom (Jeedom) :: %s', ttsLang)

                    logging.debug('[DAEMON][TTS] Options :: %s', str(options_json))
            except ValueError as e:
                logging.debug('[DAEMON][TTS] Options mal formatées (Json KO) :: %s', e)
            
            _appDing = False if myConfig.appDisableDing else _appDing
            
            if ttsEngine == "gcloudtts":
                logging.debug('[DAEMON][TTS] TTSEngine = gcloudtts')
                logging.debug('[DAEMON][TTS] Import de la clé API :: *** ')
                if myConfig.gCloudApiKey != 'noKey':
                    gKey = os.path.join(myConfig.configFullPath, myConfig.gCloudApiKey)
                    if os.path.exists(gKey):
                        credentials = service_account.Credentials.from_service_account_file(gKey)
                    else:
                        logging.error('[DAEMON][TTS] Impossible de charger le fichier JSON (clé API : KO) :: %s', gKey)
                        return False

                    logging.debug('[DAEMON][TTS] Génération du fichier TTS (mp3)')
                    raw_filename = ttsText + "|gCloudTTS|" + ttsVoiceName + "|" + ttsSpeed + "|" + str(_useSSML)
                    filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                    filepath = os.path.join(symLinkPath, filename)
                    
                    logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
                    
                    if not os.path.isfile(filepath) or _useAI:
                        language_code = "-".join(ttsVoiceName.split("-")[:2])
                        if _useSSML:
                            logging.debug('[DAEMON][TTS] Génération du TTS avec SSML')
                            text_input = googleCloudTTS.SynthesisInput(ssml=ttsText)
                        elif _useAI:
                            ttsAIText = TTSCast.genAI(ttsText, _aiCustomSysPrompt, _aiCustomTone, _aiCustomTemp)
                            if ttsAIText is not None:
                                logging.debug('[DAEMON][TTS] Génération du TTS avec IA')
                                text_input = googleCloudTTS.SynthesisInput(text=ttsAIText)
                            else:
                                logging.error('[DAEMON][TTS] Erreur lors de la génération du TTS avec IA. Génération du TTS sans IA (Backup)')
                                text_input = googleCloudTTS.SynthesisInput(text=ttsText)
                        else:
                            logging.debug('[DAEMON][TTS] Génération du TTS')
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
                    res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume, appDing=_appDing, cmdWait=_cmdWait, cmdForce=_cmdForce)
                    logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
                else:
                    logging.warning('[DAEMON][TTS] Clé API invalide :: ' + myConfig.gCloudApiKey)
            
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
                
                res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume, appDing=_appDing, cmdWait=_cmdWait)
                logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            
            elif ttsEngine == "jeedomtts":
                logging.debug('[DAEMON][TTS] TTSEngine = jeedomtts')
                
                raw_filename = ttsText + "|JeedomTTS|" + ttsLang
                filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                filepath = os.path.join(symLinkPath, filename)
                logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
                
                if not os.path.isfile(filepath):
                    ttsResult = TTSCast.jeedomTTS(ttsText, ttsLang)
                    if ttsResult is not None:
                        with open(filepath, 'wb') as f:
                            f.write(ttsResult)
                    else:
                        logging.debug('[DAEMON][TTS] JeedomTTS Error :: Incorrect Output')
                else:
                    logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                
                urlFileToPlay = urljoin(ttsSrvWeb, filename)
                logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                
                res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume, appDing=_appDing, cmdWait=_cmdWait)
                logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
            
            elif ttsEngine == "voicersstts":
                logging.debug('[DAEMON][TTS] TTSEngine = voicersstts')
                logging.debug('[DAEMON][TTS] Import de la clé API :: *** ')
                if myConfig.apiRSSKey != 'noKey':
                    raw_filename = ttsText + "|VoiceRSSTTS|" + ttsRSSVoiceName + "|" + ttsRSSSpeed + "|" + str(_useSSML)
                    filename = hashlib.md5(raw_filename.encode('utf-8')).hexdigest() + ".mp3"
                    filepath = os.path.join(symLinkPath, filename)
                    logging.debug('[DAEMON][TTS] Nom du fichier à générer :: %s', filepath)
                    
                    if not os.path.isfile(filepath):
                        ttsResult = TTSCast.voiceRSS(ttsText, ttsRSSVoiceName, ttsRSSSpeed, _useSSML)
                        if ttsResult is not None:
                            with open(filepath, 'wb') as f:
                                f.write(ttsResult)
                        else:
                            logging.debug('[DAEMON][TTS] VoiceRSS Error :: Incorrect Output')
                    else:
                        logging.debug('[DAEMON][TTS] Le fichier TTS existe déjà dans le cache :: %s', filepath)
                    
                    urlFileToPlay = urljoin(ttsSrvWeb, filename)
                    logging.debug('[DAEMON][TTS] URL du fichier TTS à diffuser :: %s', urlFileToPlay)
                    
                    res = TTSCast.castToGoogleHome(urltoplay=urlFileToPlay, googleUUID=ttsGoogleUUID, volumeForPlay=_ttsVolume, appDing=_appDing, cmdWait=_cmdWait)
                    logging.debug('[DAEMON][TTS] Résultat de la lecture du TTS sur le Google Home :: %s', str(res))
                else:
                    logging.warning('[DAEMON][TTS] Clé API (Voice RSS) invalide :: ' + myConfig.apiRSSKey)  
                    
        except Exception as e:
            logging.error('[DAEMON][TTS] Exception on TTS :: %s', e)
            logging.debug(traceback.format_exc())

    def castToGoogleHome(urltoplay, googleName='', googleUUID='', volumeForPlay=None, appDing=True, cmdWait=None, cmdForce=False):
        if googleName != '':
            logging.debug('[DAEMON][Cast] Diffusion (Test) sur le Google Home :: %s', googleName)
            
            chromecasts = None
            cast = None
            volumeBeforePlay = None
            
            try:
                chromecasts = [mycast for mycast in myConfig.NETCAST_DEVICES.values() if mycast.name == googleName]
                if not chromecasts:
                    logging.debug('[DAEMON][Cast] Aucun Chromecast avec ce nom :: %s', googleName)
                    return False
                cast = chromecasts[0]
                logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
                
                # Si DashCast alors sortir de l'appli avant sinon cela plante 
                Functions.checkIfDashCast(cast)
            
                volumeBeforePlay = cast.status.volume_level
                if not appDing:
                    cast.set_volume(volume=0)
                elif volumeForPlay is not None:
                    logging.debug('[DAEMON][Cast] Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(volumeForPlay))
                    cast.set_volume(volume=volumeForPlay / 100)
                
                urlThumb = urljoin(myConfig.ttsWebSrvImages, "tts.png")
                logging.debug('[DAEMON][Cast] Thumb path :: %s', urlThumb)
                
                app_name = "default_media_receiver"
                app_data = {
                    "media_id": urltoplay,
                    "media_type": "audio/mp3",
                    "stream_type": "BUFFERED",
                    # "stream_type": "LIVE",
                    "title": "TTSCast",
                    "thumb": urlThumb,
                    "metadata": {
                        "title": "TTSCast",
                        "subtitle": "Jeedom",
                        "images": [{"url": urlThumb}]
                    }
                }
                quick_play.quick_play(cast, app_name, app_data)
                
                if (not appDing and volumeForPlay is not None):
                    logging.debug('[DAEMON][Cast] Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(volumeForPlay))
                    cast.set_volume(volume=volumeForPlay / 100)
                elif (not appDing):
                    cast.set_volume(volume=volumeBeforePlay)
                
                cast.media_controller.block_until_active()
                
                logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', str(cast.media_controller.status))
                
                media_player_state = None
                media_has_played = False
                
                while True:
                    if media_player_state != cast.media_controller.status.player_state:
                        media_player_state = cast.media_controller.status.player_state
                        if media_has_played and media_player_state not in ['PLAYING', 'PAUSED', 'BUFFERING']:
                            break
                        if media_player_state in ['PLAYING']:
                            media_has_played = True
                            logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', str(cast.media_controller.status))
                    time.sleep(0.1)
                
                cast.quit_app()
                
                if (volumeForPlay is not None):  # que ce soit appDing ou not appDing
                    cast.set_volume(volume=volumeBeforePlay)
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return True
            except Exception as e:
                logging.debug('[DAEMON][Cast] Exception (Chromecasts) :: %s', e)
                logging.debug(traceback.format_exc())
                
                if volumeBeforePlay is not None:
                    cast.set_volume(volume=volumeBeforePlay)
                
                # Libération de la mémoire
                cast = None
                chromecasts = None
                return False
        
        elif googleUUID != '':
            logging.debug('[DAEMON][Cast] Diffusion sur le Google Home :: %s', googleUUID)
            
            cast = None
            volumeBeforePlay = None
            
            try:
                _uuid = UUID(googleUUID)
                if _uuid in myConfig.NETCAST_DEVICES:
                    cast = myConfig.NETCAST_DEVICES[_uuid]
                    logging.debug('[DAEMON][Cast] Chromecast trouvé, tentative de lecture TTS')
                else:
                    logging.debug('[DAEMON][Cast] Aucun Chromecast avec cet UUID nom :: %s', googleUUID)
                    return False
                
                if cmdForce:
                    # Tester le paramètre cmdForce pour forcer à quitter l'appli en cours de lecture
                    Functions.forceQuitApp(cast)
                    if googleUUID in myConfig.cmdWaitQueue:
                        myConfig.cmdWaitQueue[googleUUID] = 0
                        logging.debug('[DAEMON][Cast] TTS Wait Queue :: Force %s (%s)', str(myConfig.cmdWaitQueue[googleUUID]), googleUUID)
                elif cmdWait is not None:
                    # WaitQueue if option defined
                    if googleUUID in myConfig.cmdWaitQueue:
                        if int(cmdWait) == 1:
                            myConfig.cmdWaitQueue[googleUUID] = 0
                            logging.debug('[DAEMON][Cast] TTS Wait Queue :: Reset %s (%s)', cmdWait, googleUUID) 
                        elif int(cmdWait) > 1 and myConfig.cmdWaitQueue[googleUUID] == 0:
                            t = 10
                            while (myConfig.cmdWaitQueue[googleUUID] == 0 and t > 0):
                                time.sleep(0.1)
                                t -= 1
                            logging.debug('[DAEMON][Cast] TTS Wait Queue (t) :: %s ', str(t))
                            if myConfig.cmdWaitQueue[googleUUID] == 0:
                                logging.debug('[DAEMON][Cast] TTS Wait Queue :: Cancelled %s (%s)', cmdWait, googleUUID)
                                return False
                            
                    if googleUUID in myConfig.cmdWaitQueue:
                        myConfig.cmdWaitQueue[googleUUID] += 2 ** int(cmdWait)
                    else:
                        myConfig.cmdWaitQueue[googleUUID] = 2 ** int(cmdWait)
                    logging.debug('[DAEMON][Cast] TTS Wait Queue :: In %s (%s)', str(myConfig.cmdWaitQueue[googleUUID]), googleUUID)
                    logging.debug('[DAEMON][Cast] TTS Wait Queue :: Start Waiting %s (%s)', cmdWait, googleUUID)
                    queue_start_time = int(time.time())
                    while myConfig.cmdWaitQueue[googleUUID] % (2 ** int(cmdWait)) != 0:
                        queue_current_time = int(time.time())
                        if (queue_start_time + (myConfig.cmdWaitTimeout * int(cmdWait)) <= queue_current_time):
                            logging.debug('[DAEMON][Cast] TTS Wait Queue :: Timeout %s (%s)', cmdWait, googleUUID)
                            logging.debug('[DAEMON][Cast] TTS Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[googleUUID]), googleUUID)
                            return False
                        time.sleep(0.1)
                    if myConfig.cmdWaitQueue[googleUUID] == 0:
                        logging.debug('[DAEMON][Cast] TTS Wait Queue :: Cancel/Force %s (%s)', cmdWait, googleUUID)
                        logging.debug('[DAEMON][Cast] TTS Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[googleUUID]), googleUUID)
                        return False
                    logging.debug('[DAEMON][Cast] TTS Wait Queue :: End Waiting %s (%s)', cmdWait, googleUUID)
                else:
                    if googleUUID in myConfig.cmdWaitQueue:
                        myConfig.cmdWaitQueue[googleUUID] = 0
                
                # Si DashCast alors sortir de l'appli avant sinon cela plante 
                if not cmdForce: 
                    Functions.checkIfDashCast(cast)
                
                volumeBeforePlay = cast.status.volume_level
                if not appDing:
                    cast.set_volume(volume=0)
                elif volumeForPlay is not None:
                    logging.debug('[DAEMON][Cast] Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(volumeForPlay))
                    cast.set_volume(volume=volumeForPlay / 100)
            
                urlThumb = urljoin(myConfig.ttsWebSrvImages, "tts.png")
                logging.debug('[DAEMON][Cast] Thumb path :: %s', urlThumb)
            
                app_name = "default_media_receiver"
                app_data = {
                    "media_id": urltoplay, 
                    "media_type": "audio/mp3", 
                    "stream_type": "BUFFERED",
                    # "stream_type": "LIVE",
                    "title": "TTSCast", 
                    "thumb": urlThumb,
                    "metadata": {
                        "title": "TTSCast",
                        "subtitle": "Jeedom",
                        "images": [{"url": urlThumb}]
                    }
                }
                
                quick_play.quick_play(cast, app_name, app_data)
                
                if (not appDing and volumeForPlay is not None):
                    logging.debug('[DAEMON][Cast] Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(volumeForPlay))
                    cast.set_volume(volume=volumeForPlay / 100)
                elif (not appDing):
                    cast.set_volume(volume=volumeBeforePlay)
                
                cast.media_controller.block_until_active()
                    
                logging.debug('[DAEMON][Cast] Diffusion lancée :: %s', str(cast.media_controller.status))
            
                media_player_state = None
                media_has_played = False
            
                while True:
                    if media_player_state != cast.media_controller.status.player_state:
                        media_player_state = cast.media_controller.status.player_state
                        if media_has_played and media_player_state not in ['PLAYING', 'PAUSED', 'BUFFERING']:
                            break
                        if media_player_state in ['PLAYING']:
                            media_has_played = True
                            logging.debug('[DAEMON][Cast] Diffusion en cours :: %s', str(cast.media_controller.status))
                    time.sleep(0.1)
            
                cast.quit_app()
                
                if (volumeForPlay is not None):  # que ce soit appDing ou not appDing
                    cast.set_volume(volume=volumeBeforePlay)
                
                # Mise à jour de la WaitQueue
                if cmdWait is not None and cmdForce is False:
                    if myConfig.cmdWaitQueue[googleUUID] > 0:
                        myConfig.cmdWaitQueue[googleUUID] -= 2 ** int(cmdWait)
                        logging.debug('[DAEMON][Cast] TTS Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[googleUUID]), googleUUID)
                
                # Libération de la mémoire
                cast = None
                return True
            except Exception as e:
                logging.debug('[DAEMON][Cast] Exception (Chromecasts) :: %s', e)
                logging.debug(traceback.format_exc())
                
                if volumeBeforePlay is not None:
                    cast.set_volume(volume=volumeBeforePlay)
                
                # Mise à jour de la WaitQueue
                if cmdWait is not None and cmdForce is False:
                    if myConfig.cmdWaitQueue[googleUUID] > 0:
                        myConfig.cmdWaitQueue[googleUUID] -= 2 ** int(cmdWait)
                        logging.debug('[DAEMON][Cast] TTS Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[googleUUID]), googleUUID)
                
                # Libération de la mémoire
                cast = None
                return False
        else:
            logging.debug('[DAEMON][Cast] Diffusion impossible (GoogleHome + GoogleUUID manquants)')
            return False

    def genAI(_aiPrompt, _aiCustomSysPrompt=None, _aiCustomTone=None, _aiCustomTemp=None):
        """
        Reformule une phrase en utilisant l'API Gemini avec un ton spécifique.
        """
        try:
            if (myConfig.gCloudApiKey != 'noKey' and myConfig.aiProjectID != 'noProject') or myConfig.aiApiKey != 'noKey':
                # Initialisation du client Gemini
                credentials = None
                client = None
                
                if myConfig.aiAuthMode == 'oauth2' and myConfig.gCloudApiKey != 'noKey':
                    gKey = os.path.join(myConfig.configFullPath, myConfig.gCloudApiKey)
                    if os.path.exists(gKey):
                        logging.debug('[DAEMON][genAI] Chargement des credentials depuis le fichier JSON :: %s', myConfig.gCloudApiKey)
                        credentials = service_account.Credentials.from_service_account_file(gKey, scopes=myConfig.aiScopes)
                        client = genai.Client(
                            vertexai=True,
                            project=myConfig.aiProjectID,
                            location="global",
                            credentials=credentials,
                        )   
                    else:
                        logging.error('[DAEMON][genAI] Impossible de charger le fichier JSON (clé API : KO) :: %s', gKey)
                        return None
                elif myConfig.aiAuthMode == 'apikey' and myConfig.aiApiKey != 'noKey':
                    logging.debug('[DAEMON][genAI] Chargement des credentials avec la clé API')
                    client = genai.Client(api_key=myConfig.aiApiKey)
                else:
                    logging.error('[DAEMON][genAI] Mode d\'authentification invalide ou clé API manquante.')
                    return None
                
                logging.debug('[DAEMON][genAI] Reformulation de texte via IA')
                
                MODEL_ID = myConfig.aiModel
                logging.debug('[DAEMON][GenAI] Utilisation du modèle :: %s', MODEL_ID)
                
                THINKING_CONFIG = types.ThinkingConfig(thinking_budget=0)
                GOOGLE_SEARCH_TOOL = types.Tool(google_search=types.GoogleSearch())
                
                TEMPERATURE = 1.0 if _aiCustomTemp is None else float(_aiCustomTemp)
                logging.debug('[DAEMON][GenAI] Température :: %s', TEMPERATURE)

                if _aiCustomTone is not None:
                    SYSTEM_INSTRUCTION = myConfig.aiSysPrompt(_aiCustomTone)
                else:
                    SYSTEM_INSTRUCTION = myConfig.aiSysPrompt() if _aiCustomSysPrompt is None else _aiCustomSysPrompt
                logging.debug('[DAEMON][GenAI] Instructions Système :: %s', SYSTEM_INSTRUCTION)
                
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=_aiPrompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=TEMPERATURE,
                        thinking_config=THINKING_CONFIG,
                        tools=[GOOGLE_SEARCH_TOOL]
                    )
                )
                if not response.text:
                    logging.warning('[DAEMON][GenAI] Aucune réponse générée par Gemini.')
                    return None
                else:
                    logging.debug('[DAEMON][GenAI] Réponse générée par Gemini :: %s', response.text.strip())
                    return Functions.markdownToPlainText(response.text.strip())
            else:
                logging.error('[DAEMON][GenAI] Clé (JSON ou Api) et/ou ID de projet Google invalide :: %s, %s, %s', myConfig.gCloudApiKey, "***" if myConfig.aiApiKey else "N/A", myConfig.aiProjectID)
                return None
        except Exception as e:
            logging.error('[DAEMON][GenAI] Erreur: %s', e)
            return None

class Functions:
    """ Class Functions """
    
    def markdownToPlainText(text):
        """ Convert Markdown text to plain text """
        # Convert Markdown to HTML and then extract text
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def removeNonUtf8Chars(text):
        return text.encode('utf-8', 'ignore').decode('utf-8')
    
    def checkIfDashCast(chromecast=None):
        if chromecast is not None and (chromecast.status.app_id == '84912283'):  # DashCast = '84912283'
            logging.debug('[DAEMON][checkIfDashCast] QuitDashCastApp')
            chromecast.quit_app()
            t = 5
            while (chromecast.status.app_id not in [None, 'E8C28D3C']) and t > 0:
                time.sleep(0.1)
                t = t - 0.1
            time.sleep(0.5)
            return True
        else:
            return False
    
    def forceQuitApp(chromecast=None):
        if chromecast is not None and (chromecast.status.app_id not in [None, 'E8C28D3C']):
            logging.debug('[DAEMON][forceQuitApp] QuitApp')
            chromecast.quit_app()
            t = 5
            while (chromecast.status.app_id not in [None, 'E8C28D3C']) and t > 0:
                time.sleep(0.1)
                t = t - 0.1
            time.sleep(0.5)
            return True
        else:
            return False
    
    def controllerActions(_googleUUID='UNKOWN', _controller='', _value='', _options=''):
        if _googleUUID != 'UNKOWN':
            cast = None
            volumeBeforePlay = None
            
            try:
                _uuid = UUID(_googleUUID)
                if (_uuid in myConfig.NETCAST_DEVICES):
                    cast = myConfig.NETCAST_DEVICES[_uuid]    
                    logging.debug('[DAEMON][controllerActions] Chromecast trouvé, lancement des actions')
                else:
                    logging.debug('[DAEMON][controllerActions] Aucun Chromecast avec cet UUID :: %s', _googleUUID)
                    return False
                
                if (_controller == 'start_app'):
                    logging.debug('[DAEMON][controllerActions] Lancement de l\'application :: %s', _value)
                    
                    _volume = None
                    _appDing = True
                    _cmdForce = False
                    _cmdWait = None
                    
                    try:
                        if (_options is not None):
                            options_json = json.loads("{" + _options + "}")
                            _volume = options_json.get('volume', None)
                            _appDing = options_json.get('ding', True)
                            _cmdForce = options_json.get('force', False)
                            _cmdWait = options_json.get('wait', None)
                            logging.debug('[DAEMON][controllerActions] StartApp :: Options :: %s', str(options_json))
                    except ValueError as e:
                        logging.debug('[DAEMON][controllerActions] StartApp :: Options mal formatées (Json KO) :: %s', e)
                    
                    _appDing = False if myConfig.appDisableDing else _appDing
                    
                    if _cmdForce:
                        # Si cmdForce alors forcer la sortie de l'appli avant
                        Functions.forceQuitApp(cast)
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] = 0
                            logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Force %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    elif _cmdWait is not None:
                        # WaitQueue if option defined
                        if _googleUUID in myConfig.cmdWaitQueue:
                            if int(_cmdWait) == 1:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                                logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Reset %s (%s)', _cmdWait, _googleUUID)
                            elif int(_cmdWait) > 1 and myConfig.cmdWaitQueue[_googleUUID] == 0:
                                t = 10
                                while (myConfig.cmdWaitQueue[_googleUUID] == 0 and t > 0):
                                    time.sleep(0.1)
                                    t -= 1
                                logging.debug('[DAEMON][controllerActions] StartApp Wait Queue (t) :: %s ', str(t))
                                if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                    logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Cancelled %s (%s)', _cmdWait, _googleUUID)
                                    return False
                        
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] += 2 ** int(_cmdWait)
                        else:
                            myConfig.cmdWaitQueue[_googleUUID] = 2 ** int(_cmdWait)
                        logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: In %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                        logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Start Waiting %s (%s)', _cmdWait, _googleUUID)
                        queue_start_time = int(time.time())
                        while myConfig.cmdWaitQueue[_googleUUID] % (2 ** int(_cmdWait)) != 0:
                            queue_current_time = int(time.time())
                            if (queue_start_time + (myConfig.cmdWaitTimeout * int(_cmdWait)) <= queue_current_time):
                                logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Timeout %s (%s)', _cmdWait, _googleUUID)
                                logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                return False
                            time.sleep(0.1)
                        if myConfig.cmdWaitQueue[_googleUUID] == 0:
                            logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Cancel/Force %s (%s)', _cmdWait, _googleUUID)
                            logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                            return False
                        logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: End Waiting %s (%s)', _cmdWait, _googleUUID)
                    else:
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] = 0
                    
                    if not _cmdForce:
                        # Si DashCast alors sortir de l'appli avant sinon cela plante    
                        Functions.checkIfDashCast(cast)
                    
                    if not _appDing:
                        cast.set_volume(volume=0)
                    elif (_volume is not None):
                        logging.debug('[DAEMON][controllerActions] StartApp :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                        cast.set_volume(volume=_volume / 100)
                    
                    cast.start_app(_value)
                    
                    if (not _appDing and _volume is not None):
                        logging.debug('[DAEMON][controllerActions] StartApp :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                        cast.set_volume(volume=_volume / 100)
                    elif (not _appDing):
                        cast.set_volume(volume=volumeBeforePlay)
                    
                    cast.media_controller.block_until_active()
                    
                    logging.debug('[DAEMON][controllerActions] StartApp :: Application lancée :: %s', str(_value))
                    
                    # Mise à jour de la WaitQueue
                    if _cmdWait is not None and _cmdForce is False:
                        if myConfig.cmdWaitQueue[_googleUUID] > 0:
                            myConfig.cmdWaitQueue[_googleUUID] -= 2 ** int(_cmdWait)
                            logging.debug('[DAEMON][controllerActions] StartApp Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    
                    # Libération de la mémoire
                    cast = None
                    return True
                
                if (_controller == 'youtube'):
                    logging.debug('[DAEMON][controllerActions] YouTube Id @ UUID :: %s @ %s', _value, _googleUUID)
                    
                    _playlist = None
                    _enqueue = False
                    _volume = None
                    _appDing = True
                    _cmdForce = False
                    _cmdWait = None
                    
                    try:
                        if (_options is not None):
                            options_json = json.loads("{" + _options + "}")
                            _playlist = options_json.get('playlist', None)
                            _enqueue = options_json.get('enqueue', False)
                            _volume = options_json.get('volume', None)
                            _appDing = options_json.get('ding', True)
                            _cmdForce = options_json.get('force', False)
                            _cmdWait = options_json.get('wait', None)
                            logging.debug('[DAEMON][controllerActions] YouTube :: Options :: %s', str(options_json))
                    except ValueError as e:
                        logging.debug('[DAEMON][controllerActions] YouTube :: Options mal formatées (Json KO) :: %s', e)
                    
                    _appDing = False if myConfig.appDisableDing else _appDing
                    
                    # Si cmdForce alors forcer la sortie de l'appli avant
                    # Sinon si DashCast alors sortir de l'appli avant sinon cela plante
                    if _cmdForce:
                        Functions.forceQuitApp(cast)
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] = 0
                            logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Force %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    elif _cmdWait is not None:
                        # WaitQueue if option defined
                        if _googleUUID in myConfig.cmdWaitQueue:
                            if int(_cmdWait) == 1:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                                logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Reset %s (%s)', _cmdWait, _googleUUID)
                            elif int(_cmdWait) > 1 and myConfig.cmdWaitQueue[_googleUUID] == 0:
                                t = 10
                                while (myConfig.cmdWaitQueue[_googleUUID] == 0 and t > 0):
                                    time.sleep(0.1)
                                    t -= 1
                                logging.debug('[DAEMON][controllerActions] Youtube Wait Queue (t) :: %s ', str(t))
                                if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                    logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Cancelled %s (%s)', _cmdWait, _googleUUID)
                                    return False
                        
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] += 2 ** int(_cmdWait)
                        else:
                            myConfig.cmdWaitQueue[_googleUUID] = 2 ** int(_cmdWait)
                        logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: In %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                        logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Start Waiting %s (%s)', _cmdWait, _googleUUID)
                        queue_start_time = int(time.time())
                        while myConfig.cmdWaitQueue[_googleUUID] % (2 ** int(_cmdWait)) != 0:
                            queue_current_time = int(time.time())
                            if (queue_start_time + (myConfig.cmdWaitTimeout * int(_cmdWait)) <= queue_current_time):
                                logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Timeout %s (%s)', _cmdWait, _googleUUID)
                                logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                return False
                            time.sleep(0.1)
                        if myConfig.cmdWaitQueue[_googleUUID] == 0:
                            logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Cancel/Force %s (%s)', _cmdWait, _googleUUID)
                            logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                            return False
                        logging.debug('[DAEMON][controllerActions] Youtube Wait Queue :: End Waiting %s (%s)', _cmdWait, _googleUUID)
                    else:
                        myConfig.cmdWaitQueue[_googleUUID] = 0
                    
                    if not _cmdForce:
                        Functions.checkIfDashCast(cast)
                    
                    volumeBeforePlay = cast.status.volume_level
                    if not _appDing:
                        cast.set_volume(volume=0)
                    elif (_volume is not None):
                        logging.debug('[DAEMON][controllerActions] YouTube :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                        cast.set_volume(volume=_volume / 100)

                    app_name = "youtube"
                    app_data = {
                        "media_id": _value,
                        "playlist_id": _playlist,
                        "enqueue": _enqueue
                    }
                    quick_play.quick_play(cast, app_name, app_data)
                    
                    if (not _appDing and _volume is not None):
                        logging.debug('[DAEMON][controllerActions] YouTube :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                        cast.set_volume(volume=_volume / 100)
                    elif (not _appDing):
                        cast.set_volume(volume=volumeBeforePlay)
                    
                    cast.media_controller.block_until_active()
                    
                    logging.debug('[DAEMON][controllerActions] YouTube :: Diffusion lancée :: %s', str(cast.media_controller.status))
                    
                    # Mise à jour de la WaitQueue
                    if _cmdWait is not None and _cmdForce is False:
                        if myConfig.cmdWaitQueue[_googleUUID] > 0:
                            myConfig.cmdWaitQueue[_googleUUID] -= 2 ** int(_cmdWait)
                            logging.debug('[DAEMON][controllerActions] YouTube Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    
                    # Libération de la mémoire
                    cast = None
                    return True
                
                elif (_controller == 'dashcast'):
                    logging.debug('[DAEMON][controllerActions] DashCast URL / Options @ UUID :: %s / %s @ %s', _value, _options, _googleUUID)
                    
                    player = dashcast.DashCastController()
                    cast.register_handler(player)
                    
                    _force = False
                    _reload_seconds = None
                    _cmdWait = None
                    
                    try:
                        if (_options is not None):
                            options_json = json.loads("{" + _options + "}")    
                            _force = options_json.get('force', False)
                            _reload_seconds = options_json.get('reload_seconds', None)
                            _cmdWait = options_json.get('wait', None)
                    except ValueError as e:
                        logging.debug('[DAEMON][controllerActions] DashCast :: Options mal formatées (Json KO) :: %s', e)
                    
                    # waitQueue if option defined
                    if _cmdWait is not None:
                        if _googleUUID in myConfig.cmdWaitQueue:
                            if int(_cmdWait) == 1:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                                logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Reset %s (%s)', _cmdWait, _googleUUID)
                            elif int(_cmdWait) > 1 and myConfig.cmdWaitQueue[_googleUUID] == 0:
                                t = 10
                                while (myConfig.cmdWaitQueue[_googleUUID] == 0 and t > 0):
                                    time.sleep(0.1)
                                    t -= 1
                                logging.debug('[DAEMON][controllerActions] DashCast Wait Queue (t) :: %s ', str(t))
                                if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                    logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Cancelled %s (%s)', _cmdWait, _googleUUID)
                                    return False
                            
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] += 2 ** int(_cmdWait)
                        else:
                            myConfig.cmdWaitQueue[_googleUUID] = 2 ** int(_cmdWait)
                        logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                        logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Start %s (%s)', _cmdWait, _googleUUID)
                        queue_start_time = int(time.time())
                        while myConfig.cmdWaitQueue[_googleUUID] % (2 ** int(_cmdWait)) != 0:
                            queue_current_time = int(time.time())
                            if (queue_start_time + (myConfig.cmdWaitTimeout * int(_cmdWait)) <= queue_current_time):
                                logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Timeout %s (%s)', _cmdWait, _googleUUID)
                                logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                return False
                            time.sleep(0.1)
                        if myConfig.cmdWaitQueue[_googleUUID] == 0:
                            logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Cancel/Force %s (%s)', _cmdWait, _googleUUID)
                            logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                            return False
                        logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: End %s (%s)', _cmdWait, _googleUUID)
                    else:
                        if _googleUUID in myConfig.cmdWaitQueue:
                            myConfig.cmdWaitQueue[_googleUUID] = 0

                    if options_json.get('quit_app', False):
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
                    
                    # Mise à jour de la WaitQueue
                    if _cmdWait is not None:
                        if myConfig.cmdWaitQueue[_googleUUID] > 0:
                            myConfig.cmdWaitQueue[_googleUUID] -= 2 ** int(_cmdWait)
                            logging.debug('[DAEMON][controllerActions] DashCast Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    
                    # Libération de la mémoire
                    player = None
                    cast = None
                    return True
                
                elif (_controller in ['radios', 'customradios']):
                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Streaming ID @ UUID :: %s @ %s', _value, _googleUUID)
                    
                    if _value == '':
                        cast.quit_app()
                        time.sleep(1)
                    else:
                        if (_controller == 'customradios'):
                            _RadiosFilePath = myConfig.customRadiosFilePath
                        else:
                            _RadiosFilePath = myConfig.radiosFilePath
                        
                        if not os.path.isfile(_RadiosFilePath):
                            logging.error('[DAEMON][controllerActions] Radio/CustomRadio JSON GetFile ERROR :: %s @ %s', _value, _googleUUID)
                        else:
                            _volume = None
                            _appDing = True
                            _cmdForce = False
                            _cmdWait = None
                            try:
                                if (_options is not None):
                                    options_json = json.loads("{" + _options + "}")
                                    _volume = options_json.get('volume', None)
                                    _appDing = options_json.get('ding', True)
                                    _cmdForce = options_json.get('force', False)
                                    _cmdWait = options_json.get('wait', None)
                                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio :: Options :: %s', str(options_json))
                            except ValueError as e:
                                logging.debug('[DAEMON][controllerActions] Radio/CustomRadio :: Options mal formatées (Json KO) :: %s', e)

                            _appDing = False if myConfig.appDisableDing else _appDing
                         
                            if _cmdForce:
                                # Si cmdForce alors forcer la sortie de l'appli avant
                                Functions.forceQuitApp(cast)
                                if _googleUUID in myConfig.cmdWaitQueue:
                                    myConfig.cmdWaitQueue[_googleUUID] = 0
                                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Force %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                            elif _cmdWait is not None:
                                # WaitQueue if option defined
                                if _googleUUID in myConfig.cmdWaitQueue:
                                    if int(_cmdWait) == 1:
                                        myConfig.cmdWaitQueue[_googleUUID] = 0
                                        logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Reset %s (%s)', _cmdWait, _googleUUID)
                                    elif int(_cmdWait) > 1 and myConfig.cmdWaitQueue[_googleUUID] == 0:
                                        t = 10
                                        while (myConfig.cmdWaitQueue[_googleUUID] == 0 and t > 0):
                                            time.sleep(0.1)
                                            t -= 1
                                        logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue (t) :: %s', str(t))
                                        if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                            logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Cancelled %s (%s)', _cmdWait, _googleUUID)
                                            return False
                                    
                                if _googleUUID in myConfig.cmdWaitQueue:
                                    myConfig.cmdWaitQueue[_googleUUID] += 2 ** int(_cmdWait)
                                else:
                                    myConfig.cmdWaitQueue[_googleUUID] = 2 ** int(_cmdWait)
                                logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: In %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Start Waiting %s (%s)', _cmdWait, _googleUUID)
                                queue_start_time = int(time.time())
                                while myConfig.cmdWaitQueue[_googleUUID] % (2 ** int(_cmdWait)) != 0:
                                    queue_current_time = int(time.time())
                                    if (queue_start_time + (myConfig.cmdWaitTimeout * int(_cmdWait)) <= queue_current_time):
                                        logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Timeout %s (%s)', _cmdWait, _googleUUID)
                                        logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                        return False
                                    time.sleep(0.1)
                                if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Cancel/Force %s (%s)', _cmdWait, _googleUUID)
                                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                    return False
                                logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: End %s (%s)', _cmdWait, _googleUUID)
                            else:
                                if _googleUUID in myConfig.cmdWaitQueue:
                                    myConfig.cmdWaitQueue[_googleUUID] = 0
                            
                            if not _cmdForce:
                                # Si DashCast alors sortir de l'appli avant sinon cela plante
                                Functions.checkIfDashCast(cast)
                            
                            volumeBeforePlay = cast.status.volume_level
                            if not _appDing:
                                cast.set_volume(volume=0)
                            elif (_volume is not None):
                                logging.debug('[DAEMON][controllerActions] Radio/CustomRadio :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                                cast.set_volume(volume=_volume / 100)
                            
                            f = open(_RadiosFilePath, "r")
                            radiosArray = json.loads(f.read())
                            
                            if _value in radiosArray:
                                radio = radiosArray[_value]
                                if "NoLogo" in radio['image']:
                                    radioThumb = urljoin(myConfig.ttsWebSrvImages, "tts.png")
                                else:
                                    radioThumb = radio['image']
                                radioUrl = radio['location']
                                radioTitle = radio['title']
                                radioArtist = "TTSCast Radio"
                                radioAlbumName = "Jeedom"
                                
                                app_name = "default_media_receiver"
                                app_data = {
                                    "media_id": radioUrl,
                                    "media_type": "audio/mp3",
                                    "title": radioTitle,
                                    "thumb": radioThumb,
                                    "metadata": {
                                        "metadataType": 3,
                                        "title": radioTitle,
                                        "artist": radioArtist,
                                        "albumName": radioAlbumName,
                                        "images": [{"url": radioThumb}]
                                    },
                                    "stream_type": "LIVE"
                                }
                                quick_play.quick_play(cast, app_name, app_data)
                                
                                if (not _appDing and _volume is not None):
                                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                                    cast.set_volume(volume=_volume / 100)
                                elif (not _appDing):
                                    cast.set_volume(volume=volumeBeforePlay)
                                
                                cast.media_controller.block_until_active()
                                
                                logging.debug('[DAEMON][controllerActions] Diffusion Radio/CustomRadio lancée :: %s', str(cast.media_controller.status))
                            
                            # Mise à jour de la WaitQueue
                            if _cmdWait is not None and _cmdForce is False:
                                if myConfig.cmdWaitQueue[_googleUUID] > 0:
                                    myConfig.cmdWaitQueue[_googleUUID] -= 2 ** int(_cmdWait)
                                    logging.debug('[DAEMON][controllerActions] Radio/CustomRadio Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    
                    # Libération de la mémoire
                    cast = None
                    return True
                    
                elif (_controller in ['sounds', 'customsounds']):
                    logging.debug('[DAEMON][controllerActions] Sound/CustomSound Streaming ID @ UUID :: %s @ %s', _value, _googleUUID)
                    
                    if _value == '':
                        cast.quit_app()
                        time.sleep(1)
                    else:
                        _volume = None
                        _appDing = True
                        _cmdWait = None
                        _cmdForce = False
                        
                        try:
                            if (_options is not None):
                                options_json = json.loads("{" + _options + "}")
                                _volume = options_json.get('volume', None)
                                _appDing = options_json.get('ding', True)
                                _cmdWait = options_json.get('wait', None)
                                _cmdForce = options_json.get('force', False)
                                logging.debug('[DAEMON][controllerActions] Sound/CustomSound :: Options :: %s', str(options_json))
                        except ValueError as e:
                            logging.debug('[DAEMON][controllerActions] Sound/CustomSound :: Options mal formatées (Json KO) :: %s', e)

                        _appDing = False if myConfig.appDisableDing else _appDing

                        if _cmdForce:
                            Functions.forceQuitApp(cast)
                            if _googleUUID in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                                logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Force %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                        elif _cmdWait is not None:
                            if _googleUUID in myConfig.cmdWaitQueue:
                                if int(_cmdWait) == 1:
                                    myConfig.cmdWaitQueue[_googleUUID] = 0
                                    logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Reset %s (%s)', _cmdWait, _googleUUID)
                                elif int(_cmdWait) > 1 and myConfig.cmdWaitQueue[_googleUUID] == 0:
                                    t = 10
                                    while (myConfig.cmdWaitQueue[_googleUUID] == 0 and t > 0):
                                        time.sleep(0.1)
                                        t -= 1
                                    logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue (t) :: %s', str(t))
                                    if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                        logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Cancelled %s (%s)', _cmdWait, _googleUUID)
                                        return False
                            # WaitQueue if option defined
                            if _googleUUID in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[_googleUUID] += 2 ** int(_cmdWait)
                            else:
                                myConfig.cmdWaitQueue[_googleUUID] = 2 ** int(_cmdWait)
                            logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: In %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                            logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Start Waiting %s (%s)', _cmdWait, _googleUUID)
                            queue_start_time = int(time.time())
                            while myConfig.cmdWaitQueue[_googleUUID] % (2 ** int(_cmdWait)) != 0:
                                queue_current_time = int(time.time())
                                if (queue_start_time + (myConfig.cmdWaitTimeout * int(_cmdWait)) <= queue_current_time):
                                    logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Timeout %s (%s)', _cmdWait, _googleUUID)
                                    logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                    return False
                                time.sleep(0.1)
                            if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Cancel/Force %s (%s)', _cmdWait, _googleUUID)
                                logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                return False
                            logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: End Waiting %s (%s)', _cmdWait, _googleUUID)
                        else:
                            if _googleUUID in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                        
                        if not _cmdForce:
                            # Si DashCast alors sortir de l'appli avant sinon cela plante
                            Functions.checkIfDashCast(cast)
                        
                        volumeBeforePlay = cast.status.volume_level
                        if not _appDing:
                            cast.set_volume(volume=0)
                        elif (_volume is not None):
                            logging.debug('[DAEMON][controllerActions] Sound/CustomSound :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                            cast.set_volume(volume=_volume / 100)
                        
                        if (_controller == 'customsounds'):
                            soundURL = urljoin(myConfig.ttsWebSrvMedia, 'custom/' + _value)
                        else:
                            soundURL = urljoin(myConfig.ttsWebSrvMedia, _value)
                        logging.debug('[DAEMON][controllerActions] Sound/CustomSound :: FilePath :: %s', soundURL)

                        soundThumb = urljoin(myConfig.ttsWebSrvImages, "tts.png")
                        soundAlbumName = "Jeedom"
                        soundTitle = "TTSCast Sound"
                        soundArtist = _value

                        app_name = "default_media_receiver"
                        # app_name = "bubbleupnp"
                        app_data = {
                            "media_id": soundURL,
                            "media_type": "audio/mp3",
                            "stream_type": "BUFFERED",
                            "title": soundTitle,
                            "thumb": soundThumb,
                            "metadata": {
                                "metadataType": 3,
                                "title": soundTitle,
                                "artist": soundArtist,
                                "albumName": soundAlbumName,
                                "images": [{"url": soundThumb}]
                            }
                        }
                        quick_play.quick_play(cast, app_name, app_data)
                        
                        if (not _appDing and _volume is not None):
                            logging.debug('[DAEMON][controllerActions] Sound/CustomSound :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                            cast.set_volume(volume=_volume / 100)
                        elif (not _appDing):
                            cast.set_volume(volume=volumeBeforePlay)
                        
                        cast.media_controller.block_until_active()
                        
                        logging.debug('[DAEMON][controllerActions] Diffusion Sound/CustomSound lancée :: %s', str(cast.media_controller.status))
                        
                        media_player_state = None
                        media_has_played = False
	
                        while True:
                            if media_player_state != cast.media_controller.status.player_state:
                                media_player_state = cast.media_controller.status.player_state
                                if media_has_played and media_player_state not in ['PLAYING', 'PAUSED', 'BUFFERING']:
                                    break
                                if media_player_state in ['PLAYING']:
                                    media_has_played = True
                                    logging.debug('[DAEMON][controllerActions] Diffusion Sound/CustomSound en cours :: %s', str(cast.media_controller.status))
                            time.sleep(0.1)
            
                        cast.quit_app()
                        if (_volume is not None):
                            cast.set_volume(volume=volumeBeforePlay)
                    
                        # Mise à jour de la WaitQueue
                        if _cmdWait is not None and _cmdForce is False:
                            if myConfig.cmdWaitQueue[_googleUUID] > 0:
                                myConfig.cmdWaitQueue[_googleUUID] -= 2 ** int(_cmdWait)
                                logging.debug('[DAEMON][controllerActions] Sound/CustomSound Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                    
                    # Libération de la mémoire
                    cast = None
                    return True
                
                elif (_controller in ['media']):
                    logging.debug('[DAEMON][controllerActions] Media Streaming ID @ UUID :: %s @ %s', _value, _googleUUID)
                    
                    if not Functions.isURL(_value):
                        logging.error('[DAEMON][controllerActions] Media ERROR (not URL) :: %s @ %s', _value, _googleUUID)
                    else:
                        _volume = None
                        _appDing = True
                        _mediaType = None
                        _cmdForce = False
                        _cmdWait = None
                        try:
                            if (_options is not None):
                                options_json = json.loads("{" + _options + "}")
                                _volume = options_json.get('volume', None)
                                _appDing = options_json.get('ding', True)
                                _mediaType = options_json.get('type', None)
                                _cmdForce = options_json.get('force', False)
                                _cmdWait = options_json.get('wait', None)

                                logging.debug('[DAEMON][controllerActions] Media :: Options :: %s', str(options_json))
                        except ValueError as e:
                            logging.debug('[DAEMON][controllerActions] Media :: Options mal formatées (Json KO) :: %s', e)

                        _appDing = False if myConfig.appDisableDing else _appDing
                        
                        if _cmdForce:
                            Functions.forceQuitApp(cast)
                            if _googleUUID in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                                logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Force %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                        elif _cmdWait is not None:
                            if _googleUUID in myConfig.cmdWaitQueue:
                                if int(_cmdWait) == 1:
                                    myConfig.cmdWaitQueue[_googleUUID] = 0
                                    logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Reset %s (%s)', _cmdWait, _googleUUID)
                                elif int(_cmdWait) > 1 and myConfig.cmdWaitQueue[_googleUUID] == 0:
                                    t = 10
                                    while (myConfig.cmdWaitQueue[_googleUUID] == 0 and t > 0):
                                        time.sleep(0.1)
                                        t -= 1
                                    logging.debug('[DAEMON][controllerActions] Media Wait Queue (t) :: %s', str(t))
                                    if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                        logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Cancelled %s (%s)', _cmdWait, _googleUUID)
                                        return False
                            # WaitQueue if option defined
                            if _googleUUID in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[_googleUUID] += 2 ** int(_cmdWait)
                            else:
                                myConfig.cmdWaitQueue[_googleUUID] = 2 ** int(_cmdWait)
                            logging.debug('[DAEMON][controllerActions] Media Wait Queue :: In %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                            logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Start Waiting %s (%s)', _cmdWait, _googleUUID)
                            queue_start_time = int(time.time())
                            while myConfig.cmdWaitQueue[_googleUUID] % (2 ** int(_cmdWait)) != 0:
                                queue_current_time = int(time.time())
                                if (queue_start_time + (myConfig.cmdWaitTimeout * int(_cmdWait)) <= queue_current_time):
                                    logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Timeout %s (%s)', _cmdWait, _googleUUID)
                                    logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                    return False
                                time.sleep(0.1)
                            if myConfig.cmdWaitQueue[_googleUUID] == 0:
                                logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Cancel/Force %s (%s)', _cmdWait, _googleUUID)
                                logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Return %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                                return False
                            logging.debug('[DAEMON][controllerActions] Media Wait Queue :: End Waiting %s (%s)', _cmdWait, _googleUUID)
                        else:
                            if _googleUUID in myConfig.cmdWaitQueue:
                                myConfig.cmdWaitQueue[_googleUUID] = 0
                        
                        if not _cmdForce:
                            # Si DashCast alors sortir de l'appli avant sinon cela plante
                            Functions.checkIfDashCast(cast)
                        
                        volumeBeforePlay = cast.status.volume_level
                        if not _appDing:
                            cast.set_volume(volume=0)
                        elif (_volume is not None):
                            logging.debug('[DAEMON][controllerActions] Media :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                            cast.set_volume(volume=_volume / 100)
                        
                        if _mediaType is not None:
                            mediaType = _mediaType
                            if mediaType == "video/mp4":
                                metadataType = 1  # type METADATA_TYPE_MOVIE (Title + SubTitle only)
                                mediaStreamType = "BUFFERED"
                            elif mediaType == "audio/mp3":
                                metadataType = 3  # type METADATA_TYPE_MUSICTRACK ()
                                mediaStreamType = "BUFFERED"
                            else:
                                metadataType = 0  # type METADATA_TYPE_GENERIC
                                mediaStreamType = "BUFFERED"
                        else:
                            mediaType = "video/mp4"
                            metadataType = 1  # type METADATA_TYPE_MOVIE
                        
                        media = _value    
                        mediaImage = urljoin(myConfig.ttsWebSrvImages, "tts.png")
                        mediaTitle = "TTSCast Media"
                        mediaSubTitle = _value
                        mediaAlbumName = "Jeedom"
                        mediaArtist = _value
                        
                        app_name = "bubbleupnp"
                        app_data = {
                            "media_id": media,
                            "media_type": mediaType,
                            "stream_type": mediaStreamType,
                            "metadata": {
                                "metadataType": metadataType,
                                "title": mediaTitle,
                                "subtitle": mediaSubTitle,
                                "artist": mediaArtist,
                                "albumName": mediaAlbumName,
                                "images": [{"url": mediaImage}]
                            }
                        }
                        
                        quick_play.quick_play(cast, app_name, app_data)
                            
                        if (not _appDing and _volume is not None):
                            logging.debug('[DAEMON][controllerActions] Media :: Volume [avant / pendant] lecture :: [%s / %s]', str(volumeBeforePlay), str(_volume))
                            cast.set_volume(volume=_volume / 100)
                        elif (not _appDing):
                            cast.set_volume(volume=volumeBeforePlay)
                        
                        cast.media_controller.block_until_active()
                        
                        logging.debug('[DAEMON][controllerActions] Diffusion Media lancée :: %s', str(cast.media_controller.status))
                        
                        # Mise à jour de la WaitQueue
                        if _cmdWait is not None and _cmdForce is False:
                            if myConfig.cmdWaitQueue[_googleUUID] > 0:
                                myConfig.cmdWaitQueue[_googleUUID] -= 2 ** int(_cmdWait)
                                logging.debug('[DAEMON][controllerActions] Media Wait Queue :: Out %s (%s)', str(myConfig.cmdWaitQueue[_googleUUID]), _googleUUID)
                        
                    # Libération de la mémoire
                    cast = None
                    return True
                
            except Exception as e:
                logging.error('[DAEMON][controllerActions] Exception on controllerActions (%s) :: %s', _googleUUID, e)
                logging.debug(traceback.format_exc())
                
                if volumeBeforePlay is not None:
                    cast.set_volume(volume=volumeBeforePlay)
                
                # TODO : Mise à jour de la WaitQueue en cas d'erreur ???
                
                # Libération de la mémoire
                cast = None
                return False
    
    def mediaActions(_googleUUID='UNKOWN', _value='0', _mode=''):
        if _googleUUID != 'UNKOWN':
            cast = None
            try:
                _uuid = UUID(_googleUUID)
                if (_uuid in myConfig.NETCAST_DEVICES):
                    cast = myConfig.NETCAST_DEVICES[_uuid]
                    logging.debug('[DAEMON][mediaActions] Chromecast trouvé, lancement des actions')
                else:
                    logging.debug('[DAEMON][mediaActions] Aucun Chromecast avec cet UUID :: %s', _googleUUID)
                    return False
                
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
                return True
            except Exception as e:
                logging.error('[DAEMON][mediaActions] Exception on mediaActions (%s) :: %s', _googleUUID, e)
                logging.debug(traceback.format_exc())
                
                # Libération de la mémoire
                cast = None
                return False
    
    def scanChromeCast(_mode='UNKOWN'):
        try:
            logging.debug('[DAEMON][SCANNER] Start Scanner :: %s', _mode)
            myConfig.ScanPending = True
            
            if (_mode == "ScanMode"):
                currentTime = int(time.time())
                currentTimeStr = datetime.datetime.fromtimestamp(currentTime).strftime("%d/%m/%Y - %H:%M:%S")
            
                # Thread pour le discovery (pychromecast)
                """ 
                browser = pychromecast.discovery.CastBrowser(myCast.MyCastListener(), myConfig.NETCAST_ZCONF, myConfig.KNOWN_HOSTS)
                browser.start_discovery()
                logging.info('[DAEMON][MAINLOOP][NETCAST] Listening for Chromecast events...') """
                
                logging.debug('[DAEMON][SCANNER] Devices découverts :: %s', len(myConfig.NETCAST_DEVICES))
                for device in myConfig.NETCAST_DEVICES.values():
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
                
                _gcast_names = myConfig.GCAST_NAMES.copy()
                
                logging.debug('[DAEMON][SCANNER][SCHEDULE] GCAST Names :: %s', str(_gcast_names))
                
                chromecasts = [mycast for mycast in myConfig.NETCAST_DEVICES.values() if mycast.name in _gcast_names]
                logging.debug('[DAEMON][SCANNER][SCHEDULE] Nb NetCast vs JeeCast :: %s vs %s', len(myConfig.NETCAST_DEVICES), len(chromecasts))
                
                for cast in chromecasts: 
                    
                    logging.debug('[DAEMON][SCANNER][SCHEDULE] Chromecast Name :: %s', cast.name)
                    try:
                        if (cast.status is not None and cast.media_controller.status is not None):
                            castVolumeLevel = int(cast.status.volume_level * 100)
                            castAppDisplayName = cast.status.display_name if cast.status.display_name is not None else "N/A"
                            
                            castIsStandBy = '1' if cast.status.is_stand_by else '0'
                            castIsMuted = cast.status.volume_muted
                            castAppId = cast.status.app_id if cast.status.app_id is not None else "N/A"
                            castSessionId = cast.status.session_id if cast.status.session_id is not None else "N/A"
                            castStatusText = cast.status.status_text if cast.status.status_text is not None else "N/A"
                            if cast.socket_client.is_connected:
                                castIsOnline = '1'
                            else:
                                castIsOnline = '0'
                            
                            mediaLastUpdated = None
                            if (cast.media_controller.status.last_updated is not None):
                                last_updated = cast.media_controller.status.last_updated.replace(tzinfo=datetime.timezone.utc)
                                last_updated_local = last_updated.astimezone(tz=None)
                                mediaLastUpdated = last_updated_local.strftime("%d/%m/%Y - %H:%M:%S")
                            else:
                                mediaLastUpdated = "N/A"
                            
                            mediaIsIdle = '1' if cast.media_controller.status.player_is_idle or cast.media_controller.status.player_state == 'UNKNOWN' else '0'
                            mediaIsBusy = '1' if cast.media_controller.status.player_is_playing or cast.media_controller.status.player_is_paused else '0'
                            mediaPlayerState = cast.media_controller.status.player_state if cast.media_controller.status.player_state is not None else "N/A"
                            mediaTitle = cast.media_controller.status.title if cast.media_controller.status.title is not None else "N/A"
                            mediaArtist = cast.media_controller.status.artist if cast.media_controller.status.artist is not None else "N/A"
                            mediaAlbumName = cast.media_controller.status.album_name if cast.media_controller.status.album_name is not None else "N/A"
                            mediaDuration = cast.media_controller.status.duration
                            mediaCurrentTime = cast.media_controller.status.current_time
                            
                            if cast.media_controller.status.images:
                                mediaImage = cast.media_controller.status.images[0].url
                            else:
                                mediaImage = ""
                            
                            mediaContentType = cast.media_controller.status.content_type if cast.media_controller.status.content_type is not None else "N/A"
                            mediaStreamType = cast.media_controller.status.stream_type if cast.media_controller.status.stream_type is not None else "N/A"
                            
                            data = {
                                'uuid': str(cast.uuid),
                                'lastschedule': currentTimeStr,
                                'lastschedulets': currentTime,
                                'volume_level': castVolumeLevel,
                                'display_name': castAppDisplayName,
                                'is_stand_by': castIsStandBy,
                                'is_idle': mediaIsIdle,
                                'is_busy': mediaIsBusy,
                                'volume_muted': castIsMuted,
                                'app_id': castAppId,
                                'session_id': castSessionId,
                                'status_text': castStatusText,
                                'player_state': mediaPlayerState,
                                'title': mediaTitle,
                                'artist': mediaArtist,
                                'duration': mediaDuration,
                                'current_time': mediaCurrentTime,
                                'image': mediaImage,
                                'album_name': mediaAlbumName,
                                'content_type': mediaContentType,
                                'stream_type': mediaStreamType,
                                'last_updated': mediaLastUpdated,
                                'schedule': 1,
                                'online': castIsOnline
                            }

                            # Envoi vers Jeedom
                            Comm.sendToJeedom.add_changes('casts::' + data['uuid'], data)
                        else:
                            logging.warning('[DAEMON][SCANNER][SCHEDULE] Chromecast Status is KO :: %s', cast.name)
                    except Exception as e:
                        logging.error('[DAEMON][SCANNER][SCHEDULE] Exception :: %s', e)
                        logging.debug(traceback.format_exc())
                        
        except Exception as e:
            logging.error('[DAEMON][SCANNER] Exception on Scanner :: %s', e)
            logging.debug(traceback.format_exc())
            return False
        myConfig.ScanLastTime = int(time.time())
        myConfig.ScanPending = False
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
                timeDiff = currentTime - myConfig.ResourcesLastTime
                timeDiffTotal = currentTime - myConfig.ResourcesFirstTime
                logging.info('[DAEMON][RESOURCES] Total CPU Time used : %.3fs (%.2f%%) | Last %i sec : %.3fs (%.2f%%) | Memory : %s Mo', totalTime, totalTime / timeDiffTotal * 100, timeDiff, totalTime - myConfig.ResourcesLastUsed, (totalTime - myConfig.ResourcesLastUsed) / timeDiff * 100, int(round(maxRSS / 1024)))
                myConfig.ResourcesLastUsed = totalTime
                myConfig.ResourcesLastTime = currentTime
            except Exception:
                pass
        
    def purgeCache(nbDays='0'):
        if nbDays == '0':  # clean entire directory including containing folder
            logging.info('[DAEMON][PURGE-CACHE] Clean Cache :: ALL Files.')
            path = myConfig.ttsCacheFolderTmp
            try:
                if os.path.exists(path):
                    nbFiles = 0
                    for f in os.listdir(path):
                        os.remove(os.path.join(path, f))
                        nbFiles += 1
                    logging.info("[DAEMON][PURGE-CACHE] Clean Cache (OK) :: %s Files Deleted", str(nbFiles))
            except Exception as e:
                logging.error('[DAEMON][PURGE-CACHE] Error while cleaning all cache files :: %s', e)
                logging.debug(traceback.format_exc())
        else:  # clean only files older than X days
            logging.info('[DAEMON][PURGE-CACHE] Clean Cache :: Based on Files Age.')
            now = time.time()
            path = myConfig.ttsCacheFolderTmp
            try:
                if os.path.exists(path):
                    for f in os.listdir(path):
                        logging.debug("[DAEMON][PURGE-CACHE] Age for " + f + " is " + str(int((now - (os.stat(os.path.join(path, f)).st_mtime)) / 86400)) + " days")
                        if os.stat(os.path.join(path, f)).st_mtime < (now - (int(nbDays) * 86400)):
                            os.remove(os.path.join(path, f))
                            logging.info("[DAEMON][PURGE-CACHE] File Removed " + f + " due to expiration (" + nbDays + " days)")
            except Exception as e:
                logging.error('[DAEMON][PURGE-CACHE] Error while cleaning cache based on files age :: %s', e)
                logging.debug(traceback.format_exc())

    def isURL(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc, result.path])
        except Exception as e:
            logging.error('[DAEMON][isURL] Exception :: %s', e)
            return False
        
class myCast:

    def castListeners(chromecast=None, uuid=None):
        """ Connect and Add Listener for Chromecast """
        if not chromecast:
            if uuid in myConfig.NETCAST_DEVICES:
                chromecast = myConfig.NETCAST_DEVICES[uuid]
                logging.info('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Add Listeners', str(chromecast.name))
            else:
                logging.debug('[DAEMON][NETCAST][CastListeners] Aucun Chromecast avec cet UUID :: %s', uuid)
                return False
    
        if uuid not in myConfig.LISTENER_CAST:
            try:
                myConfig.LISTENER_CAST[uuid] = myCast.MyCastStatusListener(chromecast.name, chromecast)
                chromecast.register_status_listener(myConfig.LISTENER_CAST[uuid])
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastListeners][CastStatus] Exception (%s) :: %s', str(chromecast.name), e)
                logging.debug(traceback.format_exc())
        else:
            logging.debug('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Status Listener already active', str(chromecast.name))
            
        if uuid not in myConfig.LISTENER_MEDIA:
            try:
                myConfig.LISTENER_MEDIA[uuid] = myCast.MyMediaStatusListener(chromecast.name, chromecast)
                chromecast.media_controller.register_status_listener(myConfig.LISTENER_MEDIA[uuid])
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastListeners][MediaStatus] Exception (%s) :: %s', str(chromecast.name), e)
                logging.debug(traceback.format_exc())
        else:
            logging.debug('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Media Listener already active', str(chromecast.name))
            
        if uuid not in myConfig.LISTENER_CONNECT:
            try:
                myConfig.LISTENER_CONNECT[uuid] = myCast.MyConnectionStatusListener(chromecast.name, chromecast)
                chromecast.register_connection_listener(myConfig.LISTENER_CONNECT[uuid])
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastListeners][ConnectStatus] Exception (%s) :: %s', str(chromecast.name), e)
                logging.debug(traceback.format_exc())
        else:
            logging.debug('[DAEMON][NETCAST][CastListeners] Chromecast with name :: %s :: Connect Listener already active', str(chromecast.name))
                       
    def castRemove(chromecast=None, uuid=None):
        """ Remove Listener and Connection for Chromecast """
        
        if not chromecast:
            if uuid in myConfig.NETCAST_DEVICES:
                chromecast = myConfig.NETCAST_DEVICES[uuid]
            else:
                logging.debug('[DAEMON][NETCAST][CastRemove] Aucun Chromecast avec cet UUID :: %s', uuid)
                return False
    
        if (uuid in myConfig.LISTENER_CAST):
            try:
                # chromecast.register_status_listener(None)
                del myConfig.LISTENER_CAST[uuid]
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastRemove][Cast] Exception (%s) :: %s', str(chromecast.name), e)
                logging.debug(traceback.format_exc())
        else:
            logging.warning('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Status Listener already deleted', str(chromecast.name))
            
        if (uuid in myConfig.LISTENER_MEDIA):
            try:
                # chromecast.media_controller.register_status_listener(None)
                del myConfig.LISTENER_MEDIA[uuid]
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastRemove][Media] Exception (%s) :: %s', str(chromecast.name), e)
                logging.debug(traceback.format_exc())
        else:
            logging.warning('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Media Listener already deleted', str(chromecast.name))
        
        if (uuid in myConfig.LISTENER_CONNECT):
            try:
                # chromecast.register_connection_listener(None)
                del myConfig.LISTENER_CONNECT[uuid]
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastRemove][Connect] Exception (%s) :: %s', str(chromecast.name), e)
                logging.debug(traceback.format_exc())
        else:
            logging.warning('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Connect Listener already deleted', str(chromecast.name))
        
        logging.info('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Listeners Removed', str(chromecast.name))

        """ chromecast.disconnect()
        logging.info('[DAEMON][NETCAST][CastRemove] Chromecast with name :: %s :: Disconnected', str(chromecast.name)) """

    def castCallBack(chromecast=None):
        """ Service CallBack de découverte des Google Cast """

        if chromecast is not None:
            if chromecast.uuid not in myConfig.NETCAST_DEVICES:
                myConfig.NETCAST_DEVICES[chromecast.uuid] = chromecast
                logging.debug('[DAEMON][NETCAST][CastCallBack] Chromecast with name :: %s :: Added to NETCAST_DEVICES', str(chromecast.name))
                logging.debug('[DAEMON][NETCAST][CastCallBack] NETCAST_DEVICES Nb :: %s', len(myConfig.NETCAST_DEVICES))
            else:
                logging.debug('[DAEMON][NETCAST][CastCallBack] Chromecast with name :: %s :: Already in NETCAST_DEVICES', str(chromecast.name))
            
            try:
                chromecast.wait(timeout=30)
                logging.info('[DAEMON][NETCAST][CastCallBack] Chromecast with name :: %s :: Connected', str(chromecast.name))
            except Exception as e:
                logging.error('[DAEMON][NETCAST][CastCallBack] Chromecast Exception (%s) :: %s', str(chromecast.name), e)
                # logging.debug(traceback.format_exc())
             
            if chromecast.uuid in myConfig.GCAST_UUID:
                uuid = chromecast.uuid
                myCast.castListeners(chromecast=chromecast, uuid=uuid)
                
    class MyCastListener(pychromecast.discovery.AbstractCastListener):
        """Listener for discovering chromecasts."""

        def add_cast(self, uuid, _service):
            """Called when a new cast has been discovered."""
            # print(f"Found cast device '{myConfig.NETCAST_BROWSER.services[uuid].friendly_name}' with UUID {uuid}")
            logging.debug('[DAEMON][NETCAST][Add_Cast] Found Cast Device (Name/UUID) :: ' + myConfig.NETCAST_BROWSER.services[uuid].friendly_name + ' / ' + str(uuid))
            # TODO Action lorsqu'un GoogleCast est ajouté
            """ if uuid in myConfig.NETCAST_DEVICES:
                chromecasts = [mycast for mycast in myConfig.NETCAST_DEVICES if mycast.uuid == uuid]
            else:
                chromecasts = None
            if not chromecasts:
                myConfig.NETCAST_DEVICES.append(pychromecast.get_chromecast_from_cast_info(myConfig.NETCAST_BROWSER.services[uuid], myConfig.NETCAST_ZCONF, 1, 10, 30))
                logging.debug('[DAEMON][NETCAST][Add_Cast] NETCAST_DEVICES Append :: ' + myConfig.NETCAST_BROWSER.services[uuid].friendly_name + ' / ' + str(uuid))
            else:
                logging.debug('[DAEMON][NETCAST][Add_Cast] NETCAST_DEVICES :: Device déjà présent') """
            # TODO myConfig.NETCAST_DEVICES add device ?

        def remove_cast(self, uuid, _service, cast_info):
            """Called when a cast has been lost (MDNS info expired or host down)."""
            # print(f"Lost cast device '{cast_info.friendly_name}' with UUID {uuid}")
            logging.debug('[DAEMON][NETCAST][Remove_Cast] Lost Cast Device (Name/UUID) :: ' + cast_info.friendly_name + ' / ' + str(uuid))
            # TODO Action lorsqu'un GoogleCast est supprimé
            # TODO myConfig.NETCAST_DEVICES remove device + Listener ?

        def update_cast(self, uuid, _service):
            """Called when a cast has been updated (MDNS info renewed or changed)."""
            # print(f"Updated cast device '{myConfig.NETCAST_BROWSER.services[uuid].friendly_name}' with UUID {uuid}")
            logging.debug('[DAEMON][NETCAST][Update_Cast] Updated Cast Device (Name/UUID) :: ' + myConfig.NETCAST_BROWSER.services[uuid].friendly_name + ' / ' + str(uuid))
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
                castAppDisplayName = status.display_name if status.display_name is not None else "N/A"
                castAppId = status.app_id if status.app_id is not None else "N/A"
                castSessionId = status.session_id if status.session_id is not None else "N/A"
                castStatusText = status.status_text if status.status_text is not None else "N/A"
                castIsStandBy = '1' if status.is_stand_by else '0'
                
                data = {
                    'uuid': str(self.cast.uuid),
                    'is_stand_by': castIsStandBy,
                    'volume_level': castVolumeLevel,
                    'volume_muted': status.volume_muted,
                    'display_name': castAppDisplayName,
                    'app_id': castAppId,
                    'session_id': castSessionId,
                    'status_text': castStatusText,
                    'realtime': 1,
                    'status_type': 'cast'
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
                else:
                    mediaLastUpdated = "N/A"
                
                """ if self.cast.socket_client.is_connected:
                    castIsOnline = '1'
                else:
                    castIsOnline = '0' """
                
                mediaIsIdle = '1' if status.player_is_idle or status.player_state == 'UNKNOWN' else '0'
                mediaIsBusy = '1' if status.player_is_playing or status.player_is_paused else '0'
                
                mediaPlayerState = status.player_state if status.player_state is not None else "N/A"
                mediaTitle = status.title if status.title is not None else "N/A"
                mediaArtist = status.artist if status.artist is not None else "N/A"
                mediaAlbumName = status.album_name if status.album_name is not None else "N/A"
                mediaDuration = status.duration
                mediaCurrentTime = status.current_time
                
                if status.images:
                    mediaImage = status.images[0].url
                else:
                    mediaImage = ""
                    
                mediaContentType = status.content_type if status.content_type is not None else "N/A"
                mediaStreamType = status.stream_type if status.stream_type is not None else "N/A"

                data = {
                    'uuid': str(self.cast.uuid),
                    'player_state': mediaPlayerState,
                    'is_idle': mediaIsIdle,
                    'is_busy': mediaIsBusy,
                    'title': mediaTitle,
                    'artist': mediaArtist,
                    'duration': mediaDuration,
                    'current_time': mediaCurrentTime,
                    'image': mediaImage,
                    'album_name': mediaAlbumName,
                    'content_type': mediaContentType,
                    'stream_type': mediaStreamType,
                    'last_updated': mediaLastUpdated,
                    'realtime': 1,
                    'status_type': 'media'
                }

                # Envoi vers Jeedom
                Comm.sendToJeedom.add_changes('castsRT::' + data['uuid'], data)
                
            except Exception as e:
                logging.error('[DAEMON][NETCAST][New_Media_Status] Exception :: %s', e)
                logging.debug(traceback.format_exc())

        def load_media_failed(self, queue_item_id, error_code):
            logging.error('[DAEMON][NETCAST][Load_Media_Failed] ' + self.name + ' :: LOAD Media FAILED for item :: ' + str(queue_item_id) + ' with code :: ' + str(error_code))

    class MyConnectionStatusListener(ConnectionStatusListener):
        """ConnectionStatusListener"""

        def __init__(self, name, cast):
            self.name = name
            self.cast = cast

        def new_connection_status(self, status) -> None:
            """Updated connection status."""
            
            logging.debug('[DAEMON][NETCAST][New_Connect_Status] ' + self.name + ' :: STATUS Connect change :: ' + str(status))
            try:
                # The socket connection is being setup
                # CONNECTION_STATUS_CONNECTING = "CONNECTING"
                # The socket connection was complete
                CONNECTION_STATUS_CONNECTED = "CONNECTED"
                # The socket connection has been disconnected
                # CONNECTION_STATUS_DISCONNECTED = "DISCONNECTED"
                # Connecting to socket failed (after a CONNECTION_STATUS_CONNECTING)
                # CONNECTION_STATUS_FAILED = "FAILED"
                # Failed to resolve service name
                # CONNECTION_STATUS_FAILED_RESOLVE = "FAILED_RESOLVE"
                # The socket connection was lost and needs to be retried
                # CONNECTION_STATUS_LOST = "LOST"
                
                if status.status in [CONNECTION_STATUS_CONNECTED]:
                    castIsOnline = '1'
                else:
                    castIsOnline = '0'
                
                data = {
                    'uuid': str(self.cast.uuid),
                    'realtime': 1,
                    'status_type': 'connect',
                    'online': castIsOnline
                }

                # Envoi vers Jeedom
                Comm.sendToJeedom.add_changes('castsRT::' + data['uuid'], data)
            except Exception as e:
                logging.error('[DAEMON][NETCAST][New_Connect_Status] Exception :: %s', e)
                logging.debug(traceback.format_exc())

# ----------------------------------------------------------------------------

def handler(signum=None, frame=None):
    logging.debug("[DAEMON] Signal %i caught, exiting...", int(signum))
    shutdown()

def shutdown():
    logging.info("[DAEMON] Shutdown :: Begin...")
    myConfig.IS_ENDING = True
    logging.info("[DAEMON] Shutdown :: Devices Disconnect :: Begin...")
    try:
        for chromecast in myConfig.NETCAST_DEVICES.values():
            chromecast.disconnect(timeout=5)
        logging.info("[DAEMON] Shutdown :: Devices Disconnect :: OK")
        if myConfig.NETCAST_BROWSER is not None: 
            myConfig.NETCAST_BROWSER.stop_discovery()
        logging.info("[DAEMON] Shutdown :: Browser Stop :: OK")
        if myConfig.NETCAST_ZCONF is not None: 
            myConfig.NETCAST_ZCONF.close()
        logging.info("[DAEMON] Shutdown :: ZeroConf Close :: OK")
    except Exception as e:
        # pass
        logging.error('[DAEMON] Exception on Shutdown :: %s', e)
        logging.debug(traceback.format_exc())
    logging.debug("[DAEMON] Removing PID file %s", myConfig.pidFile)
    try:
        os.remove(myConfig.pidFile)
    except Exception:
        pass
    try:
        my_jeedom_socket.close()
    except Exception:
        pass
    logging.info("[DAEMON] Shutdown :: Exit 0")
    sys.stdout.flush()
    os._exit(0)

# ----------------------------------------------------------------------------

# ***** PROGRAMME PRINCIPAL *****

# Instanciation de la configuration
myConfig = Config()

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
parser.add_argument("--appdisableding", help="App Disable Ding Parameter", type=str)
parser.add_argument("--cmdwaittimeout", help="Cmd Wait Timeout Parameter", type=str)
parser.add_argument("--pid", help="Pid file", type=str)
parser.add_argument("--socketport", help="Port for TTSCast server", type=str)
parser.add_argument("--aienabled", help="Enable AI", type=str, default='0')
parser.add_argument("--aiauthmode", help="AI Auth Mode", type=str, default='noMode')
parser.add_argument("--aiprojectid", help="AI Project ID", type=str, default='noProjectId')
parser.add_argument("--aiapikey", help="AI ApiKey", type=str, default='noKey')
parser.add_argument("--aimodel", help="AI Model", type=str, default='noModel')
parser.add_argument("--aiusecustomsysprompt", help="Use Custom System Prompt for AI", type=str, default='0')
parser.add_argument("--aicustomsysprompt", help="Custom System Prompt for AI", type=str, default='NoCustomSysPrompt')
parser.add_argument("--aidefaulttone", help="Default AI Tone", type=str, default='NoDefaultTone')

args = parser.parse_args()
if args.loglevel:
    myConfig.logLevel = args.loglevel
if args.pluginversion:
    myConfig.pluginVersion = args.pluginversion
if args.callback:
    myConfig.callBack = args.callback
if args.apikey:
    myConfig.apiKey = args.apikey
if args.apittskey:
    myConfig.apiTTSKey = args.apittskey
if args.gcloudapikey:
    myConfig.gCloudApiKey = args.gcloudapikey
if args.voicerssapikey:
    myConfig.apiRSSKey = args.voicerssapikey
if args.appdisableding:
    if (args.appdisableding == '0'):
        myConfig.appDisableDing = False
    else:
        myConfig.appDisableDing = True
if args.aienabled:
    if (args.aienabled == '0'):
        myConfig.aiEnabled = False
    else:
        myConfig.aiEnabled = True
if args.aiauthmode:
    myConfig.aiAuthMode = args.aiauthmode
if args.aiprojectid and args.aiprojectid != 'noProjectId':
    myConfig.aiProjectID = args.aiprojectid
if args.aiapikey and args.aiapikey != 'noKey':
    myConfig.aiApiKey = args.aiapikey
if args.aimodel and args.aimodel != 'noModel':
    myConfig.aiModel = args.aimodel
if args.aidefaulttone and args.aidefaulttone != 'NoDefaultTone':
    myConfig.aiDefaultTone = args.aidefaulttone
if args.aiusecustomsysprompt:
    if (args.aiusecustomsysprompt == '0'):
        myConfig.aiUseCustomSysPrompt = False
    else:
        myConfig.aiUseCustomSysPrompt = True
if args.aicustomsysprompt and args.aicustomsysprompt != 'NoCustomSysPrompt':
    myConfig.aiCustomSysPrompt = args.aicustomsysprompt
if args.cmdwaittimeout:
    myConfig.cmdWaitTimeout = int(args.cmdwaittimeout)
if args.pid:
    myConfig.pidFile = args.pid
if args.cyclefactor:
    myConfig.cycleFactor = float(args.cyclefactor)
if args.socketport:
    myConfig.socketPort = int(args.socketport)
if args.ttsweb:
    myConfig.ttsWebSrvCache = urljoin(args.ttsweb, 'plugins/ttscast/data/cache/')
    myConfig.ttsWebSrvMedia = urljoin(args.ttsweb, 'plugins/ttscast/data/media/')
    myConfig.ttsWebSrvImages = urljoin(args.ttsweb, 'plugins/ttscast/data/images/')
    myConfig.ttsWebSrvJeeTTS = urljoin(args.ttsweb, 'core/api/')

jeedom_utils.set_log_level(myConfig.logLevel)

if myConfig.cycleFactor == 0:
    myConfig.cycleMain = 2.0
    myConfig.cycleComm = 0.5
    myConfig.cycleEvent = 0.5
elif myConfig.cycleFactor < 0.5:
    myConfig.cycleMain = 1.0
    myConfig.cycleComm = 0.25
    myConfig.cycleEvent = float(myConfig.cycleEvent * myConfig.cycleFactor)
else:
    myConfig.cycleMain = float(myConfig.cycleMain * myConfig.cycleFactor)
    myConfig.cycleComm = float(myConfig.cycleComm * myConfig.cycleFactor)
    myConfig.cycleEvent = float(myConfig.cycleEvent * myConfig.cycleFactor)

logging.info('[DAEMON][MAIN] Start Daemon')
logging.info('[DAEMON][MAIN] Plugin Version: %s', myConfig.pluginVersion)
logging.info('[DAEMON][MAIN] Log level: %s', myConfig.logLevel)
logging.info('[DAEMON][MAIN] Socket port: %s', myConfig.socketPort)
logging.info('[DAEMON][MAIN] Socket host: %s', myConfig.socketHost)
logging.info('[DAEMON][MAIN] CycleFactor: %s', myConfig.cycleFactor)

if myConfig.cycleFactor == 0:
    logging.warning('[DAEMON][MAIN][CYCLE] CycleFactor à 0 => Main à 2.0 / Comm à 0.5 / Event à 0.5')
elif myConfig.cycleFactor < 0.5:
    logging.warning('[DAEMON][MAIN][CYCLE] CycleFactor < 0.5 => Main à 1.0 / Comm à 0.25')

logging.info('[DAEMON][MAIN] CycleMain: %s', myConfig.cycleMain)
logging.info('[DAEMON][MAIN] CycleComm: %s', myConfig.cycleComm)
logging.info('[DAEMON][MAIN] CycleEvent: %s', myConfig.cycleEvent)
logging.info('[DAEMON][MAIN] PID file: %s', myConfig.pidFile)
logging.info('[DAEMON][MAIN] ApiKey: %s', "***" if myConfig.apiKey else "N/A")
logging.info('[DAEMON][MAIN] ApiTTSKey: %s', "***" if myConfig.apiTTSKey else "N/A")
logging.info('[DAEMON][MAIN] Google Cloud ApiKey: %s', myConfig.gCloudApiKey)
logging.info('[DAEMON][MAIN] VoiceRSS ApiKey: %s', "***" if myConfig.apiRSSKey else "N/A")
logging.info('[DAEMON][MAIN] App Disable Ding: %s', str(myConfig.appDisableDing))
logging.info('[DAEMON][MAIN] AI Enabled: %s', str(myConfig.aiEnabled))
logging.info('[DAEMON][MAIN] AI Auth Mode: %s', myConfig.aiAuthMode)
logging.info('[DAEMON][MAIN] AI Project ID: %s', myConfig.aiProjectID)
logging.info('[DAEMON][MAIN] AI ApiKey: %s', "***" if myConfig.aiApiKey else "N/A")
logging.info('[DAEMON][MAIN] AI Model: %s', myConfig.aiModel)
logging.info('[DAEMON][MAIN] AI Use Custom System Prompt: %s', str(myConfig.aiUseCustomSysPrompt))
logging.info('[DAEMON][MAIN] AI Custom System Prompt: %s', myConfig.aiCustomSysPrompt)
logging.info('[DAEMON][MAIN] AI Default Tone: %s', myConfig.aiDefaultTone)
logging.info('[DAEMON][MAIN] Cmd Wait Timeout: %s', str(myConfig.cmdWaitTimeout))
logging.info('[DAEMON][MAIN] CallBack: %s', myConfig.callBack)
logging.info('[DAEMON][MAIN] Jeedom WebSrvCache: %s', myConfig.ttsWebSrvCache)
logging.info('[DAEMON][MAIN] Jeedom WebSrvMedia: %s', myConfig.ttsWebSrvMedia)
logging.info('[DAEMON][MAIN] Jeedom WebSrvImages: %s', myConfig.ttsWebSrvImages)
logging.info('[DAEMON][MAIN] Jeedom WebSrvJeeTTS: %s', myConfig.ttsWebSrvJeeTTS)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

try:
    jeedom_utils.write_pid(str(myConfig.pidFile))
    Comm.sendToJeedom = jeedom_com(apikey=myConfig.apiKey, url=myConfig.callBack, cycle=myConfig.cycleComm)
    if not Comm.sendToJeedom.test():
        logging.error('[DAEMON][JEEDOMCOM] sendToJeedom :: Network communication ERROR (Daemon to Jeedom)')
        shutdown()
    else:
        logging.info('[DAEMON][JEEDOMCOM] sendToJeedom :: Network communication OK (Daemon to Jeedom)')
    my_jeedom_socket = jeedom_socket(port=myConfig.socketPort, address=myConfig.socketHost)
    Loops.mainLoop(myConfig.cycleMain)
except Exception as e:
    logging.error('[DAEMON][MAIN] Fatal error: %s', e)
    logging.info(traceback.format_exc())
    shutdown()
