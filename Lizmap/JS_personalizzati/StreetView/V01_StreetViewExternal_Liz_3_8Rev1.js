/* 
==========================================================================
AGis - Aldo Gessa
Streetview.js – versione finale robusta 
Apre Street View alle cordinate di click in una nuova finestra del browser
Maggio 2026
==========================================================================
*/
(function () {

  // Protezione doppio caricamento
  if (window.__STREETVIEW_INITIALIZED__) return;
  window.__STREETVIEW_INITIALIZED__ = true;

  /* ---------------------------------------------------------
     WRAPPER ROBUSTO LIZMAP
  --------------------------------------------------------- */
  function lizmapReady(callback) {

    let done = false;

    function run() {
      if (done) return;
      done = true;
      callback();
    }

    let attempts = 0;

    const i = setInterval(() => {

      attempts++;

      if (
        window.lizMap &&
        lizMap.mainLizmap?.map &&
        $('#mapmenu').length
      ) {

        clearInterval(i);

        lizMap.events.on({ uicreated: run });

        setTimeout(run, 500);
      }

      if (attempts > 300) {
        clearInterval(i);
        console.warn('Streetview: Lizmap non inizializzato');
      }

    }, 100);
  }

  /* ---------------------------------------------------------
     SCRIPT PRINCIPALE
  --------------------------------------------------------- */
  lizmapReady(function () {

    const TOOL_ID = 'Streetview';

    let active = false;
    let clickKey = null;
    let overlayMsg = null;

    // Mappa OpenLayers compatibile con tutte le versioni Lizmap
    const olMap =
      lizMap.mainLizmap.map._map ||
      lizMap.mainLizmap.map.olMap ||
      lizMap.mainLizmap.map;

    function log() {
      if (window.console) {
        console.log.apply(console, ['[streetview_ext]'].concat([].slice.call(arguments)));
      }
    }

    /* ---------------------------------------------------------
       OVERLAY MESSAGGIO
    --------------------------------------------------------- */
    function showMessage() {

      if (overlayMsg) return;

      overlayMsg = document.createElement('div');

      overlayMsg.innerHTML =
        '<div style="margin-bottom:8px;">Street View attivo<br>Clicca sulla mappa</div>' +
        '<button id="sv-exit-btn" style="' +
          'padding:6px 14px;' +
          'background:#ff4d4d;' +
          'color:white;' +
          'border:none;' +
          'border-radius:6px;' +
          'font-size:14px;' +
          'cursor:pointer;' +
        '">ESCI</button>';

      overlayMsg.setAttribute('style',
        'position:absolute;' +
        'top:20px;' +
        'left:50%;' +
        'transform:translateX(-50%);' +
        'padding:14px 20px;' +
        'background:rgba(0,0,0,0.65);' +
        'color:#fff;' +
        'font:15px/1.4 sans-serif;' +
        'text-align:center;' +
        'border-radius:10px;' +
        'box-shadow:0 2px 8px rgba(0,0,0,.35);' +
        'z-index:99999;' +
        'pointer-events:auto;' +
        'backdrop-filter:blur(4px);'
      );

      document.querySelector('#map').appendChild(overlayMsg);

      document.getElementById('sv-exit-btn')
        .addEventListener('click', deactivate);
    }

    function hideMessage() {
      if (overlayMsg && overlayMsg.parentNode) {
        overlayMsg.parentNode.removeChild(overlayMsg);
        overlayMsg = null;
      }
    }

    /* ---------------------------------------------------------
       CONVERSIONE COORDINATE
    --------------------------------------------------------- */
    function mercatorToLonLat(x, y) {
      const R = 6378137.0;
      const lon = (x / R) * 180.0 / Math.PI;
      const lat = (2 * Math.atan(Math.exp(y / R)) - Math.PI / 2) * 180.0 / Math.PI;
      return [lon, lat];
    }

    /* ---------------------------------------------------------
       ATTIVA
    --------------------------------------------------------- */
    function activate() {

      if (active) return;
      active = true;

      showMessage();

      clickKey = function (evt) {

        if (evt.preventDefault) evt.preventDefault();
        if (evt.stopPropagation) evt.stopPropagation();

        try {
          const coords = evt.coordinate;
          const lonlat = mercatorToLonLat(coords[0], coords[1]);

          const url =
            'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=' +
            lonlat[1] + ',' + lonlat[0];

          window.open(url, '_blank');

          log('Aperto Street View a lat=' + lonlat[1] + ', lon=' + lonlat[0]);

        } catch (e) {
          console.error('[streetview_ext] Errore trasformazione coordinate:', e);
        }
      };

      olMap.on('singleclick', clickKey);

      document.addEventListener('keydown', escHandler);

      log('Street View attivo');
    }

    /* ---------------------------------------------------------
       DISATTIVA
    --------------------------------------------------------- */
    function deactivate() {

      if (!active) return;
      active = false;

      if (clickKey) {
        olMap.un('singleclick', clickKey);
        clickKey = null;
      }

      hideMessage();

      document.removeEventListener('keydown', escHandler);

      $('#mapmenu li.' + TOOL_ID + ' a').css({
        background: '',
        color: ''
      });

      log('Street View disattivato');
    }

    function escHandler(evt) {
      if (evt.key === 'Escape') deactivate();
    }

    /* ---------------------------------------------------------
       UI LIZMAP
    --------------------------------------------------------- */
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
        $(this).css({
          background: '#ff4d4d',
          color: 'white'
        });
      }
    });

  }); // fine lizmapReady

})(); // fine IIFE
