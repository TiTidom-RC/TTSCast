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
include_file('core', 'authentification', 'php');
if (!isConnect()) {
    include_file('desktop', '404', 'php');
    die();
}
?>
<form class="form-horizontal">
    <fieldset>
        <div>
            <legend><i class="fas fa-info"></i> {{Plugin}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Version Plugin}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Version du Plugin (A indiquer sur Community)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="pluginVersion" readonly />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Version PyEnv}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Version de PyEnv utilisée par le Plugin (A indiquer sur Community)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="pyenvVersion" readonly />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Version Python}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Version de Python utilisée par le Plugin (A indiquer sur Community)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="pythonVersion" readonly />
                </div>
            </div>
            <legend><i class="fas fa-code"></i> {{Dépendances}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Force les mises à jour Systèmes}}
                    <sup><i class="fas fa-ban tooltips" style="color:var(--al-danger-color)!important;" title="{{Les dépendances devront être relancées après la sauvegarde de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Permet de forcer l'installation des mises à jour systèmes}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="debugInstallUpdates" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Force la réinitialisation de PyEnv}}
                    <sup><i class="fas fa-ban tooltips" style="color:var(--al-danger-color)!important;" title="{{Les dépendances devront être relancées après la sauvegarde de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Permet de forcer la réinitialisation de l'environnement Python utilisé par le plugin}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="debugRestorePyEnv" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Force la réinitialisation de Venv}}
                    <sup><i class="fas fa-ban tooltips" style="color:var(--al-danger-color)!important;" title="{{Les dépendances devront être relancées après la sauvegarde de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Permet de forcer la réinitialisation de l'environnement Venv utilisé par le plugin}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="debugRestoreVenv" />
                </div>
            </div>
            <legend><i class="fas fa-university"></i> {{Démon}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Port Socket Interne}}
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{[ATTENTION] Ne changez ce paramètre qu'en cas de nécessité. (Défaut = 55111)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="socketport" placeholder="55111" />
                </div>
            </div>
            <div class="form-group">
	            <label class="col-lg-3 control-label">{{Fréquence des cycles}}
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Facteur multiplicateur des cycles du démon (Défaut = x1)}}"></i></sup>
                </label>
	            <div class="col-lg-2">
			        <select class="configKey form-control" data-l1key="cyclefactor">
                        <option value="0.1">{{Rapide +++ (x0.1)}}</option>
                        <option value="0.25">{{Rapide ++ (x0.25)}}</option>
                        <option value="0.5">{{Rapide + (x0.5)}}</option>
			            <option value="1.0" selected>{{Normal (x1)}}</option>
			            <option value="1.5">{{Lent - (x1.5)}}</option>
                        <option value="2.0">{{Lent -- (x2)}}</option>
			            <option value="3.0">{{Lent --- (x3)}}</option>
			        </select>
	            </div>
            </div>
            <legend><i class="fab fa-chromecast"></i> {{TTS (Text To Speech)}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Moteur TTS}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Moteur TTS à utiliser pour la synthèse vocale}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <select class="configKey form-control customform-ttsengine" data-l1key="ttsEngine">
                        <option value="jeedomtts">{{Jeedom TTS (Local)}}</option>
                        <option value="gtranslatetts">{{Google Translate API (Internet)}}</option>
                        <option value="gcloudtts">{{Google Cloud Text-To-Speech (Clé & Internet)}}</option>
                        <option value="voicersstts">{{Voice RSS API (Clé & Internet)}}</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-lang">
                <label class="col-lg-3 control-label">{{Langue TTS}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Langue à utiliser avec l'API Google Translate ou Jeedom TTS (Il n'est pas possible de choisir une voix, seulement une langue)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="ttsLang">
                        <option value="fr-FR">{{Français (fr-FR)}}</option>
                        <option value="en-US">{{Anglais (en-US)}}</option>
                        <option value="es-ES">{{Espagnol (es-ES)}}</option>
                        <option value="de-DE">{{Allemand (de-DE)}}</option>
                        <option value="it-IT">{{Italien (it-IT)}}</option>
                        <option value="sr-RS">{{Serbe (sr-RS)}}</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-voicersstts">
                <label class="col-lg-3 control-label">{{Clé API (Voice RSS)}} <a class="btn btn-info btn-xs" target="_blank" href="https://www.voicerss.org/personel/">{{SITE}}</a>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Rentrer votre clé API Voice RSS, récupérable sur leur site, dans votre profil}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input class="configKey form-control custominput-voicerssapikey" type="text" data-l1key="voiceRSSAPIKey" />
                </div>
            </div>
            <div class="form-group customform-gcloudtts">
                <label class="col-lg-3 control-label">{{Clé API (gCloud TTS)}} <a class="btn btn-info btn-xs" target="_blank" href="https://console.cloud.google.com/apis">{{SITE}}</a>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Uploader votre clé JSON en utilisant le bouton 'Ajouter Clé (JSON)'}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input class="configKey form-control custominput-apikey" type="text" data-l1key="gCloudAPIKey" readonly />
                </div>
                <div class="col-lg-2">
                    <a class="btn btn-primary btn-file">
                        <i class="fas fa-cloud-upload-alt"></i> {{Ajouter Clé (JSON)}}<input class="pluginAction" data-action="uploadAPIKey" type="file" name="fileAPIKey" style="display: inline-block;" accept=".json" />
                    </a>
                    <a class="btn btn-danger customclass-resetapikey"><i class="fas fa-trash-alt"></i> {{Effacer Clé}}</a>
                </div>
            </div>
            <div class="form-group customform-voicersstts">
                <label class="col-lg-3 control-label">{{Langue/Voix TTS (Voice RSS TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Langue et Voix à utiliser avec le moteur Voice RSS TTS}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <select class="configKey form-control" data-l1key="voiceRSSTTSVoice">
                        <!-- French France -->
                        <option disabled>--- Français (France) ---</option>
                        <option value="fr-fr-Bette">Français (France) - Bette Female (fr-fr-Bette)</option>
                        <option value="fr-fr-Iva">Français (France) - Iva Female (fr-fr-Iva)</option>
                        <option value="fr-fr-Zola">Français (France) - Zola Female (fr-fr-Zola)</option>
                        <option value="fr-fr-Axel">Français (France) - Axel Male (fr-fr-Axel)</option>
                        <!-- French Canada -->
                        <option disabled>--- Français (Canada) ---</option>
                        <option value="fr-ca-Emile">Français (Canada) - Emile Female (fr-ca-Emile)</option>
                        <option value="fr-ca-Olivia">Français (Canada) - Olivia Female (fr-ca-Olivia)</option>
                        <option value="fr-ca-Logan">Français (Canada) - Logan Female (fr-ca-Logan)</option>
                        <option value="fr-ca-Felix">Français (Canada) - Felix Male (fr-ca-Felix)</option>
                        <!-- Néerlandais Belgique -->
                        <option disabled>--- Néerlandais (Belgique) ---</option>
                        <option value="nl-be-Daan">Néerlandais (Belgique) - Daan Male (nl-be-Daan)</option>
                        <!-- English US -->
                        <option disabled>--- Anglais (US) ---</option>
                        <option value="en-us-Linda">Anglais (US) - Linda Female (en-us-Linda)</option>
                        <option value="en-us-Amy">Anglais (US) - Amy Female (en-us-Amy)</option>
                        <option value="en-us-Mary">Anglais (US) - Mary Female (en-us-Mary)</option>
                        <option value="en-us-John">Anglais (US) - John Male (en-us-John)</option>
                        <option value="en-us-Mike">Anglais (US) - Mike Male (en-us-Mike)</option>
                        <!-- English GB -->
                        <option disabled>--- Anglais (GB) ---</option>
                        <option value="en-gb-Alice">Anglais (GB) - Alice Female (en-gb-Alice)</option>
                        <option value="en-gb-Nancy">Anglais (GB) - Nancy Female (en-gb-Nancy)</option>
                        <option value="en-gb-Lily">Anglais (GB) - Lily Female (en-gb-Lily)</option>
                        <option value="en-gb-Harry">Anglais (GB) - Harry Male (en-gb-Harry)</option>
                        <!-- Deutsch -->
                        <option disabled>--- Allemand (Allemagne) ---</option>
                        <option value="de-de-Hanna">Allemand (Allemagne) - Hanna Female (de-de-Hanna)</option>
                        <option value="de-de-Lina">Allemand (Allemagne) - Lina Female (de-de-Lina)</option>
                        <option value="de-de-Jonas">Allemand (Allemagne) - Jonas Male (de-de-Jonas)</option>
                        <!-- Spanish -->
                        <option disabled>--- Espagnol (Espagne) ---</option>
                        <option value="es-es-Camila">Espagnol (Espagne) - Camila Female (es-es-Camila)</option>
                        <option value="es-es-Sofia">Espagnol (Espagne) - Sofia Female (es-es-Sofia)</option>
                        <option value="es-es-Luna">Espagnol (Espagne) - Luna Female (es-es-Luna)</option>
                        <option value="es-es-Diego">Espagnol (Espagne) - Diego Male (es-es-Diego)</option>
                        <!-- Italien -->
                        <option disabled>--- Italien (Italie) ---</option>
                        <option value="it-it-Bria">Italien (Italie) - Bria Female (it-it-Bria)</option>
                        <option value="it-it-Mia">Italien (Italie) - Mia Female (it-it-Mia)</option>
                        <option value="it-it-Pietro">Italien (Italie) - Pietro Male (it-it-Pietro)</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-voicersstts">
                <label class="col-lg-3 control-label">{{Vitesse de Dictée (Voice RSS TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Valeur par défaut = Normal (0)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="voiceRSSTTSSpeed">
                        <option value="-10">{{Lent (-10)}}</option>
                        <option value="-9">{{Lent (-9)}}</option>
                        <option value="-8">{{Lent (-8)}}</option>
                        <option value="-7">{{Lent (-7)}}</option>
                        <option value="-6">{{Lent (-6)}}</option>
                        <option value="-5">{{Lent (-5)}}</option>
                        <option value="-4">{{Lent (-4)}}</option>
                        <option value="-3">{{Lent (-3)}}</option>
                        <option value="-2">{{Lent (-2)}}</option>
                        <option value="-1">{{Lent (-1)}}</option>
                        <option value="0" selected>{{Normal (0)}}</option>
                        <option value="1">{{Rapide (+1)}}</option>
                        <option value="2">{{Rapide (+2)}}</option>
                        <option value="3">{{Rapide (+3)}}</option>
                        <option value="4">{{Rapide (+4)}}</option>
                        <option value="5">{{Rapide (+5)}}</option>
                        <option value="6">{{Rapide (+6)}}</option>
                        <option value="7">{{Rapide (+7)}}</option>
                        <option value="8">{{Rapide (+8)}}</option>
                        <option value="9">{{Rapide (+9)}}</option>
                        <option value="10">{{Rapide (+10)}}</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-gcloudtts">
                <label class="col-lg-3 control-label">{{Langue/Voix TTS (gCloud TTS)}} <a class="btn btn-info btn-xs" target="_blank" href="https://cloud.google.com/text-to-speech/">{{SITE}}</a>
                    <sup><i class="fas fa-question-circle tooltips" title="{{Langue et Voix à utiliser avec le moteur Google Cloud TTS}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <select class="configKey form-control" data-l1key="gCloudTTSVoice">
                        <!-- French France -->
                        <option disabled>--- Français (France) ---</option>
                        <option value="fr-FR-Chirp-HD-D">Français (France) - Chirp HD D Male (fr-FR-Chirp-HD-D)</option>
                        <option value="fr-FR-Chirp-HD-F">Français (France) - Chirp HD F Female (fr-FR-Chirp-HD-F)</option>
                        <option value="fr-FR-Chirp-HD-O">Français (France) - Chirp HD O Female (fr-FR-Chirp-HD-O)</option>
                        <option value="fr-FR-Chirp3-HD-Achernar">Français (France) - Chirp3 HD Achernar Female (fr-FR-Chirp3-HD-Achernar)</option>
                        <option value="fr-FR-Chirp3-HD-Achird">Français (France) - Chirp3 HD Achird Male (fr-FR-Chirp3-HD-Achird)</option>
                        <option value="fr-FR-Chirp3-HD-Algenib">Français (France) - Chirp3 HD Algenib Male (fr-FR-Chirp3-HD-Algenib)</option>
                        <option value="fr-FR-Chirp3-HD-Algieba">Français (France) - Chirp3 HD Algieba Male (fr-FR-Chirp3-HD-Algieba)</option>
                        <option value="fr-FR-Chirp3-HD-Alnilam">Français (France) - Chirp3 HD Alnilam Male (fr-FR-Chirp3-HD-Alnilam)</option>
                        <option value="fr-FR-Chirp3-HD-Aoede">Français (France) - Chirp3 HD Aoede Female (fr-FR-Chirp3-HD-Aoede)</option>
                        <option value="fr-FR-Chirp3-HD-Autonoe">Français (France) - Chirp3 HD Autonoe Female (fr-FR-Chirp3-HD-Autonoe)</option>
                        <option value="fr-FR-Chirp3-HD-Callirrhoe">Français (France) - Chirp3 HD Callirrhoe Female (fr-FR-Chirp3-HD-Callirrhoe)</option>
                        <option value="fr-FR-Chirp3-HD-Charon">Français (France) - Chirp3 HD Charon Male (fr-FR-Chirp3-HD-Charon)</option>
                        <option value="fr-FR-Chirp3-HD-Despina">Français (France) - Chirp3 HD Despina Female (fr-FR-Chirp3-HD-Despina)</option>
                        <option value="fr-FR-Chirp3-HD-Enceladus">Français (France) - Chirp3 HD Enceladus Male (fr-FR-Chirp3-HD-Enceladus)</option>
                        <option value="fr-FR-Chirp3-HD-Erinome">Français (France) - Chirp3 HD Erinome Female (fr-FR-Chirp3-HD-Erinome)</option>
                        <option value="fr-FR-Chirp3-HD-Fenrir">Français (France) - Chirp3 HD Fenrir Male (fr-FR-Chirp3-HD-Fenrir)</option>
                        <option value="fr-FR-Chirp3-HD-Gacrux">Français (France) - Chirp3 HD Gacrux Female (fr-FR-Chirp3-HD-Gacrux)</option>
                        <option value="fr-FR-Chirp3-HD-Iapetus">Français (France) - Chirp3 HD Iapetus Male (fr-FR-Chirp3-HD-Iapetus)</option>
                        <option value="fr-FR-Chirp3-HD-Kore">Français (France) - Chirp3 HD Kore Female (fr-FR-Chirp3-HD-Kore)</option>
                        <option value="fr-FR-Chirp3-HD-Laomedeia">Français (France) - Chirp3 HD Laomedeia Female (fr-FR-Chirp3-HD-Laomedeia)</option>
                        <option value="fr-FR-Chirp3-HD-Leda">Français (France) - Chirp3 HD Leda Female (fr-FR-Chirp3-HD-Leda)</option>
                        <option value="fr-FR-Chirp3-HD-Orus">Français (France) - Chirp3 HD Orus Male (fr-FR-Chirp3-HD-Orus)</option>
                        <option value="fr-FR-Chirp3-HD-Puck">Français (France) - Chirp3 HD Puck Male (fr-FR-Chirp3-HD-Puck)</option>
                        <option value="fr-FR-Chirp3-HD-Pulcherrima">Français (France) - Chirp3 HD Pulcherrima Female (fr-FR-Chirp3-HD-Pulcherrima)</option>
                        <option value="fr-FR-Chirp3-HD-Rasalgethi">Français (France) - Chirp3 HD Rasalgethi Male (fr-FR-Chirp3-HD-Rasalgethi)</option>
                        <option value="fr-FR-Chirp3-HD-Sadachbia">Français (France) - Chirp3 HD Sadachbia Male (fr-FR-Chirp3-HD-Sadachbia)</option>
                        <option value="fr-FR-Chirp3-HD-Sadaltager">Français (France) - Chirp3 HD Sadaltager Male (fr-FR-Chirp3-HD-Sadaltager)</option>
                        <option value="fr-FR-Chirp3-HD-Schedar">Français (France) - Chirp3 HD Schedar Male (fr-FR-Chirp3-HD-Schedar)</option>
                        <option value="fr-FR-Chirp3-HD-Sulafat">Français (France) - Chirp3 HD Sulafat Female (fr-FR-Chirp3-HD-Sulafat)</option>
                        <option value="fr-FR-Chirp3-HD-Umbriel">Français (France) - Chirp3 HD Umbriel Male (fr-FR-Chirp3-HD-Umbriel)</option>
                        <option value="fr-FR-Chirp3-HD-Vindemiatrix">Français (France) - Chirp3 HD Vindemiatrix Female (fr-FR-Chirp3-HD-Vindemiatrix)</option>
                        <option value="fr-FR-Chirp3-HD-Zephyr">Français (France) - Chirp3 HD Zephyr Female (fr-FR-Chirp3-HD-Zephyr)</option>
                        <option value="fr-FR-Chirp3-HD-Zubenelgenubi">Français (France) - Chirp3 HD Zubenelgenubi Male (fr-FR-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="fr-FR-Neural2-F">Français (France) - Neural2 F Female (fr-FR-Neural2-F)</option>
                        <option value="fr-FR-Neural2-G">Français (France) - Neural2 G Male (fr-FR-Neural2-G)</option>
                        <option value="fr-FR-Polyglot-1">Français (France) - Polyglot 1 Male (fr-FR-Polyglot-1)</option>
                        <option value="fr-FR-Standard-F">Français (France) - Standard F Female (fr-FR-Standard-F)</option>
                        <option value="fr-FR-Standard-G">Français (France) - Standard G Male (fr-FR-Standard-G)</option>
                        <option value="fr-FR-Studio-A">Français (France) - Studio A Female (fr-FR-Studio-A)</option>
                        <option value="fr-FR-Studio-D">Français (France) - Studio D Male (fr-FR-Studio-D)</option>
                        <option value="fr-FR-Wavenet-F">Français (France) - Wavenet F Female (fr-FR-Wavenet-F)</option>
                        <option value="fr-FR-Wavenet-G">Français (France) - Wavenet G Male (fr-FR-Wavenet-G)</option>
                        <!-- French Canada -->
                        <option disabled>--- Français (Canada) ---</option>
                        <option value="fr-CA-Chirp-HD-D">Français (Canada) - Chirp HD D Male (fr-CA-Chirp-HD-D)</option>
                        <option value="fr-CA-Chirp-HD-F">Français (Canada) - Chirp HD F Female (fr-CA-Chirp-HD-F)</option>
                        <option value="fr-CA-Chirp-HD-O">Français (Canada) - Chirp HD O Female (fr-CA-Chirp-HD-O)</option>
                        <option value="fr-CA-Chirp3-HD-Achernar">Français (Canada) - Chirp3 HD Achernar Female (fr-CA-Chirp3-HD-Achernar)</option>
                        <option value="fr-CA-Chirp3-HD-Achird">Français (Canada) - Chirp3 HD Achird Male (fr-CA-Chirp3-HD-Achird)</option>
                        <option value="fr-CA-Chirp3-HD-Algenib">Français (Canada) - Chirp3 HD Algenib Male (fr-CA-Chirp3-HD-Algenib)</option>
                        <option value="fr-CA-Chirp3-HD-Algieba">Français (Canada) - Chirp3 HD Algieba Male (fr-CA-Chirp3-HD-Algieba)</option>
                        <option value="fr-CA-Chirp3-HD-Alnilam">Français (Canada) - Chirp3 HD Alnilam Male (fr-CA-Chirp3-HD-Alnilam)</option>
                        <option value="fr-CA-Chirp3-HD-Aoede">Français (Canada) - Chirp3 HD Aoede Female (fr-CA-Chirp3-HD-Aoede)</option>
                        <option value="fr-CA-Chirp3-HD-Autonoe">Français (Canada) - Chirp3 HD Autonoe Female (fr-CA-Chirp3-HD-Autonoe)</option>
                        <option value="fr-CA-Chirp3-HD-Callirrhoe">Français (Canada) - Chirp3 HD Callirrhoe Female (fr-CA-Chirp3-HD-Callirrhoe)</option>
                        <option value="fr-CA-Chirp3-HD-Charon">Français (Canada) - Chirp3 HD Charon Male (fr-CA-Chirp3-HD-Charon)</option>
                        <option value="fr-CA-Chirp3-HD-Despina">Français (Canada) - Chirp3 HD Despina Female (fr-CA-Chirp3-HD-Despina)</option>
                        <option value="fr-CA-Chirp3-HD-Enceladus">Français (Canada) - Chirp3 HD Enceladus Male (fr-CA-Chirp3-HD-Enceladus)</option>
                        <option value="fr-CA-Chirp3-HD-Erinome">Français (Canada) - Chirp3 HD Erinome Female (fr-CA-Chirp3-HD-Erinome)</option>
                        <option value="fr-CA-Chirp3-HD-Fenrir">Français (Canada) - Chirp3 HD Fenrir Male (fr-CA-Chirp3-HD-Fenrir)</option>
                        <option value="fr-CA-Chirp3-HD-Gacrux">Français (Canada) - Chirp3 HD Gacrux Female (fr-CA-Chirp3-HD-Gacrux)</option>
                        <option value="fr-CA-Chirp3-HD-Iapetus">Français (Canada) - Chirp3 HD Iapetus Male (fr-CA-Chirp3-HD-Iapetus)</option>
                        <option value="fr-CA-Chirp3-HD-Kore">Français (Canada) - Chirp3 HD Kore Female (fr-CA-Chirp3-HD-Kore)</option>
                        <option value="fr-CA-Chirp3-HD-Laomedeia">Français (Canada) - Chirp3 HD Laomedeia Female (fr-CA-Chirp3-HD-Laomedeia)</option>
                        <option value="fr-CA-Chirp3-HD-Leda">Français (Canada) - Chirp3 HD Leda Female (fr-CA-Chirp3-HD-Leda)</option>
                        <option value="fr-CA-Chirp3-HD-Orus">Français (Canada) - Chirp3 HD Orus Male (fr-CA-Chirp3-HD-Orus)</option>
                        <option value="fr-CA-Chirp3-HD-Puck">Français (Canada) - Chirp3 HD Puck Male (fr-CA-Chirp3-HD-Puck)</option>
                        <option value="fr-CA-Chirp3-HD-Pulcherrima">Français (Canada) - Chirp3 HD Pulcherrima Female (fr-CA-Chirp3-HD-Pulcherrima)</option>
                        <option value="fr-CA-Chirp3-HD-Rasalgethi">Français (Canada) - Chirp3 HD Rasalgethi Male (fr-CA-Chirp3-HD-Rasalgethi)</option>
                        <option value="fr-CA-Chirp3-HD-Sadachbia">Français (Canada) - Chirp3 HD Sadachbia Male (fr-CA-Chirp3-HD-Sadachbia)</option>
                        <option value="fr-CA-Chirp3-HD-Sadaltager">Français (Canada) - Chirp3 HD Sadaltager Male (fr-CA-Chirp3-HD-Sadaltager)</option>
                        <option value="fr-CA-Chirp3-HD-Schedar">Français (Canada) - Chirp3 HD Schedar Male (fr-CA-Chirp3-HD-Schedar)</option>
                        <option value="fr-CA-Chirp3-HD-Sulafat">Français (Canada) - Chirp3 HD Sulafat Female (fr-CA-Chirp3-HD-Sulafat)</option>
                        <option value="fr-CA-Chirp3-HD-Umbriel">Français (Canada) - Chirp3 HD Umbriel Male (fr-CA-Chirp3-HD-Umbriel)</option>
                        <option value="fr-CA-Chirp3-HD-Vindemiatrix">Français (Canada) - Chirp3 HD Vindemiatrix Female (fr-CA-Chirp3-HD-Vindemiatrix)</option>
                        <option value="fr-CA-Chirp3-HD-Zephyr">Français (Canada) - Chirp3 HD Zephyr Female (fr-CA-Chirp3-HD-Zephyr)</option>
                        <option value="fr-CA-Chirp3-HD-Zubenelgenubi">Français (Canada) - Chirp3 HD Zubenelgenubi Male (fr-CA-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="fr-CA-Neural2-A">Français (Canada) - Neural2 A Female (fr-CA-Neural2-A)</option>
                        <option value="fr-CA-Neural2-B">Français (Canada) - Neural2 B Male (fr-CA-Neural2-B)</option>
                        <option value="fr-CA-Neural2-C">Français (Canada) - Neural2 C Female (fr-CA-Neural2-C)</option>
                        <option value="fr-CA-Neural2-D">Français (Canada) - Neural2 D Male (fr-CA-Neural2-D)</option>
                        <option value="fr-CA-Standard-A">Français (Canada) - Standard A Female (fr-CA-Standard-A)</option>
                        <option value="fr-CA-Standard-B">Français (Canada) - Standard B Male (fr-CA-Standard-B)</option>
                        <option value="fr-CA-Standard-C">Français (Canada) - Standard C Female (fr-CA-Standard-C)</option>
                        <option value="fr-CA-Standard-D">Français (Canada) - Standard D Male (fr-CA-Standard-D)</option>
                        <option value="fr-CA-Wavenet-A">Français (Canada) - Wavenet A Female (fr-CA-Wavenet-A)</option>
                        <option value="fr-CA-Wavenet-B">Français (Canada) - Wavenet B Male (fr-CA-Wavenet-B)</option>
                        <option value="fr-CA-Wavenet-C">Français (Canada) - Wavenet C Female (fr-CA-Wavenet-C)</option>
                        <!-- English (US) -->
                        <option disabled>--- Anglais (US) ---</option>
                        <option value="en-US-Casual-K">Anglais (US) - Casual K Male (en-US-Casual-K)</option>
                        <option value="en-US-Chirp-HD-D">Anglais (US) - Chirp HD D Male (en-US-Chirp-HD-D)</option>
                        <option value="en-US-Chirp-HD-F">Anglais (US) - Chirp HD F Female (en-US-Chirp-HD-F)</option>
                        <option value="en-US-Chirp-HD-O">Anglais (US) - Chirp HD O Female (en-US-Chirp-HD-O)</option>
                        <option value="en-US-Chirp3-HD-Achernar">Anglais (US) - Chirp3 HD Achernar Female (en-US-Chirp3-HD-Achernar)</option>
                        <option value="en-US-Chirp3-HD-Achird">Anglais (US) - Chirp3 HD Achird Male (en-US-Chirp3-HD-Achird)</option>
                        <option value="en-US-Chirp3-HD-Algenib">Anglais (US) - Chirp3 HD Algenib Male (en-US-Chirp3-HD-Algenib)</option>
                        <option value="en-US-Chirp3-HD-Algieba">Anglais (US) - Chirp3 HD Algieba Male (en-US-Chirp3-HD-Algieba)</option>
                        <option value="en-US-Chirp3-HD-Alnilam">Anglais (US) - Chirp3 HD Alnilam Male (en-US-Chirp3-HD-Alnilam)</option>
                        <option value="en-US-Chirp3-HD-Aoede">Anglais (US) - Chirp3 HD Aoede Female (en-US-Chirp3-HD-Aoede)</option>
                        <option value="en-US-Chirp3-HD-Autonoe">Anglais (US) - Chirp3 HD Autonoe Female (en-US-Chirp3-HD-Autonoe)</option>
                        <option value="en-US-Chirp3-HD-Callirrhoe">Anglais (US) - Chirp3 HD Callirrhoe Female (en-US-Chirp3-HD-Callirrhoe)</option>
                        <option value="en-US-Chirp3-HD-Charon">Anglais (US) - Chirp3 HD Charon Male (en-US-Chirp3-HD-Charon)</option>
                        <option value="en-US-Chirp3-HD-Despina">Anglais (US) - Chirp3 HD Despina Female (en-US-Chirp3-HD-Despina)</option>
                        <option value="en-US-Chirp3-HD-Enceladus">Anglais (US) - Chirp3 HD Enceladus Male (en-US-Chirp3-HD-Enceladus)</option>
                        <option value="en-US-Chirp3-HD-Erinome">Anglais (US) - Chirp3 HD Erinome Female (en-US-Chirp3-HD-Erinome)</option>
                        <option value="en-US-Chirp3-HD-Fenrir">Anglais (US) - Chirp3 HD Fenrir Male (en-US-Chirp3-HD-Fenrir)</option>
                        <option value="en-US-Chirp3-HD-Gacrux">Anglais (US) - Chirp3 HD Gacrux Female (en-US-Chirp3-HD-Gacrux)</option>
                        <option value="en-US-Chirp3-HD-Iapetus">Anglais (US) - Chirp3 HD Iapetus Male (en-US-Chirp3-HD-Iapetus)</option>
                        <option value="en-US-Chirp3-HD-Kore">Anglais (US) - Chirp3 HD Kore Female (en-US-Chirp3-HD-Kore)</option>
                        <option value="en-US-Chirp3-HD-Laomedeia">Anglais (US) - Chirp3 HD Laomedeia Female (en-US-Chirp3-HD-Laomedeia)</option>
                        <option value="en-US-Chirp3-HD-Leda">Anglais (US) - Chirp3 HD Leda Female (en-US-Chirp3-HD-Leda)</option>
                        <option value="en-US-Chirp3-HD-Orus">Anglais (US) - Chirp3 HD Orus Male (en-US-Chirp3-HD-Orus)</option>
                        <option value="en-US-Chirp3-HD-Puck">Anglais (US) - Chirp3 HD Puck Male (en-US-Chirp3-HD-Puck)</option>
                        <option value="en-US-Chirp3-HD-Pulcherrima">Anglais (US) - Chirp3 HD Pulcherrima Female (en-US-Chirp3-HD-Pulcherrima)</option>
                        <option value="en-US-Chirp3-HD-Rasalgethi">Anglais (US) - Chirp3 HD Rasalgethi Male (en-US-Chirp3-HD-Rasalgethi)</option>
                        <option value="en-US-Chirp3-HD-Sadachbia">Anglais (US) - Chirp3 HD Sadachbia Male (en-US-Chirp3-HD-Sadachbia)</option>
                        <option value="en-US-Chirp3-HD-Sadaltager">Anglais (US) - Chirp3 HD Sadaltager Male (en-US-Chirp3-HD-Sadaltager)</option>
                        <option value="en-US-Chirp3-HD-Schedar">Anglais (US) - Chirp3 HD Schedar Male (en-US-Chirp3-HD-Schedar)</option>
                        <option value="en-US-Chirp3-HD-Sulafat">Anglais (US) - Chirp3 HD Sulafat Female (en-US-Chirp3-HD-Sulafat)</option>
                        <option value="en-US-Chirp3-HD-Umbriel">Anglais (US) - Chirp3 HD Umbriel Male (en-US-Chirp3-HD-Umbriel)</option>
                        <option value="en-US-Chirp3-HD-Vindemiatrix">Anglais (US) - Chirp3 HD Vindemiatrix Female (en-US-Chirp3-HD-Vindemiatrix)</option>
                        <option value="en-US-Chirp3-HD-Zephyr">Anglais (US) - Chirp3 HD Zephyr Female (en-US-Chirp3-HD-Zephyr)</option>
                        <option value="en-US-Chirp3-HD-Zubenelgenubi">Anglais (US) - Chirp3 HD Zubenelgenubi Male (en-US-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="en-US-Neural2-A">Anglais (US) - Neural2 A Male (en-US-Neural2-A)</option>
                        <option value="en-US-Neural2-C">Anglais (US) - Neural2 C Female (en-US-Neural2-C)</option>
                        <option value="en-US-Neural2-D">Anglais (US) - Neural2 D Male (en-US-Neural2-D)</option>
                        <option value="en-US-Neural2-E">Anglais (US) - Neural2 E Female (en-US-Neural2-E)</option>
                        <option value="en-US-Neural2-F">Anglais (US) - Neural2 F Female (en-US-Neural2-F)</option>
                        <option value="en-US-Neural2-G">Anglais (US) - Neural2 G Female (en-US-Neural2-G)</option>
                        <option value="en-US-Neural2-H">Anglais (US) - Neural2 H Female (en-US-Neural2-H)</option>
                        <option value="en-US-Neural2-I">Anglais (US) - Neural2 I Male (en-US-Neural2-I)</option>
                        <option value="en-US-Neural2-J">Anglais (US) - Neural2 J Male (en-US-Neural2-J)</option>
                        <option value="en-US-News-K">Anglais (US) - News K Female (en-US-News-K)</option>
                        <option value="en-US-News-L">Anglais (US) - News L Female (en-US-News-L)</option>
                        <option value="en-US-News-N">Anglais (US) - News N Male (en-US-News-N)</option>
                        <option value="en-US-Polyglot-1">Anglais (US) - Polyglot 1 Male (en-US-Polyglot-1)</option>
                        <option value="en-US-Standard-A">Anglais (US) - Standard A Male (en-US-Standard-A)</option>
                        <option value="en-US-Standard-B">Anglais (US) - Standard B Male (en-US-Standard-B)</option>
                        <option value="en-US-Standard-C">Anglais (US) - Standard C Female (en-US-Standard-C)</option>
                        <option value="en-US-Standard-D">Anglais (US) - Standard D Male (en-US-Standard-D)</option>
                        <option value="en-US-Standard-E">Anglais (US) - Standard E Female (en-US-Standard-E)</option>
                        <option value="en-US-Standard-F">Anglais (US) - Standard F Female (en-US-Standard-F)</option>
                        <option value="en-US-Standard-G">Anglais (US) - Standard G Female (en-US-Standard-G)</option>
                        <option value="en-US-Standard-H">Anglais (US) - Standard H Female (en-US-Standard-H)</option>
                        <option value="en-US-Standard-I">Anglais (US) - Standard I Male (en-US-Standard-I)</option>
                        <option value="en-US-Standard-J">Anglais (US) - Standard J Male (en-US-Standard-J)</option>
                        <option value="en-US-Studio-O">Anglais (US) - Studio O Female (en-US-Studio-O)</option>
                        <option value="en-US-Studio-Q">Anglais (US) - Studio Q Male (en-US-Studio-Q)</option>
                        <option value="en-US-Wavenet-A">Anglais (US) - Wavenet A Male (en-US-Wavenet-A)</option>
                        <option value="en-US-Wavenet-B">Anglais (US) - Wavenet B Male (en-US-Wavenet-B)</option>
                        <option value="en-US-Wavenet-C">Anglais (US) - Wavenet C Female (en-US-Wavenet-C)</option>
                        <option value="en-US-Wavenet-D">Anglais (US) - Wavenet D Male (en-US-Wavenet-D)</option>
                        <option value="en-US-Wavenet-E">Anglais (US) - Wavenet E Female (en-US-Wavenet-E)</option>
                        <option value="en-US-Wavenet-F">Anglais (US) - Wavenet F Female (en-US-Wavenet-F)</option>
                        <option value="en-US-Wavenet-G">Anglais (US) - Wavenet G Female (en-US-Wavenet-G)</option>
                        <option value="en-US-Wavenet-H">Anglais (US) - Wavenet H Female (en-US-Wavenet-H)</option>
                        <option value="en-US-Wavenet-I">Anglais (US) - Wavenet I Male (en-US-Wavenet-I)</option>
                        <option value="en-US-Wavenet-J">Anglais (US) - Wavenet J Male (en-US-Wavenet-J)</option>
                        <!-- English (GB) -->
                        <option disabled>--- Anglais (GB) ---</option>
                        <option value="en-GB-Chirp-HD-D">Anglais (GB) - Chirp HD D Male (en-GB-Chirp-HD-D)</option>
                        <option value="en-GB-Chirp-HD-F">Anglais (GB) - Chirp HD F Female (en-GB-Chirp-HD-F)</option>
                        <option value="en-GB-Chirp-HD-O">Anglais (GB) - Chirp HD O Female (en-GB-Chirp-HD-O)</option>
                        <option value="en-GB-Chirp3-HD-Achernar">Anglais (GB) - Chirp3 HD Achernar Female (en-GB-Chirp3-HD-Achernar)</option>
                        <option value="en-GB-Chirp3-HD-Achird">Anglais (GB) - Chirp3 HD Achird Male (en-GB-Chirp3-HD-Achird)</option>
                        <option value="en-GB-Chirp3-HD-Algenib">Anglais (GB) - Chirp3 HD Algenib Male (en-GB-Chirp3-HD-Algenib)</option>
                        <option value="en-GB-Chirp3-HD-Algieba">Anglais (GB) - Chirp3 HD Algieba Male (en-GB-Chirp3-HD-Algieba)</option>
                        <option value="en-GB-Chirp3-HD-Alnilam">Anglais (GB) - Chirp3 HD Alnilam Male (en-GB-Chirp3-HD-Alnilam)</option>
                        <option value="en-GB-Chirp3-HD-Aoede">Anglais (GB) - Chirp3 HD Aoede Female (en-GB-Chirp3-HD-Aoede)</option>
                        <option value="en-GB-Chirp3-HD-Autonoe">Anglais (GB) - Chirp3 HD Autonoe Female (en-GB-Chirp3-HD-Autonoe)</option>
                        <option value="en-GB-Chirp3-HD-Callirrhoe">Anglais (GB) - Chirp3 HD Callirrhoe Female (en-GB-Chirp3-HD-Callirrhoe)</option>
                        <option value="en-GB-Chirp3-HD-Charon">Anglais (GB) - Chirp3 HD Charon Male (en-GB-Chirp3-HD-Charon)</option>
                        <option value="en-GB-Chirp3-HD-Despina">Anglais (GB) - Chirp3 HD Despina Female (en-GB-Chirp3-HD-Despina)</option>
                        <option value="en-GB-Chirp3-HD-Enceladus">Anglais (GB) - Chirp3 HD Enceladus Male (en-GB-Chirp3-HD-Enceladus)</option>
                        <option value="en-GB-Chirp3-HD-Erinome">Anglais (GB) - Chirp3 HD Erinome Female (en-GB-Chirp3-HD-Erinome)</option>
                        <option value="en-GB-Chirp3-HD-Fenrir">Anglais (GB) - Chirp3 HD Fenrir Male (en-GB-Chirp3-HD-Fenrir)</option>
                        <option value="en-GB-Chirp3-HD-Gacrux">Anglais (GB) - Chirp3 HD Gacrux Female (en-GB-Chirp3-HD-Gacrux)</option>
                        <option value="en-GB-Chirp3-HD-Iapetus">Anglais (GB) - Chirp3 HD Iapetus Male (en-GB-Chirp3-HD-Iapetus)</option>
                        <option value="en-GB-Chirp3-HD-Kore">Anglais (GB) - Chirp3 HD Kore Female (en-GB-Chirp3-HD-Kore)</option>
                        <option value="en-GB-Chirp3-HD-Laomedeia">Anglais (GB) - Chirp3 HD Laomedeia Female (en-GB-Chirp3-HD-Laomedeia)</option>
                        <option value="en-GB-Chirp3-HD-Leda">Anglais (GB) - Chirp3 HD Leda Female (en-GB-Chirp3-HD-Leda)</option>
                        <option value="en-GB-Chirp3-HD-Orus">Anglais (GB) - Chirp3 HD Orus Male (en-GB-Chirp3-HD-Orus)</option>
                        <option value="en-GB-Chirp3-HD-Puck">Anglais (GB) - Chirp3 HD Puck Male (en-GB-Chirp3-HD-Puck)</option>
                        <option value="en-GB-Chirp3-HD-Pulcherrima">Anglais (GB) - Chirp3 HD Pulcherrima Female (en-GB-Chirp3-HD-Pulcherrima)</option>
                        <option value="en-GB-Chirp3-HD-Rasalgethi">Anglais (GB) - Chirp3 HD Rasalgethi Male (en-GB-Chirp3-HD-Rasalgethi)</option>
                        <option value="en-GB-Chirp3-HD-Sadachbia">Anglais (GB) - Chirp3 HD Sadachbia Male (en-GB-Chirp3-HD-Sadachbia)</option>
                        <option value="en-GB-Chirp3-HD-Sadaltager">Anglais (GB) - Chirp3 HD Sadaltager Male (en-GB-Chirp3-HD-Sadaltager)</option>
                        <option value="en-GB-Chirp3-HD-Schedar">Anglais (GB) - Chirp3 HD Schedar Male (en-GB-Chirp3-HD-Schedar)</option>
                        <option value="en-GB-Chirp3-HD-Sulafat">Anglais (GB) - Chirp3 HD Sulafat Female (en-GB-Chirp3-HD-Sulafat)</option>
                        <option value="en-GB-Chirp3-HD-Umbriel">Anglais (GB) - Chirp3 HD Umbriel Male (en-GB-Chirp3-HD-Umbriel)</option>
                        <option value="en-GB-Chirp3-HD-Vindemiatrix">Anglais (GB) - Chirp3 HD Vindemiatrix Female (en-GB-Chirp3-HD-Vindemiatrix)</option>
                        <option value="en-GB-Chirp3-HD-Zephyr">Anglais (GB) - Chirp3 HD Zephyr Female (en-GB-Chirp3-HD-Zephyr)</option>
                        <option value="en-GB-Chirp3-HD-Zubenelgenubi">Anglais (GB) - Chirp3 HD Zubenelgenubi Male (en-GB-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="en-GB-Neural2-A">Anglais (GB) - Neural2 A Female (en-GB-Neural2-A)</option>
                        <option value="en-GB-Neural2-B">Anglais (GB) - Neural2 B Male (en-GB-Neural2-B)</option>
                        <option value="en-GB-Neural2-C">Anglais (GB) - Neural2 C Female (en-GB-Neural2-C)</option>
                        <option value="en-GB-Neural2-D">Anglais (GB) - Neural2 D Male (en-GB-Neural2-D)</option>
                        <option value="en-GB-Neural2-F">Anglais (GB) - Neural2 F Female (en-GB-Neural2-F)</option>
                        <option value="en-GB-Neural2-N">Anglais (GB) - Neural2 N Female (en-GB-Neural2-N)</option>
                        <option value="en-GB-Neural2-O">Anglais (GB) - Neural2 O Male (en-GB-Neural2-O)</option>
                        <option value="en-GB-News-G">Anglais (GB) - News G Female (en-GB-News-G)</option>
                        <option value="en-GB-News-H">Anglais (GB) - News H Female (en-GB-News-H)</option>
                        <option value="en-GB-News-I">Anglais (GB) - News I Female (en-GB-News-I)</option>
                        <option value="en-GB-News-J">Anglais (GB) - News J Male (en-GB-News-J)</option>
                        <option value="en-GB-News-K">Anglais (GB) - News K Male (en-GB-News-K)</option>
                        <option value="en-GB-News-L">Anglais (GB) - News L Male (en-GB-News-L)</option>
                        <option value="en-GB-News-M">Anglais (GB) - News M Male (en-GB-News-M)</option>
                        <option value="en-GB-Standard-A">Anglais (GB) - Standard A Female (en-GB-Standard-A)</option>
                        <option value="en-GB-Standard-B">Anglais (GB) - Standard B Male (en-GB-Standard-B)</option>
                        <option value="en-GB-Standard-C">Anglais (GB) - Standard C Female (en-GB-Standard-C)</option>
                        <option value="en-GB-Standard-D">Anglais (GB) - Standard D Male (en-GB-Standard-D)</option>
                        <option value="en-GB-Standard-F">Anglais (GB) - Standard F Female (en-GB-Standard-F)</option>
                        <option value="en-GB-Standard-N">Anglais (GB) - Standard N Female (en-GB-Standard-N)</option>
                        <option value="en-GB-Standard-O">Anglais (GB) - Standard O Male (en-GB-Standard-O)</option>
                        <option value="en-GB-Studio-B">Anglais (GB) - Studio B Male (en-GB-Studio-B)</option>
                        <option value="en-GB-Studio-C">Anglais (GB) - Studio C Female (en-GB-Studio-C)</option>
                        <option value="en-GB-Wavenet-A">Anglais (GB) - Wavenet A Female (en-GB-Wavenet-A)</option>
                        <option value="en-GB-Wavenet-B">Anglais (GB) - Wavenet B Male (en-GB-Wavenet-B)</option>
                        <option value="en-GB-Wavenet-C">Anglais (GB) - Wavenet C Female (en-GB-Wavenet-C)</option>
                        <option value="en-GB-Wavenet-D">Anglais (GB) - Wavenet D Male (en-GB-Wavenet-D)</option>
                        <option value="en-GB-Wavenet-F">Anglais (GB) - Wavenet F Female (en-GB-Wavenet-F)</option>
                        <option value="en-GB-Wavenet-N">Anglais (GB) - Wavenet N Female (en-GB-Wavenet-N)</option>
                        <option value="en-GB-Wavenet-O">Anglais (GB) - Wavenet O Male (en-GB-Wavenet-O)</option>
                        <!-- Italian -->
                        <option disabled>--- Italien (Italie) ---</option>
                        <option value="it-IT-Chirp-HD-D">Italien (Italie) - Chirp HD D Male (it-IT-Chirp-HD-D)</option>
                        <option value="it-IT-Chirp-HD-F">Italien (Italie) - Chirp HD F Female (it-IT-Chirp-HD-F)</option>
                        <option value="it-IT-Chirp-HD-O">Italien (Italie) - Chirp HD O Female (it-IT-Chirp-HD-O)</option>
                        <option value="it-IT-Chirp3-HD-Achernar">Italien (Italie) - Chirp3 HD Achernar Female (it-IT-Chirp3-HD-Achernar)</option>
                        <option value="it-IT-Chirp3-HD-Achird">Italien (Italie) - Chirp3 HD Achird Male (it-IT-Chirp3-HD-Achird)</option>
                        <option value="it-IT-Chirp3-HD-Algenib">Italien (Italie) - Chirp3 HD Algenib Male (it-IT-Chirp3-HD-Algenib)</option>
                        <option value="it-IT-Chirp3-HD-Algieba">Italien (Italie) - Chirp3 HD Algieba Male (it-IT-Chirp3-HD-Algieba)</option>
                        <option value="it-IT-Chirp3-HD-Alnilam">Italien (Italie) - Chirp3 HD Alnilam Male (it-IT-Chirp3-HD-Alnilam)</option>
                        <option value="it-IT-Chirp3-HD-Aoede">Italien (Italie) - Chirp3 HD Aoede Female (it-IT-Chirp3-HD-Aoede)</option>
                        <option value="it-IT-Chirp3-HD-Autonoe">Italien (Italie) - Chirp3 HD Autonoe Female (it-IT-Chirp3-HD-Autonoe)</option>
                        <option value="it-IT-Chirp3-HD-Callirrhoe">Italien (Italie) - Chirp3 HD Callirrhoe Female (it-IT-Chirp3-HD-Callirrhoe)</option>
                        <option value="it-IT-Chirp3-HD-Charon">Italien (Italie) - Chirp3 HD Charon Male (it-IT-Chirp3-HD-Charon)</option>
                        <option value="it-IT-Chirp3-HD-Despina">Italien (Italie) - Chirp3 HD Despina Female (it-IT-Chirp3-HD-Despina)</option>
                        <option value="it-IT-Chirp3-HD-Enceladus">Italien (Italie) - Chirp3 HD Enceladus Male (it-IT-Chirp3-HD-Enceladus)</option>
                        <option value="it-IT-Chirp3-HD-Erinome">Italien (Italie) - Chirp3 HD Erinome Female (it-IT-Chirp3-HD-Erinome)</option>
                        <option value="it-IT-Chirp3-HD-Fenrir">Italien (Italie) - Chirp3 HD Fenrir Male (it-IT-Chirp3-HD-Fenrir)</option>
                        <option value="it-IT-Chirp3-HD-Gacrux">Italien (Italie) - Chirp3 HD Gacrux Female (it-IT-Chirp3-HD-Gacrux)</option>
                        <option value="it-IT-Chirp3-HD-Iapetus">Italien (Italie) - Chirp3 HD Iapetus Male (it-IT-Chirp3-HD-Iapetus)</option>
                        <option value="it-IT-Chirp3-HD-Kore">Italien (Italie) - Chirp3 HD Kore Female (it-IT-Chirp3-HD-Kore)</option>
                        <option value="it-IT-Chirp3-HD-Laomedeia">Italien (Italie) - Chirp3 HD Laomedeia Female (it-IT-Chirp3-HD-Laomedeia)</option>
                        <option value="it-IT-Chirp3-HD-Leda">Italien (Italie) - Chirp3 HD Leda Female (it-IT-Chirp3-HD-Leda)</option>
                        <option value="it-IT-Chirp3-HD-Orus">Italien (Italie) - Chirp3 HD Orus Male (it-IT-Chirp3-HD-Orus)</option>
                        <option value="it-IT-Chirp3-HD-Puck">Italien (Italie) - Chirp3 HD Puck Male (it-IT-Chirp3-HD-Puck)</option>
                        <option value="it-IT-Chirp3-HD-Pulcherrima">Italien (Italie) - Chirp3 HD Pulcherrima Female (it-IT-Chirp3-HD-Pulcherrima)</option>
                        <option value="it-IT-Chirp3-HD-Rasalgethi">Italien (Italie) - Chirp3 HD Rasalgethi Male (it-IT-Chirp3-HD-Rasalgethi)</option>
                        <option value="it-IT-Chirp3-HD-Sadachbia">Italien (Italie) - Chirp3 HD Sadachbia Male (it-IT-Chirp3-HD-Sadachbia)</option>
                        <option value="it-IT-Chirp3-HD-Sadaltager">Italien (Italie) - Chirp3 HD Sadaltager Male (it-IT-Chirp3-HD-Sadaltager)</option>
                        <option value="it-IT-Chirp3-HD-Schedar">Italien (Italie) - Chirp3 HD Schedar Male (it-IT-Chirp3-HD-Schedar)</option>
                        <option value="it-IT-Chirp3-HD-Sulafat">Italien (Italie) - Chirp3 HD Sulafat Female (it-IT-Chirp3-HD-Sulafat)</option>
                        <option value="it-IT-Chirp3-HD-Umbriel">Italien (Italie) - Chirp3 HD Umbriel Male (it-IT-Chirp3-HD-Umbriel)</option>
                        <option value="it-IT-Chirp3-HD-Vindemiatrix">Italien (Italie) - Chirp3 HD Vindemiatrix Female (it-IT-Chirp3-HD-Vindemiatrix)</option>
                        <option value="it-IT-Chirp3-HD-Zephyr">Italien (Italie) - Chirp3 HD Zephyr Female (it-IT-Chirp3-HD-Zephyr)</option>
                        <option value="it-IT-Chirp3-HD-Zubenelgenubi">Italien (Italie) - Chirp3 HD Zubenelgenubi Male (it-IT-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="it-IT-Neural2-A">Italien (Italie) - Neural2 A Female (it-IT-Neural2-A)</option>
                        <option value="it-IT-Neural2-E">Italien (Italie) - Neural2 E Female (it-IT-Neural2-E)</option>
                        <option value="it-IT-Neural2-F">Italien (Italie) - Neural2 F Male (it-IT-Neural2-F)</option>
                        <option value="it-IT-Standard-E">Italien (Italie) - Standard E Female (it-IT-Standard-E)</option>
                        <option value="it-IT-Standard-F">Italien (Italie) - Standard F Male (it-IT-Standard-F)</option>
                        <option value="it-IT-Wavenet-E">Italien (Italie) - Wavenet E Female (it-IT-Wavenet-E)</option>
                        <option value="it-IT-Wavenet-F">Italien (Italie) - Wavenet F Male (it-IT-Wavenet-F)</option>
                        <!-- Spanish (Espagne) -->
                        <option disabled>--- Espagnol (Espagne) ---</option>
                        <option value="es-ES-Chirp-HD-D">Espagnol (Espagne) - Chirp HD D Male (es-ES-Chirp-HD-D)</option>
                        <option value="es-ES-Chirp-HD-F">Espagnol (Espagne) - Chirp HD F Female (es-ES-Chirp-HD-F)</option>
                        <option value="es-ES-Chirp-HD-O">Espagnol (Espagne) - Chirp HD O Female (es-ES-Chirp-HD-O)</option>
                        <option value="es-ES-Chirp3-HD-Achernar">Espagnol (Espagne) - Chirp3 HD Achernar Female (es-ES-Chirp3-HD-Achernar)</option>
                        <option value="es-ES-Chirp3-HD-Achird">Espagnol (Espagne) - Chirp3 HD Achird Male (es-ES-Chirp3-HD-Achird)</option>
                        <option value="es-ES-Chirp3-HD-Algenib">Espagnol (Espagne) - Chirp3 HD Algenib Male (es-ES-Chirp3-HD-Algenib)</option>
                        <option value="es-ES-Chirp3-HD-Algieba">Espagnol (Espagne) - Chirp3 HD Algieba Male (es-ES-Chirp3-HD-Algieba)</option>
                        <option value="es-ES-Chirp3-HD-Alnilam">Espagnol (Espagne) - Chirp3 HD Alnilam Male (es-ES-Chirp3-HD-Alnilam)</option>
                        <option value="es-ES-Chirp3-HD-Aoede">Espagnol (Espagne) - Chirp3 HD Aoede Female (es-ES-Chirp3-HD-Aoede)</option>
                        <option value="es-ES-Chirp3-HD-Autonoe">Espagnol (Espagne) - Chirp3 HD Autonoe Female (es-ES-Chirp3-HD-Autonoe)</option>
                        <option value="es-ES-Chirp3-HD-Callirrhoe">Espagnol (Espagne) - Chirp3 HD Callirrhoe Female (es-ES-Chirp3-HD-Callirrhoe)</option>
                        <option value="es-ES-Chirp3-HD-Charon">Espagnol (Espagne) - Chirp3 HD Charon Male (es-ES-Chirp3-HD-Charon)</option>
                        <option value="es-ES-Chirp3-HD-Despina">Espagnol (Espagne) - Chirp3 HD Despina Female (es-ES-Chirp3-HD-Despina)</option>
                        <option value="es-ES-Chirp3-HD-Enceladus">Espagnol (Espagne) - Chirp3 HD Enceladus Male (es-ES-Chirp3-HD-Enceladus)</option>
                        <option value="es-ES-Chirp3-HD-Erinome">Espagnol (Espagne) - Chirp3 HD Erinome Female (es-ES-Chirp3-HD-Erinome)</option>
                        <option value="es-ES-Chirp3-HD-Fenrir">Espagnol (Espagne) - Chirp3 HD Fenrir Male (es-ES-Chirp3-HD-Fenrir)</option>
                        <option value="es-ES-Chirp3-HD-Gacrux">Espagnol (Espagne) - Chirp3 HD Gacrux Female (es-ES-Chirp3-HD-Gacrux)</option>
                        <option value="es-ES-Chirp3-HD-Iapetus">Espagnol (Espagne) - Chirp3 HD Iapetus Male (es-ES-Chirp3-HD-Iapetus)</option>
                        <option value="es-ES-Chirp3-HD-Kore">Espagnol (Espagne) - Chirp3 HD Kore Female (es-ES-Chirp3-HD-Kore)</option>
                        <option value="es-ES-Chirp3-HD-Laomedeia">Espagnol (Espagne) - Chirp3 HD Laomedeia Female (es-ES-Chirp3-HD-Laomedeia)</option>
                        <option value="es-ES-Chirp3-HD-Leda">Espagnol (Espagne) - Chirp3 HD Leda Female (es-ES-Chirp3-HD-Leda)</option>
                        <option value="es-ES-Chirp3-HD-Orus">Espagnol (Espagne) - Chirp3 HD Orus Male (es-ES-Chirp3-HD-Orus)</option>
                        <option value="es-ES-Chirp3-HD-Puck">Espagnol (Espagne) - Chirp3 HD Puck Male (es-ES-Chirp3-HD-Puck)</option>
                        <option value="es-ES-Chirp3-HD-Pulcherrima">Espagnol (Espagne) - Chirp3 HD Pulcherrima Female (es-ES-Chirp3-HD-Pulcherrima)</option>
                        <option value="es-ES-Chirp3-HD-Rasalgethi">Espagnol (Espagne) - Chirp3 HD Rasalgethi Male (es-ES-Chirp3-HD-Rasalgethi)</option>
                        <option value="es-ES-Chirp3-HD-Sadachbia">Espagnol (Espagne) - Chirp3 HD Sadachbia Male (es-ES-Chirp3-HD-Sadachbia)</option>
                        <option value="es-ES-Chirp3-HD-Sadaltager">Espagnol (Espagne) - Chirp3 HD Sadaltager Male (es-ES-Chirp3-HD-Sadaltager)</option>
                        <option value="es-ES-Chirp3-HD-Schedar">Espagnol (Espagne) - Chirp3 HD Schedar Male (es-ES-Chirp3-HD-Schedar)</option>
                        <option value="es-ES-Chirp3-HD-Sulafat">Espagnol (Espagne) - Chirp3 HD Sulafat Female (es-ES-Chirp3-HD-Sulafat)</option>
                        <option value="es-ES-Chirp3-HD-Umbriel">Espagnol (Espagne) - Chirp3 HD Umbriel Male (es-ES-Chirp3-HD-Umbriel)</option>
                        <option value="es-ES-Chirp3-HD-Vindemiatrix">Espagnol (Espagne) - Chirp3 HD Vindemiatrix Female (es-ES-Chirp3-HD-Vindemiatrix)</option>
                        <option value="es-ES-Chirp3-HD-Zephyr">Espagnol (Espagne) - Chirp3 HD Zephyr Female (es-ES-Chirp3-HD-Zephyr)</option>
                        <option value="es-ES-Chirp3-HD-Zubenelgenubi">Espagnol (Espagne) - Chirp3 HD Zubenelgenubi Male (es-ES-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="es-ES-Neural2-A">Espagnol (Espagne) - Neural2 A Female (es-ES-Neural2-A)</option>
                        <option value="es-ES-Neural2-E">Espagnol (Espagne) - Neural2 E Female (es-ES-Neural2-E)</option>
                        <option value="es-ES-Neural2-F">Espagnol (Espagne) - Neural2 F Male (es-ES-Neural2-F)</option>
                        <option value="es-ES-Neural2-G">Espagnol (Espagne) - Neural2 G Male (es-ES-Neural2-G)</option>
                        <option value="es-ES-Neural2-H">Espagnol (Espagne) - Neural2 H Female (es-ES-Neural2-H)</option>
                        <option value="es-ES-Polyglot-1">Espagnol (Espagne) - Polyglot 1 Male (es-ES-Polyglot-1)</option>
                        <option value="es-ES-Standard-E">Espagnol (Espagne) - Standard E Male (es-ES-Standard-E)</option>
                        <option value="es-ES-Standard-F">Espagnol (Espagne) - Standard F Female (es-ES-Standard-F)</option>
                        <option value="es-ES-Standard-G">Espagnol (Espagne) - Standard G Male (es-ES-Standard-G)</option>
                        <option value="es-ES-Standard-H">Espagnol (Espagne) - Standard H Female (es-ES-Standard-H)</option>
                        <option value="es-ES-Studio-C">Espagnol (Espagne) - Studio C Female (es-ES-Studio-C)</option>
                        <option value="es-ES-Studio-F">Espagnol (Espagne) - Studio F Male (es-ES-Studio-F)</option>
                        <option value="es-ES-Wavenet-E">Espagnol (Espagne) - Wavenet E Male (es-ES-Wavenet-E)</option>
                        <option value="es-ES-Wavenet-F">Espagnol (Espagne) - Wavenet F Female (es-ES-Wavenet-F)</option>
                        <option value="es-ES-Wavenet-G">Espagnol (Espagne) - Wavenet G Male (es-ES-Wavenet-G)</option>
                        <option value="es-ES-Wavenet-H">Espagnol (Espagne) - Wavenet H Female (es-ES-Wavenet-H)</option>
                        <!-- Deutsch (Allemagne) -->
                        <option disabled>--- Allemand (Allemagne) ---</option>
                        <option value="de-DE-Chirp-HD-D">Allemand (Allemagne) - Chirp HD D Male (de-DE-Chirp-HD-D)</option>
                        <option value="de-DE-Chirp-HD-F">Allemand (Allemagne) - Chirp HD F Female (de-DE-Chirp-HD-F)</option>
                        <option value="de-DE-Chirp-HD-O">Allemand (Allemagne) - Chirp HD O Female (de-DE-Chirp-HD-O)</option>
                        <option value="de-DE-Chirp3-HD-Achernar">Allemand (Allemagne) - Chirp3 HD Achernar Female (de-DE-Chirp3-HD-Achernar)</option>
                        <option value="de-DE-Chirp3-HD-Achird">Allemand (Allemagne) - Chirp3 HD Achird Male (de-DE-Chirp3-HD-Achird)</option>
                        <option value="de-DE-Chirp3-HD-Algenib">Allemand (Allemagne) - Chirp3 HD Algenib Male (de-DE-Chirp3-HD-Algenib)</option>
                        <option value="de-DE-Chirp3-HD-Algieba">Allemand (Allemagne) - Chirp3 HD Algieba Male (de-DE-Chirp3-HD-Algieba)</option>
                        <option value="de-DE-Chirp3-HD-Alnilam">Allemand (Allemagne) - Chirp3 HD Alnilam Male (de-DE-Chirp3-HD-Alnilam)</option>
                        <option value="de-DE-Chirp3-HD-Aoede">Allemand (Allemagne) - Chirp3 HD Aoede Female (de-DE-Chirp3-HD-Aoede)</option>
                        <option value="de-DE-Chirp3-HD-Autonoe">Allemand (Allemagne) - Chirp3 HD Autonoe Female (de-DE-Chirp3-HD-Autonoe)</option>
                        <option value="de-DE-Chirp3-HD-Callirrhoe">Allemand (Allemagne) - Chirp3 HD Callirrhoe Female (de-DE-Chirp3-HD-Callirrhoe)</option>
                        <option value="de-DE-Chirp3-HD-Charon">Allemand (Allemagne) - Chirp3 HD Charon Male (de-DE-Chirp3-HD-Charon)</option>
                        <option value="de-DE-Chirp3-HD-Despina">Allemand (Allemagne) - Chirp3 HD Despina Female (de-DE-Chirp3-HD-Despina)</option>
                        <option value="de-DE-Chirp3-HD-Enceladus">Allemand (Allemagne) - Chirp3 HD Enceladus Male (de-DE-Chirp3-HD-Enceladus)</option>
                        <option value="de-DE-Chirp3-HD-Erinome">Allemand (Allemagne) - Chirp3 HD Erinome Female (de-DE-Chirp3-HD-Erinome)</option>
                        <option value="de-DE-Chirp3-HD-Fenrir">Allemand (Allemagne) - Chirp3 HD Fenrir Male (de-DE-Chirp3-HD-Fenrir)</option>
                        <option value="de-DE-Chirp3-HD-Gacrux">Allemand (Allemagne) - Chirp3 HD Gacrux Female (de-DE-Chirp3-HD-Gacrux)</option>
                        <option value="de-DE-Chirp3-HD-Iapetus">Allemand (Allemagne) - Chirp3 HD Iapetus Male (de-DE-Chirp3-HD-Iapetus)</option>
                        <option value="de-DE-Chirp3-HD-Kore">Allemand (Allemagne) - Chirp3 HD Kore Female (de-DE-Chirp3-HD-Kore)</option>
                        <option value="de-DE-Chirp3-HD-Laomedeia">Allemand (Allemagne) - Chirp3 HD Laomedeia Female (de-DE-Chirp3-HD-Laomedeia)</option>
                        <option value="de-DE-Chirp3-HD-Leda">Allemand (Allemagne) - Chirp3 HD Leda Female (de-DE-Chirp3-HD-Leda)</option>
                        <option value="de-DE-Chirp3-HD-Orus">Allemand (Allemagne) - Chirp3 HD Orus Male (de-DE-Chirp3-HD-Orus)</option>
                        <option value="de-DE-Chirp3-HD-Puck">Allemand (Allemagne) - Chirp3 HD Puck Male (de-DE-Chirp3-HD-Puck)</option>
                        <option value="de-DE-Chirp3-HD-Pulcherrima">Allemand (Allemagne) - Chirp3 HD Pulcherrima Female (de-DE-Chirp3-HD-Pulcherrima)</option>
                        <option value="de-DE-Chirp3-HD-Rasalgethi">Allemand (Allemagne) - Chirp3 HD Rasalgethi Male (de-DE-Chirp3-HD-Rasalgethi)</option>
                        <option value="de-DE-Chirp3-HD-Sadachbia">Allemand (Allemagne) - Chirp3 HD Sadachbia Male (de-DE-Chirp3-HD-Sadachbia)</option>
                        <option value="de-DE-Chirp3-HD-Sadaltager">Allemand (Allemagne) - Chirp3 HD Sadaltager Male (de-DE-Chirp3-HD-Sadaltager)</option>
                        <option value="de-DE-Chirp3-HD-Schedar">Allemand (Allemagne) - Chirp3 HD Schedar Male (de-DE-Chirp3-HD-Schedar)</option>
                        <option value="de-DE-Chirp3-HD-Sulafat">Allemand (Allemagne) - Chirp3 HD Sulafat Female (de-DE-Chirp3-HD-Sulafat)</option>
                        <option value="de-DE-Chirp3-HD-Umbriel">Allemand (Allemagne) - Chirp3 HD Umbriel Male (de-DE-Chirp3-HD-Umbriel)</option>
                        <option value="de-DE-Chirp3-HD-Vindemiatrix">Allemand (Allemagne) - Chirp3 HD Vindemiatrix Female (de-DE-Chirp3-HD-Vindemiatrix)</option>
                        <option value="de-DE-Chirp3-HD-Zephyr">Allemand (Allemagne) - Chirp3 HD Zephyr Female (de-DE-Chirp3-HD-Zephyr)</option>
                        <option value="de-DE-Chirp3-HD-Zubenelgenubi">Allemand (Allemagne) - Chirp3 HD Zubenelgenubi Male (de-DE-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="de-DE-Neural2-G">Allemand (Allemagne) - Neural2 G Female (de-DE-Neural2-G)</option>
                        <option value="de-DE-Neural2-H">Allemand (Allemagne) - Neural2 H Male (de-DE-Neural2-H)</option>
                        <option value="de-DE-Polyglot-1">Allemand (Allemagne) - Polyglot 1 Male (de-DE-Polyglot-1)</option>
                        <option value="de-DE-Standard-G">Allemand (Allemagne) - Standard G Female (de-DE-Standard-G)</option>
                        <option value="de-DE-Standard-H">Allemand (Allemagne) - Standard H Male (de-DE-Standard-H)</option>
                        <option value="de-DE-Studio-B">Allemand (Allemagne) - Studio B Male (de-DE-Studio-B)</option>
                        <option value="de-DE-Studio-C">Allemand (Allemagne) - Studio C Female (de-DE-Studio-C)</option>
                        <option value="de-DE-Wavenet-G">Allemand (Allemagne) - Wavenet G Female (de-DE-Wavenet-G)</option>
                        <option value="de-DE-Wavenet-H">Allemand (Allemagne) - Wavenet H Male (de-DE-Wavenet-H)</option>
                        <!-- Néerlandais (Belgique) -->
                        <option disabled>--- Néerlandais (Belgique) ---</option>
                        <option value="nl-BE-Chirp3-HD-Achernar">Néerlandais (Belgique) - Chirp3 HD Achernar Female (nl-BE-Chirp3-HD-Achernar)</option>
                        <option value="nl-BE-Chirp3-HD-Achird">Néerlandais (Belgique) - Chirp3 HD Achird Male (nl-BE-Chirp3-HD-Achird)</option>
                        <option value="nl-BE-Chirp3-HD-Algenib">Néerlandais (Belgique) - Chirp3 HD Algenib Male (nl-BE-Chirp3-HD-Algenib)</option>
                        <option value="nl-BE-Chirp3-HD-Algieba">Néerlandais (Belgique) - Chirp3 HD Algieba Male (nl-BE-Chirp3-HD-Algieba)</option>
                        <option value="nl-BE-Chirp3-HD-Alnilam">Néerlandais (Belgique) - Chirp3 HD Alnilam Male (nl-BE-Chirp3-HD-Alnilam)</option>
                        <option value="nl-BE-Chirp3-HD-Aoede">Néerlandais (Belgique) - Chirp3 HD Aoede Female (nl-BE-Chirp3-HD-Aoede)</option>
                        <option value="nl-BE-Chirp3-HD-Autonoe">Néerlandais (Belgique) - Chirp3 HD Autonoe Female (nl-BE-Chirp3-HD-Autonoe)</option>
                        <option value="nl-BE-Chirp3-HD-Callirrhoe">Néerlandais (Belgique) - Chirp3 HD Callirrhoe Female (nl-BE-Chirp3-HD-Callirrhoe)</option>
                        <option value="nl-BE-Chirp3-HD-Despina">Néerlandais (Belgique) - Chirp3 HD Despina Female (nl-BE-Chirp3-HD-Despina)</option>
                        <option value="nl-BE-Chirp3-HD-Enceladus">Néerlandais (Belgique) - Chirp3 HD Enceladus Male (nl-BE-Chirp3-HD-Enceladus)</option>
                        <option value="nl-BE-Chirp3-HD-Erinome">Néerlandais (Belgique) - Chirp3 HD Erinome Female (nl-BE-Chirp3-HD-Erinome)</option>
                        <option value="nl-BE-Chirp3-HD-Fenrir">Néerlandais (Belgique) - Chirp3 HD Fenrir Male (nl-BE-Chirp3-HD-Fenrir)</option>
                        <option value="nl-BE-Chirp3-HD-Gacrux">Néerlandais (Belgique) - Chirp3 HD Gacrux Female (nl-BE-Chirp3-HD-Gacrux)</option>
                        <option value="nl-BE-Chirp3-HD-Iapetus">Néerlandais (Belgique) - Chirp3 HD Iapetus Male (nl-BE-Chirp3-HD-Iapetus)</option>
                        <option value="nl-BE-Chirp3-HD-Kore">Néerlandais (Belgique) - Chirp3 HD Kore Female (nl-BE-Chirp3-HD-Kore)</option>
                        <option value="nl-BE-Chirp3-HD-Laomedeia">Néerlandais (Belgique) - Chirp3 HD Laomedeia Female (nl-BE-Chirp3-HD-Laomedeia)</option>
                        <option value="nl-BE-Chirp3-HD-Leda">Néerlandais (Belgique) - Chirp3 HD Leda Female (nl-BE-Chirp3-HD-Leda)</option>
                        <option value="nl-BE-Chirp3-HD-Orus">Néerlandais (Belgique) - Chirp3 HD Orus Male (nl-BE-Chirp3-HD-Orus)</option>
                        <option value="nl-BE-Chirp3-HD-Puck">Néerlandais (Belgique) - Chirp3 HD Puck Male (nl-BE-Chirp3-HD-Puck)</option>
                        <option value="nl-BE-Chirp3-HD-Pulcherrima">Néerlandais (Belgique) - Chirp3 HD Pulcherrima Female (nl-BE-Chirp3-HD-Pulcherrima)</option>
                        <option value="nl-BE-Chirp3-HD-Rasalgethi">Néerlandais (Belgique) - Chirp3 HD Rasalgethi Male (nl-BE-Chirp3-HD-Rasalgethi)</option>
                        <option value="nl-BE-Chirp3-HD-Sadachbia">Néerlandais (Belgique) - Chirp3 HD Sadachbia Male (nl-BE-Chirp3-HD-Sadachbia)</option>
                        <option value="nl-BE-Chirp3-HD-Sadaltager">Néerlandais (Belgique) - Chirp3 HD Sadaltager Male (nl-BE-Chirp3-HD-Sadaltager)</option>
                        <option value="nl-BE-Chirp3-HD-Schedar">Néerlandais (Belgique) - Chirp3 HD Schedar Male (nl-BE-Chirp3-HD-Schedar)</option>
                        <option value="nl-BE-Chirp3-HD-Sulafat">Néerlandais (Belgique) - Chirp3 HD Sulafat Female (nl-BE-Chirp3-HD-Sulafat)</option>
                        <option value="nl-BE-Chirp3-HD-Umbriel">Néerlandais (Belgique) - Chirp3 HD Umbriel Male (nl-BE-Chirp3-HD-Umbriel)</option>
                        <option value="nl-BE-Chirp3-HD-Vindemiatrix">Néerlandais (Belgique) - Chirp3 HD Vindemiatrix Female (nl-BE-Chirp3-HD-Vindemiatrix)</option>
                        <option value="nl-BE-Chirp3-HD-Zephyr">Néerlandais (Belgique) - Chirp3 HD Zephyr Female (nl-BE-Chirp3-HD-Zephyr)</option>
                        <option value="nl-BE-Chirp3-HD-Zubenelgenubi">Néerlandais (Belgique) - Chirp3 HD Zubenelgenubi Male (nl-BE-Chirp3-HD-Zubenelgenubi)</option>
                        <option value="nl-BE-Standard-C">Néerlandais (Belgique) - Standard C Female (nl-BE-Standard-C)</option>
                        <option value="nl-BE-Standard-D">Néerlandais (Belgique) - Standard D Male (nl-BE-Standard-D)</option>
                        <option value="nl-BE-Wavenet-C">Néerlandais (Belgique) - Wavenet C Female (nl-BE-Wavenet-C)</option>
                        <option value="nl-BE-Wavenet-D">Néerlandais (Belgique) - Wavenet D Male (nl-BE-Wavenet-D)</option>
                        <!-- Serbian -->
                        <option disabled>--- Serbe (Serbie) ---</option>
                        <option value="sr-RS-Standard-B">Serbe (Serbie) - Standard B Female (sr-RS-Standard-B)</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-gcloudtts">
                <label class="col-lg-3 control-label">{{Vitesse de Dictée (gCloud TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Valeur par défaut = Normal (1.0)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="gCloudTTSSpeed">
                        <option value="0.5">{{Lent ---- (0.5)}}</option>    
                        <option value="0.6">{{Lent --- (0.6)}}</option>
                        <option value="0.7">{{Lent -- (0.7)}}</option>
                        <option value="0.8">{{Lent - (0.8)}}</option>
                        <option value="0.85">{{Normal --- (0.85)}}</option>
                        <option value="0.9">{{Normal -- (0.9)}}</option>
                        <option value="0.95">{{Normal - (0.95)}}</option>
                        <option value="1.0" selected>{{Normal (1.0)}}</option>
                        <option value="1.05">{{Normal + (1.05)}}</option>
                        <option value="1.1">{{Normal ++ (1.1)}}</option>
                        <option value="1.15">{{Normal +++ (1.15)}}</option>
                        <option value="1.2">{{Rapide + (1.2)}}</option>
                        <option value="1.25">{{Rapide ++ (1.25)}}</option>
                        <option value="1.3">{{Rapide +++ (1.3)}}</option>
                        <option value="1.4">{{Rapide ++++ (1.4)}}</option>
                        <option value="1.5">{{Rapide +++++ (1.5)}}</option>
                        <option value="1.6">{{Rapide ++++++ (1.6)}}</option>
                    </select>
                </div>
            </div>
            <legend><i class="fas fas fa-brain"></i> {{IA}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Active l'IA Générative}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Autoriser l'usage de l'IA pour la reformulation des réponses. Désactivez cette option si vous ne souhaitez pas utiliser l'IA}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="ttsAIEnable" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Authentification IA}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sélectionnez le mode d'authentification à utiliser pour se connecter au moteur d'IA.}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="ttsAIAuthMode">
                        <option value="apikey">{{Clé API (AI Studio)}}</option>
                        <option value="oauth2" selected>{{Fichier JSON (Vertex AI)}}</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{ID Projet (Google)}} <a class="btn btn-info btn-xs" target="_blank" href="https://console.cloud.google.com/apis">{{SITE}}</a>
                    <sup><i class="fas fa-question-circle tooltips" title="{{Entrez votre ID de projet Google pour l'authentification avec le moteur d'IA.}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <input class="configKey form-control" type="text" data-l1key="ttsAIProjectID" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Clé API}} <a class="btn btn-info btn-xs" target="_blank" href="https://aistudio.google.com/apikey">{{SITE}}</a>
                    <sup><i class="fas fa-question-circle tooltips" title="{{Entrez votre clé API pour l'authentification avec le moteur d'IA.}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <input class="configKey form-control" type="text" data-l1key="ttsAIAPIKey" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Modèle IA}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sélectionnez le modèle d'IA à utiliser pour la reformulation des réponses.}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="ttsAIModel">
                        <option value="gemini-2.5-flash-lite" selected>Gemini 2.5 Flash Lite</option>
                        <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Ton de Reformulation}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sauvegardez bien votre configuration AVANT d'utiliser ce prompt système personnalisé}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input class="configKey form-control" type="text" data-l1key="ttsAIDefaultTone" placeholder="{{Ex: Enthousiaste et humoristique}}" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Prompt Système Personnalisé}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sauvegardez bien votre configuration AVANT d'utiliser ce prompt système personnalisé}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input type="checkbox" class="configKey" data-l1key="ttsAIUseCustomSysPrompt" />
                    <input class="configKey form-control" type="text" data-l1key="ttsAICustomSysPrompt" placeholder="{{Ex: Répond à la question s'il y en a une et reformule la phrase}}" />
                </div>
            </div>
            <legend><i class="fas fa-clipboard-check"></i> {{Tests}}</legend>
            <div class="form-group">
               <label class="col-lg-3 control-label">{{Tester avec la syntaxe SSML (TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Ce paramètre est utilisé uniquement pour le test de synthèse vocale (TTS)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="ttsTestSSML" />
                </div>
            </div>
            <div class="form-group">
               <label class="col-lg-3 control-label">{{Tester avec l'IA}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Ce paramètre permet de tester la reformulation des réponses à l'aide de l'IA.}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="ttsTestAI" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Tester la Synthèse Vocale (TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sauvegardez bien votre configuration AVANT d'utiliser le bouton [Générer + Diffuser]}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input class="configKey form-control" type="text" data-l1key="ttsTestFileGen" placeholder="{{Ex: Ceci est un message de test pour la synthèse vocale à partir de Jeedom.}}" />
                </div>
                <div class="col-lg-2">
                    <input class="configKey form-control" type="text" data-l1key="ttsTestGoogleName" placeholder="{{Ex: Nest Salon}}" />
                </div>
                <div class="col-lg-1">
                    <a class="btn btn-success customclass-ttstestplay"><i class="fas fa-play-circle"></i> {{Générer + Diffuser}}</a>
                </div>
            </div>
            <legend><i class="fas fa-list-alt"></i> {{Options}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{URL Jeedom Externe}}
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Utilise l'URL externe de Jeedom pour la lecture des fichiers TTS plutôt que l'URL interne (Recommandé = décoché)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <input type="checkbox" class="configKey customform-address" data-l1key="ttsUseExtAddr" />
                    <span class="addressTestURL"></span>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Ne PAS utiliser le cache}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Génère les fichiers TTS à chaque demande. Il est vivement recommandé de ne PAS cocher cette case, sauf pour faire des tests}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="ttsDisableCache" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Durée de conservation du cache (jours)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Le cache des fichiers TTS générés sera purgé automatiquement tous les X (0 à 90) jours via le cron daily}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" type="number" data-l1key="ttsPurgeCacheDays" min="0" max="90" placeholder="{{Nombre de jours}}" />
                </div>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-purgettscache"><i class="fas fa-trash-alt"></i> {{Vider le Cache}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Désactiver le 'ding' des commandes}}
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>    
                    <sup><i class="fas fa-question-circle tooltips" title="{{Désactive (globalement) le 'ding' au lancement d'une commande sur un Google Home}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="appDisableDing" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Durée maximale de l'option 'Wait' (secondes)}}
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-warning-color)!important;" title="{{Le démon devra être redémarré après la modification de ce paramètre}}"></i></sup>        
                    <sup><i class="fas fa-question-circle tooltips" title="{{Temps (entre 0 et 3600 sec) au bout duquel la commande est dans tous les cas exécutée, même si l'équipement Google est encore en cours de lecture (par défaut : 60sec)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" type="number" data-l1key="cmdWaitTimeout" min="0" max="3600" placeholder="{{Timeout}}" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Timeout de l'API 'GenerateTTS' (secondes)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Timeout (entre 5 et 300 sec) d'attente de la génération du fichier TTS lors d'un appel via API (par défaut : 30sec)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" type="number" data-l1key="ttsGenTimeout" min="5" max="300" placeholder="{{Timeout}}" />
                </div>
            </div>
            <legend><i class="fas fa-list-ol"></i> {{Listes (Radios, CustomRadios, Sounds, Custom Sounds)}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mise à jour des listes :: Radios}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des radios de vos équipements. ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updateradios"><i class="fas fa-sync"></i> {{MàJ Radios}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mise à jour des listes :: Custom Radios}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des custom radios de vos équipements. ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updatecustomradios"><i class="fas fa-sync"></i> {{MàJ Custom Radios}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mise à jour des listes :: Sounds}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des sons (.mp3). ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updatesounds"><i class="fas fa-file-audio"></i> {{MàJ Sounds}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mise à jour des listes :: Custom Sounds}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des sons personnalisés (.mp3). ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updatecustomsounds"><i class="fas fa-file-audio"></i> {{MàJ Custom Sounds}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Ajouter un fichier :: Custom Sound}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Upload un fichier (.mp3) pour l'ajouter au répertoire des Custom Sounds}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-info btn-file">
                        <i class="fas fa-file-upload"></i> {{Ajouter un Custom Sound (.mp3)}}<input class="pluginAction" data-action="uploadCustomSound" type="file" name="fileCustomSound" style="display: inline-block;" accept=".mp3" />
                    </a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Ajouter un fichier :: Custom Radios}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Upload d'un fichier (.json) pour mettre à jour la liste des Custom Radios}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-info btn-file">
                        <i class="fas fa-file-upload"></i> {{Ajouter des Custom Radios (.json)}}<input class="pluginAction" data-action="uploadCustomRadios" type="file" name="fileCustomRadios" style="display: inline-block;" accept=".json" />
                    </a>
                </div>
            </div>
        </div>
    </fieldset>
</form>

<script>
    function ttsEngineSelect() {
        var val = $('.customform-ttsengine').val();
        if (val == 'gcloudtts') {
            $('.customform-gcloudtts').show();
            $('.customform-gtts').hide();
            $('.customform-lang').hide();
            $('.customform-voicersstts').hide();
        } else if (val == 'gtranslatetts') {
            $('.customform-gcloudtts').hide();
            $('.customform-gtts').show();
            $('.customform-lang').show();
            $('.customform-voicersstts').hide();
        } else if (val == 'voicersstts') {
            $('.customform-gcloudtts').hide();
            $('.customform-gtts').hide();
            $('.customform-lang').hide();
            $('.customform-voicersstts').show();
        } else {
            $('.customform-gcloudtts').hide();
            $('.customform-gtts').hide();
            $('.customform-lang').show();
            $('.customform-voicersstts').hide();
        }
    }

    $(document).ready(function() {
        ttsEngineSelect();
    });
    $('.customform-ttsengine').on('change', ttsEngineSelect);

    $('.customclass-resetapikey').on('click', function () {
        const fileName = $('.custominput-apikey').val();
        $('.custominput-apikey').val('');
        jeedom.config.save({ 
            plugin: 'ttscast', 
            configuration: { 
                gCloudAPIKey: ''
            },
            error: function (error) {
                $('#div_alert').showAlert({ message: error.message, level: 'danger' });
                return;
            },
            success: function () {
                $('#div_alert').showAlert({ message: '{{Reset Clé API :: Sauvegarde OK}}', level: 'success' });
            }
        });
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "resetAPIKey",
                filename: fileName
            },
            dataType: 'json',
            error: function (request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function (data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({ message: data.result, level: 'danger' });
                    return;
                }
                $('#div_alert').showAlert({ message: '{{Reset Clé API (OK) :: }}' + data.result, level: 'success' });
            }
        });
    });

    $('.pluginAction[data-action=uploadAPIKey]').on('click', function () {
        $(this).fileupload({
            replaceFileInput: false,
            url: 'plugins/ttscast/core/ajax/ttscast.ajax.php?action=uploadAPIKey',
            dataType: 'json',
            done: function (e, data) {
                if (data.result.state != 'ok') {
                    $('#div_alert').showAlert({ message: data.result.result, level: 'danger' });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Upload Clé API (OK) :: }}' + data.result.result,
                    level: 'success'
                });
                $('.custominput-apikey').val(data.result.result);
                jeedom.config.save({ 
                    plugin: 'ttscast', 
                    configuration: { 
                        gCloudAPIKey: $('.custominput-apikey').val()
                    },
                    error: function (error) {
                        $('#div_alert').showAlert({ message: error.message, level: 'danger' });
                        return;
                    },
                    success: function () {
                        $('#div_alert').showAlert({ message: '{{Upload Clé API :: Sauvegarde OK}}', level: 'success' });
                    }
                });
            }
        });
    });

    $('.pluginAction[data-action=uploadCustomSound]').on('click', function () {
        $(this).fileupload({
            replaceFileInput: false,
            url: 'plugins/ttscast/core/ajax/ttscast.ajax.php?action=uploadCustomSound',
            dataType: 'json',
            done: function (e, data) {
                if (data.result.state != 'ok') {
                    $('#div_alert').showAlert({ message: data.result.result, level: 'danger' });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Upload Custom Sound (OK) :: }}' + data.result.result,
                    level: 'success'
                });
            }
        });
    });

    $('.pluginAction[data-action=uploadCustomRadios]').on('click', function () {
        $(this).fileupload({
            replaceFileInput: false,
            url: 'plugins/ttscast/core/ajax/ttscast.ajax.php?action=uploadCustomRadios',
            dataType: 'json',
            done: function (e, data) {
                if (data.result.state != 'ok') {
                    $('#div_alert').showAlert({ message: data.result.result, level: 'danger' });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Upload Custom Radios (OK) :: }}' + data.result.result,
                    level: 'success'
                });
            }
        });
    });

    $('.customclass-purgettscache').on('click', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "purgeTTSCache"
            },
            dataType: 'json',
            error: function(request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({
                        message: data.result,
                        level: 'danger'
                    });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Demande de purge du cache envoyée (voir les logs du démon pour le résultat)}}',
                    level: 'success'
                });
            }
        });
    });

    $('.customclass-updateradios').on('click', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "updateRadios"
            },
            dataType: 'json',
            error: function(request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({
                        message: data.result,
                        level: 'danger'
                    });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Demande de mise à jour des listes :: Radios :: envoyée (voir les logs ttscast)}}',
                    level: 'success'
                });
            }
        });
    });

    $('.customclass-updatecustomradios').on('click', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "updateCustomRadios"
            },
            dataType: 'json',
            error: function(request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({
                        message: data.result,
                        level: 'danger'
                    });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Demande de mise à jour des listes :: CustomRadios :: envoyée (voir les logs ttscast)}}',
                    level: 'success'
                });
            }
        });
    });

    $('.customclass-updatesounds').on('click', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "updateSounds"
            },
            dataType: 'json',
            error: function(request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({
                        message: data.result,
                        level: 'danger'
                    });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Demande de mise à jour des listes :: Sounds :: envoyée (voir les logs ttscast)}}',
                    level: 'success'
                });
            }
        });
    });

    $('.customclass-updatecustomsounds').on('click', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "updateCustomSounds"
            },
            dataType: 'json',
            error: function(request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({
                        message: data.result,
                        level: 'danger'
                    });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Demande de mise à jour des listes :: Custom Sounds :: envoyée (voir les logs ttscast)}}',
                    level: 'success'
                });
            }
        });
    });
    
    $('.customclass-ttstestplay').on('click', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "playTestTTS"
            },
            dataType: 'json',
            error: function(request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({
                        message: data.result,
                        level: 'danger'
                    });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Demande de génération du TTS de test envoyée (voir les logs du démon pour le résultat)}}',
                    level: 'success'
                });
            }
        });
    });

    $('.customform-address').on('change', function() {
        $.ajax({
            type: "POST",
            url: "plugins/ttscast/core/ajax/ttscast.ajax.php",
            data: {
                action: "testExternalAddress",
                value: $('.customform-address').prop('checked')
            },
            dataType: 'json',
            error: function(request, status, error) {
                $('.addressTestURL').text("");
                handleAjaxError(request, status, error);
            },
            success: function(data) {
                var spanContent = ' <a class="btn btn-info btn-xs" href="' + data.result + '" target="_blank">TEST (Lecture .mp3)</a>';
                $('.addressTestURL').html(spanContent);
            }
        });
    });
</script>
