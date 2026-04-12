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

require_once dirname(__FILE__) . '/../../../core/php/core.inc.php';

// Fonction exécutée automatiquement après l'installation du plugin
function ttscast_install() {
    $pluginVersion = ttscast::getPluginVersion();
    config::save('pluginVersion', $pluginVersion, 'ttscast');

    message::removeAll('ttscast');
    message::add('ttscast', 'Installation du plugin TTS Cast (Version : ' . $pluginVersion . ')', null, null);

    ttscast::getPythonDepFromRequirements();

    if (config::byKey('pythonVersion', 'ttscast') == '') {
        config::save('pythonVersion', '?.?.?', 'ttscast');
    }
    if (config::byKey('pyenvVersion', 'ttscast') == '') {
        config::save('pyenvVersion', '?.?.?', 'ttscast');
    }
    if (config::byKey('socketport', 'ttscast') == '') {
        config::save('socketport', '55111', 'ttscast');
    }
    if (config::byKey('cyclefactor', 'ttscast') == '') {
        config::save('cyclefactor', '1.0', 'ttscast');
    }
    if (config::byKey('ttsEngine', 'ttscast') == '') {
        config::save('ttsEngine', 'jeedomtts', 'ttscast');
    }
    if (config::byKey('ttsLang', 'ttscast') == '') {
        config::save('ttsLang', 'fr-FR', 'ttscast');
    }
    if (config::byKey('gCloudTTSSpeed', 'ttscast') == '') {
        config::save('gCloudTTSSpeed', '1.0', 'ttscast');
    }
    if (config::byKey('gCloudAudioEncoding', 'ttscast') == '') {
        config::save('gCloudAudioEncoding', 'MP3', 'ttscast');
    }
    if (config::byKey('gCloudTTSVoice', 'ttscast') == '') {
        config::save('gCloudTTSVoice', 'fr-FR-Standard-A', 'ttscast');
    }
    if (config::byKey('ttsDisableCache', 'ttscast') == '') {
        config::save('ttsDisableCache', '0', 'ttscast');
    }
    if (config::byKey('ttsPurgeCacheDays', 'ttscast') == '') {
        config::save('ttsPurgeCacheDays', '10', 'ttscast');
    }
    if (config::byKey('appDisableDing', 'ttscast') == '') {
        config::save('appDisableDing', '0', 'ttscast');
    }
    if (config::byKey('appConvertSingleQuote', 'ttscast') == '') {
        config::save('appConvertSingleQuote', '0', 'ttscast');
    }
    if (config::byKey('cmdWaitTimeout', 'ttscast') == '') {
        config::save('cmdWaitTimeout', '60', 'ttscast');
    }
    if (config::byKey('ttsGenTimeout', 'ttscast') == '') {
        config::save('ttsGenTimeout', '30', 'ttscast');
    }
    if (config::byKey('debugInstallUpdates', 'ttscast') == '') {
        config::save('debugInstallUpdates', '0', 'ttscast');
    }
    if (config::byKey('debugRestorePyEnv', 'ttscast') == '') {
        config::save('debugRestorePyEnv', '0', 'ttscast');
    }
    if (config::byKey('debugRestoreVenv', 'ttscast') == '') {
        config::save('debugRestoreVenv', '0', 'ttscast');
    }
    if (config::byKey('ttsAIDefault', 'ttscast') == '') {
        config::save('ttsAIDefault', '0', 'ttscast');
    }
    if (config::byKey('disableUpdateMsg', 'ttscast') == '') {
        config::save('disableUpdateMsg', '0', 'ttscast');
    }

    $dependencyInfo = ttscast::dependancy_info();
    if (!isset($dependencyInfo['state'])) {
        message::add('ttscast', __('Veuillez vérifier les dépendances', __FILE__));
    } elseif ($dependencyInfo['state'] == 'nok') {
        try {
            $plugin = plugin::byId('ttscast');
            $plugin->dependancy_install();
        } catch (\Throwable $th) {
            message::add('ttscast', __('Une erreur est survenue à la mise à jour automatique des dépendances. Vérifiez les logs et relancez les dépendances manuellement', __FILE__));
        }
    }
}

// Fonction exécutée automatiquement après la mise à jour du plugin
function ttscast_update() {
    $pluginVersion = ttscast::getPluginVersion();
    config::save('pluginVersion', $pluginVersion, 'ttscast');

    if (config::byKey('disableUpdateMsg', 'ttscast', '0') == '0') {
        message::removeAll('ttscast');
        message::add('ttscast', 'Mise à jour du plugin TTS Cast (Version : ' . $pluginVersion . ')', null, null);
    }

    ttscast::getPythonDepFromRequirements();

    if (config::byKey('pythonVersion', 'ttscast') == '') {
        config::save('pythonVersion', '?.?.?', 'ttscast');
    }
    if (config::byKey('pyenvVersion', 'ttscast') == '') {
        config::save('pyenvVersion', '?.?.?', 'ttscast');
    }
    if (config::byKey('socketport', 'ttscast') == '') {
        config::save('socketport', '55111', 'ttscast');
    }
    if (config::byKey('cyclefactor', 'ttscast') == '') {
        config::save('cyclefactor', '1.0', 'ttscast');
    }
    if (config::byKey('ttsEngine', 'ttscast') == '') {
        config::save('ttsEngine', 'jeedomtts', 'ttscast');
    }
    if (config::byKey('ttsLang', 'ttscast') == '') {
        config::save('ttsLang', 'fr-FR', 'ttscast');
    }
    if (config::byKey('gCloudTTSSpeed', 'ttscast') == '') {
        config::save('gCloudTTSSpeed', '1.0', 'ttscast');
    }
    if (config::byKey('gCloudAudioEncoding', 'ttscast') == '') {
        config::save('gCloudAudioEncoding', 'MP3', 'ttscast');
    }
    if (config::byKey('gCloudTTSVoice', 'ttscast') == '') {
        config::save('gCloudTTSVoice', 'fr-FR-Standard-A', 'ttscast');
    }
    if (config::byKey('ttsDisableCache', 'ttscast') == '') {
        config::save('ttsDisableCache', '0', 'ttscast');
    }
    if (config::byKey('ttsPurgeCacheDays', 'ttscast') == '') {
        config::save('ttsPurgeCacheDays', '10', 'ttscast');
    }
    if (config::byKey('appDisableDing', 'ttscast') == '') {
        config::save('appDisableDing', '0', 'ttscast');
    }
    if (config::byKey('appConvertSingleQuote', 'ttscast') == '') {
        config::save('appConvertSingleQuote', '0', 'ttscast');
    }
    if (config::byKey('cmdWaitTimeout', 'ttscast') == '') {
        config::save('cmdWaitTimeout', '60', 'ttscast');
    }
    if (config::byKey('ttsGenTimeout', 'ttscast') == '') {
        config::save('ttsGenTimeout', '30', 'ttscast');
    }
    if (config::byKey('debugInstallUpdates', 'ttscast') == '') {
        config::save('debugInstallUpdates', '0', 'ttscast');
    }
    if (config::byKey('debugRestorePyEnv', 'ttscast') == '') {
        config::save('debugRestorePyEnv', '0', 'ttscast');
    }
    if (config::byKey('debugRestoreVenv', 'ttscast') == '') {
        config::save('debugRestoreVenv', '0', 'ttscast');
    }
    if (config::byKey('ttsAIDefault', 'ttscast') == '') {
        config::save('ttsAIDefault', '0', 'ttscast');
    }
    if (config::byKey('disableUpdateMsg', 'ttscast') == '') {
        config::save('disableUpdateMsg', '0', 'ttscast');
    }

    $dependencyInfo = ttscast::dependancy_info();
    if (!isset($dependencyInfo['state'])) {
        message::add('ttscast', __('Veuillez vérifier les dépendances', __FILE__));
    } elseif ($dependencyInfo['state'] == 'nok') {
        try {
            $plugin = plugin::byId('ttscast');
            $plugin->dependancy_install();
        } catch (\Throwable $th) {
            message::add('ttscast', __('Une erreur est survenue à la mise à jour automatique des dépendances. Vérifiez les logs et relancez les dépendances manuellement', __FILE__));
        }
    }
    
    // Nettoyage des anciens fichiers et répertoires obsolètes
    $pluginDir = dirname(__DIR__);
    try {
        $pathsToRemove = array(
            // Accepte fichiers ET répertoires (rm -rf) — ajouter ici les chemins à supprimer à chaque mise à jour
            $pluginDir . '/core/php/.htaccess',
        );
        $cleanupRemoved = 0;
        $cleanupErrors = 0;
        foreach ($pathsToRemove as $path) {
            if (file_exists($path)) {
                $output = array();
                $returnVar = 0;
                exec('rm -rf ' . escapeshellarg($path) . ' 2>&1', $output, $returnVar);
                if ($returnVar !== 0) {
                    $cleanupErrors++;
                    log::add('ttscast', 'warning', '[CLEANUP_KO] Echec suppression "' . $path . '" (Code: ' . $returnVar . ') : ' . implode(' ', $output));
                } else {
                    $cleanupRemoved++;
                    log::add('ttscast', 'info', '[CLEANUP_OK] Chemin supprimé : ' . $path);
                }
            }
        }
        $cleanupSummary = count($pathsToRemove) . ' chemin(s) vérifié(s), ' . $cleanupRemoved . ' supprimé(s)';
        if ($cleanupErrors > 0) {
            $cleanupSummary .= ', ' . $cleanupErrors . ' erreur(s)';
        }
        log::add('ttscast', 'debug', '[CLEANUP] ' . $cleanupSummary);
    } catch (Exception $e) {
        log::add('ttscast', 'warning', '[CLEANUP_KO] Erreur lors du nettoyage : ' . $e->getMessage());
    }

    // Créer/configurer les équipements IA si l'IA est déjà activée
    ttscast::manageAIEquipments();
}

// Fonction exécutée automatiquement après la suppression du plugin
function ttscast_remove() {

}
