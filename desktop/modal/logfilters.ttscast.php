<?php
if (!isConnect('admin')) {
    throw new Exception('{{401 - Accès non autorisé}}');
}
$logFiltersData = ttscast::getLogFiltersFileContent();
?>

<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
    <span class="text-muted">
        <i class="fas fa-info-circle"></i>
        {{Définissez les patterns à intercepter et le niveau de log à appliquer. Cochez/décochez pour activer/désactiver une règle sans la perdre.}}
    </span>
    <a class="btn btn-success btn-sm" id="bt_saveLogFilters">
        <i class="fas fa-save"></i> {{Sauvegarder}}
    </a>
</div>

<div style="margin-bottom:10px; display:flex; gap:6px; flex-wrap:wrap;">
    <a class="btn btn-sm btn-success" id="bt_addLogFilter"><i class="fas fa-plus"></i> {{Ajouter}}</a>
    <a class="btn btn-sm btn-default" id="bt_selectAllLogFilters" title="{{Tout activer}}"><i class="fas fa-check-double"></i></a>
    <a class="btn btn-sm btn-default" id="bt_unselectAllLogFilters" title="{{Tout désactiver}}"><i class="fas fa-minus-square"></i></a>
</div>

<table class="table table-bordered table-condensed" style="width:100%; table-layout:fixed;">
    <thead>
        <tr>
            <th style="width:60px; text-align:center;">{{Actif}}</th>
            <th>{{Pattern (sous-chaîne du message de log)}}</th>
            <th style="width:180px;">{{Niveau cible}}</th>
            <th style="width:40px;"></th>
        </tr>
    </thead>
    <tbody id="logFiltersContainer"></tbody>
</table>

<div style="margin-top:8px; font-size:11px; color:var(--al-info-color)">
    {{Suggestions :}}
    <a href="#" class="ttscast-logfilter-suggest" data-pattern="Failed to connect to service" data-level="DEBUG">Failed to connect to service &rarr; DEBUG</a>
    &nbsp;|&nbsp;
    <a href="#" class="ttscast-logfilter-suggest" data-pattern="Cannot ping until reconnected" data-level="DEBUG">Cannot ping until reconnected &rarr; DEBUG</a>
</div>

<?php include_file('desktop', 'logfilters.ttscast', 'js', 'ttscast'); ?>
<script>
    initLogFilters(<?= json_encode($logFiltersData) ?>);
</script>
