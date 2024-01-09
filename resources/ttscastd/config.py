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

class Config:
    KNOWN_DEVICES = {}
    GCAST_DEVICES = {}

    sendToJeedom = ''

    ttsCacheFolder = 'data/cache'
    ttsCacheFolderWeb = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ttsCacheFolder))
    ttsCacheFolderTmp = os.path.join('/tmp/jeedom/', 'ttscast_cache')
    ttsWebSrvCache = ''
    ttsWebSrvMedia = ''

    gCloudApiKey = ''

    mediaFolder = 'data/media'
    mediaFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), mediaFolder))

    configFolder = 'core/config'
    configFullPath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), configFolder))
    
    logLevel = "error"
    socketPort = 55999
    socketHost = 'localhost'
    pidFile = '/tmp/ttscastd.pid'
    apiKey = ''
    pluginVersion = ''
    callBack = ''
    cycle = 0.3
    cycleEvent = 0.5