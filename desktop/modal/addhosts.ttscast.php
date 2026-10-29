<?php
if (!isConnect('admin')) {
    throw new Exception('{{401 - Accès non autorisé}}');
}
// Adresses des équipements mis à jour via leur adresse IP (actifs ou non), pour le bouton qui les ajoute à la saisie
$ipHosts = array();
foreach (eqLogic::byType('ttscast') as $eqLogic) {
    $host = trim($eqLogic->getConfiguration('host', ''));
    if ($eqLogic->getConfiguration('updatedBy', '') == 'ip' && $host != '' && !in_array($host, $ipHosts)) {
        $ipHosts[] = $host;
    }
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
    <div style="display:flex; flex-direction:column; gap:6px;">
        <a class="btn btn-primary btn-sm" id="bt_ttscastSearchHosts">
            <i class="fas fa-network-wired"></i> {{Lancer le Scan (IP)}}
        </a>
        <a class="btn btn-default btn-sm<?php echo (count($ipHosts) == 0) ? ' disabled' : ''; ?>" id="bt_ttscastAddIpHosts"
            data-hosts="<?php echo htmlspecialchars(json_encode($ipHosts), ENT_QUOTES, 'UTF-8'); ?>"
            title="<?php echo (count($ipHosts) == 0) ? '{{Aucun équipement mis à jour via son adresse IP}}' : '{{Ajoute à la saisie l\'adresse des équipements mis à jour via leur adresse IP (badge IP), actifs ou non : pour les mettre à jour, ou vérifier qu\'ils répondent}}'; ?>">
            <i class="fas fa-list"></i> {{Ajouter les adresses des équipements IP}}
        </a>
    </div>
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
