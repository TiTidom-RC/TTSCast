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
import string
import sys
import os
import time
import datetime
import traceback
import re
import signal
from optparse import OptionParser
from os.path import join
import json
import argparse

try:
	from jeedom.jeedom import *
except ImportError:
	print("Error: importing module jeedom.jeedom")
	sys.exit(1)

# ***** GLOBALS VAR *****

KNOWN_DEVICES = {}
NOWPLAYING_DEVICES = {}
GCAST_DEVICES = {}

TTS_CACHEFOLDER = 'data/cache'
TTS_CACHEFOLDERWEB = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), TTS_CACHEFOLDER))
TTS_CACHEFOLDERTMP = os.path.join('/tmp/jeedom/', 'ttscast_cache')

MEDIA_FOLDER = 'data/media'
MEDIA_FULLPATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), MEDIA_FOLDER))

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
					purgeCache(int(message['days']))
				else:
					purgeCache()
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


def purgeCache(nbDays='0'):
    if nbDays == '0':  # clean entire directory including containing folder
        logging.debug('[DAEMON][PURGE-CACHE] nbDays is 0.')
        try:
            if os.path.exists(TTS_CACHEFOLDERTMP):
                shutil.rmtree(TTS_CACHEFOLDERTMP)
            # generate_warmupnotif()
        except Exception as e:
            logging.warning('[DAEMON][PURGE-CACHE]Error while cleaning cache entirely (nbDays = 0) :: %s', e)
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
            # generate_warmupnotif()
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
	except:
		pass
	try:
		jeedom_socket.close()
	except:
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

parser = argparse.ArgumentParser(description='Desmond Daemon for Jeedom plugin')
parser.add_argument("--device", help="Device", type=str)
parser.add_argument("--loglevel", help="Log Level for the daemon", type=str)
parser.add_argument("--callback", help="Callback", type=str)
parser.add_argument("--apikey", help="Apikey", type=str)
parser.add_argument("--cycle", help="Cycle to send event", type=str)
parser.add_argument("--pid", help="Pid file", type=str)
parser.add_argument("--socketport", help="Port for TTSCast server", type=str)

args = parser.parse_args()

if args.device:
	_device = args.device
if args.loglevel:
	_log_level = args.loglevel
if args.callback:
	_callback = args.callback
if args.apikey:
	_apikey = args.apikey
if args.pid:
	_pidfile = args.pid
if args.cycle:
	_cycle = float(args.cycle)
if args.socketport:
	_socket_port = args.socketport
	_socket_port = int(_socket_port)

jeedom_utils.set_log_level(_log_level)

logging.info('[DAEMON][MAIN] Start ttscastd')
logging.info('[DAEMON][MAIN] Log level: %s', _log_level)
logging.info('[DAEMON][MAIN] Socket port: %s', _socket_port)
logging.info('[DAEMON][MAIN] Socket host: %s', _socket_host)
logging.info('[DAEMON][MAIN] PID file: %s', _pidfile)
# logging.info('[DAEMON][MAIN] Apikey: %s', _apikey)
logging.info('[DAEMON][MAIN] CallBack: %s', _callback)

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
