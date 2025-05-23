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
    ajax::init(array('uploadAPIKey', 'uploadCustomSound', 'uploadCustomRadios'));

    if (init('action') == 'testExternalAddress') {
        ajax::success(ttscast::testExternalAddress(init('value')));
    }

    if (init('action') == 'purgeTTSCache') {
		ajax::success(ttscast::purgeTTSCache());
	}

    if (init('action') == 'playTestTTS') {
		ajax::success(ttscast::playTestTTS());
	}

    if (init('action') == 'updateRadios') {
		ajax::success(ttscast::updateRadioList());
	}

    if (init('action') == 'updateCustomRadios') {
		ajax::success(ttscast::updateCustomRadioList());
	}

    if (init('action') == 'updateSounds') {
		ajax::success(ttscast::updateSoundList());
	}

    if (init('action') == 'updateCustomSounds') {
		ajax::success(ttscast::updateCustomSoundList());
	}

    if (init('action') == 'uploadAPIKey') {
        if (!isset($_FILES['fileAPIKey'])) {
            throw new Exception(__('[UPLOAD][APIKEY] Aucun fichier trouvé. Vérifiez le paramètre PHP (post size limit)', __FILE__));
        }
        log::add('ttscast', 'debug', "[UPLOAD][APIKEY] filename: {$_FILES['fileAPIKey']['name']}");
        $extension = strtolower(strrchr($_FILES['fileAPIKey']['name'], '.'));
        if (!in_array($extension, array('.json'))) {
            throw new Exception('[UPLOAD][APIKEY] Extension de fichier non valide (autorisé .json) : ' . $extension);
        }
        if (filesize($_FILES['fileAPIKey']['tmp_name']) > 10000) {
            throw new Exception(__('[UPLOAD][APIKEY] Le fichier est trop gros (max. 10Ko)', __FILE__));
        }
      
        $filepath = __DIR__ . "/../../data/config/{$_FILES['fileAPIKey']['name']}";
        log::add('ttscast', 'debug', "[UPLOAD][APIKEY] filepath: {$filepath}");
        file_put_contents($filepath, file_get_contents($_FILES['fileAPIKey']['tmp_name']));
        if (!file_exists($filepath)) {
            throw new Exception(__('[UPLOAD][APIKEY] Impossible de sauvegarder le fichier JSON', __FILE__));
        }

        ajax::success("{$_FILES['fileAPIKey']['name']}");
	}

    if (init('action') == 'resetAPIKey') {
        $filepath = __DIR__ . "/../../data/config/" . init('filename');
        if (!file_exists($filepath)) {
            throw new Exception('[RESET][APIKEY] Fichier introuvable : ' . $filepath);
        }    
        log::add('ttscast', 'debug', "[RESET][APIKEY] filepath: {$filepath}");
        unlink($filepath);
        ajax::success("{$filepath}");
    }

    if (init('action') == 'changeScanState') {
        ttscast::changeScanState(init('scanState'));
        ajax::success();
    }
    
    if (init('action') == 'uploadCustomSound') {
        if (!isset($_FILES['fileCustomSound'])) {
            throw new Exception(__('[UPLOAD][CustomSound] Aucun fichier trouvé. Vérifiez le paramètre PHP (post size limit)', __FILE__));
        }
        log::add('ttscast', 'debug', "[UPLOAD][CustomSound] filename: {$_FILES['fileCustomSound']['name']}");
        $extension = strtolower(strrchr($_FILES['fileCustomSound']['name'], '.'));
        if (!in_array($extension, array('.mp3'))) {
            throw new Exception('[UPLOAD][CustomSound] Extension de fichier non valide (autorisé .mp3) : ' . $extension);
        }

        # TODO limiter taille upload mp3 dans les customSounds ?
        /* if (filesize($_FILES['fileCustomSound']['tmp_name']) > 10000) {
            throw new Exception(__('[UPLOAD][CustomSound] Le fichier est trop gros (max. 10Ko)', __FILE__));
        } */
      
        $filepath = __DIR__ . "/../../data/media/custom/{$_FILES['fileCustomSound']['name']}";
        log::add('ttscast', 'debug', "[UPLOAD][CustomSound] filepath: {$filepath}");
        file_put_contents($filepath, file_get_contents($_FILES['fileCustomSound']['tmp_name']));
        if (!file_exists($filepath)) {
            throw new Exception(__('[UPLOAD][CustomSound] Impossible de sauvegarder le fichier', __FILE__));
        }
        log::add('ttscast', 'info', "[UPLOAD][CustomSound] Upload OK :: {$_FILES['fileCustomSound']['name']}");
        ajax::success("{$_FILES['fileCustomSound']['name']}");
	}

    if (init('action') == 'uploadCustomRadios') {
        if (!isset($_FILES['fileCustomRadios'])) {
            throw new Exception(__('[UPLOAD][CustomRadios] Aucun fichier trouvé. Vérifiez le paramètre PHP (post size limit)', __FILE__));
        }
        log::add('ttscast', 'debug', "[UPLOAD][CustomRadios] filename: {$_FILES['fileCustomRadios']['name']}");
        $extension = strtolower(strrchr($_FILES['fileCustomRadios']['name'], '.'));
        if (!in_array($extension, array('.json'))) {
            throw new Exception('[UPLOAD][CustomRadios] Extension de fichier non valide (autorisé .json) : ' . $extension);
        }
      
        if (filesize($_FILES['fileCustomRadios']['tmp_name']) > 500000) {
            throw new Exception(__('[UPLOAD][CustomRadios] Le fichier est trop gros (max. 500Ko)', __FILE__));
        }

        $filepath = __DIR__ . "/../../data/radios/custom/radios.json";
        log::add('ttscast', 'debug', "[UPLOAD][CustomRadios] filepath: {$filepath}");
        file_put_contents($filepath, file_get_contents($_FILES['fileCustomRadios']['tmp_name']));
        if (!file_exists($filepath)) {
            throw new Exception(__('[UPLOAD][CustomRadios] Impossible de sauvegarder le fichier', __FILE__));
        }
        log::add('ttscast', 'info', "[UPLOAD][CustomRadios] Upload OK :: {$_FILES['fileCustomRadios']['name']}");
        ajax::success("{$_FILES['fileCustomRadios']['name']}");
	}

    throw new Exception(__('Aucune méthode correspondante à', __FILE__) . ' : ' . init('action'));
    /*     * *********Catch exception*************** */
} catch (Exception $e) {
    ajax::error(displayException($e), $e->getCode());
}
