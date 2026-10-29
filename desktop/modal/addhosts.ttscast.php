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

<div class="alert alert-info" style="margin-bottom:10px;">
    <i class="fas fa-info-circle"></i> {{Saisissez une ou plusieurs adresses IP (IPv4 ou IPv6) ou noms d'hôte, une par ligne ou séparées par des virgules ou des espaces.}}<br>
    {{Les appareils Cast qui répondent, ainsi que les groupes qu'ils hébergent, sont ajoutés ou mis à jour.}}
</div>

<div style="display:flex; gap:8px; justify-content:space-between; flex-wrap:wrap; margin-bottom:8px;">
    <!-- Infobulle sur l'enveloppe : un bouton .disabled ne reçoit pas le survol (pointer-events: none), son title ne s'afficherait pas -->
    <span title="<?php echo (count($ipHosts) == 0) ? '{{Aucun équipement existant mis à jour via son adresse IP (badge IP) : lancez d\'abord un Scan (IP)}}' : '{{Ajoute à la saisie l\'adresse des équipements existants mis à jour via leur adresse IP (badge IP), actifs ou non : pour les mettre à jour, ou vérifier qu\'ils répondent}}'; ?>">
        <a class="btn btn-default btn-sm<?php echo (count($ipHosts) == 0) ? ' disabled' : ''; ?>" id="bt_ttscastAddIpHosts"
            data-hosts="<?php echo htmlspecialchars(json_encode($ipHosts), ENT_QUOTES, 'UTF-8'); ?>">
            <i class="fas fa-list"></i> {{Ajouter les adresses des équipements IP existants}}
        </a>
    </span>
    <a class="btn btn-success btn-sm" id="bt_ttscastSearchHosts">
        <i class="fas fa-network-wired"></i> {{Lancer le Scan (IP)}}
    </a>
</div>

<textarea class="form-control" id="ta_ttscastHosts" rows="5" style="width:100%; font-family:monospace; margin-bottom:10px;" placeholder="192.168.1.20&#10;192.168.1.21, 192.168.1.22&#10;2001:db8::20&#10;nest-salon.lan"></textarea>

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
