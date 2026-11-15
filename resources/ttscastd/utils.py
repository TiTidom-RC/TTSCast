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
    # Découverte par IP : adresse de chaque équipement actif, interrogée en complément du mDNS { UUID: 'adresse' }
    IP_HOSTS = {}
    GCAST_UUID = []
    
    NETCAST_BROWSER = None
    NETCAST_DEVICES = {}
    NETCAST_GROUPS = {}
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
    ttsStreamFolderTmp = os.path.join('/tmp/jeedom/ttscast_cache', 'stream')
    
    radiosFilePath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/radios/radios.json'))
    customRadiosFilePath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/radios/custom/radios.json'))
    logFiltersFilePath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/filters/logfilters.json'))
    # soundsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/media'))
    # soundsCustomPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/media/custom'))
    
    ttsWebSrvCache = ''
    ttsWebSrvMediaProxy = ''
    ttsWebSrvImages = ''
    ttsWebSrvJeeTTS = ''
    
    ttsVoiceRSSUrl = 'https://api.voicerss.org/'
    # ttsVoiceRSSUrl = 'api.voicerss.org:443'

    gCloudApiKey = ''
    gCloudAudioEncoding = 'MP3'
    gCloudSampleRate = 24000
    
    # AI Configuration
    # Clés d'options consommées par le démon (jamais renvoyées comme options de notification)
    DAEMON_OPTION_KEYS = frozenset({
        'genai', 'aitone', 'aisysprompt', 'aimodel', 'aithinking',  # IA
        'ssml', 'markup', 'style', 'before', 'voice', 'speaker', 'ttsmodel',  # TTS voix / format
        'engine',                                     # TTS moteur (override par commande)
        'volume', 'ding', 'wait', 'force',            # TTS comportement
    })

    aiEnabled = False
    aiDefault = False
    aiAuthMode = 'noMode'  # 'noMode', 'apikey', 'oauth2'
    aiProjectID = 'noProjectID'  # Google Cloud Project ID for AI
    aiApiKey = ''
    aiModel = 'noModel'  # modèle de reformulation de la configuration, parmi aiModels
    aiDefaultTone = 'enthousiaste et humoristique'  # Default tone for AI TTS
    aiBaseTimeout = 30  # secondes — délai de l'appel IA sans réflexion
    aiMaxTimeout = 60  # secondes — délai maximal de l'appel IA (avec réflexion), réglage de la page de configuration (ttsAIMaxTimeout), transmis au démarrage
    # Relance des appels Gemini (reformulation, Gemini TTS) sur erreur transitoire, à l'intérieur du délai total de l'appel
    geminiRetryAttempts = 3  # tentatives au total, première comprise
    geminiRetryDelays = (1, 2)  # secondes — attente avant la 2e puis la 3e tentative (sauf retryDelay indiqué par Gemini)
    geminiRetryMinRemaining = 5  # secondes — pas de nouvelle tentative s'il reste moins que cela dans le délai de l'appel
    geminiRetryHttpCodes = (429, 500, 502, 503, 504)  # trop de requêtes, erreurs serveur et surcharge : erreurs rapides et transitoires
    # Modèles de reformulation et niveaux de réflexion (thinking_level) acceptés, d'après la documentation Google, du plus bas
    # au plus haut. Le premier niveau est envoyé quand aucun niveau n'est demandé (option aithinking) : Gemini 3 et 4 ne
    # permettent pas de désactiver la réflexion, et thinking_budget est refusé à partir de Gemini 3.5.
    # Aucune température n'est envoyée : ces modèles l'ignorent.
    aiModels = {
        'gemini-3.5-flash-lite': ('minimal', 'low', 'medium', 'high'),
        'gemini-4-hydrogen': ('low', 'medium', 'high', 'xhigh'),
    }
    
    def aiSysPrompt(self, aiCustomTone=None):
        _aiTone = aiCustomTone if aiCustomTone else self.aiDefaultTone
        return (
            'Tu es un assistant vocal qui reformule et enrichit les annonces diffusées sur les enceintes Google Home de la maison, sur un ton ' + _aiTone + '.\n\n'
            'Contenu :\n'
            '- Reformule la phrase d\'origine de façon naturelle et réponds à la question posée s\'il y en a une.\n'
            '- Conserve toutes les valeurs chiffrées présentes dans la phrase d\'origine.\n'
            '- Ne mentionne jamais la date ni le jour de la semaine de façon spontanée. Indique-les uniquement si la phrase d\'origine les demande explicitement (question sur la date, la météo du jour, un événement calendaire, un lever/coucher de soleil…).\n'
            '- Pour toute question nécessitant des données actuelles ou factuelles (météo, actualités, résultats…), utilise la recherche en ligne.\n\n'
            'Format de tes réponses :\n'
            '- Réponds en phrases courtes et fluides, adaptées à une diffusion vocale.\n'
            '- Conserve impérativement les accents, apostrophes et caractères typographiques de la langue.\n'
            '- Ne décris pas tes propres actions ni le processus de génération.'
        )

    aiUseCustomSysPrompt = False
    aiCustomSysPrompt = ''
    aiScopes = ['https://www.googleapis.com/auth/cloud-platform']

    # Gemini TTS Configuration
    geminiTTSEnabled = False
    geminiTTSModel   = 'noModel'
    # Modèles Gemini TTS
    geminiTTSAllowedModels = ('gemini-3.8-flash-tts', 'gemini-3.8-flash-lite-tts')
    geminiTTSDefault = False
    geminiTTSTimeout = 30  # secondes — délai total d'un appel Gemini TTS (relances comprises)
    # Version de l'API Gemini Developer (clé API) : google-genai utilise 'v1' par défaut, version sans sortie audio (speech_config,
    # Gemini TTS) n'existe pas. Le mode Enterprise (oauth2) n'est pas concerné (v1beta1 par défaut).
    geminiApiVersion = 'v1beta'
    geminiTTSStyle   = ''  # Style par défaut, peut être surchargé par style: dans les options de scénario
    streamingDefault = False  # Gemini TTS uniquement — ignoré pour les autres moteurs

    # Paths for various resources
    mediaFolder = 'data/media'
    mediaFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), mediaFolder))

    imagesFolder = 'data/images'
    imagesFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), imagesFolder))

    configFolder = 'data/config'
    configFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), configFolder))

    # Piper TTS
    piperVoiceName = ''
    piperSpeakerId = 0
    piperVoiceCache: dict = {'key': None, 'model': None}  # Cache mémoire du modèle ONNX chargé
    piperBaseHfUrl = 'https://huggingface.co/rhasspy/piper-voices/resolve/main'
    piperVoicesJsonUrl = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json'
    piperModelsDir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/models'))
    piperVoicesCatalogPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/config/piper_voices.json'))
    piperTmpDir = os.path.join('/tmp/jeedom/', 'ttscast')

    ttsDisableCache = False
    appDisableDing = False
    appConvertSingleQuote = False  # Convertit les apostrophes simples en guillemets doubles pour contourner un bug de prononciation Google TTS
    cmdWaitTimeout = 60  # secondes — délai maximal sans progression d'une notification (lecture qui ne démarre pas, pause, lecture figée)
    cmdWaitTimeoutMin = 10  # secondes — minimum appliqué à cmdWaitTimeout au démarrage du démon
    mediaActivationTimeout = 15  # secondes — borne l'attente d'activation de la session média (block_until_active)
    playbackStatusRefresh = 5  # secondes — intervalle des demandes d'état à l'enceinte pendant l'attente de fin de lecture
    ttsRequestTimeout = 30  # secondes — délai des requêtes aux moteurs TTS en ligne (gTTS, Google Cloud TTS)
    # Dernier échec de chargement d'un média (LOAD_FAILED) par équipement : { uuid (str) : (time.monotonic(), code) }
    loadFailures = {}
    # Codes d'échec de chargement remontés par l'enceinte (DetailedErrorCode du SDK Google Cast) : { code : (nom, libellé) }
    castLoadErrors = {
        100: ('MEDIA_UNKNOWN', 'erreur média inconnue'),
        101: ('MEDIA_ABORTED', 'récupération du média interrompue'),
        102: ('MEDIA_DECODE', 'fichier audio illisible ou corrompu'),
        103: ('MEDIA_NETWORK', 'téléchargement du média interrompu'),
        104: ('MEDIA_SRC_NOT_SUPPORTED', 'format non supporté'),
        110: ('SOURCE_BUFFER_FAILURE', 'lecture du média impossible par l\'enceinte'),
        300: ('NETWORK_UNKNOWN', 'erreur réseau inconnue'),
        301: ('SEGMENT_NETWORK', 'téléchargement d\'un segment impossible'),
        900: ('APP', 'erreur de l\'application de l\'enceinte'),
        904: ('LOAD_INTERRUPTED', 'chargement interrompu par un autre'),
        905: ('LOAD_FAILED', 'commande de chargement en échec'),
        999: ('GENERIC', 'erreur inconnue'),
    }
    dashCastAppId = '84912283'  # app_id du récepteur Chromecast DashCast
    # File d'attente des notifications, une par équipement (UUID canonique, resolveCanonicalUUID) : { targetUUID : waitqueue.DeviceQueue }
    deviceQueues = {}
    queueMaxAge = 600  # secondes — au-delà de cette attente, une notification en file n'est pas diffusée (information périmée)
    queueStallMargin = 15  # secondes — marge ajoutée à l'échéance de chaque étape avant de déclarer une notification bloquée
    queuePrepTimeout = 30  # secondes — échéance de la préparation d'une notification avant son tour (hors reformulation IA)
    queueLaunchTimeout = 60  # secondes — échéance du lancement sur l'enceinte (quick_play, activation, volume) et de la fin
    queuePiperTimeout = 300  # secondes — échéance de la génération Piper (locale, sans délai propre)
    queueForceCutWait = 10  # secondes — attente maximale par un « force » de la sortie de la notification qu'il a coupée

    # Tracking de session Cast par équipement (targetUUID résolu) — utilisé pour calculer playback_owner :
    # { targetUUID: { 'mediaSessionId': int|None, 'controller': str } } — mis à jour à chaque lancement plugin réussi (quick_play/start_app)
    # 'controller' vaut 'tts'/'sounds'/'customsounds' (notification, transitoire) ou 'radios'/'customradios'/'media'/'youtube'/'dashcast'/'start_app' (plugin, persistant)
    # DASHCAST est déterminé via app_id (computePlaybackOwner), indépendamment de ce dict.
    pluginSessions = {}

    logLevel = "error"
    castLogLevel = "daemon"
    logFiltersEnabled: bool = False
    logFilters: list = []  # [{ "pattern": str, "level": str, "enabled": bool }]
    ipDiscoveryEnabled: bool = False
    socketPort = 55111
    socketHost = 'localhost'
    pidFile = '/tmp/ttscastd.pid'
    apiKey = ''
    apiTTSKey = ''
    apiRSSKey = ''
    # Texte affiché à la place d'un secret dans les logs (identique aux autres plugins). Sans astérisques :
    # ils sont interprétés comme du Markdown quand les logs sont collés sur un forum ou dans une issue.
    secretMask = 'sEcReT'
    pluginVersion = ''
    callBack = ''
    
    cycleFactor = 1.0
    cycleEvent = 0.5  # cycle de la boucle des events
    cycleComm = 0.5  # cycle de la boucle des comm Jeedom
    cycleMain = 2.0  # cycle de la boucle MainLoop et par héritage du socket read
    
class Comm:
    sendToJeedom = ''