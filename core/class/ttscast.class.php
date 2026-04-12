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

    /* ************************ Méthodes statiques : Démon & Dépendances *************************** */

    public static function backupExclude() {
        return [
            'resources/venv', 
            'resources/pyenv'
        ];
    }

    public static function tts($_filename, $_text) {
        try {
            log::add('ttscast', 'debug', '[generateTTS] TTS API :: ' . $_filename . ' :: ' . $_text);
            if (config::byKey('ttsEngine', 'ttscast', 'gtranslatetts') != 'jeedomtts') {
                ttscast::generateTTS($_filename, $_text);
            
                $timeout = config::byKey('ttsGenTimeout', 'ttscast', 30); // Maximum time to wait in seconds
                $start = time(); // Start time
            
                // Wait for the file to be created
                while (!file_exists($_filename)) {
                    // Check if the maximum timeout has been reached
                    if (time() - $start > $timeout) {
                        throw new \Exception('Timeout: File not created');
                    }
                
                    // Sleep for a short period before checking again
                    usleep(250000); // 250 milliseconds
                }
            
                log::add('ttscast', 'debug', '[generateTTS] File created: ' . $_filename);
                return true;
            } else {
                // file_put_contents($_filename, '');
                log::add('ttscast', 'error', '[generateTTS] You can\'t use Jeedom TTS as engine (in the plugin) and call it from Jeedom TTS API !!');
                return false;
            }
            
        } catch (Exception $e) {
            log::add('ttscast', 'error', '[generateTTS] ' . $e->getMessage());
            return false;
        }
    }
    
    public static function dependancy_install() {
        log::remove(__CLASS__ . '_update');
        
        // debug options for install script
        $script_sysUpdates = 0;
        $script_restorePyEnv = 0;
        $script_restoreVenv = 0;

        if (config::byKey('debugInstallUpdates', 'ttscast') == '1') {
            $script_sysUpdates = 1;
            config::save('debugInstallUpdates', '0', 'ttscast');
        }
        if (config::byKey('debugRestorePyEnv', 'ttscast') == '1') {
            $script_restorePyEnv = 1;
            config::save('debugRestorePyEnv', '0', 'ttscast');
        }
        if (config::byKey('debugRestoreVenv', 'ttscast') == '1') {
            $script_restoreVenv = 1;
            config::save('debugRestoreVenv', '0', 'ttscast');
        }

        return array('script' => __DIR__ . '/../../resources/install_#stype#.sh ' . jeedom::getTmpFolder(__CLASS__) . '/dependency' . ' ' . $script_sysUpdates . ' ' . $script_restorePyEnv . ' ' . $script_restoreVenv, 'log' => log::getPathToLog(__CLASS__ . '_update'));
    }

    public static function dependancy_info() {
        $return = array();
        $return['log'] = log::getPathToLog(__CLASS__ . '_update');
        $return['progress_file'] = jeedom::getTmpFolder(__CLASS__) . '/dependency';
        if (file_exists(jeedom::getTmpFolder(__CLASS__) . '/dependency')) {
            $return['state'] = 'in_progress';
        } else {
            if (exec(system::getCmdSudo() . system::get('cmd_check') . '-Ec "python3\-requests|python3\-setuptools|python3\-dev|python3\-venv"') < 4) {
                log::add('ttscast', 'debug', '[DepInfo][ERROR] Missing system dependencies');
                $return['state'] = 'nok';
            } elseif (!file_exists(self::PYTHON3_PATH)) {
                $return['state'] = 'nok';
            } elseif (exec(system::getCmdSudo() . self::PYTHON3_PATH . ' -m pip freeze | grep -Eiwc "' . config::byKey('pythonDepString', 'ttscast', '', true) . '"') < config::byKey('pythonDepNum', 'ttscast', 0, true)) {
                log::add('ttscast', 'debug', '[DepInfo][ERROR] Missing Python dependencies');
                $return['state'] = 'nok';
            } else {
                log::add('ttscast', 'debug', '[DepInfo][INFO] All dependencies are installed');
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
        $cmd .= ' --gcloudaudioencoding ' . config::byKey('gCloudAudioEncoding', __CLASS__, 'MP3');
        $cmd .= ' --voicerssapikey ' . config::byKey('voiceRSSAPIKey', __CLASS__, 'noKey');
        $cmd .= ' --ttsdisablecache ' . config::byKey('ttsDisableCache', __CLASS__, '0');
        $cmd .= ' --appdisableding ' . config::byKey('appDisableDing', __CLASS__, '0');
        $cmd .= ' --appconvertsinglequote ' . config::byKey('appConvertSingleQuote', __CLASS__, '0');
        $cmd .= ' --cmdwaittimeout ' . config::byKey('cmdWaitTimeout', __CLASS__, '60');
        $cmd .= ' --aienabled ' . config::byKey('ttsAIEnable', __CLASS__, '0');
        $cmd .= ' --aidefault ' . config::byKey('ttsAIDefault', __CLASS__, '0');
        $cmd .= ' --aiauthmode ' . config::byKey('ttsAIAuthMode', __CLASS__, 'noMode');
        $cmd .= ' --aiprojectid ' . config::byKey('ttsAIProjectID', __CLASS__, 'noProjectID');
        $cmd .= ' --aiapikey ' . config::byKey('ttsAIAPIKey', __CLASS__, 'noKey');
        $cmd .= ' --aimodel ' . config::byKey('ttsAIModel', __CLASS__, 'noModel');
        $cmd .= ' --aidefaulttone "' . config::byKey('ttsAIDefaultTone', __CLASS__, 'NoDefaultTone') . '"';
        $cmd .= ' --aiusecustomsysprompt ' . config::byKey('ttsAIUseCustomSysPrompt', __CLASS__, '0');
        $cmd .= ' --aicustomsysprompt "' . config::byKey('ttsAICustomSysPrompt', __CLASS__, 'NoCustomSysPrompt') . '"';

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
            if ($pid > 0) {
                system::kill($pid, false); // SIGTERM seul, sans SIGKILL immédiat
                for ($i = 0; $i < 30 && file_exists($pid_file); $i++) {
                    usleep(100000); // Attend max 3s que le processus meure
                }
            }
            @unlink($pid_file);
        }
        system::kill('ttscastd.py'); // SIGKILL de sécurité si zombie
        system::fuserk(config::byKey('socketport', __CLASS__, '55111'));
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
            return true;
        } catch (\Exception $e) {
            log::add('ttscast', 'error', '[SOCKET][SendToDaemon] Exception :: ' . $e->getMessage());
            /* event::add('jeedom::alert', array(
                'level' => 'warning',
                'page' => 'ttscast',
                'message' => __('[sendToDaemon] Exception :: ' . $e->getMessage(), __FILE__),
            )); */
            return false;
        }
    }

    /**
     * Envoie un message sur le socket et attend la réponse (synchrone).
     * Utilisé pour les commandes request/response comme aiReformat.
     */
    public static function sendToDaemonSync($params, $timeout = 30) {
        try {
            $deamon_info = self::deamon_info();
            if ($deamon_info['state'] != 'ok') {
                throw new Exception("Le Démon n'est pas démarré !");
            }
            $params['apikey'] = jeedom::getApiKey(__CLASS__);
            $payLoad = json_encode($params);
            $socket = socket_create(AF_INET, SOCK_STREAM, 0);
            socket_set_option($socket, SOL_SOCKET, SO_RCVTIMEO, ['sec' => $timeout, 'usec' => 0]);
            socket_connect($socket, '127.0.0.1', config::byKey('socketport', __CLASS__, '55111'));
            socket_write($socket, $payLoad, strlen($payLoad));
            socket_shutdown($socket, 1); // SHUT_WR : signale EOF au démon
            $response = '';
            while (($chunk = socket_read($socket, 4096)) !== false && $chunk !== '') {
                $response .= $chunk;
            }
            socket_close($socket);
            if ($response === '') {
                return null;
            }
            return json_decode($response, true);
        } catch (\Exception $e) {
            log::add('ttscast', 'error', '[SOCKET][SendToDaemonSync] Exception :: ' . $e->getMessage());
            return null;
        }
    }

    /* ************************ Méthodes static : PLUGIN *************************** */

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
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'gtranslatetts');  // jeedomtts | gtranslatetts | gcloudtts | voicersstts
        $ttsLang = config::byKey('ttsLang', 'ttscast', 'fr-FR');
        $ttsSpeed = config::byKey('gCloudTTSSpeed', 'ttscast', '1.0');
        $ttsSSML = config::byKey('ttsTestSSML', 'ttscast', '0');
        $ttsAI = config::byKey('ttsTestAI', 'ttscast', '0');
        $value = array('cmd' => 'action', 'cmd_action' => 'ttstest', 'ttsEngine' => $ttsEngine, 'ttsLang' => $ttsLang, 'ttsSpeed' => $ttsSpeed, 'ttsText' => $ttsText, 'ttsGoogleName' => $ttsGoogleName, 'ttsVoiceName' => $ttsVoiceName, 'ttsRSSVoiceName' => $ttsRSSVoiceName, 'ttsRSSSpeed' => $ttsRSSSpeed, 'ttsSSML' => $ttsSSML, 'ttsAI' => $ttsAI);
        self::sendToDaemon($value);
    }

    public static function generateTTS($file=null, $message=null, $options=null) {
        $ttsFile = $file;
        $ttsText = $message;
        $ttsVoiceName = config::byKey('gCloudTTSVoice', 'ttscast', 'fr-FR-Standard-A');
        $ttsRSSVoiceName = config::byKey('voiceRSSTTSVoice', 'ttscast', 'fr-fr-Bette');
        $ttsRSSSpeed = config::byKey('voiceRSSTTSSpeed', 'ttscast', '0');
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'gtranslatetts');  // jeedomtts | gtranslatetts | gcloudtts
        $ttsLang = config::byKey('ttsLang', 'ttscast', 'fr-FR');
        $ttsSpeed = config::byKey('gCloudTTSSpeed', 'ttscast', '1.0');

        $ttsOptions = $options;
        log::add('ttscast', 'debug', '[generateTTS] ttsOptions After Array :: ' . $ttsOptions);
        
        $value = array('cmd' => 'action', 'cmd_action' => 'generatetts', 'ttsLang' => $ttsLang, 'ttsEngine' => $ttsEngine, 'ttsSpeed' => $ttsSpeed, 'ttsOptions' => $ttsOptions, 'ttsText' => $ttsText, 'ttsFile' => $ttsFile, 'ttsVoiceName' => $ttsVoiceName, 'ttsRSSVoiceName' => $ttsRSSVoiceName, 'ttsRSSSpeed' => $ttsRSSSpeed);
        self::sendToDaemon($value);
    }

    public static function playTTS($gHome=null, $message=null, $options=null, $cmdNotificationId=0) {
        $ttsText = $message;
        $ttsGoogleUUID = $gHome;
        $ttsVoiceName = config::byKey('gCloudTTSVoice', 'ttscast', 'fr-FR-Standard-A');
        $ttsRSSVoiceName = config::byKey('voiceRSSTTSVoice', 'ttscast', 'fr-fr-Bette');
        $ttsRSSSpeed = config::byKey('voiceRSSTTSSpeed', 'ttscast', '0');
        $ttsEngine = config::byKey('ttsEngine', 'ttscast', 'gtranslatetts');  // jeedomtts | gtranslatetts | gcloudtts
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
        
        $value = array('cmd' => 'action', 'cmd_action' => 'tts', 'ttsLang' => $ttsLang, 'ttsEngine' => $ttsEngine, 'ttsSpeed' => $ttsSpeed, 'ttsOptions' => $ttsOptions, 'ttsText' => $ttsText, 'ttsGoogleUUID' => $ttsGoogleUUID, 'ttsVoiceName' => $ttsVoiceName, 'ttsRSSVoiceName' => $ttsRSSVoiceName, 'ttsRSSSpeed' => $ttsRSSSpeed, 'cmdNotificationId' => $cmdNotificationId);
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
            $optionKeys = [
                'force', 'reload_seconds', 'quit_app', 'playlist', 'enqueue', 'volume',
                'ding', 'wait', 'type', 'ssml', 'genai', 'before', 'voice', 'aitone', 'aisysprompt', 'aitemp'
            ];
            foreach ($optionKeys as $key) {
                if (array_key_exists($key, $data)) {
                    $resOptions[$key] = $data[$key];
                }
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
                return $pluginVersion;
            }
            $data = json_decode(file_get_contents(dirname(__FILE__) . '/../../plugin_info/info.json'), true);
            if (!is_array($data)) {
                log::add('ttscast', 'warning', '[Plugin-Version] Impossible de décoder le fichier info.json');
                return $pluginVersion;
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

    public static function getPythonDepFromRequirements() {
        $pythonDepString = '';
        $pythonDepNum = 0;
        try {
            if (!file_exists(dirname(__FILE__) . '/../../resources/requirements.txt')) {
                log::add('ttscast', 'error', '[Python-Dep] Fichier requirements.txt manquant');
                config::save('pythonDepString', $pythonDepString, 'ttscast');
                config::save('pythonDepNum', $pythonDepNum, 'ttscast');
                return false;
            }
            $data = file_get_contents(dirname(__FILE__) . '/../../resources/requirements.txt');
            if (!is_string($data)) {
                log::add('ttscast', 'error', '[Python-Dep] Impossible de lire le fichier requirements.txt');
                config::save('pythonDepString', $pythonDepString, 'ttscast');
                config::save('pythonDepNum', $pythonDepNum, 'ttscast');
                return false;
            }
            $lines = explode("\n", $data);
            $nonEmptyLines = array_filter($lines, function($line) {
                return trim($line) !== '';
            });
            $pythonDepString = join("|", $nonEmptyLines);
            $pythonDepNum = count($nonEmptyLines);
        }
        catch (\Exception $e) {
            log::add('ttscast', 'debug', '[Python-Dep] Get requirements.txt ERROR :: ' . $e->getMessage());
        }
        log::add('ttscast', 'debug', '[Python-Dep] PythonDepString / PythonDepNum :: ' . $pythonDepString . " / " . $pythonDepNum);
        config::save('pythonDepString', $pythonDepString, 'ttscast');
        config::save('pythonDepNum', $pythonDepNum, 'ttscast');
        return true;
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

    public static function removeNonUTF8chars($string) {
        return mb_convert_encoding($string, 'UTF-8', 'UTF-8');
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
                'message' => __('[SCAN] TTSCast AJOUTE :: ', __FILE__) . $_data['friendly_name'],
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
                'message' => __('[SCAN] TTSCast MAJ :: ', __FILE__) . $_data['friendly_name'],
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
        foreach(self::byType('ttscast', false) as $eqLogic) {
            // Ignorer l'équipement virtuel AI Stats
            if ($eqLogic->getLogicalId() == 'TTSCast_AI_Stats') {
                continue;
            }
            
            if ($eqLogic->getIsEnable()) {
                /** @var ttscast $eqLogic */
                $eqLogic->enableCastToDaemon();
            }
            else {
                /** @var ttscast $eqLogic */
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
            foreach(self::byType('ttscast', false) as $eqLogic) {
                // Ignorer l'équipement virtuel AI Stats
                if ($eqLogic->getLogicalId() == 'TTSCast_AI_Stats') {
                    continue;
                }
                $cmd = $eqLogic->getCmd(null, 'radios');
                if (is_object($cmd)) {
                    /** @var ttscast $eqLogic */
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
            foreach(self::byType('ttscast', false) as $eqLogic) {
                // Ignorer l'équipement virtuel AI Stats
                if ($eqLogic->getLogicalId() == 'TTSCast_AI_Stats') {
                    continue;
                }
                $cmd = $eqLogic->getCmd(null, 'customradios');
                if (is_object($cmd)) {
                    /** @var ttscast $eqLogic */
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
            foreach(self::byType('ttscast', false) as $eqLogic) {
                // Ignorer l'équipement virtuel AI Stats
                if ($eqLogic->getLogicalId() == 'TTSCast_AI_Stats') {
                    continue;
                }
                $cmd = $eqLogic->getCmd(null, 'sounds');
                if (is_object($cmd)) {
                    /** @var ttscast $eqLogic */
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
            foreach(self::byType('ttscast', false) as $eqLogic) {
                // Ignorer l'équipement virtuel AI Stats
                if ($eqLogic->getLogicalId() == 'TTSCast_AI_Stats') {
                    continue;
                }
                $cmd = $eqLogic->getCmd(null, 'customsounds');
                if (is_object($cmd)) {
                    /** @var ttscast $eqLogic */
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
        // Icône spécifique pour l'équipement virtuel AI Stats
        if ($this->getLogicalId() == 'TTSCast_AI_Stats') {
            if (file_exists(__DIR__ . "/../../data/images/ai_stats.png")) {
                return 'plugins/ttscast/data/images/ai_stats.png';
            }
            return parent::getImage();
        }
        
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

    /* ************************ Static Methods : JEEDOM *************************** */

    /*
     * Fonction exécutée automatiquement toutes les minutes par Jeedom
    public static function cron() {}
    */

    
    // * Fonction exécutée automatiquement toutes les 5 minutes par Jeedom
    public static function cron5() {
        $currentTime = time();
        foreach(self::byType('ttscast', true) as $eqLogic) {
            // Ignorer l'équipement virtuel AI Stats
            if ($eqLogic->getLogicalId() == 'TTSCast_AI_Stats') {
                continue;
            }
            
            $lastSchedule = $eqLogic->getCmd('info', 'lastschedulets');
            if (!is_object($lastSchedule)) {
                continue;
            }
            
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

    /**
     * Gère l'équipement virtuel TTSCast AI Stats en fonction de l'activation de l'IA
     */
    public static function manageAIEquipments() {
        $aiEnabled = config::byKey('ttsAIEnable', 'ttscast', '0');

        // --- TTSCast_AI_Stats (métriques tokens) ---
        $statsEq = self::byLogicalId('TTSCast_AI_Stats', 'ttscast');
        
        if ($aiEnabled == '1') {
            // L'IA est activée, créer ou mettre à jour l'équipement de stats
            if (!is_object($statsEq)) {
                log::add('ttscast', 'info', '[AI Stats] Création de l\'équipement virtuel TTSCast AI Stats');
                $statsEq = new ttscast();
                $statsEq->setLogicalId('TTSCast_AI_Stats');
                $statsEq->setName('TTSCast - Stats IA');
                $statsEq->setEqType_name('ttscast');
                $statsEq->setIsEnable(1);
                $statsEq->setIsVisible(1);
                $statsEq->save();
            }
            
            // Créer/mettre à jour les commandes de tokens
            $orderCmd = 1;
            
            // Configuration display commune pour les commandes de tokens
            $tokenDisplayConfig = [
                'showNameOndashboard' => '1',
                'showNameOnmobile' => '1',
                'showIconAndNamedashboard' => '1',
                'showIconAndNamemobile' => '1',
                'showStatsOndashboard' => '1',
                'showStatsOnmobile' => '1',
                'graphType' => 'column',
                'groupingType' => '',
                'graphDerive' => '0',
                'graphStep' => '0'
            ];
            
            // Configuration commune pour les commandes de tokens
            $tokenConfig = [
                'historizeMode' => 'none',
                'history::smooth' => '-1',
                'historyPurge' => '-6 month',
                'repeatEventManagement' => 'always'
            ];
            
            // Commande: Tokens d'entrée
            $cmd = $statsEq->getCmd(null, 'ai_tokens_input');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Tokens IA Entrée', __FILE__));
                $cmd->setEqLogic_id($statsEq->getId());
                $cmd->setLogicalId('ai_tokens_input');
                $cmd->setType('info');
                $cmd->setSubType('numeric');
                $cmd->setUnite('Tokens');
                $cmd->setIsVisible(1);
                $cmd->setIsHistorized(1);
                
                foreach ($tokenDisplayConfig as $key => $value) {
                    $cmd->setDisplay($key, $value);
                }
                $cmd->setDisplay('icon', '<i class="fas fa-arrow-circle-down"></i>');
                
                foreach ($tokenConfig as $key => $value) {
                    $cmd->setConfiguration($key, $value);
                }
                
                $cmd->setTemplate('dashboard', 'core::tile');
                $cmd->setTemplate('mobile', 'core::tile');
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            }
            
            // Commande: Tokens de sortie
            $cmd = $statsEq->getCmd(null, 'ai_tokens_output');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Tokens IA Sortie', __FILE__));
                $cmd->setEqLogic_id($statsEq->getId());
                $cmd->setLogicalId('ai_tokens_output');
                $cmd->setType('info');
                $cmd->setSubType('numeric');
                $cmd->setUnite('Tokens');
                $cmd->setIsVisible(1);
                $cmd->setIsHistorized(1);
                
                foreach ($tokenDisplayConfig as $key => $value) {
                    $cmd->setDisplay($key, $value);
                }
                $cmd->setDisplay('icon', '<i class="fas fa-arrow-circle-up"></i>');
                
                foreach ($tokenConfig as $key => $value) {
                    $cmd->setConfiguration($key, $value);
                }
                
                $cmd->setTemplate('dashboard', 'core::tile');
                $cmd->setTemplate('mobile', 'core::tile');
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            }
            
            // Commande: Tokens total
            $cmd = $statsEq->getCmd(null, 'ai_tokens_total');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Tokens IA Total', __FILE__));
                $cmd->setEqLogic_id($statsEq->getId());
                $cmd->setLogicalId('ai_tokens_total');
                $cmd->setType('info');
                $cmd->setSubType('numeric');
                $cmd->setUnite('Tokens');
                $cmd->setIsVisible(1);
                $cmd->setIsHistorized(1);
                
                foreach ($tokenDisplayConfig as $key => $value) {
                    $cmd->setDisplay($key, $value);
                }
                $cmd->setDisplay('icon', '<i class="fas fa-calculator"></i>');
                
                foreach ($tokenConfig as $key => $value) {
                    $cmd->setConfiguration($key, $value);
                }
                
                $cmd->setTemplate('dashboard', 'core::tile');
                $cmd->setTemplate('mobile', 'core::tile');
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            }
            
            // Commande: Tokens cache
            // $cmd = $statsEq->getCmd(null, 'ai_cache_tokens');
            // if (!is_object($cmd)) {
            //     $cmd = new ttscastCmd();
            //     $cmd->setName(__('Tokens Cache', __FILE__));
            //     $cmd->setEqLogic_id($statsEq->getId());
            //     $cmd->setLogicalId('ai_cache_tokens');
            //     $cmd->setType('info');
            //     $cmd->setSubType('numeric');
            //     $cmd->setUnite('Tokens');
            //     $cmd->setIsVisible(1);
            //     $cmd->setIsHistorized(1);
            //     
            //     foreach ($tokenDisplayConfig as $key => $value) {
            //         $cmd->setDisplay($key, $value);
            //     }
            //     $cmd->setDisplay('icon', '<i class="fas fa-database"></i>');
            //     
            //     foreach ($tokenConfig as $key => $value) {
            //         $cmd->setConfiguration($key, $value);
            //     }
            //     
            //     $cmd->setTemplate('dashboard', 'core::tile');
            //     $cmd->setTemplate('mobile', 'core::tile');
            //     $cmd->setOrder($orderCmd++);
            //     $cmd->save();
            // }
            
            // Commande: Tokens outils
            // $cmd = $statsEq->getCmd(null, 'ai_tool_tokens');
            // if (!is_object($cmd)) {
            //     $cmd = new ttscastCmd();
            //     $cmd->setName(__('Tokens Outils', __FILE__));
            //     $cmd->setEqLogic_id($statsEq->getId());
            //     $cmd->setLogicalId('ai_tool_tokens');
            //     $cmd->setType('info');
            //     $cmd->setSubType('numeric');
            //     $cmd->setUnite('Tokens');
            //     $cmd->setIsVisible(1);
            //     $cmd->setIsHistorized(1);
            //     
            //     foreach ($tokenDisplayConfig as $key => $value) {
            //         $cmd->setDisplay($key, $value);
            //     }
            //     $cmd->setDisplay('icon', '<i class="fas fa-wrench"></i>');
            //     
            //     foreach ($tokenConfig as $key => $value) {
            //         $cmd->setConfiguration($key, $value);
            //     }
            //     
            //     $cmd->setTemplate('dashboard', 'core::tile');
            //     $cmd->setTemplate('mobile', 'core::tile');
            //     $cmd->setOrder($orderCmd++);
            //     $cmd->save();
            // }
            
            // Commande: Tokens réflexion
            // $cmd = $statsEq->getCmd(null, 'ai_thoughts_tokens');
            // if (!is_object($cmd)) {
            //     $cmd = new ttscastCmd();
            //     $cmd->setName(__('Tokens Réflexion', __FILE__));
            //     $cmd->setEqLogic_id($statsEq->getId());
            //     $cmd->setLogicalId('ai_thoughts_tokens');
            //     $cmd->setType('info');
            //     $cmd->setSubType('numeric');
            //     $cmd->setUnite('Tokens');
            //     $cmd->setIsVisible(1);
            //     $cmd->setIsHistorized(1);
            //     
            //     foreach ($tokenDisplayConfig as $key => $value) {
            //         $cmd->setDisplay($key, $value);
            //     }
            //     $cmd->setDisplay('icon', '<i class="fas fa-brain"></i>');
            //     
            //     foreach ($tokenConfig as $key => $value) {
            //         $cmd->setConfiguration($key, $value);
            //     }
            //     
            //     $cmd->setTemplate('dashboard', 'core::tile');
            //     $cmd->setTemplate('mobile', 'core::tile');
            //     $cmd->setOrder($orderCmd++);
            //     $cmd->save();
            // }
            
            // Commande: Raison de fin
            $cmd = $statsEq->getCmd(null, 'ai_finish_reason');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Msg Retour IA', __FILE__));
                $cmd->setEqLogic_id($statsEq->getId());
                $cmd->setLogicalId('ai_finish_reason');
                $cmd->setType('info');
                $cmd->setSubType('string');
                $cmd->setIsVisible(1);
                $cmd->setIsHistorized(0);
                
                $cmd->setDisplay('showNameOndashboard', 1);
                $cmd->setDisplay('showNameOnmobile', 1);
                $cmd->setDisplay('icon', '<i class="fas fa-flag-checkered"></i>');
                
                $cmd->setTemplate('dashboard', 'core::tile');
                $cmd->setTemplate('mobile', 'core::tile');
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            }
            
            // Commande: Score de confiance moyen
            // $cmd = $statsEq->getCmd(null, 'ai_avg_logprobs');
            // if (!is_object($cmd)) {
            //     $cmd = new ttscastCmd();
            //     $cmd->setName(__('Confiance IA', __FILE__));
            //     $cmd->setEqLogic_id($statsEq->getId());
            //     $cmd->setLogicalId('ai_avg_logprobs');
            //     $cmd->setType('info');
            //     $cmd->setSubType('numeric');
            //     $cmd->setIsVisible(1);
            //     $cmd->setIsHistorized(1);
            //     
            //     foreach ($tokenDisplayConfig as $key => $value) {
            //         $cmd->setDisplay($key, $value);
            //     }
            //     $cmd->setDisplay('icon', '<i class="fas fa-chart-line"></i>');
            //     
            //     foreach ($tokenConfig as $key => $value) {
            //         $cmd->setConfiguration($key, $value);
            //     }
            //     
            //     $cmd->setTemplate('dashboard', 'core::tile');
            //     $cmd->setTemplate('mobile', 'core::tile');
            //     $cmd->setOrder($orderCmd++);
            //     $cmd->save();
            // }
            
            // Commande: Sécurité bloquée
            $cmd = $statsEq->getCmd(null, 'ai_safety_blocked');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Réponse IA Bloquée', __FILE__));
                $cmd->setEqLogic_id($statsEq->getId());
                $cmd->setLogicalId('ai_safety_blocked');
                $cmd->setType('info');
                $cmd->setSubType('binary');
                $cmd->setIsVisible(1);
                $cmd->setIsHistorized(1);
                
                foreach ($tokenDisplayConfig as $key => $value) {
                    $cmd->setDisplay($key, $value);
                }
                $cmd->setDisplay('icon', '<i class="fas fa-shield-alt"></i>');
                
                foreach ($tokenConfig as $key => $value) {
                    $cmd->setConfiguration($key, $value);
                }
                
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            }
            
            log::add('ttscast', 'debug', '[AI Stats] Équipement virtuel TTSCast AI Stats configuré');
        } else {
            if (is_object($statsEq)) {
                log::add('ttscast', 'info', '[AI] Désactivation TTSCast_AI_Stats (IA désactivée)');
                $statsEq->setIsEnable(0);
                $statsEq->save();
            }
        }

        // --- TTSCast_AI (équipement reformulation) ---
        $aiEq = self::byLogicalId('TTSCast_AI', 'ttscast');

        if ($aiEnabled == '1') {
            if (!is_object($aiEq)) {
                log::add('ttscast', 'info', '[AI] Création de l\'équipement virtuel TTSCast_AI');
                $aiEq = new ttscast();
                $aiEq->setLogicalId('TTSCast_AI');
                $aiEq->setName('TTSCast - IA');
                $aiEq->setEqType_name('ttscast');
                $aiEq->setIsEnable(1);
                $aiEq->setIsVisible(1);
                $aiEq->save();
            } elseif (!$aiEq->getIsEnable()) {
                $aiEq->setIsEnable(1);
                $aiEq->save();
            }

            $orderCmd = 1;

            // ai_reformat (action/message)
            $cmd = $aiEq->getCmd(null, 'ai_reformat');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Reformuler IA', __FILE__));
                $cmd->setEqLogic_id($aiEq->getId());
                $cmd->setLogicalId('ai_reformat');
                $cmd->setType('action');
                $cmd->setSubType('message');
                $cmd->setIsVisible(1);
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            } else {
                $orderCmd++;
            }

            // ai_reformat_message (info/string)
            $cmd = $aiEq->getCmd(null, 'ai_reformat_message');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Message IA', __FILE__));
                $cmd->setEqLogic_id($aiEq->getId());
                $cmd->setLogicalId('ai_reformat_message');
                $cmd->setType('info');
                $cmd->setSubType('string');
                $cmd->setIsVisible(1);
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            } else {
                $orderCmd++;
            }

            // ai_reformat_input (info/string)
            $cmd = $aiEq->getCmd(null, 'ai_reformat_input');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('Texte pré-IA', __FILE__));
                $cmd->setEqLogic_id($aiEq->getId());
                $cmd->setLogicalId('ai_reformat_input');
                $cmd->setType('info');
                $cmd->setSubType('string');
                $cmd->setIsVisible(1);
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            } else {
                $orderCmd++;
            }

            log::add('ttscast', 'debug', '[AI] Équipement virtuel TTSCast_AI configuré');
        } else {
            if (is_object($aiEq)) {
                log::add('ttscast', 'info', '[AI] Désactivation TTSCast_AI (IA désactivée)');
                $aiEq->setIsEnable(0);
                $aiEq->save();
            }
        }
    }

    /**
     * Action après modification de la configuration ttsAIEnable
     */
    public static function postConfig_ttsAIEnable($value) {
        self::manageAIEquipments();
    }

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
        // Ignorer les équipements virtuels IA (leurs commandes sont gérées dans manageAIEquipments)
        if (in_array($this->getLogicalId(), ['TTSCast_AI_Stats', 'TTSCast_AI'])) {
            // Bloquer la réactivation manuelle de TTSCast_AI si l'IA est désactivée
            if ($this->getLogicalId() === 'TTSCast_AI' && $this->getIsEnable() == 1) {
                $aiEnabled = config::byKey('ttsAIEnable', 'ttscast', '0');
                if ($aiEnabled != '1') {
                    \DB::Prepare('UPDATE eqLogic SET `isEnable`=:enable WHERE `id`=:id', ['enable' => 0, 'id' => $this->getId()], \DB::FETCH_TYPE_ROW);
                    message::add('ttscast', __('TTSCast - IA ne peut pas être activé manuellement. Activez l\'IA dans la configuration du plugin (IA Générative).', __FILE__));
                }
            }
            return;
        }
        
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

        $cmd = $this->getCmd(null, 'session_id');
        if (!is_object($cmd)) {
            $cmd = new ttscastCmd();
            $cmd->setName(__('Cast Session Id', __FILE__));
            $cmd->setEqLogic_id($this->getId());
            $cmd->setLogicalId('session_id');
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

        // Commandes IA (créées uniquement si l'IA est activée globalement)
        if (config::byKey('ttsAIEnable', 'ttscast', '0') == '1') {
            $cmd = $this->getCmd(null, 'tts_last_message');
            if (!is_object($cmd)) {
                $cmd = new ttscastCmd();
                $cmd->setName(__('TTS Last Message', __FILE__));
                $cmd->setEqLogic_id($this->getId());
                $cmd->setLogicalId('tts_last_message');
                $cmd->setType('info');
                $cmd->setSubType('string');
                $cmd->setDisplay('forceReturnLineBefore', '1');
                $cmd->setDisplay('forceReturnLineAfter', '1');
                $cmd->setIsVisible(0);
                $cmd->setIsHistorized(0);
                $cmd->setOrder($orderCmd++);
                $cmd->save();
            } else {
                $orderCmd++;
            }
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

        $cmd = $this->getCmd(null, 'start_app');
        if (!is_object($cmd)) {
            $cmd = new ttscastCmd();
            $cmd->setName(__('Start App', __FILE__));
            $cmd->setEqLogic_id($this->getId());
            $cmd->setLogicalId('start_app');
            $cmd->setType('action');
            $cmd->setSubType('message');
            $cmd->setDisplay('forceReturnLineBefore', '1');
            $cmd->setDisplay('forceReturnLineAfter', '1');
            $cmd->setIsVisible(0);
            $cmd->setDisplay('parameters', array("title_placeholder" => "Options", "message_placeholder" => "App Id"));
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
        // Ne pas notifier le démon pour les équipements virtuels IA
        if (!in_array($this->getLogicalId(), ['TTSCast_AI_Stats', 'TTSCast_AI'])) {
            $this->disableCastToDaemon();
        }
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

    /* ***********************Getter Setter*************************** */
}

class ttscastCmd extends cmd
{
    /* **************************Attributs****************************** */

    public static $_widgetPossibility = array('custom' => true);

    /* ************************Static Method*************************** */


    /* **********************Instance Method************************* */

    // Permet d'empêcher la suppression des commandes même si elles ne sont pas dans la nouvelle configuration de l'équipement envoyé en JS
    public function dontRemoveCmd() {
        $eqLogic = $this->getEqLogic();
        // Empêcher la suppression automatique des commandes des équipements virtuels IA
        if (is_object($eqLogic) && in_array($eqLogic->getLogicalId(), ['TTSCast_AI_Stats', 'TTSCast_AI'])) {
            return true;
        }
        return false;
    }

    // Fonction exécutée automatiquement avant la suppression de la commande
    public function preRemove() {
        
    }

    public function getWidgetTemplateCode($_version = 'dashboard', $_clean = true, $_widgetName = '') {
        if ($_version != 'scenario') {
            return parent::getWidgetTemplateCode($_version, $_clean, $_widgetName);
        }

        $logicalId = $this->getLogicalId();

        if (!in_array($logicalId, ['tts', 'ai_reformat'])) {
            return parent::getWidgetTemplateCode($_version, $_clean, $_widgetName);
        }

        $templateFilename = ($logicalId === 'ai_reformat') ? 'cmd.aiReformat' : 'cmd.tts';
        $replace = [
            '#uid#' => 'cmd' . $this->getId() . eqLogic::UIDDELIMITER . mt_rand() . eqLogic::UIDDELIMITER,
        ];

        $html = template_replace($replace, getTemplate('core', 'scenario', $templateFilename, 'ttscast'));
        $html = translate::exec($html, 'plugins/ttscast/core/template/scenario/' . $templateFilename . '.html');

        if (!is_null($html) && !is_array($html) && $html !== '') {
            return array('template' => $html, 'isCoreWidget' => false);
        }

        return parent::getWidgetTemplateCode($_version, $_clean, $_widgetName);
    }

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
                    $cmdNotificationId = 0;
                    if (!empty($_options['cmdNotification'])) {
                        $cmdNotification = cmd::byString($_options['cmdNotification']);
                        if (!is_object($cmdNotification)) {
                            log::add('ttscast', 'warning', '[CMD] tts :: Commande notification introuvable :: ' . $_options['cmdNotification']);
                        } else {
                            $cmdNotificationId = $cmdNotification->getId();
                        }
                    }
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Message / GoogleUUID / CmdNotification) :: ' . $_options['message'] . " / " . $googleUUID . " / " . $cmdNotificationId);
                    ttscast::playTTS($googleUUID, $_options['message'], isset($_options['title']) ? $_options['title'] : null, $cmdNotificationId);
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour diffuser un message TTS');
                }
            } elseif ($logicalId == 'ai_reformat' && $eqLogic->getLogicalId() == 'TTSCast_AI') {
                log::add('ttscast', 'debug', '[CMD] ai_reformat :: ' . json_encode($_options));
                $text = isset($_options['message']) ? trim($_options['message']) : '';
                if ($text === '') {
                    log::add('ttscast', 'warning', '[CMD] ai_reformat :: texte vide, rien à reformuler');
                    return true;
                }
                $payload = [
                    'cmd' => 'aiReformat',
                    'text' => $text,
                    'ttsOptions' => isset($_options['title']) ? $_options['title'] : null,
                ];
                $result = ttscast::sendToDaemonSync($payload);
                if ($result === null || isset($result['error'])) {
                    log::add('ttscast', 'warning', '[CMD] ai_reformat :: Pas de réponse du démon, retour texte original');
                    $result = ['reformulated' => $text, 'original' => $text];
                }
                $reformulated = isset($result['reformulated']) ? $result['reformulated'] : $text;
                $original = isset($result['original']) ? $result['original'] : $text;
                // Toujours mettre à jour les commandes info de TTSCast_AI
                $aiEqLogic = ttscast::byLogicalId('TTSCast_AI', 'ttscast');
                if (is_object($aiEqLogic)) {
                    $cmdMsg = $aiEqLogic->getCmd(null, 'ai_reformat_message');
                    if (is_object($cmdMsg)) $cmdMsg->event($reformulated);
                    $cmdInput = $aiEqLogic->getCmd(null, 'ai_reformat_input');
                    if (is_object($cmdInput)) $cmdInput->event($original);
                }
                // storeTarget optionnel : variable ou commande info
                $target = trim(isset($_options['storeTarget']) ? $_options['storeTarget'] : '');
                if ($target !== '') {
                    if (strpos($target, '#[') === 0) { // TODO: PHP 8.0 — str_starts_with
                        $targetCmd = cmd::byString($target);
                        if (is_object($targetCmd)) {
                            $targetCmd->event($reformulated);
                        } else {
                            log::add('ttscast', 'warning', '[CMD] ai_reformat :: Commande storeTarget introuvable :: ' . $target);
                        }
                    } else {
                        // Sauvegarde dans une variable globale Jeedom via dataStore
                        $dataStore = \dataStore::byTypeLinkIdKey('scenario', -1, $target);
                        if (!is_object($dataStore)) {
                            $dataStore = new \dataStore();
                            $dataStore->setKey($target);
                            $dataStore->setType('scenario');
                            $dataStore->setLink_id(-1);
                        }
                        $dataStore->setValue($reformulated);
                        $dataStore->save();
                    }
                }
                log::add('ttscast', 'debug', '[CMD] ai_reformat :: Résultat :: ' . $reformulated);
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
            } elseif (in_array($logicalId, ["youtube", "dashcast", "media", "start_app"])) {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID) && isset($_options['message'])) {
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Message / GoogleUUID) :: ' . $_options['message'] . " / " . $googleUUID);
                    ttscast::mediaGCast($googleUUID, $logicalId, $_options['message'], isset($_options['title']) ? $_options['title'] : null);
                }
                else {
                    log::add('ttscast', 'debug', '[CMD] Il manque un paramètre pour lancer la commande '. $logicalId);
                }                
            } elseif (in_array($logicalId, ["radios", "customradios", "sounds", "customsounds"])) {
                log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' :: ' . json_encode($_options));
                $googleUUID = $eqLogic->getLogicalId();
                if (isset($googleUUID) && isset($_options['select'])) {
                    log::add('ttscast', 'debug', '[CMD] ' . $logicalId . ' (Select / GoogleUUID) :: ' . $_options['select'] . " / " . $googleUUID);
                    ttscast::mediaGCast($googleUUID, $logicalId, $_options['select'], isset($_options['title']) ? $_options['title'] : null);
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
}
