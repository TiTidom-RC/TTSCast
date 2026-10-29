<?php
if (!isConnect('admin')) {
    throw new Exception('{{401 - Accès non autorisé}}');
}
?>

<div style="margin-bottom:10px;">
    <span class="text-muted">
        <i class="fas fa-info-circle"></i>
        {{Saisissez une ou plusieurs adresses IP (IPv4 ou IPv6) ou noms d'hôte, une par ligne ou séparées par des virgules ou des espaces. Les appareils Cast qui répondent à ces adresses, ainsi que les groupes qu'ils hébergent, sont ajoutés ou mis à jour.}}
    </span>
</div>

<div style="display:flex; gap:8px; align-items:flex-start; flex-wrap:wrap; margin-bottom:10px;">
    <textarea class="form-control" id="ta_ttscastHosts" rows="4" style="flex:1; min-width:250px; font-family:monospace;" placeholder="192.168.1.20&#10;192.168.1.21, 192.168.1.22&#10;2001:db8::20&#10;nest-salon.lan"></textarea>
    <a class="btn btn-primary btn-sm" id="bt_ttscastSearchHosts">
        <i class="fas fa-network-wired"></i> {{Lancer le Scan (IP)}}
    </a>
</div>

<div id="div_ttscastHostsResults" style="display:none;">
    <table class="table table-bordered table-condensed" style="width:100%; table-layout:fixed;">
        <thead>
            <tr>
                <th style="width:40px; text-align:center;"></th>
                <th style="width:28%;">{{Adresse}}</th>
                <th style="width:28%;">{{Appareil}}</th>
                <th>{{Résultat}}</th>
            </tr>
        </thead>
        <tbody id="tb_ttscastHostsResults"></tbody>
    </table>
</div>

<?php include_file('desktop', 'addhosts.ttscast', 'js', 'ttscast'); ?>
<script>
    initAddHosts();
</script>
