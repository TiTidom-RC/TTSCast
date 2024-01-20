PROGRESS_FILE=/tmp/jeedom/ttscast/dependency
if [ ! -z $1 ]; then
	PROGRESS_FILE=$1
fi

BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR=$BASE_DIR/venv

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
echo 5 > ${PROGRESS_FILE}
apt-get clean | log
echo 10 > ${PROGRESS_FILE}
apt-get update | log
echo 20 > ${PROGRESS_FILE}

log "****************************"
log "* Install apt-get packages *"
log "****************************"
apt-get install -y python3 python3-requests python3-pip python3-setuptools python3-dev python3-venv | log
echo 50 > ${PROGRESS_FILE}

log "***********************"
log "* Create Python3 venv *"
log "***********************"
python3 -m venv $VENV_DIR --upgrade-deps | log
echo 60 > ${PROGRESS_FILE}
log "Python3 venv : done"

log "*****************************"
log "* Install Python3 libraries *"
log "*****************************"
$VENV_DIR/bin/python3 -m pip install --upgrade pip wheel | log
echo 70 > ${PROGRESS_FILE}
# $VENV_DIR/bin/python3 -m pip install -r requirements.txt | log
$VENV_DIR/bin/python3 -m pip install pychromecast==13.1.0 google-cloud-texttospeech==2.15.1 gTTS==2.5.0 pydub==0.25.1 | log

echo 100 > ${PROGRESS_FILE}
log "****************"
log "* Install DONE *"
log "****************"
rm ${PROGRESS_FILE}
