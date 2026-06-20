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
const LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'DROP']

function buildLevelSelect(selected) {
    const select = document.createElement('select')
    select.className = 'form-control lf-level'
    LEVELS.forEach(function(l) {
        const opt = document.createElement('option')
        opt.value = l
        opt.textContent = l === 'DROP' ? '---' : l
        opt.selected = l === selected
        select.appendChild(opt)
    })
    return select
}

function addRow(item) {
    item = item || {}
    const container = document.getElementById('logFiltersContainer')
    if (!container) return
    const enabled = item.enabled !== false
    const level   = ((item.level || 'DEBUG') + '').toUpperCase()

    const row = document.createElement('tr')
    row.className = 'logFilterItem'

    const tdCheck = document.createElement('td')
    tdCheck.style.textAlign = 'center'
    const cb = document.createElement('input')
    cb.type = 'checkbox'
    cb.className = 'lf-enabled'
    cb.checked = enabled
    tdCheck.appendChild(cb)

    const tdPattern = document.createElement('td')
    const input = document.createElement('input')
    input.type = 'text'
    input.className = 'form-control lf-pattern'
    input.placeholder = '{{Ex: Failed to connect to service}}'
    input.value = item.pattern || ''
    tdPattern.appendChild(input)

    const tdLevel = document.createElement('td')
    tdLevel.appendChild(buildLevelSelect(level))

    const tdRemove = document.createElement('td')
    tdRemove.style.textAlign = 'center'
    const icon = document.createElement('i')
    icon.className = 'fas fa-minus-circle lf-remove icon_red'
    icon.style.cursor = 'pointer'
    icon.title = '{{Supprimer}}'
    tdRemove.appendChild(icon)

    row.append(tdCheck, tdPattern, tdLevel, tdRemove)
    container.appendChild(row)
}

function collectRows() {
    const rows = document.querySelectorAll('.logFilterItem')
    const result = []
    rows.forEach(function(row) {
        const pattern = row.querySelector('.lf-pattern').value.trim()
        if (!pattern) return
        result.push({
            enabled: row.querySelector('.lf-enabled').checked,
            pattern: pattern,
            level:   row.querySelector('.lf-level').value
        })
    })
    return result
}

window.initLogFilters = function(data) {
    const dataArray = Array.isArray(data) ? data : []
    dataArray.forEach(addRow)

    const addBtn = document.getElementById('bt_addLogFilter')
    if (addBtn) addBtn.addEventListener('click', function() { addRow({}) })

    const container = document.getElementById('logFiltersContainer')
    if (container) {
        container.addEventListener('click', function(e) {
            const btn = e.target.closest('.lf-remove')
            if (btn) btn.closest('.logFilterItem').remove()
        })
    }

    const selectAllBtn = document.getElementById('bt_selectAllLogFilters')
    if (selectAllBtn) selectAllBtn.addEventListener('click', function() {
        document.querySelectorAll('.lf-enabled').forEach(function(cb) { cb.checked = true })
    })

    const unselectAllBtn = document.getElementById('bt_unselectAllLogFilters')
    if (unselectAllBtn) unselectAllBtn.addEventListener('click', function() {
        document.querySelectorAll('.lf-enabled').forEach(function(cb) { cb.checked = false })
    })

    document.querySelectorAll('.ttscast-logfilter-suggest').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault()
            addRow({ pattern: link.dataset.pattern, level: link.dataset.level, enabled: true })
        })
    })

    const saveBtn = document.getElementById('bt_saveLogFilters')
    if (saveBtn) saveBtn.addEventListener('click', function() {
        const filters = collectRows()
        domUtils.ajax({
            type: 'POST',
            url: AJAX_URL,
            data: { action: 'saveLogFilters', logFiltersData: JSON.stringify(filters) },
            dataType: 'json',
            error: function(request) {
                jeedomUtils.showAlert({ message: (request.responseJSON && request.responseJSON.result) || '{{Erreur lors de la sauvegarde}}', level: 'danger' })
            },
            success: function(data) {
                if (data.state !== 'ok') {
                    jeedomUtils.showAlert({ message: data.result, level: 'danger' })
                    return
                }
                jeedomUtils.showAlert({ message: '{{Filtres sauvegardés}} — {{Redémarrez le démon pour appliquer les changements}}', level: 'success' })
            }
        })
    })
}

})()
