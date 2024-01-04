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
    $pluginVersion = googlecast::getPluginVersion();
    config::save('pluginVersion', $pluginVersion, 'ttscast');

    // TODO initialiser les valeurs par défaut lors de l'install du plugin
    if (config::byKey('socketport', 'ttscast') == '') {
        config::save('socketport', '55999', 'ttscast');
    }
    if (config::byKey('ttsPurgeCacheDays', 'ttscast') == '') {
        config::save('ttsPurgeCacheDays', '10', 'ttscast');
    }

    message::removeAll('ttscast');
    message::add('ttscast', 'Installation du plugin TTS Cast terminée (version ' . $pluginVersion . ').', null, null);

}

// Fonction exécutée automatiquement après la mise à jour du plugin
function ttscast_update() {
    $daemonInfo = ttscast::deamon_info();
    if ($daemonInfo['state'] == 'ok') {
        ttscast::deamon_stop();
    }

    $pluginVersion = googlecast::getPluginVersion();
    config::save('pluginVersion', $pluginVersion, 'ttscast');

    // TODO intitaliser les valeurs par défaut lors de l'update du plugin
    if (config::byKey('socketport', 'ttscast') == '') {
        config::save('socketport', '55999', 'ttscast');
    }
    if (config::byKey('ttsPurgeCacheDays', 'ttscast') == '') {
        config::save('ttsPurgeCacheDays', '10', 'ttscast');
    }

    message::add('ttscast', 'Mise à jour du plugin TTS Cast terminée (version ' . $pluginVersion . ').', null, null);
    ttscast::deamon_start();
}

// Fonction exécutée automatiquement après la suppression du plugin
function ttscast_remove() {
}
