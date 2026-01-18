//VERSIONE PER LIZ 3.8
//=========================================
(function () {
  var TOOL_ID = 'Streetview';
  var active = false;
  var clickKey = null;
  var overlayMsg = null;
  var map = null;

  function log() {
    if (window.console) console.log.apply(console, ['[streetview_ext]'].concat([].slice.call(arguments)));
  }

  // Messaggio overlay
  function showMessage() {
    if (overlayMsg) return;
    overlayMsg = document.createElement('div');
    overlayMsg.textContent = 'Street View attivo: clicca sulla mappa (ESC per uscire)';
    overlayMsg.setAttribute('style',
      'position:absolute; top:8px; right:8px; padding:6px 8px; ' +
      'background:#1f2937; color:#ff0000; font:12px/1.2 sans-serif; ' +
      'border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,.25); z-index:99999;'
    );
    document.body.appendChild(overlayMsg);
  }

  function hideMessage() {
    if (overlayMsg && overlayMsg.parentNode) {
      overlayMsg.parentNode.removeChild(overlayMsg);
      overlayMsg = null;
    }
  }

  // Conversione EPSG:3857 → EPSG:4326
  function mercatorToLonLat(x, y) {
    var R = 6378137.0;
    var lon = (x / R) * 180.0 / Math.PI;
    var lat = (2 * Math.atan(Math.exp(y / R)) - (Math.PI / 2)) * 180.0 / Math.PI;
    return [lon, lat];
  }

  // --- ATTIVA ---
  function activate() {
    if (active) return;
    active = true;

    map = lizMap.mainLizmap.map;
    showMessage();

    clickKey = function (evt) {
      evt.preventDefault();
      evt.stopPropagation();

      try {
        var coords = evt.coordinate;
        var lonlat = mercatorToLonLat(coords[0], coords[1]);
        var lon = lonlat[0];
        var lat = lonlat[1];

        var url = 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=' + lat + ',' + lon;
        window.open(url, '_blank');
        log('Aperto Street View a lat=' + lat + ', lon=' + lon);
      } catch (e) {
        console.error('[streetview_ext] Errore trasformazione coordinate:', e);
      }
    };
    map.on('singleclick', clickKey);

    document.addEventListener('keydown', escHandler);
    log('Street View attivo');
  }

  // --- DISATTIVA ---
  function deactivate() {
    if (!active) return;
    active = false;

    if (clickKey) {
      map.un('singleclick', clickKey);
      clickKey = null;
    }

    hideMessage();
    document.removeEventListener('keydown', escHandler);
    log('Street View disattivato');

    $('#mapmenu li.' + TOOL_ID + ' a').css('background', '');
  }

  function escHandler(evt) {
    if (evt.key === "Escape") {
      deactivate();
    }
  }

  // --- UI Lizmap ---
  lizMap.events.on({
    uicreated: function () {
      lizMap.addDock(
        TOOL_ID,
        'Street View (nuova scheda)',
        'rightdock',
        '<div style="padding:8px">Clicca il pulsante e poi un punto sulla mappa.</div>',
        'icon-road'
      );

      $('#mapmenu').on('click', 'li.' + TOOL_ID + ' a', function () {
        if (active) {
          deactivate();
        } else {
          activate();
          $(this).css('background', 'red');
        }
      });
    }
  });
})();
