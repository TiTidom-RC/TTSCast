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
            ttscast::sendOnStartCastToDaemon();

        }
    } elseif (isset($result['heartbeat'])) {
        if ($result['heartbeat'] == 1) {
            log::add('ttscast','info','[CALLBACK] TTSCast Daemon Heartbeat (600s)');
        }
    } elseif (isset($result['daemonStarted'])) {
        if ($result['daemonStarted'] == '1') {
            log::add('ttscast', 'info', '[CALLBACK] Daemon Started');
            ttscast::sendOnStartCastToDaemon();
        }
    } elseif (isset($result['actionReturn'])) {
        log::add('ttscast','debug','[CALLBACK] TTSCast ActionReturn :: ' . json_encode($result));
        if ($result['actionReturn'] == "setvolume" || $result['actionReturn'] == "volumeup" || $result['actionReturn'] == "volumedown") {
            if (!isset($result['uuid']) || !isset($result['volumelevel'])) {
                log::add('ttscast','debug','[CALLBACK] Action Return Volume :: UUID et/ou VolumeLevel non défini(s) !');
            } else {
                log::add('ttscast','debug','[CALLBACK] Action Return Volume :: Les paramètres sont bien définis...');
                $ttscast = ttscast::byLogicalId($result['uuid'], 'ttscast');
                if (is_object($ttscast)) { 
                    log::add('ttscast','debug','[CALLBACK] Action Return Volume :: Le Cast a été trouvé...');
                    $cmd = $ttscast->getCmd('info', 'volumelevel');
                    if (is_object($cmd)) {
                        log::add('ttscast','debug','[CALLBACK] Action Return Volume :: SetVolume in Config :: ' . $result['volumelevel']);
                        $cmd->event($result['volumelevel']);
                    }
                }
            }
        } else {
            log::add('ttscast','debug','[CALLBACK] Action Return :: ERROR SetVolume Return...');
        }
        
            
    } elseif (isset($result['devices'])) {
        log::add('ttscast','debug','[CALLBACK] TTSCast Devices Discovery');
        foreach ($result['devices'] as $key => $data) {
            if (!isset($data['uuid'])) {
                log::add('ttscast','debug','[CALLBACK] TTSCast Device :: UUID non défini !');
                continue;
            }
            log::add('ttscast','debug','[CALLBACK] TTSCast Device :: ' . $data['uuid']);
            if ($data['scanmode'] != 1) {
                log::add('ttscast','debug','[CALLBACK] TTSCast Device :: NoScanMode');
                continue;
            }
            $ttscast = ttscast::byLogicalId($data['uuid'], 'ttscast');
            if (!is_object($ttscast)) {    
                log::add('ttscast','debug','[CALLBACK] NEW TTSCast détecté :: ' . $data['friendly_name'] . ' (' . $data['uuid'] . ')');
                /* event::add('ttscast::newdevice', array(
                    'friendly_name' => $data['friendly_name'],
                    'newone' => '1'
                )); */
                $newttscast = ttscast::createAndUpdCastFromScan($data);
            }
            else {
                log::add('ttscast','debug','[CALLBACK] TTSCast Update :: ' . $data['friendly_name'] . ' (' . $data['uuid'] . ')');
                /* event::add('ttscast::newdevice', array(
                    'friendly_name' => $data['friendly_name'],
                    'newone' => '0'
                )); */
                $updttscast = ttscast::createAndUpdCastFromScan($data);
            }
        }
    } elseif (isset($result['casts'])) {
        log::add('ttscast','debug','[CALLBACK] TTSCast Schedule');
        foreach ($result['casts'] as $key => $data) {
            if (!isset($data['uuid'])) {
                log::add('ttscast','debug','[CALLBACK] TTSCast Schedule :: UUID non défini !');
                continue;
            }
            log::add('ttscast','debug','[CALLBACK] TTSCast Schedule :: ' . $data['uuid']);
            if ($data['schedule'] != 1) {
                # log::add('ttscast','debug','[CALLBACK] TTSCast Schedule :: NoScheduleMode');
                continue;
            }
            # log::add('ttscast','debug','[CALLBACK] TTSCast Schedule Volume :: ' . $data['uuid'] . ' = ' . $data['volume_level']);

            $ttscast = ttscast::byLogicalId($data['uuid'], 'ttscast');
            if (!is_object($ttscast)) {    
                # log::add('ttscast','debug','[CALLBACK] TTSCast Schedule NON EXIST :: ' . $data['uuid']);
                continue;
            }
            else {
                $updttscast = ttscast::scheduleUpdateCast($data);
            }
        }
    } elseif (isset($result['castsRT'])) {
        log::add('ttscast','debug','[CALLBACK] TTSCast RealTime');
        foreach ($result['castsRT'] as $key => $data) {
            if (!isset($data['uuid'])) {
                log::add('ttscast','debug','[CALLBACK] TTSCast RealTime :: UUID non défini !');
                continue;
            }
            log::add('ttscast','debug','[CALLBACK] TTSCast RealTime :: ' . $data['uuid']);
            if ($data['realtime'] != 1) {
                # log::add('ttscast','debug','[CALLBACK] TTSCast RealTime :: NoRealTimeMode');
                continue;
            }
            $ttscast = ttscast::byLogicalId($data['uuid'], 'ttscast');
            if (!is_object($ttscast)) {    
                # log::add('ttscast','debug','[CALLBACK] TTSCast RealTime NON EXIST :: ' . $data['uuid']);
                continue;
            }
            else {
                $rtcast = ttscast::realtimeUpdateCast($data);
            }
        }
    } else {
        log::add('ttscast', 'error', '[CALLBACK] unknown message received from daemon'); 
    }
} catch (Exception $e) {
    log::add('ttscast', 'error', displayException($e));
}
