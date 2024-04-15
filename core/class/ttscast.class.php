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
    const PYENV_PATH = '/opt/pyenv/bin/pyenv';

    /* ************************** Attributs ****************************** */

    /*
     * Permet de définir les possibilités de personnalisation du widget (en cas d'utilisation de la fonction 'toHtml' par exemple)
     * Tableau multidimensionnel - exemple: array('custom' => true, 'custom::layout' => false) */
    public static $_widgetPossibility = array('custom' => true);

    /*
     * Permet de crypter/décrypter automatiquement des champs de configuration du plugin
     * Exemple : "param1" & "param2" seront cryptés mais pas "param3"
     */
    public static $_encryptConfigKey = array('voiceRSSAPIKey');    

    /* ************************ Methodes statiques : Démon & Dépendances *************************** */

    public static function backupExclude() {
		return [
			'resources/venv', 
            'resources/pyenv'
		];
	}
    
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
            } elseif (exec(system::getCmdSudo() . self::PYTHON3_PATH . ' -m pip freeze | grep -Ewc "PyChromecast==14.0.1|google-cloud-texttospeech==2.16.3|gTTS==2.5.1"') < 3) {
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

        try {
            self::getPyEnvVersion();
            self::getPythonVersion();
        }
        catch (Exception $e) {
            log::add('ttscast', 'error', '[DAEMON][START][PyVersions] Exception :: ' . $e->getMessage());
        }

        $path = realpath(__DIR__ . '/../../resources/ttscastd');
        $cmd = self::PYTHON3_PATH . " {$path}/ttscastd.py";
        $cmd .= ' --loglevel ' . log::convertLogLevel(log::getLogLevel(__CLASS__));
        $cmd .= ' --pluginversion ' . config::byKey('pluginVersion', __CLASS__, '0.0.0');
        $cmd .= ' --socketport ' . config::byKey('socketport', __CLASS__, '55111');
        $cmd .= ' --cyclefactor ' . config::byKey('cyclefactor', __CLASS__, '1');
        $cmd .= ' --callback ' . network::getNetworkAccess('internal', 'http:127.0.0.1:port:comp') . '/plugins/ttscast/core/php/jeettscast.php'; // chemin du callback
        if (config::byKey('ttsUseExtAddr', 'ttscast') == 1) {
            $cmd .= ' --ttsweb ' . network::getNetworkAccess('external');
        } else {
            $cmd .= ' --ttsweb ' . network::getNetworkAccess('internal');
        }
        $cmd .= ' --apikey ' . jeedom::getApiKey(__CLASS__);
        $cmd .= ' --apittskey ' . jeedom::getApiKey("apitts");
        $cmd .= ' --gcloudapikey ' . config::byKey('gCloudAPIKey', __CLASS__, 'noKey');
        $cmd .= ' --voicerssapikey ' . config::byKey('voiceRSSAPIKey', __CLASS__, 'noKey');
        $cmd .= ' --appdisableding ' . config::byKey('appDisableDing', __CLASS__, '0');
        $cmd .= ' --pid ' . jeedom::getTmpFolder(__CLASS__) . '/deamon.pid'; // ne PAS modifier
        # log::add(__CLASS__, 'debug', 'Lancement du démon :: ' . $cmd);
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
        config::save('scanState', '0', 'ttscast');
        return true;
    }

    public static function deamon_stop() {
        $pid_file = jeedom::getTmpFolder(__CLASS__) . '/deamon.pid'; // Ne PAS modifier
        if (file_exists($pid_file)) {
            $pid = intval(trim(file_get_contents($pid_file)));
            system::kill($pid);
        }
        system::kill('ttscastd.py');
        system::fuserk(config::byKey('socketport', __CLASS__, '55111'));
        sleep(1);
    }

    public static function sendToDaemon($params) {
        try {
            $deamon_info = self::deamon_info();
            if ($deamon_info['state'] != 'ok') {
                throw new Exception("Le Démon n'est pas démarré !");
            }
            $params['apikey'] = jeedom::getApiKey(__CLASS__);
            $payLoad = json_encode($params);
            $socket = socket_create(AF_INET, SOCK_STREAM, 0);
            socket_connect($socket, '127.0.0.1', config::byKey('socketport', __CLASS__, '55111'));
            socket_write($socket, $payLoad, strlen($payLoad));
            socket_close($socket);
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[SOCKET][SendToDaemon] Exception :: ' . $e->getMessage());
            /* event::add('jeedom::alert', array(
                'level' => 'warning',
                'page' => 'ttscast',
                'message' => __('[sendToDaemon] Exception :: ' . $e->getMessage(), __FILE__),
            )); */
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
        $ttsText = config::byKey('ttsTestFileGen', 'ttscast', '');
        $ttsGoogleName = config::byKey('ttsTestGoogleName', 'ttscast', '');
        $ttsVoiceName = config::byKey('gCloudTTSVoice', 'ttscast', 'fr-FR-Standard-A');
        $ttsRSSVoiceName = config::byKey('voiceRSSTTSVoice', 'ttscast', 'fr-fr-Bette');
        $ttsRSSSpeed = config::byKey('voiceRSSTTSSpeed', 'ttscast', '0');
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'jeedomtts');  // jeedomtts | gtranslatetts | gcloudtts | voicersstts
        $ttsLang = config::byKey('ttsLang', 'ttscast', 'fr-FR');
        $ttsSpeed = config::byKey('gCloudTTSSpeed', 'ttscast', '1.0');
        $value = array('cmd' => 'action', 'cmd_action' => 'ttstest', 'ttsEngine' => $ttsEngine, 'ttsLang' => $ttsLang, 'ttsSpeed' => $ttsSpeed, 'ttsText' => $ttsText, 'ttsGoogleName' => $ttsGoogleName, 'ttsVoiceName' => $ttsVoiceName, 'ttsRSSVoiceName' => $ttsRSSVoiceName, 'ttsRSSSpeed' => $ttsRSSSpeed);
        self::sendToDaemon($value);
    }

    public static function playTTS($gHome=null, $message=null, $options=null) {
        $ttsText = $message;
        $ttsGoogleUUID = $gHome;
        $ttsVoiceName = config::byKey('gCloudTTSVoice', 'ttscast', 'fr-FR-Standard-A');
        $ttsRSSVoiceName = config::byKey('voiceRSSTTSVoice', 'ttscast', 'fr-fr-Bette');
        $ttsRSSSpeed = config::byKey('voiceRSSTTSSpeed', 'ttscast', '0');
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'picotts');  // jeedomtts | gtranslatetts | gcloudtts
        $ttsLang = config::byKey('ttsLang', 'ttscast', 'fr-FR');
        $ttsSpeed = config::byKey('gCloudTTSSpeed', 'ttscast', '1.0');
        
        /* log::add('ttscast', 'debug', '[PlayTTS] Options Before Array :: ' . $options);

        $_appDisableDing = config::byKey('appDisableDing', 'ttscast', false);
        if ($_appDisableDing) {
            if ($options == null) {
                $_resOptions = array();
            } else {
                $_resOptions = json_decode("{" . $options . "}", true);
            }
            $_resOptions['ding'] = false;
            log::add('ttscast', 'debug', '[PlayTTS] _res Ding :: ' . json_encode($_resOptions['ding']));
            $ttsOptions = substr(json_encode($_resOptions), 1, -1);
        }
        else {
            $ttsOptions = $options;
        } */
        $ttsOptions = $options;
        log::add('ttscast', 'debug', '[PlayTTS] ttsOptions After Array :: ' . $ttsOptions);
        
        $value = array('cmd' => 'action', 'cmd_action' => 'tts', 'ttsLang' => $ttsLang, 'ttsEngine' => $ttsEngine, 'ttsSpeed' => $ttsSpeed, 'ttsOptions' => $ttsOptions, 'ttsText' => $ttsText, 'ttsGoogleUUID' => $ttsGoogleUUID, 'ttsVoiceName' => $ttsVoiceName, 'ttsRSSVoiceName' => $ttsRSSVoiceName, 'ttsRSSSpeed' => $ttsRSSSpeed);
        self::sendToDaemon($value);
    }

    public static function actionGCast($gHomeUUID=null, $action=null, $message=null) {
        log::add('ttscast', 'debug', '[ActionGCast] Infos :: ' . $gHomeUUID . ' / ' . $action . " / " . $message);
        $value = array('cmd' => 'action', 'cmd_action' => $action, 'value' => $message, 'googleUUID' => $gHomeUUID);
        log::add('ttscast', 'debug', '[ActionGCast] ArrayToSend :: ' . json_encode($value));
        self::sendToDaemon($value);
    }

    public static function mediaGCast($gHomeUUID=null, $action=null, $message=null, $options=null) {
        log::add('ttscast', 'debug', '[MediaGCast] Infos :: ' . $gHomeUUID . ' / ' . $action . " / " . $message . " / " . $options);
        $value = array('cmd' => 'action', 'cmd_action' => $action, 'value' => $message, 'googleUUID' => $gHomeUUID, 'options' => $options);
        log::add('ttscast', 'debug', '[MediaGCast] ArrayToSend :: ' . json_encode($value));
        self::sendToDaemon($value);
    }

    public static function customCmdDecoder($customCmd=null) {
        log::add('ttscast', 'debug', '[customCmdDecoder] CustomCmd :: ' . $customCmd);
        try {
            $data = json_decode("{" . $customCmd . "}", true);
            log::add('ttscast', 'debug', '[customCmdDecoder] CustomCmd Data :: ' . json_encode($data));
            $resAction = '';
            $resCmd = array();
            $resOptions = array();

            # Commande et Valeur
            if (array_key_exists('action', $data)) {
                $resAction = $data['action'];
            }
            if (array_key_exists('value', $data)) {
                if (in_array($resAction, ["radios", "customradios", "sounds", "customsounds"])) {
                    $resCmd['select'] = $data['value'];
                }
                elseif (in_array($resAction, ["volumeset"])) {
                    $resCmd['slider'] = $data['value'];
                }
                else {
                    $resCmd['message'] = $data['value'];
                }
            }

            # Options
            if (array_key_exists('force', $data)) {
                $resOptions['force'] = $data['force'];
            }
            if (array_key_exists('reload_seconds', $data)) {
                $resOptions['reload_seconds'] = $data['reload_seconds'];
            }
            if (array_key_exists('quit_app', $data)) {
                $resOptions['quit_app'] = $data['quit_app'];
            }
            if (array_key_exists('playlist', $data)) {
                $resOptions['playlist'] = $data['playlist'];
            }
            if (array_key_exists('enqueue', $data)) {
                $resOptions['enqueue'] = $data['enqueue'];
            }
            if (array_key_exists('volume', $data)) {
                $resOptions['volume'] = $data['volume'];
            }
            if (array_key_exists('ding', $data)) {
                $resOptions['ding'] = $data['ding'];
            }
            if (array_key_exists('type', $data)) {
                $resOptions['type'] = $data['type'];
            }

            $resCmd['title'] = substr(json_encode($resOptions), 1, -1);
            log::add('ttscast', 'debug', '[customCmdDecoder] CustomCmd Title :: ' . $resCmd['title']);
            return [$resAction, $resCmd];
        }
        catch (Exception $e) {
            log::add('ttscast', 'error', '[customCmdDecoder] CustomCmd Decoder Exception :: ' . $e->getMessage());
            return null;
        }
    }

    public static function getPluginVersion() {
        $pluginVersion = '0.0.0';
        try {
            if (!file_exists(dirname(__FILE__) . '/../../plugin_info/info.json')) {
                log::add('ttscast', 'warning', '[Plugin-Version] fichier info.json manquant');
            }
            $data = json_decode(file_get_contents(dirname(__FILE__) . '/../../plugin_info/info.json'), true);
            if (!is_array($data)) {
                log::add('ttscast', 'warning', '[Plugin-Version] Impossible de décoder le fichier info.json');
            }
            try {
                $pluginVersion = $data['pluginVersion'];
                // $pluginVersion .= " (" . update::byLogicalId('ttscast')->getLocalVersion() . ")";
            } catch (\Exception $e) {
                log::add('ttscast', 'warning', '[Plugin-Version] Impossible de récupérer la version du plugin');
            }
        }
        catch (\Exception $e) {
            log::add('ttscast', 'debug', '[Plugin-Version] Get ERROR :: ' . $e->getMessage());
        }
        log::add('ttscast', 'info', '[Plugin-Version] PluginVersion :: ' . $pluginVersion);
        return $pluginVersion;
    }

    public static function getPythonVersion() {
        $pythonVersion = '0.0.0';
        try {
            if (file_exists(self::PYTHON3_PATH)) {
               $pythonVersion = exec(system::getCmdSudo() . self::PYTHON3_PATH . " --version | awk '{ print $2 }'");
               config::save('pythonVersion', $pythonVersion, 'ttscast');
            }
            else {
                log::add('ttscast', 'error', '[Python-Version] Python File (venv) :: KO');
            }
        }
        catch (\Exception $e) {
            log::add('ttscast', 'error', '[Python-Version] Exception :: ' . $e->getMessage());
        }
        log::add('ttscast', 'info', '[Python-Version] PythonVersion (venv) :: ' . $pythonVersion);
        return $pythonVersion;
    }

    public static function getPyEnvVersion() {
        $pyenvVersion = '0.0.0';
        try {
            if (file_exists(self::PYENV_PATH)) {
               $pyenvVersion = exec(system::getCmdSudo() . self::PYENV_PATH . " --version | awk '{ print $2 }'");
               config::save('pyenvVersion', $pyenvVersion, 'ttscast');
            }
            elseif (file_exists(self::PYTHON3_PATH)) {
                $pythonPyEnvInUse = (exec(system::getCmdSudo() . 'dirname $(readlink ' . self::PYTHON3_PATH . ') | grep -Ewc "opt/pyenv"') == 1) ? true : false;
                if (!$pythonPyEnvInUse) {
                    $pyenvVersion = "-";
                    config::save('pyenvVersion', $pyenvVersion, 'ttscast');
                }
            }
            else {
                log::add('ttscast', 'error', '[PyEnv-Version] PyEnv File :: KO');
            }
        }
        catch (\Exception $e) {
            log::add('ttscast', 'error', '[PyEnv-Version] Exception :: ' . $e->getMessage());
        }
        log::add('ttscast', 'info', '[PyEnv-Version] PyEnvVersion :: ' . $pyenvVersion);
        return $pyenvVersion;
    }

    public static function changeScanState($_scanState)
    {
        if ($_scanState == "scanOn") {
            $value = array('cmd' => 'scanOn');
            self::sendToDaemon($value);
        } else {
            $value = array('cmd' => 'scanOff');
            self::sendToDaemon($value);
        }
    }

    public static function createAndUpdCastFromScan($_data)
    {
        if (!isset($_data['uuid'])) {
            log::add('ttscast', 'error', '[CREATEFROMSCAN] Information manquante (UUID) pour créer l\'équipement');
            event::add('jeedom::alert', array(
                'level' => 'danger',
                'page' => 'ttscast',
                'message' => __('[KO] Information manquante (UUID) pour créer l\'équipement', __FILE__),
            ));
            return false;
        }
        
        $newttscast = ttscast::byLogicalId($_data['uuid'], 'ttscast');
        if (!is_object($newttscast)) {
            $eqLogic = new ttscast();
            $eqLogic->setLogicalId($_data['uuid']);
            $eqLogic->setIsEnable(1);
            $eqLogic->setIsVisible(1);
            $eqLogic->setName($_data['friendly_name']);
            $eqLogic->setEqType_name('ttscast');
            $eqLogic->setCategory('multimedia','1');
            $eqLogic->setConfiguration('friendly_name', $_data['friendly_name']);
            $eqLogic->setConfiguration('model_name', $_data['model_name']);
            $eqLogic->setConfiguration('manufacturer', $_data['manufacturer']);
            $eqLogic->setConfiguration('cast_type', $_data['cast_type']);
            $eqLogic->setConfiguration('host', $_data['host']);
            $eqLogic->setConfiguration('port', $_data['port']);
            $eqLogic->setConfiguration('lastscan', $_data['lastscan']);
            $eqLogic->save();

            event::add('jeedom::alert', array(
                'level' => 'success',
                'page' => 'ttscast',
                'message' => __('[SCAN] TTSCast AJOUTE :: ' .$_data['friendly_name'], __FILE__),
            ));
            return $eqLogic;
        }
        else {
            $newttscast->setConfiguration('friendly_name', $_data['friendly_name']);
            $newttscast->setConfiguration('model_name', $_data['model_name']);
            $newttscast->setConfiguration('manufacturer', $_data['manufacturer']);
            $newttscast->setConfiguration('cast_type', $_data['cast_type']);
            $newttscast->setConfiguration('host', $_data['host']);
            $newttscast->setConfiguration('port', $_data['port']);
            $newttscast->setConfiguration('lastscan', $_data['lastscan']);
            $newttscast->save();

            event::add('jeedom::alert', array(
                'level' => 'success',
                'page' => 'ttscast',
                'message' => __('[SCAN] TTSCast MAJ :: ' .$_data['friendly_name'], __FILE__),
            ));
            return $newttscast;
        }
    }

    public static function scheduleUpdateCast($_data)
    {
        if (!isset($_data['uuid'])) {
            log::add('ttscast', 'error', '[SCHEDULE][CAST] Information manquante (UUID) pour mettre à jour l\'équipement');
            return false;
        }
        $updttscast = ttscast::byLogicalId($_data['uuid'], 'ttscast');
        if (!is_object($updttscast)) {
            log::add('ttscast', 'error', '[SCHEDULE][CAST] Cast non existant dans Jeedom');
            return false;
        }
        else {
            /* $cmd = $updttscast->getCmd('info', 'online');
            if (is_object($cmd)) {
                $cmd->event('1');
                log::add('ttscast', 'debug', '[SCHEDULE][CAST] Cast cmd event :: online');
            } */
            foreach($updttscast->getCmd('info') as $cmd) {
                $logicalId = $cmd->getLogicalId();
                # log::add('ttscast', 'debug', '[SCHEDULE][CAST] Cast cmd :: ' . $logicalId);
                if (key_exists($logicalId, $_data)) {
                    log::add('ttscast', 'debug', '[SCHEDULE][CAST] Cast cmd event :: ' . $logicalId . ' = ' . $_data[$logicalId]);
                    $cmd->event($_data[$logicalId]);
                } else {
                    # log::add('ttscast', 'debug', '[SCHEDULE][CAST] Cast cmd NON EXIST :: ' . $logicalId);
                    continue;       
                }
            }
        }
    }

    public static function realtimeUpdateCast($_data)
    {
        if (!isset($_data['uuid'])) {
            log::add('ttscast', 'error', '[REALTIME][CAST] Information manquante (UUID) pour mettre à jour l\'équipement');
            return false;
        }
        if (!isset($_data['status_type'])) {
            log::add('ttscast', 'error', '[REALTIME][CAST] Information manquante (Status_Type) pour mettre à jour l\'équipement');
            return false;
        } else {
            log::add('ttscast', 'debug', '[REALTIME][CAST] Status Type :: ' . $_data['status_type']);
        }
        $rtcast = ttscast::byLogicalId($_data['uuid'], 'ttscast');
        if (!is_object($rtcast)) {
            log::add('ttscast', 'error', '[REALTIME][CAST] Cast non existant dans Jeedom');
            return false;
        }
        else {
            foreach($rtcast->getCmd('info') as $cmd) {
                $logicalId = $cmd->getLogicalId();
                # log::add('ttscast', 'debug', '[REALTIME][CAST] Cast cmd :: ' . $logicalId);
                if (key_exists($logicalId, $_data)) {
                    log::add('ttscast', 'debug', '[REALTIME][CAST] Cast cmd event :: ' . $logicalId . ' = ' . $_data[$logicalId]);
                    $cmd->event($_data[$logicalId]);
                } else {
                    log::add('ttscast', 'debug', '[REALTIME][CAST] Cast cmd NON EXIST :: ' . $logicalId);
                    continue;
                }
            }
        }
    }

    public static function sendOnStartCastToDaemon()
    {
        log::add('ttscast', 'info', '[SendOnStart] Envoi Equipements TTSCast Actifs');
        $i = 0;
        while ($i < 10) {
            $deamon_info = self::deamon_info();
            if ($deamon_info['state'] == 'ok') {
                break;
            }
            sleep(1);
            $i++;
        }
        if ($i >= 10) {
            log::add('ttscast', 'error', '[SendOnStart] Démon non lancé (>10s) :: KO');
            return false;
        }
        foreach(self::byType('ttscast') as $eqLogic) {
            if ($eqLogic->getIsEnable()) {
                $eqLogic->enableCastToDaemon();
            }
            else {
                $eqLogic->disableCastToDaemon();
            }   
        }
    }

    public function enableCastToDaemon()
    {
        if ($this->getLogicalId() != '') {
            $value = array(
                'cmd' => 'addcast',
                'uuid' => $this->getLogicalId(),
                'host' => $this->getConfiguration('host'),
                'friendly_name' => $this->getConfiguration('friendly_name')
            );
            self::sendToDaemon($value);
        }

    }

    public function disableCastToDaemon()
    {
        if ($this->getLogicalId() != '') {
            $value = array(
                'cmd' => 'removecast',
                'uuid' => $this->getLogicalId(),
                'host' => $this->getConfiguration('host'),
                'friendly_name' => $this->getConfiguration('friendly_name')
            );
            self::sendToDaemon($value);
        }
    }

    public function getRadioList()
    {
        $radiosReturn = '';
        try {
            if (!file_exists(dirname(__FILE__) . '/../../data/radios/radios.json')) {
                log::add('ttscast', 'error', '[getRadioList] Radios File Missing :: KO');
                return $radiosReturn;
            }
            $radiosJson = json_decode(file_get_contents(dirname(__FILE__) . "/../../data/radios/radios.json"), true);            
            if (!is_array($radiosJson)) {
                log::add('ttscast', 'error', '[getRadioList] Impossible de décoder le fichier radios.json :: KO');
                return $radiosReturn;
            }

            $radiosArray = array();
            foreach ($radiosJson as $radioId => $radioData) {
                $radiosArray[$radioId] = $radioData['title'];
            }
            ksort($radiosArray);

            foreach ($radiosArray as $radioId => $radioTitle) {
                $radiosReturn .= $radioId . '|' . $radioTitle . ';';
            }
            $radiosReturn = trim($radiosReturn, ";");

        } catch (Exception $e) {
            log::add('ttscast', 'error', '[getRadioList] Radio Listing ERROR :: ' . $e->getMessage());
        }
        return $radiosReturn;
    }

    public function getCustomRadioList()
    {
        $customRadiosReturn = '';
        try {
            if (!file_exists(dirname(__FILE__) . '/../../data/radios/custom/radios.json')) {
                log::add('ttscast', 'warning', '[getCustomRadioList] Custom Radios :: No Custom File');
                return $customRadiosReturn;
            }
            $customRadiosJson = json_decode(file_get_contents(dirname(__FILE__) . "/../../data/radios/custom/radios.json"), true);
            if (!is_array($customRadiosJson)) {
                log::add('ttscast', 'error', '[getCustomRadioList] Impossible de décoder le fichier radios.json :: KO');
                return $customRadiosReturn;
            }

            $customRadiosArray = array();
            foreach ($customRadiosJson as $radioId => $radioData) {
                $customRadiosArray[$radioId] = $radioData['title'];
            }
            ksort($customRadiosArray);

            foreach ($customRadiosArray as $radioId => $radioTitle) {
                $customRadiosReturn .= $radioId . '|' . $radioTitle . ';';
            }
            $customRadiosReturn = trim($customRadiosReturn, ";");

        } catch (Exception $e) {
            log::add('ttscast', 'error', '[getCustomRadioList] Custom Radios Listing ERROR :: ' . $e->getMessage());
        }
        return $customRadiosReturn;
    }

    public function getSoundList()
    {
        $filesReturn = '';
        try {
            $filesArray = array();
            foreach (glob(dirname(__FILE__) . '/../../data/media/*.mp3') as $fileName) {
                $filesArray[pathinfo($fileName, PATHINFO_BASENAME)] = ucwords(str_replace(["_", "-"], " ", pathinfo($fileName, PATHINFO_FILENAME)));
            }
            natsort($filesArray);
            foreach ($filesArray as $filePath => $fileName) {
                $filesReturn .= $filePath . '|' . $fileName . ';';
            }
            $filesReturn = trim($filesReturn, ";");
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[getSoundList] Sound Listing ERROR :: ' . $e->getMessage());
        }
        return $filesReturn;
    }

    public function getCustomSoundList()
    {
        $filesReturn = '';
        try {
            $filesArray = array();
            foreach (glob(dirname(__FILE__) . '/../../data/media/custom/*.mp3') as $fileName) {
                $filesArray[pathinfo($fileName, PATHINFO_BASENAME)] = ucwords(str_replace(["_", "-"], " ", pathinfo($fileName, PATHINFO_FILENAME)));
            }
            natsort($filesArray);
            foreach ($filesArray as $filePath => $fileName) {
                $filesReturn .= $filePath . '|' . $fileName . ';';
            }
            $filesReturn = trim($filesReturn, ";");
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[getCustomSoundList] Custom Sound Listing ERROR :: ' . $e->getMessage());
        }
        return $filesReturn;
    }

    public static function updateRadioList()
    {
        try {
            foreach(self::byType('ttscast') as $eqLogic) {
                $cmd = $eqLogic->getCmd(null, 'radios');
                if (is_object($cmd)) {
                    $radioList = $eqLogic->getRadioList();
                    $cmd->setConfiguration('listValue', $radioList);
                    $cmd->save();
                }
            }
            log::add('ttscast', 'info', '[updateRadioList] Radio List Update :: OK ');
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[updateRadioList] Radio Update ERROR :: ' . $e->getMessage());
        }
    }

    public static function updateCustomRadioList()
    {
        try {
            foreach(self::byType('ttscast') as $eqLogic) {
                $cmd = $eqLogic->getCmd(null, 'customradios');
                if (is_object($cmd)) {
                    $customRadioList = $eqLogic->getCustomRadioList();
                    $cmd->setConfiguration('listValue', $customRadioList);
                    $cmd->save();
                }
            }
            log::add('ttscast', 'info', '[updateCustomRadioList] CustomRadio List Update :: OK ');
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[updateCustomRadioList] CustomRadio Update ERROR :: ' . $e->getMessage());
        }
    }

    public static function updateSoundList()
    {
        try {
            foreach(self::byType('ttscast') as $eqLogic) {
                $cmd = $eqLogic->getCmd(null, 'sounds');
                if (is_object($cmd)) {
                    $soundList = $eqLogic->getSoundList();
                    $cmd->setConfiguration('listValue', $soundList);
                    $cmd->save();
                }
            }
            log::add('ttscast', 'info', '[updateSoundList] Sound List Update :: OK ');
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[updateSoundList] Sound Update ERROR :: ' . $e->getMessage());
        }
    }

    public static function updateCustomSoundList()
    {
        try {
            foreach(self::byType('ttscast') as $eqLogic) {
                $cmd = $eqLogic->getCmd(null, 'customsounds');
                if (is_object($cmd)) {
                    $customSoundList = $eqLogic->getCustomSoundList();
                    $cmd->setConfiguration('listValue', $customSoundList);
                    $cmd->save();
                }
            }
            log::add('ttscast', 'info', '[updateCustomSoundList] Custom Sound List Update :: OK ');
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[updateCustomSoundList] Custom Sound Update ERROR :: ' . $e->getMessage());
        }
    }

    public function cleanupFileName($name)
    {
        $name = trim(strtolower($name));
        $name = sanitizeAccent($name);
        $name = str_replace([' ', '-'], '_', $name);
        $name = preg_replace('/[^a-z0-9_]/i', '', $name);
        return $name;
    }

    public function getImage()
    {
        $model = $this->getConfiguration('model_name');
        if ($model != '') {
            $model = ttscast::cleanupFileName($model);
            if (file_exists(__DIR__ . "/../../data/images/models/{$model}.png")) {
                return "plugins/ttscast/data/images/models/{$model}.png";
            }
            log::add(__CLASS__, 'info', "[GetImage] No Image available for {$model}");
        }
        return parent::getImage();
    }

    /* ************************ Methodes static : JEEDOM *************************** */

    /*
     * Fonction exécutée automatiquement toutes les minutes par Jeedom
    public static function cron() {}
    */

    
    // * Fonction exécutée automatiquement toutes les 5 minutes par Jeedom
    public static function cron5() {
        $currentTime = time();
        foreach(self::byType('ttscast') as $eqLogic) {
            $lastSchedule = $eqLogic->getCmd('info', 'lastschedulets');
            if ($currentTime - intval($lastSchedule->execCmd()) >= 180) {
                log::add('ttscast', 'debug', '[CRON5][ONLINE] TTSCast :: ' . $eqLogic->getConfiguration('friendly_name') . ' is OFFLINE');
                $cmd = $eqLogic->getCmd('info', 'online');
                if (is_object($cmd)) {
                    $cmd->event('0');
                }
                // TODO Envoyer l'event au démon pour désactiver ce cast   
            }
        }   

    }
    

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
        $orderCmd = 1;

        $cmd = $this->getCmd(null, 'refresh');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Rafraîchir', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('refresh');
            $cmd->setType('action');
            $cmd->setSubType('other');    
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }
        
        $cmd = $this->getCmd(null, 'refreshcast');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Rafraîchir Cast', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('refreshcast');
            $cmd->setType('action');
            $cmd->setSubType('other');
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'online');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('En Ligne', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('online');
            $cmd->setType('info');
            $cmd->setSubType('binary');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }
        
        $cmd = $this->getCmd(null, 'is_idle');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Idle', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('is_idle');
            $cmd->setType('info');
            $cmd->setSubType('binary');
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'is_busy');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Busy', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('is_busy');
            $cmd->setType('info');
            $cmd->setSubType('binary');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'volume_level');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Volume', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('volume_level');
            $cmd->setType('info');
            $cmd->setSubType('numeric');
            $cmd->setUnite('%');
            $cmd->setConfiguration('minValue', 0);
            $cmd->setConfiguration('maxValue', 100);
            $cmd->setTemplate('dashboard', 'core::tile');
            $cmd->setTemplate('mobile', 'core::tile');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }
        $volumeLevelId = $cmd->getId();

        $cmd = $this->getCmd(null, 'volumeset');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Volume Set', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('volumeset');
            $cmd->setType('action');
            $cmd->setSubType('slider');
	        $cmd->setIsVisible(1);
            $cmd->setTemplate('dashboard', 'core::value');
            $cmd->setTemplate('mobile', 'core::value');
            $cmd->setValue($volumeLevelId);
            $cmd->setConfiguration('minValue', 0);
            $cmd->setConfiguration('maxValue', 100);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'volume_muted');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Mute', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('volume_muted');
            $cmd->setType('info');
            $cmd->setSubType('binary');
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }
        $mute_cmd_id = $cmd->getId();

        $cmd = $this->getCmd(null, 'mute_on');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Mute On', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('mute_on');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-volume-mute"></i>');
            $cmd->setValue($mute_cmd_id);
	        $cmd->setIsVisible(1);
            $cmd->setTemplate('dashboard', 'core::toggle');
            $cmd->setTemplate('mobile', 'core::toggle');
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'mute_off');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Mute Off', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('mute_off');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-volume-off"></i>');
            $cmd->setValue($mute_cmd_id);
	        $cmd->setIsVisible(1);
            $cmd->setTemplate('dashboard', 'core::toggle');
            $cmd->setTemplate('mobile', 'core::toggle');
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'volumedown');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Volume Down', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('volumedown');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-volume-down"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'volumeup');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Volume Up', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('volumeup');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-volume-up"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_previous');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Previous', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_previous');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-step-backward"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_rewind');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Rewind', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_rewind');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-backward"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_play');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Play', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_play');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-play"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_pause');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Pause', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_pause');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-pause"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_stop');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Stop', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_stop');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-stop"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_next');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Next', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_next');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-step-forward"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'media_quit');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media Quit', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media_quit');
            $cmd->setType('action');
            $cmd->setSubType('other');
            $cmd->setDisplay('icon', '<i class="fas fa-eject"></i>');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'lastschedule');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Schedule LastTime', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('lastschedule');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'lastschedulets');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Schedule LastTime (TS)', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('lastschedulets');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'player_state');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media State', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('player_state');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'display_name');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast App Name', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('display_name');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'app_id');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast App Id', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('app_id');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'status_text');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Status Text', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('status_text');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'title');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Title', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('title');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'artist');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Artist', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('artist');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'album_name');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Album', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('album_name');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'duration');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Duration', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('duration');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'current_time');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media CurrentTime', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('current_time');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'content_type');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Type', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('content_type');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'stream_type');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Stream Type', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('stream_type');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'last_updated');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Updated', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('last_updated');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'image');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Media Image', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('image');
            $cmd->setType('info');
            $cmd->setSubType('string');
            $cmd->setTemplate('dashboard', 'ttscast::cast-image');
            $cmd->setTemplate('mobile', 'ttscast::cast-image');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
            $cmd->setDisplay('showNameOndashboard', '0');
            $cmd->setDisplay('showNameOnmobile', '0');
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
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
            $cmd->setDisplay('parameters', array("title_placeholder" => "Options", "message_placeholder" => "TTS"));
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        if ($this->getConfiguration('cast_type', '') == 'cast') {
            $cmd = $this->getCmd(null, 'youtube');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('YouTube', __FILE__));
                $cmd->setEqLogic_id($this->getId());
                $cmd->setLogicalId('youtube');
                $cmd->setType('action');
                $cmd->setSubType('message');
                $cmd->setIsVisible(0);
                $cmd->setDisplay('parameters', array("title_placeholder" => "Options", "message_placeholder" => "Vidéo Id"));
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            } else {
                $orderCmd++;
            }

            $cmd = $this->getCmd(null, 'dashcast');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Web', __FILE__));
                $cmd->setEqLogic_id($this->getId());
                $cmd->setLogicalId('dashcast');
                $cmd->setType('action');
                $cmd->setSubType('message');
                $cmd->setIsVisible(0);
                $cmd->setDisplay('parameters', array("title_placeholder" => "Options", "message_placeholder" => "Page Web (URL)"));
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            } else {
                $orderCmd++;
            }
        }

        $cmd = $this->getCmd(null, 'media');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Media', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('media');
            $cmd->setType('action');
            $cmd->setSubType('message');
            $cmd->setIsVisible(0);
            $cmd->setDisplay('parameters', array("title_placeholder" => "Options", "message_placeholder" => "Media"));
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'radios');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Radios', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('radios');
            $cmd->setType('action');
            $cmd->setSubType('select');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
            $radioList = $this->getRadioList();
            $cmd->setConfiguration('listValue', $radioList);
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'customradios');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Custom Radios', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('customradios');
            $cmd->setType('action');
            $cmd->setSubType('select');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
            $customRadioList = $this->getCustomRadioList();
            $cmd->setConfiguration('listValue', $customRadioList);
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'sounds');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Sounds', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('sounds');
            $cmd->setType('action');
            $cmd->setSubType('select');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
            $soundList = $this->getSoundList();
            $cmd->setConfiguration('listValue', $soundList);
	        $cmd->setIsVisible(1);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'customsounds');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Custom Sounds', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('customsounds');
            $cmd->setType('action');
            $cmd->setSubType('select');
            $customSoundList = $this->getCustomSoundList();
            $cmd->setConfiguration('listValue', $customSoundList);
	        $cmd->setIsVisible(0);
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        $cmd = $this->getCmd(null, 'customcmd');
        if (!is_object($cmd)) {
	        $cmd = new ttscastCmd();
            $cmd->setName(__('Custom Cmd', __FILE__));
            $cmd->setEqLogic_id($this->getId());
	        $cmd->setLogicalId('customcmd');
            $cmd->setType('action');
            $cmd->setSubType('message');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
	        $cmd->setIsVisible(0);
            $cmd->setDisplay('parameters', array("title_disable" => "1", "title_placeholder" => "Options", "message_placeholder" => "Custom Cmd"));
            $cmd->setOrder($orderCmd++);
            $cmd->save();
        } else {
            $orderCmd++;
        }

        if ($this->getIsEnable()) {
            $this->enableCastToDaemon();
        } else {
            $this->disableCastToDaemon();
        }
    }

    // Fonction exécutée automatiquement avant la suppression de l'équipement
    public function preRemove() {
        $this->disableCastToDaemon();
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

    public static $_widgetPossibility = array('custom' => true);

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
        
        log::add('ttscast', 'debug', '[CMD] LogicalId :: ' . $logicalId);

        if ( $this->getType() == "action" ) {
			if (in_array($logicalId, ["customcmd"])) {
                if (isset($_options['message'])) {
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                    [$logicalId, $_options] = ttscast::customCmdDecoder($_options['message']);
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Custom Decoded Message) :: ' . json_encode($_options));
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour lancer la commande '. $logicalId);
                }                
            }
            
            if ($logicalId == "tts") {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID) && isset($_options['message'])) {
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Message / GoogleUUID) :: ' . $_options['message'] . " / " . $googleUUID);
                    ttscast::playTTS($googleUUID, $_options['message'], $_options['title']);
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour diffuser un message TTS');
                }                
            } elseif ($logicalId == "volumeset") {
                log::add('ttscast', 'debug', '[CMD] VolumeSet Keys :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID) && isset($_options['slider'])) {
                    log::add('ttscast', 'debug', '[CMD] VolumeSet :: ' . $_options['slider'] . ' / ' . $googleUUID);
                    ttscast::actionGCast($googleUUID, "volumeset", $_options['slider']);
                } else {
                    log::add('ttscast', 'debug', '[CMD] VolumeSet :: ERROR = Mauvais paramètre');
                }
            } elseif (in_array($logicalId, ["volumedown", "volumeup", "media_pause", "media_play", "media_stop", "media_previous", "media_next", "media_quit", "media_rewind", "mute_on", "mute_off"])) {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID)) {
                    ttscast::actionGCast($googleUUID, $logicalId);
                }
            } elseif (in_array($logicalId, ["youtube", "dashcast", "media"])) {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID) && isset($_options['message'])) {
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Message / GoogleUUID) :: ' . $_options['message'] . " / " . $googleUUID);
                    ttscast::mediaGCast($googleUUID, $logicalId, $_options['message'], $_options['title']);
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour lancer la commande '. $logicalId);
                }                
            } elseif (in_array($logicalId, ["radios", "customradios", "sounds", "customsounds"])) {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID) && isset($_options['select'])) {
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Select / GoogleUUID) :: ' . $_options['select'] . " / " . $googleUUID);
                    ttscast::mediaGCast($googleUUID, $logicalId, $_options['select'], $_options['title']);
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour lancer la commande '. $logicalId);
                }                
            } elseif (in_array($logicalId, ["refresh", "refreshcast"])) {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
            }
            else {
                throw new Exception(__('Commande Action non implémentée actuellement', __FILE__));    
            }
		} else {
			throw new Exception(__('Commande non implémentée actuellement', __FILE__));
		}
		return true;
    }

    /* ***********************Getteur Setteur*************************** */
}
