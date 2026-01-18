/*
=======================================================
VERSIONE FUNZIONANTE IN LIZ 3.8
Segnaposto all'ultimo punto di click sulla mappa
=======================================================
*/

(function () {
  var TOOL_ID = 'Segnaposto';
  var markerActive = true;
  var markerEl = null;
  var lastCoord = null;
  var map = null;

  function ensureMarkerEl() {
    if (markerEl) return markerEl;
    var target = document.querySelector('.ol-overlaycontainer-stopevent');
    if (!target) return null;

    var cs = window.getComputedStyle(target);
    if (cs.position === 'static') target.style.position = 'relative';

    markerEl = document.createElement('img');
    markerEl.src = 'https://maps.google.com/mapfiles/ms/icons/red-dot.png';
    markerEl.style.position = 'absolute';
    markerEl.style.transform = 'translate(-50%, -100%)';
    markerEl.style.width = '32px';
    markerEl.style.height = '32px';
    markerEl.style.zIndex = 1;
    markerEl.style.pointerEvents = 'none';
    target.appendChild(markerEl);
    return markerEl;
  }

  function updateMarkerPosition() {
    if (!lastCoord) return;
    var target = map.getTargetElement();
    if (!target) return;
    var el = ensureMarkerEl();
    if (!el) return;
    var px = map.getPixelFromCoordinate(lastCoord);
    if (!px) return;
    el.style.left = px[0] + 'px';
    el.style.top  = px[1] + 'px';
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

  function insertButtonAtEndOfNavbar() {
    var navbar = document.querySelector('lizmap-navbar');
    if (!navbar) {
      setTimeout(insertButtonAtEndOfNavbar, 300);
      return;
    }

    var btn = document.createElement('button');
    btn.className = 'btn segnaposto';
    btn.title = 'Attiva/Disattiva segnaposto';

    btn.innerHTML = '<img src="https://maps.google.com/mapfiles/ms/icons/red-dot.png" alt="Segnaposto" style="width:24px; height:24px;">';

    btn.style.display = 'flex';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.style.padding = '0';
    btn.style.margin = '0';
    btn.style.height = '30px';
    btn.style.width = '30px';
    btn.style.background = 'lightblue';
    btn.style.borderRadius = '4px';
    btn.style.border = '2px solid #000';
    btn.style.boxSizing = 'border-box';

    btn.addEventListener('click', function () {
      markerActive = !markerActive;
      if (!markerActive) {
        removeMarker();
        btn.style.background = '#fff';
        btn.style.border = '2px solid #000';
      } else {
        btn.style.background = 'lightblue';
        btn.style.border = '2px solid #000';
      }
    });

    navbar.appendChild(btn);
  }

  lizMap.events.on({
    uicreated: function () {
      map = lizMap.mainLizmap.map;

      insertButtonAtEndOfNavbar();

      map.on('singleclick', function (evt) {
        if (!markerActive) return;
        setMarkerAt(evt.coordinate);
      });

      // ✅ Modifica qui: sostituito rendercomplete con moveend
      map.on('moveend', function () {
        updateMarkerPosition();
      });
    }
  });
})();
