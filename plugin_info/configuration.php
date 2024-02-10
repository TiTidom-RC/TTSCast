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
                <label class="col-lg-3 control-label">{{Version}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Version du plugin à indiquer sur Community}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="pluginVersion" readonly />
                </div>
            </div>
            <legend><i class="fas fa-university"></i> {{Démon}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Port Socket Interne}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{[ATTENTION] Ne changez ce paramètre qu'en cas de nécessité. (Défaut = 55111)}}"></i></sup>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-danger-color)!important;" title="{{Le Démon devra être redémarré après la modification de ce paramètre}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="socketport" placeholder="55111" />
                </div>
            </div>
            <div class="form-group">
	            <label class="col-lg-3 control-label">{{Fréquence des cycles}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Facteur multiplicateur des cycles du démon (Défaut = 1)}}"></i></sup>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-danger-color)!important;" title="{{Le Démon devra être redémarré après la modification de ce paramètre}}"></i></sup>
                </label>
	            <div class="col-lg-2">
			        <select class="configKey form-control" data-l1key="cyclefactor">
				        <option value="0.5">{{Plus Rapide - 0.5}}</option>
			            <option value="1" selected>{{Normal - 1 (Recommandé)}}</option>
			            <option value="2">{{Plus Lent - 2}}</option>
			            <option value="3">{{Encore Plus Lent - 3}}</option>
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
                    <sup><i class="fas fa-question-circle tooltips" title="{{Langue à utiliser avec l'API Google Translate ou Jeedom TTS (Il n'est pas possible choisir une voix, seulement une langue)}}"></i></sup>
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
                    <sup><i class="fas fa-question-circle tooltips" title="{{Rentrer votre clé API Voice RSS, récupérable sur leur site, dans votre profil'}}"></i></sup>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-danger-color)!important;" title="{{Le Démon devra être redémarré après la modification de ce paramètre}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input class="configKey form-control custominput-voicerssapikey" type="text" data-l1key="voiceRSSAPIKey" />
                </div>
            </div>
            <div class="form-group customform-gcloudtts">
                <label class="col-lg-3 control-label">{{Clé API (gCloud TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Uploader votre clé JSON en utilisant le bouton 'Ajouter Clé (JSON)'}}"></i></sup>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-danger-color)!important;" title="{{Le Démon devra être redémarré après la modification de ce paramètre}}"></i></sup>
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
                        <!-- French -->
                        <option value="fr-fr-Bette">Français (France) - Bette Female (fr-fr-Bette)</option>
                        <option value="fr-fr-Iva">Français (France) - Iva Female (fr-fr-Iva)</option>
                        <option value="fr-fr-Zola">Français (France) - Zola Female (fr-fr-Zola)</option>
                        <option value="fr-fr-Axel">Français (France) - Axel Male (fr-fr-Axel)</option>
                        <!-- English -->
                        <option value="en-us-Linda">Anglais (US) - Linda Female (en-us-Linda)</option>
                        <option value="en-us-Amy">Anglais (US) - Amy Female (en-us-Amy)</option>
                        <option value="en-us-Mary">Anglais (US) - Mary Female (en-us-Mary)</option>
                        <option value="en-us-John">Anglais (US) - John Male (en-us-John)</option>
                        <option value="en-us-Mike">Anglais (US) - Mike Male (en-us-Mike)</option>
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
                        <!-- French -->
                        <option value="fr-FR-Standard-A">Français (France) - Standard A Female (fr-FR-Standard-A)</option>
                        <option value="fr-FR-Standard-B">Français (France) - Standard B Male (fr-FR-Standard-B)</option>
                        <option value="fr-FR-Standard-C">Français (France) - Standard C Female (fr-FR-Standard-C)</option>
                        <option value="fr-FR-Standard-D">Français (France) - Standard D Male (fr-FR-Standard-D)</option>
                        <option value="fr-FR-Standard-E">Français (France) - Standard E Female (fr-FR-Standard-E)</option>
                        <option value="fr-FR-Wavenet-A">Français (France) - WaveNet A Female (fr-FR-Wavenet-A)</option>
                        <option value="fr-FR-Wavenet-B">Français (France) - WaveNet B Male (fr-FR-Wavenet-B)</option>
                        <option value="fr-FR-Wavenet-C">Français (France) - WaveNet C Female (fr-FR-Wavenet-C)</option>
                        <option value="fr-FR-Wavenet-D">Français (France) - WaveNet D Male (fr-FR-Wavenet-D)</option>
                        <option value="fr-FR-Wavenet-E">Français (France) - WaveNet E Female (fr-FR-Wavenet-E)</option>
                        <option value="fr-FR-Neural2-A">Français (France) - Neural2 A Female (fr-FR-Neural2-A)</option>
                        <option value="fr-FR-Neural2-B">Français (France) - Neural2 B Male (fr-FR-Neural2-B)</option>
                        <option value="fr-FR-Neural2-C">Français (France) - Neural2 C Female (fr-FR-Neural2-C)</option>
                        <option value="fr-FR-Neural2-D">Français (France) - Neural2 D Male (fr-FR-Neural2-D)</option>
                        <option value="fr-FR-Neural2-E">Français (France) - Neural2 E Female (fr-FR-Neural2-E)</option>
                        <option value="fr-FR-Studio-A">Français (France) - Studio A Female (fr-FR-Studio-A)</option>
                        <option value="fr-FR-Studio-D">Français (France) - Studio D Male (fr-FR-Studio-D)</option>
                        <option value="fr-FR-Polyglot-1">Français (France) - Polyglot 1 Male (fr-FR-Polyglot-1)</option>
                        <option value="fr-CA-Standard-A">Français (Canada) - Standard A Female (fr-CA-Standard-A)</option>
                        <option value="fr-CA-Standard-B">Français (Canada) - Standard B Male (fr-CA-Standard-B)</option>
                        <option value="fr-CA-Standard-C">Français (Canada) - Standard C Female (fr-CA-Standard-C)</option>
                        <option value="fr-CA-Standard-D">Français (Canada) - Standard D Male (fr-CA-Standard-D)</option>
                        <option value="fr-CA-Wavenet-A">Français (Canada) - Wavenet A Female (fr-CA-Wavenet-A)</option>
                        <option value="fr-CA-Wavenet-B">Français (Canada) - Wavenet B Male (fr-CA-Wavenet-B)</option>
                        <option value="fr-CA-Wavenet-C">Français (Canada) - Wavenet C Female (fr-CA-Wavenet-C)</option>
                        <option value="fr-CA-Wavenet-D">Français (Canada) - Wavenet D Male (fr-CA-Wavenet-D)</option>
                        <option value="fr-CA-Neural2-A">Français (Canada) - Neural2 A Female (fr-CA-Neural2-A)</option>
                        <option value="fr-CA-Neural2-B">Français (Canada) - Neural2 B Male (fr-CA-Neural2-B)</option>
                        <option value="fr-CA-Neural2-C">Français (Canada) - Neural2 C Female (fr-CA-Neural2-C)</option>
                        <option value="fr-CA-Neural2-D">Français (Canada) - Neural2 D Male (fr-CA-Neural2-D)</option>
                        <!-- English -->
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
                        <option value="en-US-Neural2-A">Anglais (US) - Neural2 A Male (en-US-Neural2-A)</option>
                        <option value="en-US-Neural2-C">Anglais (US) - Neural2 C Female (en-US-Neural2-C)</option>
                        <option value="en-US-Neural2-D">Anglais (US) - Neural2 D Male (en-US-Neural2-D)</option>
                        <option value="en-US-Neural2-E">Anglais (US) - Neural2 E Female (en-US-Neural2-E)</option>
                        <option value="en-US-Neural2-F">Anglais (US) - Neural2 F Female (en-US-Neural2-F)</option>
                        <option value="en-US-Neural2-G">Anglais (US) - Neural2 G Female (en-US-Neural2-G)</option>
                        <option value="en-US-Neural2-H">Anglais (US) - Neural2 H Female (en-US-Neural2-H)</option>
                        <option value="en-US-Neural2-I">Anglais (US) - Neural2 I Male (en-US-Neural2-I)</option>
                        <option value="en-US-Neural2-J">Anglais (US) - Neural2 J Male (en-US-Neural2-J)</option>
                        <option value="en-US-Studio-O">Anglais (US) - Studio O Female (en-US-Studio-O)</option>
                        <option value="en-US-Studio-Q">Anglais (US) - Studio Q Male (en-US-Studio-Q)</option>
                        <option value="en-US-Polyglot-1">Anglais (US) - Polyglot 1 Male (en-US-Polyglot-1)</option>
                        <option value="en-US-Journey-D">Anglais (US) - Journey D Male (en-US-Journey-D)</option>
                        <option value="en-US-Journey-F">Anglais (US) - Journey F Female (en-US-Journey-F)</option>
                        <option value="en-US-News-K">Anglais (US) - News K Female (en-US-News-K)</option>
                        <option value="en-US-News-L">Anglais (US) - News L Female (en-US-News-L)</option>
                        <option value="en-US-News-N">Anglais (US) - News N Male (en-US-News-N)</option>
                        <!-- Serbian -->
                        <option value="sr-RS-Standard-A">Serbe (Serbie) - Standard A Female (sr-RS-Standard-A)</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-gcloudtts">
                <label class="col-lg-3 control-label">{{Vitesse de Dictée (gCloud TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Valeur par défaut = Normal (1.0)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="gCloudTTSSpeed">
                        <option value="0.8">{{Lent (0.8)}}</option>
                        <option value="1.0" selected>{{Normal (1.0)}}</option>
                        <option value="1.2">{{Normal + (1.2)}}</option>
                        <option value="1.25">{{Normal ++ (1.25)}}</option>
                        <option value="1.3">{{Rapide (1.3)}}</option>
                        <option value="1.4">{{Rapide + (1.4)}}</option>
                        <option value="1.6">{{Rapide ++ (1.6)}}</option>
                        <option value="1.8">{{Rapide +++ (1.8)}}</option>
                    </select>
                </div>
            </div>
            <legend><i class="fas fa-clipboard-check"></i> {{Tests}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Tester la Synthèse Vocale (TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sauvegardez bien votre configuration AVANT d'utiliser le bouton (GENERER + DIFFUSER)}}"></i></sup>
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
                    <sup><i class="fas fa-question-circle tooltips" title="{{Utilise l'URL externe de Jeedom pour la lecture des fichiers TTS plutôt que l'URL interne (Recommandé = décoché)}}"></i></sup>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-danger-color)!important;" title="{{Le Démon devra être redémarré après la modification de ce paramètre}}"></i></sup>
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
                <label class="col-lg-3 control-label">{{Désactiver le "Ding" au lancement des commandes}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Cocher cette option pour Désactiver le 'Ding' au lancement d'une commande sur un Google Home. Cela désactivera ce son sur l'ensemble des commandes. (Ce son est Actif par défaut)}}"></i></sup>
                    <sup><i class="fas fa-exclamation-triangle tooltips" style="color:var(--al-danger-color)!important;" title="{{Le Démon devra être redémarré après la modification de ce paramètre}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="appDisableDing" />
                </div>
            </div>
            <legend><i class="fas fa-list-ol"></i> {{Listes (Radios, Sounds, Custom Sounds)}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mettre à jour les listes :: Radio}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des radios de vos équipements. ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updateradios"><i class="fas fa-sync"></i> {{MàJ Radios}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mettre à jour les listes :: Sound}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des sons (.mp3). ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updatesounds"><i class="fas fa-file-audio"></i> {{MàJ Sounds}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Mettre à jour les listes :: Custom Sound}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Met à jour la liste des sons personnalisés (.mp3). ATTENTION : cela peut avoir un impact sur vos scénarios !}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-updatecustomsounds"><i class="fas fa-file-audio"></i> {{MàJ Custom Sounds}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Ajouter un fichier :: Custom Sound}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Télécharge un fichier (.mp3) pour l'ajouter au répertoire des Custom Sounds}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <a class="btn btn-primary btn-file">
                        <i class="fas fa-file-upload"></i> {{Ajouter un Custom Sound (.mp3)}}<input class="pluginAction" data-action="uploadCustomSound" type="file" name="fileCustomSound" style="display: inline-block;" accept=".mp3" />
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
                    message: '{{Demande de mise à jour des listes :: Radio :: envoyée (voir les logs ttscast)}}',
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
                    message: '{{Demande de mise à jour des listes :: Sound :: envoyée (voir les logs ttscast)}}',
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
                    message: '{{Demande de mise à jour des listes :: Custom Sound :: envoyée (voir les logs ttscast)}}',
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