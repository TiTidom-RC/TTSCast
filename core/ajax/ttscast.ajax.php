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

try {
    require_once dirname(__FILE__) . '/../../../../core/php/core.inc.php';
    include_file('core', 'authentification', 'php');

    if (!isConnect('admin')) {
        throw new Exception(__('401 - Accès non autorisé', __FILE__));
    }

    /* Fonction permettant l'envoi de l'entête 'Content-Type: application/json'
     En V3 : indiquer l'argument 'true' pour contrôler le token d'accès Jeedom
     En V4 : autoriser l'exécution d'une méthode 'action' en GET en indiquant le(s) nom(s) de(s) action(s) dans un tableau en argument
    */
    ajax::init();

    if (init('action') == 'testExternalAddress') {
        ajax::success(ttscast::testExternalAddress(init('value')));
    }

    if (init('action') == 'purgeTTSCache') {
		ajax::success(ttscast::purgeTTSCache());
	}

    if (init('action') == 'playTestTTS') {
		ajax::success(ttscast::playTestTTS());
	}

    if (init('action') == 'uploadAPIKey') {
        if (!isset($_FILES['fileAPIKey'])) {
            throw new Exception(__('Aucun fichier trouvé. Vérifiez le paramètre PHP (post size limit)', __FILE__));
        }
        log::add('ttscast', 'debug', "[UPLOAD][APIKEY] filepath: {$_FILES['fileAPIKey']['name']}");
        $extension = strtolower(strrchr($_FILES['fileAPIKey']['name'], '.'));
        if (!in_array($extension, array('.json'))) {
            throw new Exception('Extension de fichier non valide (autorisé .json) : ' . $extension);
        }
        if (filesize($_FILES['fileAPIKey']['tmp_name']) > 10000) {
            throw new Exception(__('Le fichier est trop gros (max. 10Ko)', __FILE__));
        }
        $apiKey = ttscast::sanitizeFileName(init('apiKey'));
      
        $filepath = __DIR__ . "/../../core/config/{$apikey}{$extension}";
        log::add('ttscast', 'debug', "[UPLOAD][APIKEY] filepath: {$filepath}");
        file_put_contents($filepath, file_get_contents($_FILES['file']['tmp_name']));
        if (!file_exists($filepath)) {
            throw new \Exception(__('Impossible de sauvegarder l\'image', __FILE__));
        }

        ajax::success("plugins/ttscast/core/config/{$model}{$extension}");
	}


    
    throw new Exception(__('Aucune méthode correspondante à', __FILE__) . ' : ' . init('action'));
    /*     * *********Catch exeption*************** */
} catch (Exception $e) {
    ajax::error(displayException($e), $e->getCode());
}
