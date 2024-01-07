<?php
/* This file is part of Jeedom.
 * 
 * Jeedom is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Jeedom is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Jeedom. If not, see <http://www.gnu.org/licenses/>.
*/

/* ***************************Includes********************************* */
require_once __DIR__  . '/../../../../core/php/core.inc.php';

class ttscast extends eqLogic
{
    /* ************************** Variables Globales ****************************** */

    const PYTHON3_PATH = __DIR__ . '/../../resources/venv/bin/python3';

    /* ************************** Attributs ****************************** */

    /*
     * Permet de définir les possibilités de personnalisation du widget (en cas d'utilisation de la fonction 'toHtml' par exemple)
     * Tableau multidimensionnel - exemple: array('custom' => true, 'custom::layout' => false)
    public static $_widgetPossibility = array();
    */

    /*
     * Permet de crypter/décrypter automatiquement des champs de configuration du plugin
     * Exemple : "param1" & "param2" seront cryptés mais pas "param3"
    public static $_encryptConfigKey = array('param1', 'param2');
    */

    /* ************************ Methodes statiques : Démon & Dépendances *************************** */

    public static function dependancy_install() {
        log::remove(__CLASS__ . '_update');
        return array('script' => __DIR__ . '/../../resources/install_#stype#.sh ' . jeedom::getTmpFolder(__CLASS__) . '/dependency', 'log' => log::getPathToLog(__CLASS__ . '_update'));
    }

    public static function dependancy_info() {
        $return = array();
        $return['log'] = log::getPathToLog(__CLASS__ . '_update');
        $return['progress_file'] = jeedom::getTmpFolder(__CLASS__) . '/dependency';
        if (file_exists(jeedom::getTmpFolder(__CLASS__) . '/dependency')) {
            $return['state'] = 'in_progress';
        } else {
            if (exec(system::getCmdSudo() . system::get('cmd_check') . '-Ec "python3\-requests|python3\-setuptools|python3\-dev|python3\-venv"') < 4) {
                $return['state'] = 'nok';
            } elseif (!file_exists(self::PYTHON3_PATH)) {
                $return['state'] = 'nok';
            } elseif (exec(system::getCmdSudo() . self::PYTHON3_PATH . ' -m pip list | grep -Ewc "PyChromecast|pydub|gTTS|google-cloud-texttospeech|google-auth|click|protobuf|requests|zeroconf"') < 9) {
                $return['state'] = 'nok';
            } else {
                $return['state'] = 'ok';
            }
        }
        return $return;
    }

    public static function deamon_info() {
        $return = array();
        $return['log'] = __CLASS__;
        $return['state'] = 'nok';
        $pid_file = jeedom::getTmpFolder(__CLASS__) . '/deamon.pid';
        if (file_exists($pid_file)) {
            if (@posix_getsid(trim(file_get_contents($pid_file)))) {
                $return['state'] = 'ok';
            } else {
                shell_exec(system::getCmdSudo() . 'rm -rf ' . $pid_file . ' 2>&1 > /dev/null');
            }
        }
        $return['launchable'] = 'ok';
        return $return;
    }

    public static function deamon_start() {
        self::deamon_stop();
        $deamon_info = self::deamon_info();
        if ($deamon_info['launchable'] != 'ok') {
            throw new Exception(__('Veuillez vérifier la configuration', __FILE__));
        }

        $path = realpath(__DIR__ . '/../../resources/ttscastd');
        $cmd = self::PYTHON3_PATH . " {$path}/ttscastd.py";
        $cmd .= ' --loglevel ' . log::convertLogLevel(log::getLogLevel(__CLASS__));
        $cmd .= ' --pluginversion ' . config::byKey('pluginVersion', __CLASS__, '0.0.0');
        $cmd .= ' --socketport ' . config::byKey('socketport', __CLASS__, '55999'); // TODO Modifier le numéro de port du démon
        $cmd .= ' --cycle ' . config::byKey('cycle', __CLASS__, '1');
        $cmd .= ' --callback ' . network::getNetworkAccess('internal', 'http:127.0.0.1:port:comp') . '/plugins/ttscast/core/php/jeettscast.php'; // chemin du callback
        if (config::byKey('ttsUseExtAddr', 'ttscast')==1) {
            $cmd .= ' --ttsweb ' . network::getNetworkAccess('external');
        } else {
            $cmd .= ' --ttsweb ' . network::getNetworkAccess('internal');
        }
        $cmd .= ' --apikey ' . jeedom::getApiKey(__CLASS__);
        $cmd .= ' --gcloudapikey ' . config::byKey('gCloudAPIKey', __CLASS__, 'noKey');
        $cmd .= ' --pid ' . jeedom::getTmpFolder(__CLASS__) . '/deamon.pid'; // ne PAS modifier
        log::add(__CLASS__, 'info', 'Lancement du démon');
        $result = exec($cmd . ' >> ' . log::getPathToLog('ttscast_daemon') . ' 2>&1 &');
        $i = 0;
        while ($i < 20) {
            $deamon_info = self::deamon_info();
            if ($deamon_info['state'] == 'ok') {
                break;
            }
            sleep(1);
            $i++;
        }
        if ($i >= 20) {
            log::add(__CLASS__, 'error', __('Impossible de lancer le démon, vérifiez le log', __FILE__), 'unableStartDeamon');
            return false;
        }
        message::removeAll(__CLASS__, 'unableStartDeamon');
        return true;
    }

    public static function deamon_stop() {
        $pid_file = jeedom::getTmpFolder(__CLASS__) . '/deamon.pid'; // Ne PAS modifier
        if (file_exists($pid_file)) {
            $pid = intval(trim(file_get_contents($pid_file)));
            system::kill($pid);
        }
        system::kill('ttscastd.py');
        sleep(1);
    }

    public static function sendToDaemon($params) {
        try {
            $deamon_info = self::deamon_info();
            if ($deamon_info['state'] != 'ok') {
                throw new Exception("Le démon n'est pas démarré");
            }
            $params['apikey'] = jeedom::getApiKey(__CLASS__);
            $payLoad = json_encode($params);
            $socket = socket_create(AF_INET, SOCK_STREAM, 0);
            socket_connect($socket, '127.0.0.1', config::byKey('socketport', __CLASS__, '55999')); // TODO Port du plugin à modifier
            socket_write($socket, $payLoad, strlen($payLoad));
            socket_close($socket);
        } catch (Exception $e) {
            log::add('ttscast', 'debug', '[sendToDaemon] ERROR :: ' . $e->getMessage());
            return false;
        }
    }

    /* ************************ Methodes static : PLUGIN *************************** */

    public static function testExternalAddress($useExternal=NULL)
    {
        if (is_null($useExternal)) {
            // log::add('ttscast', 'debug', '[testExternalAddress] useExternal is NULL :: ' . $useExternal);
            $useExternal = config::byKey('ttsUseExtAddr', 'ttscast');
        }

        $testAddress = '';
        // log::add('ttscast', 'debug', '[testExternalAddress] useExternal :: ' . $useExternal);
        if ($useExternal === 1 || $useExternal === true || $useExternal === 'true') {
            // log::add('ttscast', 'debug', '[testExternalAddress] useExternal :: YES');
            $testAddress .= network::getNetworkAccess('external');
        } else {
            // log::add('ttscast', 'debug', '[testExternalAddress] useExternal :: NO');
            $testAddress .= network::getNetworkAccess('internal');
        }
        return $testAddress . "/plugins/ttscast/data/media/bigben1.mp3";
    }

    public static function purgeTTSCache($days="0") {
        $value = array('cmd' => 'purgettscache', 'days' => $days);
        self::sendToDaemon($value);
    }

    public static function playTestTTS() {
        $ttsText = config::byKey('ttsTestFileGen', 'ttscast', 'Bonjour, Ceci est un test de synthèse vocale via le plugin TTS Cast.');
        $ttsGoogleName = config::byKey('ttsTestGoogleName', 'ttscast', '');
        $ttsVoiceName = config::byKey('gCloudTTSVoice', 'ttscast', 'fr-FR-Standard-A');
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'picotts');  // jeedomtts | picotts | gtranslatetts | gcloudtts
        $ttsSpeed = config::byKey('gCloudTTSSpeed', 'ttscast', '1.0');
        $value = array('cmd' => 'playtesttts', 'ttsengine' => $ttsEngine, 'ttsspeed' => $ttsSpeed, 'ttsText' => $ttsText, 'ttsGoogleName' => $ttsGoogleName, 'ttsVoiceName' => $ttsVoiceName);
        self::sendToDaemon($value);
    }

    public static function playTTS($gHome=null, $message=null, $volume=30) {
        $ttsText = $message;
        $ttsGoogleName = $gHome;
        $ttsVoiceName = config::byKey('gCloudTTSVoice', 'ttscast', 'fr-FR-Standard-A');
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'picotts');  // jeedomtts | picotts | gtranslatetts | gcloudtts
        $ttsSpeed = config::byKey('gCloudTTSSpeed', 'ttscast', '1.0');
        $value = array('cmd' => 'playtts', 'ttsengine' => $ttsEngine, 'ttsspeed' => $ttsSpeed, 'ttsText' => $ttsText, 'ttsGoogleName' => $ttsGoogleName, 'ttsVoiceName' => $ttsVoiceName);
        self::sendToDaemon($value);
    }

    public static function getPluginVersion()
    {
        $pluginVersion = 'N/A';
        if (!file_exists(dirname(__FILE__) . '/../../plugin_info/info.json')) {
            log::add('ttscast', 'warning', '[VERSION] fichier info.json manquant');
        }
        $data = json_decode(file_get_contents(dirname(__FILE__) . '/../../plugin_info/info.json'), true);
        if (!is_array($data)) {
            log::add('ttscast', 'warning', '[VERSION] Impossible de décoder le fichier info.json');
        }
        try {
            $pluginVersion = $data['pluginVersion'];
        } catch (\Exception $e) {
            log::add('ttscast', 'warning', '[VERSION] Impossible de récupérer la version du plugin');
        }

        return $pluginVersion;
    }

    /* public static function sanitizeFileName($_file) {
        log::add('ttscast', 'debug', '[UPLOAD][Sanitize] FileName ::' . $_file);
        
        $_file = trim(strtolower($_file));
        if ($_file == '') return $_file;

        $_file = sanitizeAccent($_file);
        $_file = preg_replace('/[^a-z0-9_]/i', '', $_file);
        return $_file;
    } */

    /* ************************ Methodes static : JEEDOM *************************** */

    /*
     * Fonction exécutée automatiquement toutes les minutes par Jeedom
    public static function cron() {}
    */

    /*
     * Fonction exécutée automatiquement toutes les 5 minutes par Jeedom
    public static function cron5() {}
    */

    /*
     * Fonction exécutée automatiquement toutes les 10 minutes par Jeedom
    public static function cron10() {}
    */

    /*
     * Fonction exécutée automatiquement toutes les 15 minutes par Jeedom
    public static function cron15() {}
    */

    /*
     * Fonction exécutée automatiquement toutes les 30 minutes par Jeedom
    public static function cron30() {}
    */

    /*
     * Fonction exécutée automatiquement toutes les heures par Jeedom
    public static function cronHourly() {}
    */

    // Fonction exécutée automatiquement tous les jours par Jeedom
    public static function cronDaily() {
        try {
            $nbdays = config::byKey('ttsPurgeCacheDays', 'ttscast', '10');
            if ($nbdays != '') {
                ttscast::purgeTTSCache($nbdays);
            }
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[Cron Daily] Purge Cache ERROR :: ' . $e->getMessage());
        }
    }

    /*
     * Permet de déclencher une action avant modification d'une variable de configuration du plugin
     * Exemple avec la variable "param3"
    public static function preConfig_param3( $value ) {
        // do some checks or modify on $value
        return $value;
    }
    */

    /*
     * Permet de déclencher une action après modification d'une variable de configuration du plugin
     * Exemple avec la variable "param3"
    public static function postConfig_param3($value) {
        // no return value
    }
    */

    /*
   * Permet d'indiquer des éléments supplémentaires à remonter dans les informations de configuration
   * lors de la création semi-automatique d'un post sur le forum community
   public static function getConfigForCommunity() {
      return "les infos essentiel de mon plugin";
   }
   */

    /*     * *********************Méthodes d'instance************************* */

    // Fonction exécutée automatiquement avant la création de l'équipement
    public function preInsert() {
    }

    // Fonction exécutée automatiquement après la création de l'équipement
    public function postInsert() {
    }

    // Fonction exécutée automatiquement avant la mise à jour de l'équipement
    public function preUpdate() {
    }

    // Fonction exécutée automatiquement après la mise à jour de l'équipement
    public function postUpdate() {
    }

    // Fonction exécutée automatiquement avant la sauvegarde (création ou mise à jour) de l'équipement
    public function preSave() {
    }

    // Fonction exécutée automatiquement après la sauvegarde (création ou mise à jour) de l'équipement
    public function postSave() {
        $cmd = $this->getCmd(null, 'friendlyname');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Friendly Name', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('friendlyname');
            $cmd->setType('info');
            $cmd->setSubType('string');    
	        $cmd->setIsVisible(1);
	        // $cmd->setConfiguration('ttscastCmd', true);
            $cmd->save();
        }

        $cmd = $this->getCmd(null, 'tts');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('TTS', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('tts');
            $cmd->setType('action');
            $cmd->setSubType('message');    
	        $cmd->setIsVisible(1);
	        // $cmd->setConfiguration('ttscastCmd', true);
            $cmd->save();
        }

        $cmd = $this->getCmd(null, 'customcmd');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Custom Cmd', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('customcmd');
            $cmd->setType('action');
            $cmd->setSubType('message');    
	        $cmd->setIsVisible(1);
	        // $cmd->setConfiguration('ttscastCmd', true);
            $cmd->save();
        }
    }

    // Fonction exécutée automatiquement avant la suppression de l'équipement
    public function preRemove() {
    }

    // Fonction exécutée automatiquement après la suppression de l'équipement
    public function postRemove() {
    }

    /*
     * Permet de crypter/décrypter automatiquement des champs de configuration des équipements
     * Exemple avec le champ "Mot de passe" (password)
    public function decrypt() {
        $this->setConfiguration('password', utils::decrypt($this->getConfiguration('password')));
    }
    public function encrypt() {
        $this->setConfiguration('password', utils::encrypt($this->getConfiguration('password')));
    }
    */

    /*
     * Permet de modifier l'affichage du widget (également utilisable par les commandes)
    public function toHtml($_version = 'dashboard') {}
    */

    /* ***********************Getteur Setteur*************************** */
}

class ttscastCmd extends cmd
{
    /* **************************Attributs****************************** */

    /*
    public static $_widgetPossibility = array();
    */

    /* ************************Methode static*************************** */


    /* **********************Methode d'instance************************* */

    /*
     * Permet d'empêcher la suppression des commandes même si elles ne sont pas dans la nouvelle configuration de l'équipement envoyé en JS
    public function dontRemoveCmd() {
        return true;
    }
    */

    // Exécution d'une commande
    public function execute($_options = array()) {
        $eqLogic = $this->getEqLogic();
        $logicalId = $this->getLogicalId();
        
        log::add('ttscast', 'debug', '[CMD] eqLogic :: ');
        log::add('ttscast', 'debug', '[CMD] LogicalId :: ');

        if ( $this->GetType = "action" ) {
			if ($logicalId == "tts") {
                $googleName = $this->getConfiguration('friendlyname', null);
                log::add('ttscast', 'debug', '[CMD] Message / Volume / GoogleName :: ' . $_options['message'] . " / " . $_options['title'] . " / " . $googleName);
                if ($logicalId == "tts" && isset($googleName) && isset($_options['message']) && isset($_options['title']) && is_numeric($_options['title'])) {
                    ttscast::playTTS($googleName, $_options['message'], intval($_options['title']));
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour diffuser un message TTS');
                }
                
            } 
            
		} else {
			throw new Exception(__('Commande non implémentée actuellement', __FILE__));
		}
		return true;
    }

    /* ***********************Getteur Setteur*************************** */
}
