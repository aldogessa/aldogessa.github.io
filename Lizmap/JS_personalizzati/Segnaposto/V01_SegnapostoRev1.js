/* 
======================================================================
AGis - Aldo Gessa
Segnaposto.js – versione finale robusta e 
con bottone sempre in fondo 
Maggio 2026
Prossimo refactoring: sostituire l'icona di google con una
icona personalizzata servita dal servere Gter (per maggiore sicurezza)
======================================================================
*/

(function () {

  if (window.__SEGNAPOSTO_INITIALIZED__) return;
  window.__SEGNAPOSTO_INITIALIZED__ = true;

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
        document.querySelector('lizmap-navbar')
      ) {

        clearInterval(i);

        lizMap.events.on({ uicreated: run });

        setTimeout(run, 500);
      }

      if (attempts > 300) {
        clearInterval(i);
        console.warn('Segnaposto: Lizmap non inizializzato');
      }

    }, 100);
  }

  /* ---------------------------------------------------------
     SCRIPT PRINCIPALE
  --------------------------------------------------------- */
  lizmapReady(function () {

    let markerActive = true;
    let markerEl = null;
    let lastCoord = null;

    const olMap =
      lizMap.mainLizmap.map._map ||
      lizMap.mainLizmap.map.olMap ||
      lizMap.mainLizmap.map;

    /* ---------------------------------------------------------
       MARKER
    --------------------------------------------------------- */
    function ensureMarkerEl() {

      if (markerEl) return markerEl;

      const target = document.querySelector('.ol-overlaycontainer-stopevent');
      if (!target) return null;

      const cs = window.getComputedStyle(target);
      if (cs.position === 'static') target.style.position = 'relative';

      markerEl = document.createElement('img');
      markerEl.src = 'https://maps.google.com/mapfiles/ms/icons/red-dot.png';

      Object.assign(markerEl.style, {
        position: 'absolute',
        transform: 'translate(-50%, -100%)',
        width: '32px',
        height: '32px',
        zIndex: 1,
        pointerEvents: 'none'
      });

      target.appendChild(markerEl);
      return markerEl;
    }

    function updateMarkerPosition() {
      if (!lastCoord) return;

      const el = ensureMarkerEl();
      if (!el) return;

      const px = olMap.getPixelFromCoordinate(lastCoord);
      if (!px) return;

      el.style.left = px[0] + 'px';
      el.style.top = px[1] + 'px';
    }

    function setMarkerAt(coord3857) {
      lastCoord = coord3857;
      updateMarkerPosition();
    }

    function removeMarker() {
      lastCoord = null;

      if (markerEl && markerEl.parentNode) {
        markerEl.parentNode.removeChild(markerEl);
      }

      markerEl = null;
    }

    /* ---------------------------------------------------------
       BUTTON
    --------------------------------------------------------- */
    function createButton() {

      const btn = document.createElement('button');
      btn.className = 'btn segnaposto';
      btn.title = 'Attiva/Disattiva segnaposto';

      btn.innerHTML =
        '<img src="https://maps.google.com/mapfiles/ms/icons/red-dot.png" ' +
        'style="width:24px; height:24px;">';

      Object.assign(btn.style, {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0',
        margin: '0',
        height: '30px',
        width: '30px',
        background: 'lightblue',
        borderRadius: '4px',
        border: '2px solid #000',
        boxSizing: 'border-box'
      });

      btn.addEventListener('click', function () {
        markerActive = !markerActive;

        if (!markerActive) {
          removeMarker();
          btn.style.background = '#fff';
        } else {
          btn.style.background = 'lightblue';
        }
      });

      return btn;
    }

    /* ---------------------------------------------------------
       NAVBAR — VERSIONE ORIGINALE (FUNZIONA SEMPRE)
    --------------------------------------------------------- */
    function waitForNavbarAndInsertButton() {

      const navbar = document.querySelector('lizmap-navbar');

      if (!navbar) {

        const obs = new MutationObserver(() => {

          const nb = document.querySelector('lizmap-navbar');

          if (nb) {
            obs.disconnect();
            setupButton(nb);
          }
        });

        obs.observe(document.body, { childList: true, subtree: true });
        return;
      }

      setupButton(navbar);
    }

    function setupButton(navbar) {

      const btn = createButton();
      navbar.appendChild(btn); // SEMPRE IN FONDO

      const navObs = new MutationObserver(() => {

        if (navbar.lastElementChild !== btn) {
          navbar.appendChild(btn); // RIPRISTINA POSIZIONE
        }
      });

      navObs.observe(navbar, { childList: true });
    }

    /* ---------------------------------------------------------
       EVENTI MAPPA
    --------------------------------------------------------- */
    olMap.on('singleclick', function (evt) {
      if (!markerActive) return;
      setMarkerAt(evt.coordinate);
    });

    olMap.on('moveend', updateMarkerPosition);

    /* ---------------------------------------------------------
       OVERLAY OBSERVER ROBUSTO
    --------------------------------------------------------- */
    const overlayObserver = new MutationObserver(() => {

      if (document.querySelector('.ol-overlaycontainer-stopevent')) {
        ensureMarkerEl();
        updateMarkerPosition();
      }
    });

    const mapContainer = document.querySelector('#map');

    if (mapContainer) {
      overlayObserver.observe(mapContainer, {
        childList: true,
        subtree: true
      });
    }

    /* ---------------------------------------------------------
       FALLBACK FINALE
    --------------------------------------------------------- */
    let attempts = 0;

    const fallback = setInterval(() => {

      attempts++;

      if (markerEl || attempts > 10) {
        clearInterval(fallback);
        return;
      }

      ensureMarkerEl();
      updateMarkerPosition();

    }, 500);

    /* ---------------------------------------------------------
       AVVIO
    --------------------------------------------------------- */
    waitForNavbarAndInsertButton();

  });

})();
