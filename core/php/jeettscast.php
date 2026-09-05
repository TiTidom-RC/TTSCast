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
        log::add('ttscast','debug','[CALLBACK] TTSCast Devices Discovery :: ' . count($result['devices']) . ' device(s) reçu(s)');
        foreach ($result['devices'] as $key => $data) {
            if (!isset($data['uuid'])) {
                continue;
            }
            if ($data['scanmode'] != 1) {
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
        $uuids = array_column($result['casts'], 'uuid');
        log::add('ttscast','debug','[CALLBACK] TTSCast Schedule :: ' . count($result['casts']) . ' cast(s) reçu(s) :: ' . implode(', ', $uuids));
        foreach ($result['casts'] as $key => $data) {
            if (!isset($data['uuid'])) {
                continue;
            }
            if ($data['schedule'] != 1) {
                continue;
            }

            $ttscast = ttscast::byLogicalId($data['uuid'], 'ttscast');
            if (!is_object($ttscast)) {    
                continue;
            }
            else {
                $updttscast = ttscast::scheduleUpdateCast($data);
            }
        }
    } elseif (isset($result['castsRT'])) {
        $uuids = array_column($result['castsRT'], 'uuid');
        log::add('ttscast','debug','[CALLBACK] TTSCast RealTime :: ' . count($result['castsRT']) . ' event(s) reçu(s) :: ' . implode(', ', $uuids));
        foreach ($result['castsRT'] as $key => $data) {
            if (!isset($data['uuid'])) {
                continue;
            }
            if ($data['realtime'] != 1) {
                continue;
            }
            $ttscast = ttscast::byLogicalId($data['uuid'], 'ttscast');
            if (!is_object($ttscast)) {    
                continue;
            }
            else {
                $rtcast = ttscast::realtimeUpdateCast($data);
            }
        }
    } elseif (isset($result['aiStats'])) {
        foreach ($result['aiStats'] as $key => $data) {
            if ($key != 'TTSCast_AI_Stats') {
                log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats :: LogicalId non reconnu: ' . $key);
                continue;
            }
            
            $statsEq = ttscast::byLogicalId('TTSCast_AI_Stats', 'ttscast');
            if (!is_object($statsEq)) {
                log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats :: Équipement virtuel non trouvé');
                continue;
            }
            
            $logParts = array();
            
            // Mise à jour des commandes de tokens (valeur de l'appel en cours)
            if (isset($data['ai_tokens_input'])) {
                $cmd = $statsEq->getCmd('info', 'ai_tokens_input');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_tokens_input']));
                    $logParts[] = 'Input=' . $data['ai_tokens_input'];
                }
            }
            
            if (isset($data['ai_tokens_output'])) {
                $cmd = $statsEq->getCmd('info', 'ai_tokens_output');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_tokens_output']));
                    $logParts[] = 'Output=' . $data['ai_tokens_output'];
                }
            }
            
            if (isset($data['ai_tokens_total'])) {
                $cmd = $statsEq->getCmd('info', 'ai_tokens_total');
                if (is_object($cmd)) {
                    $cmd->event(intval($data['ai_tokens_total']));
                    $logParts[] = 'Total=' . $data['ai_tokens_total'];
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
                    $logParts[] = 'FinishReason=' . $data['ai_finish_reason'];
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
                    $logParts[] = 'SafetyBlocked=' . $data['ai_safety_blocked'];
                }
            }
            
            log::add('ttscast','debug','[CALLBACK] TTSCast AI Stats :: ' . implode(' | ', $logParts));
        }
    } elseif (isset($result['ttsTestResult'])) {
        log::add('ttscast', 'debug', '[CALLBACK] TTSCast TTS Test Result');
        message::add('ttscast', '[TTS Test] ' . strval($result['ttsTestResult']));
    } elseif (isset($result['ttsLastMessage'])) {
        log::add('ttscast', 'debug', '[CALLBACK] TTSCast TTS Last Message');
        foreach ($result['ttsLastMessage'] as $uuid => $text) {
            $deviceEq = ttscast::byLogicalId($uuid, 'ttscast');
            if (!is_object($deviceEq)) {
                log::add('ttscast', 'debug', '[CALLBACK] TTS Last Message :: Équipement non trouvé :: UUID=' . $uuid);
                continue;
            }
            $cmd = $deviceEq->getCmd('info', 'tts_last_message');
            if (is_object($cmd)) {
                $cmd->event(strval($text));
                log::add('ttscast', 'debug', '[CALLBACK] TTS Last Message [' . $deviceEq->getName() . '] :: "' . strval($text) . '" (UUID=' . $uuid . ')');
            }
        }
    } elseif (isset($result['ttsNotifyResult'])) {
        log::add('ttscast', 'debug', '[CALLBACK] TTS Notify Result');
        $data              = $result['ttsNotifyResult'];
        $googleUUID        = isset($data['googleUUID'])        ? $data['googleUUID']        : '';
        $cmdNotificationId = isset($data['cmdNotificationId']) ? $data['cmdNotificationId'] : 0;
        $reformulatedText  = isset($data['reformulatedText'])  ? strval($data['reformulatedText']) : '';
        $cmdOptions        = isset($data['cmdOptions'])        ? $data['cmdOptions']        : array();

        // Exécution de la commande notification avec le texte reformulé + options pass-through
        // Note : tts_last_message est mis à jour via le handler ttsLastMessage (envoyé séparément par le démon)
        if ($cmdNotificationId > 0 && $reformulatedText !== '') {
            $cmdNotification = cmd::byId($cmdNotificationId);
            if (is_object($cmdNotification)) {
                $execOptions = array_merge($cmdOptions, array('message' => $reformulatedText));
                $cmdNotification->execCmd($execOptions);
                log::add('ttscast', 'debug', '[CALLBACK] TTS Notify Result :: execCmd :: cmdId=' . $cmdNotificationId . ' | options=' . json_encode($execOptions));
            } else {
                log::add('ttscast', 'warning', '[CALLBACK] TTS Notify Result :: Commande notification introuvable :: cmdId=' . $cmdNotificationId);
            }
        }
    } else {
        log::add('ttscast', 'error', '[CALLBACK] unknown message received from daemon'); 
    }
} catch (Exception $e) {
    log::add('ttscast', 'error', displayException($e));
}
