#!/bin/bash
PROGRESS_FILE=/tmp/jeedom/ttscast/dependency
if [ ! -z $1 ]; then
	PROGRESS_FILE=$1
fi

BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR=${BASE_DIR}/venv
PYENV_OLDDIR=${BASE_DIR}/pyenv
PYENV_DIR=/opt/pyenv

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

cd ${BASE_DIR}

touch ${PROGRESS_FILE}
echo 0 > ${PROGRESS_FILE}
log "*******************"
log "* Check PyEnv Dir *"
log "*******************"
if [ -d ${PYENV_DIR} ]; then
	log "** PyEnv Directory (Exists) :: ${PYENV_DIR} **"
else
	log "** PyEnv Directory (Not exists) :: ${PYENV_DIR} **"
fi
log "** Check PyEnv :: Done **"
echo 1 > ${PROGRESS_FILE}
log "***********************"
log "* Check Old PyEnv Dir *"
log "***********************"
if [ -d ${PYENV_OLDDIR} ]; then
	log "** PyEnv Old Directory (Exists) :: ${PYENV_OLDDIR} **"
	rm -rf ${PYENV_OLDDIR}
	VenvToUpdate=1
	log "** Venv Update :: Needed **"
else
	log "** PyEnv Old Directory (Not exists) :: ${PYENV_OLDDIR} **"
	VenvToUpdate=0
	log "** Venv Update :: Not Needed **"
fi
log "** Check Old PyEnv :: Done **"
log "******************"
log "* Update apt-get *"
log "******************"
echo 3 > ${PROGRESS_FILE}
export DEBIAN_FRONTEND=noninteractive
echo 4 > ${PROGRESS_FILE}
apt-get clean | log
log "** Clean apt-get :: Done **"
echo 5 > ${PROGRESS_FILE}
apt-get update | log
log "** Update apt-get :: Done **"
echo 10 > ${PROGRESS_FILE}
log "****************************"
log "* Simulate apt-get upgrade *"
log "****************************"
apt-get -y -s -V upgrade | log
log "** Upgrade Simulation :: Done **"
echo 20 > ${PROGRESS_FILE}
log "****************************************"
log "* Install apt-get packages for Python3 *"
log "****************************************"
apt-get install -y python3 python3-requests python3-pip python3-setuptools python3-dev python3-venv | log
log "** Install packages for Python3 :: Done **"
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
	log "Python3.x Version :: 3.${versionPython}"
fi
log "** Check Python3 Version :: Done **"
echo 35 > ${PROGRESS_FILE}
if [ "$versionPython" -lt 11 ]; then 
	log "******************************************************"
	log "* Install apt-get packages for PyEnv (Python < 3.11) *"
	log "******************************************************"
	apt-get install -y git build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev | log
	log "** Install packages for PyEnv :: Done **"
	log "*********************************"
	log "* Install PyEnv (Python < 3.11) *"
	log "*********************************"
	if [ -v PYENV_ROOT ]; then
		log "** PYENV_ROOT (already set) :: ${PYENV_ROOT} **"
	else
		log "** PYENV_ROOT (not set) :: OK **"
	fi
	if [ -d ${PYENV_DIR} ]; then
		PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv update | log
	else
		curl https://pyenv.run | PYENV_ROOT="${PYENV_DIR}" bash | log
	fi
	log "** PyEnv Installation / Update :: Done **"
	echo 40 > ${PROGRESS_FILE}
	log "**************************************************"
	log "* Compile and Install Python 3.11.8 (with PyEnv) *"
	log "**************************************************"
	log "*                                                *"
	log "* ATTENTION : Cette phase de l'installation peut *"
	log "* être longue et durer de 2 minutes (Config ++)  *"
	log "* à plus de 40 minutes sur des petites config !  *" 
	log "**************************************************"
	# PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv install -s 3.11 | log
	PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv install -s 3.11.8 | log
	log "** Python 3.11.8 Installation :: Done **"
else
	log "*********************"
	log "* PyEnv Environment *"
	log "*********************"
	log "** PyEnv not required (Python >= 3.11) **"
fi
echo 55 > ${PROGRESS_FILE}
log "**************************"
log "* Create Python3.11 venv *"
log "**************************"
if [ "$versionPython" -ge 11 ]; then
	if [ "$VenvToUpdate" -eq 1 ]; then
		python3 -m venv --clear --upgrade-deps ${VENV_DIR} | log 
	else
		python3 -m venv --upgrade-deps ${VENV_DIR} | log 
	fi
else
	vPythonVenv=$(${VENV_DIR}/bin/python3 --version 2>/dev/null | awk -F'[ ,.]' '{print $3}')
	[[ -z "$vPythonVenv" ]] && vPythonVenv=0
	if [ "$vPythonVenv" -eq 0 ]; then 
		log "Python3 (Venv) Version :: None"
	else
		log "Python3 (Venv) Version :: 3.${vPythonVenv}"
	fi
	if [ "$vPythonVenv" -ge 11 ]; then
		log "Latest Python version installed with PyEnv :: $(PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv latest -q 3.11)"
		if [ "$VenvToUpdate" -eq 1 ]; then
			# ${PYENV_DIR}/versions/$(PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv latest -q 3.11)/bin/python3 -m venv --clear --upgrade-deps ${VENV_DIR} | log
			${PYENV_DIR}/versions/3.11.8/bin/python3 -m venv --clear --upgrade-deps ${VENV_DIR} | log
		else
			# ${PYENV_DIR}/versions/$(PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv latest -q 3.11)/bin/python3 -m venv --upgrade-deps ${VENV_DIR} | log
			${PYENV_DIR}/versions/3.11.8/bin/python3 -m venv --upgrade-deps ${VENV_DIR} | log
		fi
	else
		log "Latest Python version installed with PyEnv :: $(PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv latest -q 3.11)"
		# ${PYENV_DIR}/versions/$(PYENV_ROOT="${PYENV_DIR}" ${PYENV_DIR}/bin/pyenv latest -q 3.11)/bin/python3 -m venv --clear --upgrade-deps ${VENV_DIR} | log
		${PYENV_DIR}/versions/3.11.8/bin/python3 -m venv --clear --upgrade-deps ${VENV_DIR} | log
	fi
fi
log "** Create Python3.11 Venv :: Done **" 
echo 70 > ${PROGRESS_FILE}
log "*****************************"
log "* Install Python3 libraries *"
log "*****************************"
${VENV_DIR}/bin/python3 -m pip install --upgrade pip wheel | log
log "** Install Pip / Wheel :: Done **"
echo 75 > ${PROGRESS_FILE}
${VENV_DIR}/bin/python3 -m pip install PyChromecast==14.0.0 google-cloud-texttospeech==2.16.2 gTTS==2.5.1 | log
log "** Install Python3 librairies :: Done **"
echo 95 > ${PROGRESS_FILE}
log "****************************"
log "* Set Owner on Directories *"
log "****************************"
if [ -d ${VENV_DIR} ]; then
	chown -Rh www-data:www-data ${VENV_DIR} | log
	log "** Set Owner for Venv Dir :: Done **"
fi
echo 100 > ${PROGRESS_FILE}
log "****************"
log "* Install DONE *"
log "****************"
rm ${PROGRESS_FILE}
