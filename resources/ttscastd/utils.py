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
#

import os
import time

class Config:
    KNOWN_HOSTS = []
    GCAST_UUID = []
    GCAST_NAMES = []
    
    NETCAST_BROWSER = None
    NETCAST_DEVICES = {}
    NETCAST_ZCONF = None
    LISTENER_CAST = {}
    LISTENER_MEDIA = {}
    LISTENER_CONNECT = {}

    IS_ENDING = False

    ScanMode = False
    ScanModeStart = int(time.time())
    ScanModeTimeOut = 60
    
    ScanPending = False
    ScanTimeout = 10
    ScanSchedule = 60
    ScanLastTime = int(time.time())
    
    HeartbeatFrequency = 600
    HeartbeatLastTime = int(time.time())
    
    ResourcesLastUsed = 0
    ResourcesLastTime = int(time.time())
    ResourcesFirstTime = int(time.time())
    
    ttsCacheFolder = 'data/cache'
    ttsCacheFolderWeb = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ttsCacheFolder))
    ttsCacheFolderTmp = os.path.join('/tmp/jeedom/', 'ttscast_cache')
    
    radiosFilePath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/radios/radios.json'))
    customRadiosFilePath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/radios/custom/radios.json'))
    # soundsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/media'))
    # soundsCustomPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/media/custom'))
    
    ttsWebSrvCache = ''
    ttsWebSrvMedia = ''
    ttsWebSrvImages = ''
    ttsWebSrvJeeTTS = ''
    
    ttsVoiceRSSUrl = 'https://api.voicerss.org/'
    # ttsVoiceRSSUrl = 'api.voicerss.org:443'

    gCloudApiKey = ''
    
    # AI Configuration
    aiEnabled = False
    aiAuthMode = 'noMode'  # 'noMode', 'apikey', 'oauth2'
    aiApiKey = ''
    aiModel = 'noModel'  # 'noModel', 'gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro'
    aiDefaultTone = 'Enthousiaste et humoristique'  # Default tone for AI TTS
    aiUseCustomSysPrompt = False
    aiCustomSysPrompt = ''
    
    # Paths for various resources
    mediaFolder = 'data/media'
    mediaFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), mediaFolder))

    imagesFolder = 'data/images'
    imagesFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), imagesFolder))

    configFolder = 'data/config'
    configFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), configFolder))
    
    appDisableDing = False
    cmdWaitTimeout = 60
    cmdWaitQueue = {}
    
    logLevel = "error"
    socketPort = 55111
    socketHost = 'localhost'
    pidFile = '/tmp/ttscastd.pid'
    apiKey = ''
    apiTTSKey = ''
    apiRSSKey = ''
    pluginVersion = ''
    callBack = ''
    
    cycleFactor = 1.0
    cycleEvent = 0.5  # cycle de la boucle des events
    cycleComm = 0.5  # cycle de la boucle des comm Jeedom
    cycleMain = 2.0  # cycle de la boucle MainLoop et par héritage du socket read
    
class Comm:
    sendToJeedom = ''