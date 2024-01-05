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
            <legend><i class="fas fa-university"></i> {{Démon}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Durée de Cycle}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Fréquence d'envoi des informations vers Jeedom; valeur entre 0.5 et 10 (Défaut = 1)}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="cycle" placeholder="1" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Port Socket Interne}}</label>
                <div class="col-lg-1">
                    <input class="configKey form-control" data-l1key="socketport" placeholder="55999" />
                </div>
            </div>
            <legend><i class="fas fa-volume-down"></i> {{TTS - Text To Speech}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{URL Jeedom Externe}}</label>
                <div class="col-lg-2">
                    <input type="checkbox" class="configKey customform-address" data-l1key="ttsUseExtAddr" />
                    <span class="addressTestURL"></span>
                </div>
            </div>
            <div class="form-group customform-lang">
                <label class="col-lg-3 control-label">{{Langue TTS}}</label>
                <div class="col-lg-2">
                    <select class="configKey form-control" data-l1key="ttsLang">
                        <option value="fr-FR">{{Français (fr-FR)}}</option>
                        <option value="en-US">{{Anglais (en-US)}}</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Moteur TTS}}</label>
                <div class="col-lg-3">
                    <select class="configKey form-control customform-ttsengine" data-l1key="ttsEngine">
                        <option value="jeedomtts">{{Jeedom TTS (Local)}}</option>
                        <option value="picotts">{{PicoTTS (Local)}}</option>
                        <option value="gtranslatetts">{{Google Translate API (Internet)}}</option>
                        <option value="gcloudtts">{{Google Cloud Text-To-Speech (Clé & Internet)}}</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-gcloudttsvoice">
                <label class="col-lg-3 control-label">{{Voix Google Cloud Text-to-Speech}} [<a target="_blank" href="https://cloud.google.com/text-to-speech/">{{TESTER}}</a>]</label>
                <div class="col-lg-4">
                    <select class="configKey form-control" data-l1key="gCloudTTSVoice">
                        <option value="fr-FR-Standard-A">French (France) - Standard A Female (fr-FR-Standard-A)</option>
                        <option value="fr-FR-Standard-B">French (France) - Standard B Male (fr-FR-Standard-B)</option>
                        <option value="fr-FR-Standard-C">French (France) - Standard C Female (fr-FR-Standard-C)</option>
                        <option value="fr-FR-Standard-D">French (France) - Standard D Male (fr-FR-Standard-D)</option>
                        <option value="fr-FR-Standard-E">French (France) - Standard E Female (fr-FR-Standard-E)</option>
                        <option value="fr-FR-Wavenet-A">French (France) - WaveNet A Female (fr-FR-Wavenet-A)</option>
                        <option value="fr-FR-Wavenet-B">French (France) - WaveNet B Male (fr-FR-Wavenet-B)</option>
                        <option value="fr-FR-Wavenet-C">French (France) - WaveNet C Female (fr-FR-Wavenet-C)</option>
                        <option value="fr-FR-Wavenet-D">French (France) - WaveNet D Male (fr-FR-Wavenet-D)</option>
                        <option value="fr-FR-Wavenet-E">French (France) - WaveNet E Female (fr-FR-Wavenet-E)</option>
                        <option value="fr-FR-Neural2-A">French (France) - Neural2 A Female (fr-FR-Neural2-A)</option>
                        <option value="fr-FR-Neural2-B">French (France) - Neural2 B Male (fr-FR-Neural2-B)</option>
                        <option value="fr-FR-Neural2-C">French (France) - Neural2 C Female (fr-FR-Neural2-C)</option>
                        <option value="fr-FR-Neural2-D">French (France) - Neural2 D Male (fr-FR-Neural2-D)</option>
                        <option value="fr-FR-Neural2-E">French (France) - Neural2 E Female (fr-FR-Neural2-E)</option>
                        <option value="fr-FR-Studio-A">French (France) - Studio A Female (fr-FR-Studio-A)</option>
                        <option value="fr-FR-Studio-D">French (France) - Studio D Male (fr-FR-Studio-D)</option>
                        <option value="fr-FR-Polyglot-1">French (France) - Polyglot 1 Male (fr-FR-Polyglot-1)</option>
                    </select>
                </div>
            </div>
            <div class="form-group customform-gcloudttsspeed">
                <label class="col-lg-3 control-label">{{Vitesse de parole}}
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
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Delai POST Lecture}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Silence ajouté APRES la lecture (avant de restaurer le volume initial). Valeur de -1000 à 10000 (Défaut = 1300)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <input class="configKey form-control" type="number" data-l1key="ttsDelayPostRead" min="-1000" max="10000" placeholder="{{ms (-1000 <-> 10000)}}" />
                </div>
                <div class="col-lg-2">ms (Défaut: 1300)</div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Délai PRE Lecture}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Silence ajouté AVANT la lecture. Permet d'éviter de tronquer le début du fichier. Valeur de 0 à 10000 (Défaut = 300)}}"></i></sup>
                </label>
                <div class="col-lg-2">
                    <input class="configKey form-control" type="number" data-l1key="ttsDelayPreRead" min="0" max="10000" placeholder="{{ms (0 <-> 10000)}}" />
                </div>
                <div class="col-lg-2">ms (Défaut: 300)</div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Ne PAS utiliser le cache (Déconseillé !)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Génère le fichier TTS à chaque demande. Il est vivement conseillé de ne PAS cocher cette case, sauf en cas de tests}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="ttsDisableCache" />
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Durée de conservation du cache (jours)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Le cache sera purgé automatiquement tous les X (0 à 90) jours via le cron daily}}"></i></sup>
                </label>
                <div class="col-lg-1">
                    <input class="configKey form-control" type="number" data-l1key="ttsPurgeCacheDays" min="0" max="90" placeholder="{{Nombre de jours}}" />
                </div>
                <div class="col-lg-1">
                    <a class="btn btn-warning customclass-purgettscache">{{VIDER le cache}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{TEST (génération d'un fichier TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Sauvegardez bien votre configuration AVANT d'utiliser le bouton (GENERER + DIFFUSER)}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <input class="configKey form-control" type="text" data-l1key="ttsTestFileGen" placeholder="{{Bonjour TiTidom, Ceci est un message de test pour la synthèse vocale à partir de Jeedom.}}" />
                </div>
                <div class="col-lg-2">
                    <input class="configKey form-control" type="text" data-l1key="ttsTestGoogleName" placeholder="{{Nest Hub Bureau}}" />
                </div>
                <div class="col-lg-1">
                    <a class="btn btn-success customclass-ttstestplay">{{GENERER + DIFFUSER}}</a>
                </div>
            </div>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Clé API (Google Cloud TTS)}}
                    <sup><i class="fas fa-question-circle tooltips" title="{{Uploader votre clé JSON en utilisant le bouton UPLOAD}}"></i></sup>
                </label>
                <div class="col-lg-3">
                    <div class="input-group">
                        <input class="configKey form-control roundedLeft custominput-apikey" type="text" data-l1key="gCloudAPIKey" readonly />
                        <span class="configKey input-group-addon roundedRight"><a class="pluginAction btn btn-sm btn-default" data-action="resetAPIKey" title="{{Réinitialiser la clé API}}"><i class="fas fa-undo"></i></a></span>
                    </div>
                </div>
                <div class="col-lg-2">      
                    <a class="btn btn-primary btn-file">
                        <i class="fas fa-cloud-upload-alt"></i> {{Envoyer une clé API (JSON)}}<input class="pluginAction" data-action="uploadAPIKey" type="file" name="fileAPIKey" style="display: inline-block;" accept=".json">
                    </a>
                </div>
                
            </div>
            <legend><i class="fas fa-comment"></i> {{Notifications}}</legend>
            <div class="form-group">
                <label class="col-lg-3 control-label">{{Désactiver les notifications pour les nouveaux GoogleCast}}</label>
                <div class="col-lg-1">
                    <input type="checkbox" class="configKey" data-l1key="ttsDisableNotifNewCast" />
                </div>
            </div>
        </div>
    </fieldset>
</form>

<script>
    function ttsEngineSelect() {
        var val = $('.customform-ttsengine').val();

        if (val == 'jeedomtts') {
            $('.customform-gcloudttsspeed').hide();
        } else {
            $('.customform-gcloudttsspeed').show();
        }

        if (val == 'gcloudtts') {
            $('.customform-gcloudttsvoice').show();
        } else {
            $('.customform-gcloudttsvoice').hide();
        }
    }

    $(document).ready(function() {
        ttsEngineSelect();
    });
    $('.customform-ttsengine').on('change', ttsEngineSelect);

    $('.pluginAction[data-action=resetAPIKey]').on('click', function () {
        const fileName = $('.custominput-apikey').value;
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
                    $('#modal_alert').showAlert({ message: data.result, level: 'danger' });
                    return;
                }
                $('#div_alert').showAlert({
                    message: '{{Reset Clé API (OK) :: }}' + data.result.result,
                    level: 'success'
                });
                $('.custominput-apikey').val('');
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
                    message: '{{Demande de génération du TTS de test evoyée (voir les logs du démon pour le résultat)}}',
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
                var spanContent = ' <a href="' + data.result + '" target="_blank">[TEST]</a>';
                $('.addressTestURL').html(spanContent);
            }
        });
    });
</script>