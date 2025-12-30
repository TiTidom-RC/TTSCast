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

// Protect against multiple script loads (Jeedom SPA navigation, cache, etc.)
(function() {
'use strict'

// Constants for better maintainability and performance
const AJAX_URL = 'plugins/ttscast/core/ajax/ttscast.ajax.php'

// DOM Selectors constants (better minification + no string repetition + immutable)
const SELECTORS = Object.freeze({
  TABLE_CMD: '#table_cmd',
  EQ_ID: '.eqLogicAttr[data-l1key=id]',
  SCAN_BUTTONS: '.customclass-scanState',
  SCAN_ICONS: '.customicon-scanState',
  SCAN_TEXTS: '.customtext-scanState',
  VALUE_SELECT: '.cmdAttr[data-l1key=value]',
  OPEN_LOCATION: '.pluginAction[data-action=openLocation]'
})

// Bridge jQuery events to native CustomEvents (bidirectional, if jQuery is available)
if (typeof jQuery !== 'undefined') {
  const eventsToBridge = ['ttscast::newdevice', 'ttscast::scanState']
  
  eventsToBridge.forEach(eventName => {
    // jQuery → CustomEvents
    $('body').on(eventName, function(event, data) {
      if (event.originalEvent?.__bridged) return  // Prevent infinite loop
      
      const customEvent = new CustomEvent(eventName, {
        detail: data,
        bubbles: true,
        cancelable: true
      })
      customEvent.__bridged = true
      document.body.dispatchEvent(customEvent)
    })
    
    // CustomEvents → jQuery (bidirectional bridge)
    document.body.addEventListener(eventName, (event) => {
      if (event.__jQueryBridged) return  // Prevent infinite loop
      
      const jQueryEvent = $.Event(eventName)
      jQueryEvent.__jQueryBridged = true
      $('body').trigger(jQueryEvent, event.detail)
    })
  })
}

/* Fonction permettant l'affichage des commandes dans l'équipement */
function addCmdToTable(_cmd) {
  if (!isset(_cmd)) {
    _cmd = { configuration: {} }
  }
  if (!isset(_cmd.configuration)) {
    _cmd.configuration = {}
  }

  // Build test buttons
  const testButtons = is_numeric(_cmd.id)
    ? '<a class="btn btn-default btn-xs cmdAction" data-action="configure"><i class="fas fa-cogs"></i></a> <a class="btn btn-default btn-xs cmdAction" data-action="test"><i class="fas fa-rss"></i> {{Tester}}</a>'
    : ''

  // Build complete row HTML with template literals
  const rowHtml = `<td class="hidden-xs"><span class="cmdAttr" data-l1key="id"></span></td>
    <td>
      <div class="input-group">
        <input class="cmdAttr form-control input-sm roundedLeft" data-l1key="name" placeholder="{{Nom de la commande}}">
        <span class="input-group-btn"><a class="cmdAction btn btn-sm btn-default" data-l1key="chooseIcon" title="{{Choisir une icône}}"><i class="fas fa-icons"></i></a></span>
        <span class="cmdAttr input-group-addon roundedRight" data-l1key="display" data-l2key="icon" style="font-size:19px;padding:0 5px 0 0!important;"></span>
      </div>
      <select class="cmdAttr form-control input-sm" data-l1key="value" style="display:none;margin-top:5px;" title="{{Commande info liée}}">
        <option value="">{{Aucune}}</option>
      </select>
    </td>
    <td>
      <span class="type" type="${init(_cmd.type)}">${jeedom.cmd.availableType()}</span>
      <span class="subType" subType="${init(_cmd.subType)}"></span>
    </td>
    <td>
      <label class="checkbox-inline"><input type="checkbox" class="cmdAttr" data-l1key="isVisible"/>{{Afficher}}</label>
      <label class="checkbox-inline"><input type="checkbox" class="cmdAttr" data-l1key="isHistorized"/>{{Historiser}}</label>
      <label class="checkbox-inline"><input type="checkbox" class="cmdAttr" data-l1key="display" data-l2key="invertBinary"/>{{Inverser}}</label>
      <div style="margin-top:7px;">
        <input class="tooltips cmdAttr form-control input-sm" data-l1key="configuration" data-l2key="minValue" placeholder="{{Min}}" title="{{Min}}" style="width:30%;max-width:80px;display:inline-block;margin-right:2px;">
        <input class="tooltips cmdAttr form-control input-sm" data-l1key="configuration" data-l2key="maxValue" placeholder="{{Max}}" title="{{Max}}" style="width:30%;max-width:80px;display:inline-block;margin-right:2px;">
        <input class="tooltips cmdAttr form-control input-sm" data-l1key="unite" placeholder="Unité" title="{{Unité}}" style="width:30%;max-width:80px;display:inline-block;margin-right:2px;">
      </div>
    </td>
    <td><span class="cmdAttr" data-l1key="htmlstate"></span></td>
    <td>
      ${testButtons}
      <i class="fas fa-minus-circle pull-right cmdAction cursor" data-action="remove" title="{{Supprimer la commande}}"></i>
    </td>`

  // Create and configure row element
  const newRow = Object.assign(document.createElement('tr'), {
    className: 'cmd',
    innerHTML: rowHtml
  })
  newRow.setAttribute('data-cmd_id', init(_cmd.id))

  // Cache table body for performance
  const tableBody = document.querySelector(`${SELECTORS.TABLE_CMD} tbody`)
  if (!tableBody) return console.error('Table body not found')

  tableBody.appendChild(newRow)

  // Cache eqLogic ID to avoid multiple DOM queries
  const eqLogicIdElement = document.querySelector(SELECTORS.EQ_ID)
  if (!eqLogicIdElement) return console.error('Equipment ID element not found')

  const eqLogicId = eqLogicIdElement.jeeValue()

  // Populate info commands select using Jeedom native function
  jeedom.eqLogic.buildSelectCmd({
    id: eqLogicId,
    filter: { type: 'info' },
    error: (error) => {
      jeedomUtils.showAlert({ message: error.message, level: 'danger' })
    },
    success: (result) => {
      const valueSelect = newRow.querySelector(SELECTORS.VALUE_SELECT)
      if (valueSelect) {
        valueSelect.insertAdjacentHTML('beforeend', result)
      }
      
      // Set values and update display
      newRow.setJeeValues(_cmd, '.cmdAttr')
      jeedom.cmd.changeType(newRow, init(_cmd.subType))
    }
  })
}

// Event delegation for dynamic elements (optimal: single listener for multiple actions)
document.body.addEventListener('click', (event) => {
  // Handle open location action
  const locationTarget = event.target.closest(SELECTORS.OPEN_LOCATION)
  if (locationTarget) {
    const location = locationTarget.getAttribute('data-location')
    if (location) {
      window.open(location, '_blank', null)
    }
    return
  }

  // Handle scan state buttons
  const scanTarget = event.target.closest(SELECTORS.SCAN_BUTTONS)
  if (scanTarget) {
    const scanState = scanTarget.getAttribute('data-scanState')
    if (scanState) {
      changeScanState(scanState)
    }
    return
  }
})

// Function to change scan state via AJAX
const changeScanState = (_scanState) => {
  domUtils.ajax({
    type: 'POST',
    url: AJAX_URL,
    data: {
      action: 'changeScanState',
      scanState: _scanState
    },
    dataType: 'json',
    error: (request, status, error) => handleAjaxError(request, status, error),
    success: (data) => {
      if (data.state !== 'ok') {
        jeedomUtils.showAlert({ message: data.result, level: 'danger' })
      }
    }
  })
}

// Listen to new device events
document.body.addEventListener('ttscast::newdevice', (event) => {
  const _option = event.detail
  if (!_option) return

  const { friendly_name, newone } = _option
  
  if (friendly_name && newone === '1') {
    jeedomUtils.showAlert({ message: `[SCAN] NEW TTSCast détecté :: ${friendly_name}`, level: 'warning' })
  } else if (friendly_name && newone === '0') {
    jeedomUtils.showAlert({ message: `[SCAN] TTSCast MAJ :: ${friendly_name}`, level: 'warning' })
  }
})

// Listen to scan state events
document.body.addEventListener('ttscast::scanState', (event) => {
  const scanState = event.detail?.scanState

  const scanButtons = document.querySelectorAll(SELECTORS.SCAN_BUTTONS)
  const scanIcons = document.querySelectorAll(SELECTORS.SCAN_ICONS)
  const scanTexts = document.querySelectorAll(SELECTORS.SCAN_TEXTS)

  jeedomUtils.hideAlert()

  const isScanOn = scanState === 'scanOn'

  // Batch DOM updates with for...of (optimal performance)
  for (const el of scanButtons) {
    const currentState = el.getAttribute('data-scanState')
    
    if (isScanOn && currentState === 'scanOn') {
      el.setAttribute('data-scanState', 'scanOff')
      el.removeClass('logoPrimary').addClass('logoSecondary')
    } else if (!isScanOn && currentState === 'scanOff') {
      el.setAttribute('data-scanState', 'scanOn')
      el.removeClass('logoSecondary').addClass('logoPrimary')
    }
  }

  for (const el of scanIcons) {
    if (isScanOn) {
      el.addClass('icon_red')
    } else {
      el.removeClass('icon_red')
    }
  }

  for (const el of scanTexts) {
    el.textContent = isScanOn ? '{{Stop Scan}}' : '{{Scan}}'
  }

  if (isScanOn) {
    jeedomUtils.showAlert({ message: '{{Mode SCAN actif pendant 60 secondes. (Cliquez sur STOP SCAN pour arrêter la découverte des équipements)}}', level: 'warning' })
  } else {
    window.location.reload()
  }
})

})() // End IIFE protection