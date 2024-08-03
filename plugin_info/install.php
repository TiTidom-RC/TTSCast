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
    if (config::byKey('gCloudTTSVoice', 'ttscast') == '') {
        config::save('gCloudTTSVoice', 'fr-FR-Standard-A', 'ttscast');
    }
    if (config::byKey('ttsPurgeCacheDays', 'ttscast') == '') {
        config::save('ttsPurgeCacheDays', '10', 'ttscast');
    }
    if (config::byKey('appDisableDing', 'ttscast') == '') {
        config::save('appDisableDing', '0', 'ttscast');
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

    message::removeAll('ttscast');
    message::add('ttscast', 'Mise à jour du plugin TTS Cast (Version : ' . $pluginVersion . ')', null, null);

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
    if (config::byKey('gCloudTTSVoice', 'ttscast') == '') {
        config::save('gCloudTTSVoice', 'fr-FR-Standard-A', 'ttscast');
    }
    if (config::byKey('ttsPurgeCacheDays', 'ttscast') == '') {
        config::save('ttsPurgeCacheDays', '10', 'ttscast');
    }
    if (config::byKey('appDisableDing', 'ttscast') == '') {
        config::save('appDisableDing', '0', 'ttscast');
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

// Fonction exécutée automatiquement après la suppression du plugin
function ttscast_remove() {

}
