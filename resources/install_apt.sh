#!/bin/bash
PROGRESS_FILE=/tmp/jeedom/ttscast/dependency
if [ ! -z $1 ]; then
	PROGRESS_FILE=$1
fi

BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR=$BASE_DIR/venv
PYENV_DIR=$BASE_DIR/pyenv

function log(){
	if [ -n "$1" ]
	then
		echo "$(date +'[%F %T]') $1";
	else
		while read IN  # If it is output from command then loop it
		do
			echo "$(date +'[%F %T]') $IN";
		done
	fi
}

cd $BASE_DIR

touch ${PROGRESS_FILE}
echo 0 > ${PROGRESS_FILE}
log "******************"
log "* Update apt-get *"
log "******************"
echo 2 > ${PROGRESS_FILE}
export DEBIAN_FRONTEND=noninteractive
echo 3 > ${PROGRESS_FILE}
apt-get clean | log
echo 5 > ${PROGRESS_FILE}
apt-get update | log
echo 10 > ${PROGRESS_FILE}
log "****************************"
log "* Simulate apt-get upgrade *"
log "****************************"
apt-get -y -s -V upgrade | log
echo 20 > ${PROGRESS_FILE}
log "***************************************"
log "* Install apt-get packages for Python3 *"
log "***************************************"
apt-get install -y python3 python3-requests python3-pip python3-setuptools python3-dev python3-venv | log
echo 30 > ${PROGRESS_FILE}
log "***************************"
log "* Check Python3.x Version *"
log "***************************"
versionPython=$(python3 --version | awk -F'[ ,.]' '{print $3}')
[[ -z "$versionPython" ]] && versionPython=0
if [ "$versionPython" -eq 0 ]; then 
	log "Python3.x :: VERSION ERROR :: NOT FOUND"
	exit 1
else
	log "Python3.x Version :: 3.$versionPython"
fi
echo 35 > ${PROGRESS_FILE}
if [ "$versionPython" -lt 11 ]; then 
	log "******************************************************"
	log "* Install apt-get packages for PyEnv (Python < 3.11) *"
	log "******************************************************"
	apt-get install -y git build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev | log
	log "*********************************"
	log "* Install PyEnv (Python < 3.11) *"
	log "*********************************"
	if [ -d ${BASE_DIR}/pyenv ]; then
		chown -Rh root:root ${BASE_DIR}/pyenv | log
		cd ${BASE_DIR}/pyenv && git reset --hard | log
		cd ${BASE_DIR}/pyenv/plugins/pyenv-doctor && git reset --hard | log
		cd ${BASE_DIR}/pyenv/plugins/pyenv-update && git reset --hard | log
		cd ${BASE_DIR}/pyenv/plugins/pyenv-virtualenv && git reset --hard | log
		cd ${BASE_DIR} | log
		PYENV_ROOT="${BASE_DIR}/pyenv" ${BASE_DIR}/pyenv/bin/pyenv update | log
	else
		curl https://pyenv.run | PYENV_ROOT="${BASE_DIR}/pyenv" bash | log
	fi
	log "PyEnv installation / update : done"
	echo 40 > ${PROGRESS_FILE}
	log "**************************************************"
	log "* Compile and Install Python 3.11.8 (with PyEnv) *"
	log "**************************************************"
	log "*                                                *"
	log "* ATTENTION : Cette phase de l'installation      *"
	log "* peut être longue et durer jusqu'à 20 minutes.  *"
	log "**************************************************"
	PYENV_ROOT="${BASE_DIR}/pyenv" ${BASE_DIR}/pyenv/bin/pyenv install -s 3.11.8 | log
	log "Python 3.11.8 installation : done"
fi
echo 55 > ${PROGRESS_FILE}
log "**************************"
log "* Create Python3.11 venv *"
log "**************************"
if [ "$versionPython" -ge 11 ]; then
	python3 -m venv --upgrade-deps $VENV_DIR | log 
else
	vPythonVenv=$($VENV_DIR/bin/python3 --version 2>/dev/null | awk -F'[ ,.]' '{print $3}')
	[[ -z "$vPythonVenv" ]] && vPythonVenv=0
	if [ "$vPythonVenv" -eq 0 ]; then 
		log "Python3 (Venv) Version :: None"
	else
		log "Python3 (Venv) Version :: 3.$vPythonVenv"
	fi
	if [ "$vPythonVenv" -ge 11 ]; then
		${BASE_DIR}/pyenv/versions/3.11.8/bin/python3 -m venv --upgrade-deps $VENV_DIR | log
	else
		${BASE_DIR}/pyenv/versions/3.11.8/bin/python3 -m venv --clear --upgrade-deps $VENV_DIR | log
	fi
fi 
echo 70 > ${PROGRESS_FILE}
log "Python3.11 venv : done"

log "*****************************"
log "* Install Python3 libraries *"
log "*****************************"
$VENV_DIR/bin/python3 -m pip install --upgrade pip wheel | log
echo 75 > ${PROGRESS_FILE}
$VENV_DIR/bin/python3 -m pip install PyChromecast==14.0.0 google-cloud-texttospeech==2.16.2 gTTS==2.5.1 pydub==0.25.1 | log

echo 100 > ${PROGRESS_FILE}
log "****************"
log "* Install DONE *"
log "****************"
rm ${PROGRESS_FILE}
