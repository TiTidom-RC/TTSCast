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
                /* event::add('ttscast::newDevice', array(
                    'friendly_name' => $data['friendly_name'],
                    'newone' => '1'
                )); */
                $newttscast = ttscast::createAndUpdCastFromScan($data);
            }
            else {
                log::add('ttscast','debug','[CALLBACK] TTSCast Update :: ' . $data['friendly_name'] . ' (' . $data['uuid'] . ')');
                /* event::add('ttscast::newDevice', array(
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
    } elseif (isset($result['aiStats'])) {
        log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats');
        foreach ($result['aiStats'] as $key => $data) {
            if ($key != 'TTSCast_AI_Stats') {
                log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats :: LogicalId non reconnu: ' . $key);
                continue;
            }
            log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats :: Mise à jour des tokens');
            
            $statsEq = ttscast::byLogicalId('TTSCast_AI_Stats', 'ttscast');
            if (!is_object($statsEq)) {
                log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats :: Équipement virtuel non trouvé');
                continue;
            }
            
            // Mise à jour des commandes de tokens (valeur de l'appel en cours)
            if (isset($data['ai_tokens_input'])) {
                $cmd = $statsEq->getCmd('info', 'ai_tokens_input');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_tokens_input']));
                    log::add('ttscast','debug','[CALLBACK] AI Stats :: Input tokens: ' . $data['ai_tokens_input']);
                }
            }
            
            if (isset($data['ai_tokens_output'])) {
                $cmd = $statsEq->getCmd('info', 'ai_tokens_output');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_tokens_output']));
                    log::add('ttscast','debug','[CALLBACK] AI Stats :: Output tokens: ' . $data['ai_tokens_output']);
                }
            }
            
            if (isset($data['ai_tokens_total'])) {
                $cmd = $statsEq->getCmd('info', 'ai_tokens_total');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_tokens_total']));
                    log::add('ttscast','debug','[CALLBACK] AI Stats :: Total tokens: ' . $data['ai_tokens_total']);
                }
            }
            
            // if (isset($data['ai_cache_tokens'])) {
            //     $cmd = $statsEq->getCmd('info', 'ai_cache_tokens');
            //     if (is_object($cmd)) {
            //         $cmd->event(intval($data['ai_cache_tokens']));
            //         log::add('ttscast','debug','[CALLBACK] AI Stats :: Cache tokens: ' . $data['ai_cache_tokens']);
            //     }
            // }
            
            // if (isset($data['ai_tool_tokens'])) {
            //     $cmd = $statsEq->getCmd('info', 'ai_tool_tokens');
            //     if (is_object($cmd)) {
            //         $cmd->event(intval($data['ai_tool_tokens']));
            //         log::add('ttscast','debug','[CALLBACK] AI Stats :: Tool tokens: ' . $data['ai_tool_tokens']);
            //     }
            // }
            
            // if (isset($data['ai_thoughts_tokens'])) {
            //     $cmd = $statsEq->getCmd('info', 'ai_thoughts_tokens');
            //     if (is_object($cmd)) {
            //         $cmd->event(intval($data['ai_thoughts_tokens']));
            //         log::add('ttscast','debug','[CALLBACK] AI Stats :: Thoughts tokens: ' . $data['ai_thoughts_tokens']);
            //     }
            // }
            
            if (isset($data['ai_finish_reason'])) {
                $cmd = $statsEq->getCmd('info', 'ai_finish_reason');
                if (is_object($cmd)) {
                    $cmd->event($data['ai_finish_reason']);
                    log::add('ttscast','debug','[CALLBACK] AI Stats :: Finish reason: ' . $data['ai_finish_reason']);
                }
            }
            
            // if (isset($data['ai_avg_logprobs'])) {
            //     $cmd = $statsEq->getCmd('info', 'ai_avg_logprobs');
            //     if (is_object($cmd)) {
            //         $cmd->event(floatval($data['ai_avg_logprobs']));
            //         log::add('ttscast','debug','[CALLBACK] AI Stats :: Avg logprobs: ' . $data['ai_avg_logprobs']);
            //     }
            // }
            
            if (isset($data['ai_safety_blocked'])) {
                $cmd = $statsEq->getCmd('info', 'ai_safety_blocked');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_safety_blocked']));
                    log::add('ttscast','debug','[CALLBACK] AI Stats :: Safety blocked: ' . $data['ai_safety_blocked']);
                }
            }
        }
    } elseif (isset($result['aiTestResult'])) {
        log::add('ttscast', 'debug', '[CALLBACK] TTSCast AI Test Result');
        message::add('ttscast', '[AI Test] ' . strval($result['aiTestResult']), '', '', false);
    } elseif (isset($result['aiLastMessage'])) {
        log::add('ttscast', 'debug', '[CALLBACK] TTSCast AI Last Message');
        foreach ($result['aiLastMessage'] as $uuid => $text) {
            $deviceEq = ttscast::byLogicalId($uuid, 'ttscast');
            if (!is_object($deviceEq)) {
                log::add('ttscast', 'debug', '[CALLBACK] AI Last Message :: Équipement non trouvé :: UUID=' . $uuid);
                continue;
            }
            $cmd = $deviceEq->getCmd('info', 'ai_last_message');
            if (is_object($cmd)) {
                $cmd->event(strval($text));
                log::add('ttscast', 'debug', '[CALLBACK] AI Last Message :: Mise à jour :: UUID=' . $uuid);
            }
        }
    } else {
        log::add('ttscast', 'error', '[CALLBACK] unknown message received from daemon'); 
    }
} catch (Exception $e) {
    log::add('ttscast', 'error', displayException($e));
}
