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
    require_once dirname(__FILE__) . "/../../../../core/php/core.inc.php";

    if (!jeedom::apiAccess(init('apikey'), 'ttscast')) { 
        echo __('Vous n\'etes pas autorisé à effectuer cette action', __FILE__);
        die();
    }
    if (init('test') != '') {
        echo 'OK';
        die();
    }
    $result = json_decode(file_get_contents("php://input"), true);
    if (!is_array($result)) {
        die();
    }

    if (isset($result['scanState'])) {
        if ($result['scanState'] == "scanOn") {
            log::add('ttscast', 'debug', '[CALLBACK] scanState = scanOn'); 
            config::save('scanState', 'scanOn', 'ttscast');
            event::add('ttscast::scanState', array(
                'scanState' => 'scanOn')
            );
        } else {
            log::add('ttscast', 'debug', '[CALLBACK] scanState = scanOff'); 
            config::save('scanState', 'scanOff', 'ttscast');
            event::add('ttscast::scanState', array(
                'scanState' => 'scanOff')
            );
        }
    } elseif (isset($result['heartbeat'])) {
        if ($result['heartbeat'] == 1) {
            log::add('ttscast','info','[CALLBACK] TTSCast Daemon Heartbeat (60s)');
        }
    } elseif (isset($result['devices'])) {
        log::add('ttscast','debug','[CALLBACK] TTSCast Devices Discovery');
        foreach ($result['devices'] as $key => $data) {
            log::add('ttscast','debug','[CALLBACK] TTSCast NEW Device :: ' . $data['uuid']);
            if (!isset($data['uuid'])) {
                log::add('ttscast','debug','[CALLBACK] Devices :: UUID non défini !');
                continue;
            }
            $ttscast = ttscast::byLogicalId($data['uuid'], 'ttscast');
            if (!is_object($googlecast)) {
                if ($data['scanmode'] != 1) {
                    continue;
                }
                log::add('ttscast','debug','[CALLBACK] Devices :: NEW Chromecast détecté :: ' . $data['friendly_name'] . ' (' . $data['uuid'] . ')');
                event::add('ttscast::newdevice', array(
                    'friendly_name' => $data['friendly_name']
                ));
                $newttscast = ttscast::createCastFromScan($data);
            }
        }
    } else {
        log::add('ttscast', 'error', '[CALLBACK] unknown message received from daemon'); 
    }
} catch (Exception $e) {
    log::add('ttscast', 'error', displayException($e));
}
