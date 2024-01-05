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

    // TODO initialiser les valeurs par défaut lors de l'install du plugin
    if (config::byKey('socketport', 'ttscast') == '') {
        config::save('socketport', '55999', 'ttscast');
    }
    if (config::byKey('cycle', 'ttscast') == '') {
        config::save('cycle', '1', 'ttscast');
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
}

// Fonction exécutée automatiquement après la mise à jour du plugin
function ttscast_update() {
    /* $daemonInfo = ttscast::deamon_info();
    if ($daemonInfo['state'] == 'ok') {
        ttscast::deamon_stop();
    } */

    $pluginVersion = ttscast::getPluginVersion();
    config::save('pluginVersion', $pluginVersion, 'ttscast');

    message::removeAll('ttscast');
    message::add('ttscast', 'Mise à jour du plugin TTS Cast (Version : ' . $pluginVersion . ')', null, null);

    // TODO intitaliser les valeurs par défaut lors de l'update du plugin
    if (config::byKey('socketport', 'ttscast') == '') {
        config::save('socketport', '55999', 'ttscast');
    }
    if (config::byKey('cycle', 'ttscast') == '') {
        config::save('cycle', '1', 'ttscast');
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

    $dependencyInfo = ttscast::dependancy_info();
    if (!isset($dependencyInfo['state'])) {
        message::add('ttscast', __('Veuilez vérifier les dépendances', __FILE__));
    } elseif ($dependencyInfo['state'] == 'nok') {
        try {
            $plugin = plugin::byId('ttscast');
            $plugin->dependancy_install();
        } catch (\Throwable $th) {
            message::add('ttscast', __('Cette mise à jour nécessite la réinstallation des dépendances même si elles sont marquées comme OK', __FILE__));
        }
    }

    // ttscast::deamon_start();
}

// Fonction exécutée automatiquement après la suppression du plugin
function ttscast_remove() {

}
