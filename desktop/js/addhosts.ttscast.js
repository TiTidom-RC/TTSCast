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

(() => {
'use strict'

const AJAX_URL = 'plugins/ttscast/core/ajax/ttscast.ajax.php'
const EVENT_NAME = 'ttscast::hostSearch'
// Le démon interroge les adresses en parallèle (8 s max par requête), puis les groupes des appareils multizone
const RESPONSE_TIMEOUT = 90000

// État de la fenêtre tenu sur window et non dans ce script : s'il est exécuté plusieurs fois (fenêtre rechargée), le compte rendu
// et la fermeture pourraient sinon lire deux copies différentes :
// - ttscastAddHostsSearchId : Scan (IP) en cours (identifiant renvoyé par startHostSearch)
// - ttscastAddHostsChanged : équipements ajoutés / mis à jour (rechargement de la page à la fermeture)
// Délai d'attente du compte rendu
let responseTimeout = null

const TYPE_LABELS = {
    device: '{{Appareil}}',
    group: '{{Groupe}}'
}

const STATUS_LABELS = {
    created: '{{Ajouté}}',
    updated: '{{Mis à jour}}',
    failed: '{{Échec de l\'enregistrement de l\'équipement (voir les logs)}}'
}

const ERROR_LABELS = {
    invalid: '{{Adresse invalide (adresse IP ou nom d\'hôte attendu ; les adresses link-local ne sont pas acceptées)}}',
    unresolved: '{{Nom introuvable (DNS)}}',
    noDevice: '{{Aucun appareil Cast ne répond à cette adresse}}'
}

function formatAddress(host, port) {
    const address = (host && host.indexOf(':') !== -1) ? '[' + host + ']' : (host || '')
    return port ? address + ':' + port : address
}

function addRow(icon, iconColor, address, device, result) {
    const tbody = document.getElementById('tb_ttscastHostsResults')
    if (!tbody) return
    const row = document.createElement('tr')
    const tdIcon = document.createElement('td')
    tdIcon.style.textAlign = 'center'
    const i = document.createElement('i')
    i.className = 'fas ' + icon
    i.style.color = iconColor
    tdIcon.appendChild(i)
    row.appendChild(tdIcon)
    for (const text of [address, device, result]) {
        const td = document.createElement('td')
        td.textContent = text
        row.appendChild(td)
    }
    tbody.appendChild(row)
}

function setBusy(busy) {
    const button = document.getElementById('bt_ttscastSearchHosts')
    if (!button) return
    button.classList.toggle('disabled', busy)
    button.innerHTML = busy ? '<i class="fas fa-spinner fa-spin"></i> {{Scan (IP) en cours...}}' : button.dataset.label
}

function renderReport(report) {
    const tbody = document.getElementById('tb_ttscastHostsResults')
    const container = document.getElementById('div_ttscastHostsResults')
    if (!tbody || !container) return
    tbody.innerHTML = ''

    if (report.error === 'disabled') {
        // Option cochée dans la configuration, mais démon lancé avant son activation
        jeedomUtils.showAlert({ message: '{{La découverte par IP est activée dans la configuration, mais le démon n\'a pas encore été redémarré : redémarrez-le pour l\'appliquer}}', level: 'warning' })
        container.style.display = 'none'
        return
    }
    if (report.error) {
        jeedomUtils.showAlert({ message: '{{Erreur du démon pendant le Scan (IP) : consultez les logs}}', level: 'danger' })
    }

    for (const device of (Array.isArray(report.devices) ? report.devices : [])) {
        const ok = device.status !== 'failed'
        if (ok) window.ttscastAddHostsChanged = true
        addRow(ok ? 'fa-check-circle' : 'fa-times-circle', ok ? 'var(--al-success-color)' : 'var(--al-danger-color)',
            formatAddress(device.host, device.port),
            device.friendly_name + ' (' + (TYPE_LABELS[device.type] || device.type) + ')',
            ok ? STATUS_LABELS[device.status] + ' : ' + (device.eqName || device.friendly_name) : STATUS_LABELS.failed)
    }
    for (const error of (Array.isArray(report.errors) ? report.errors : [])) {
        addRow('fa-times-circle', 'var(--al-danger-color)', error.input, '—', ERROR_LABELS[error.reason] || error.reason)
    }
    for (const group of (Array.isArray(report.groupsNotAdded) ? report.groupsNotAdded : [])) {
        addRow('fa-info-circle', 'var(--al-info-color)', formatAddress(group.host),
            group.friendly_name + ' (' + TYPE_LABELS.group + ')',
            '{{Hébergé par}} ' + group.host + ' : {{non ajouté, saisissez cette adresse pour l\'inclure}}')
    }

    if (tbody.children.length === 0) {
        addRow('fa-info-circle', 'var(--al-info-color)', '—', '—', '{{Aucun résultat}}')
    }
    container.style.display = ''
}

// Compte rendu poussé par Jeedom (rappel du démon) : seul celui du Scan (IP) lancé depuis cette fenêtre est pris en compte
function onHostSearch(event) {
    const report = event.detail || {}
    if (!window.ttscastAddHostsSearchId || report.searchId !== window.ttscastAddHostsSearchId) return
    clearTimeout(responseTimeout)
    window.ttscastAddHostsSearchId = ''
    setBusy(false)
    renderReport(report)
}

function startHostSearch() {
    const button = document.getElementById('bt_ttscastSearchHosts')
    const input = document.getElementById('ta_ttscastHosts')
    if (!button || !input || button.classList.contains('disabled')) return
    if (input.value.trim() === '') {
        jeedomUtils.showAlert({ message: '{{Saisissez au moins une adresse IP ou un nom d\'hôte}}', level: 'warning' })
        return
    }
    setBusy(true)
    domUtils.ajax({
        type: 'POST',
        url: AJAX_URL,
        data: { action: 'startHostSearch', hosts: input.value },
        dataType: 'json',
        error: function(request) {
            setBusy(false)
            jeedomUtils.showAlert({ message: (request.responseJSON && request.responseJSON.result) || '{{Erreur lors du lancement du Scan (IP)}}', level: 'danger' })
        },
        success: function(data) {
            if (data.state !== 'ok') {
                setBusy(false)
                jeedomUtils.showAlert({ message: data.result, level: 'danger' })
                return
            }
            window.ttscastAddHostsSearchId = data.result
            clearTimeout(responseTimeout)
            responseTimeout = setTimeout(function() {
                window.ttscastAddHostsSearchId = ''
                setBusy(false)
                jeedomUtils.showAlert({ message: '{{Pas de réponse du démon : consultez les logs}}', level: 'warning' })
            }, RESPONSE_TIMEOUT)
        }
    })
}

// Ajoute à la saisie l'adresse des équipements mis à jour via leur adresse IP (sans doublon avec ce qui est déjà saisi)
function addIpHosts(event) {
    const button = event.currentTarget
    const input = document.getElementById('ta_ttscastHosts')
    if (!input || button.classList.contains('disabled')) return
    let hosts = []
    try {
        hosts = JSON.parse(button.dataset.hosts || '[]')
    } catch (e) {
        hosts = []
    }
    const typed = input.value.split(/[\s,;]+/).filter(function(value) { return value !== '' })
    const missing = hosts.filter(function(host) { return typed.indexOf(host) === -1 })
    if (missing.length === 0) return
    input.value = typed.concat(missing).join('\n')
}

window.initAddHosts = function() {
    window.ttscastAddHostsSearchId = ''
    window.ttscastAddHostsChanged = false
    const button = document.getElementById('bt_ttscastSearchHosts')
    if (button) {
        button.dataset.label = button.innerHTML
        button.addEventListener('click', startHostSearch)
    }
    const ipHostsButton = document.getElementById('bt_ttscastAddIpHosts')
    if (ipHostsButton) {
        ipHostsButton.addEventListener('click', addIpHosts)
    }
    // Inscription unique : une réouverture de la fenêtre remplace l'écouteur précédent
    if (window.ttscastHostSearchHandler) {
        document.body.removeEventListener(EVENT_NAME, window.ttscastHostSearchHandler)
    }
    window.ttscastHostSearchHandler = onHostSearch
    document.body.addEventListener(EVENT_NAME, window.ttscastHostSearchHandler)
}

// Fermeture de la fenêtre : retire l'écouteur et indique si des équipements ont été ajoutés / mis à jour (rechargement de la page)
window.closeAddHosts = function() {
    clearTimeout(responseTimeout)
    if (window.ttscastAddHostsSearchId) {
        // Le démon termine la recherche et les équipements sont bien ajoutés, mais le compte rendu ne sera plus affiché
        jeedomUtils.showAlert({ message: '{{Scan (IP) en cours : rafraîchissez la page dans quelques secondes pour voir les équipements ajoutés}}', level: 'info' })
    }
    window.ttscastAddHostsSearchId = ''
    if (window.ttscastHostSearchHandler) {
        document.body.removeEventListener(EVENT_NAME, window.ttscastHostSearchHandler)
        window.ttscastHostSearchHandler = null
    }
    return window.ttscastAddHostsChanged === true
}

})()
