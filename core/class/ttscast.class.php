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

    /* ************************Methode static*************************** */

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

        $path = realpath(dirname(__FILE__) . '/../../resources/ttscastd');
        $cmd = 'python3 ' . $path . '/ttscastd.py';
        $cmd .= ' --loglevel ' . log::convertLogLevel(log::getLogLevel(__CLASS__));
        $cmd .= ' --socketport ' . config::byKey('socketport', __CLASS__, '55999'); // TODO Modifier le numéro de port du démon
        $cmd .= ' --callback ' . network::getNetworkAccess('internal', 'http:127.0.0.1:port:comp') . '/plugins/ttscast/core/php/jeettscast.php'; // chemin du callback
        $cmd .= ' --apikey ' . jeedom::getApiKey(__CLASS__);
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

    public static function testExternalAddress($useExternal=NULL)
    {
        if (is_null($useExternal)) {
            $useExternal = config::byKey('ttsUseExtAddr', 'ttscast');
        }

        $testAddress = '';
        if ($useExternal) {
            $testAddress .= network::getNetworkAccess('external');
        } else {
            $testAddress .= network::getNetworkAccess('internal');
        }
        return $testAddress . "/plugins/ttscast/data/media/bigben1.mp3";
    }

    public static function purgeTTSCache($days=0) {
        $value = array('cmd' => 'purgettscache', 'days' => $days);
        self::sendToDaemon($value);
    }

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
                ttscast::purgeTTSCache(intval($nbdays));
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
    }

    /* ***********************Getteur Setteur*************************** */
}
