/*
===================================================================
VERSIONE PER LIZ 3.8
Catturare le coordinate del punto di click e copiarle negli appunti
===================================================================
*/

(function () {
  var TOOL_ID = 'CoordCapture';
  var active = false;
  var clickKey = null;
  var map = null;
  var coordBox = null;
  var currentCoords = null;
  var defsInitialized = false;

  // EPSG:3857 → EPSG:4326
  function mercatorToLonLat(x, y) {
    var R = 6378137.0;
    var lon = (x / R) * 180.0 / Math.PI;
    var lat = (2 * Math.atan(Math.exp(y / R)) - (Math.PI / 2)) * 180.0 / Math.PI;
    return [lon, lat];
  }

  // Lazy-load proj4js
  function ensureProj4(callback) {
    if (typeof proj4 !== 'undefined') return callback();
    var s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/proj4@2.9.0/dist/proj4.min.js';
    s.onload = function () { callback(); };
    s.onerror = function () { console.error('[coord_ext] Impossibile caricare proj4js'); callback(true); };
    document.head.appendChild(s);
  }

  // Definizioni EPSG
  function initProjDefs() {
    if (defsInitialized || typeof proj4 === 'undefined') return;
    proj4.defs('EPSG:4326', '+proj=longlat +datum=WGS84 +no_defs');
    proj4.defs('EPSG:3003', '+proj=tmerc +lat_0=0 +lon_0=9 +k=0.9996 +x_0=1500000 +y_0=0 +ellps=intl +towgs84=-225,-65,9,0,0,0,0 +units=m +no_defs');
    proj4.defs('EPSG:32632', '+proj=utm +zone=32 +datum=WGS84 +units=m +no_defs');
    defsInitialized = true;
  }

  function transformCoordsFrom4326(lon, lat, targetEpsg) {
    initProjDefs();
    if (typeof proj4 === 'undefined') return { x: lon, y: lat, projected: false };
    try {
      var out = proj4('EPSG:4326', targetEpsg, [lon, lat]);
      return { x: out[0], y: out[1], projected: true };
    } catch (e) {
      console.error('[coord_ext] Errore trasformazione verso ' + targetEpsg + ':', e);
      return { x: lon, y: lat, projected: false };
    }
  }

  // UI box con menu + bottone + X
  function ensureCoordBox() {
    if (coordBox) return;
    coordBox = document.createElement('div');
    coordBox.setAttribute('style',
      'position:absolute; bottom:10px; left:10px; width:300px;' +
      'background:white; padding:8px; border:1px solid #333; border-radius:4px;' +
      'box-shadow:0 2px 6px rgba(0,0,0,.25); z-index:99999; font:12px/1.4 sans-serif;'
    );
    coordBox.innerHTML =
      '<div style="display:flex; justify-content:space-between; align-items:center;">' +
        '<strong>Coordinate:</strong>' +
        '<span id="close-btn" style="cursor:pointer; font-weight:bold; color:#900;">✖</span>' +
      '</div>' +
      '<div id="coord-values">Clicca un punto sulla mappa</div>' +
      '<label for="sr-select" style="display:block; margin-top:6px;">Sistema di riferimento:</label>' +
      '<select id="sr-select" style="width:100%; margin-bottom:6px;">' +
        '<option value="EPSG:4326">EPSG:4326 (Lat/Lon)</option>' +
        '<option value="EPSG:3003">EPSG:3003 (Gauss-Boaga Ovest)</option>' +
        '<option value="EPSG:32632">EPSG:32632 (UTM 32N)</option>' +
      '</select>' +
      '<button id="copy-btn" style="margin-top:6px; padding:4px 8px; font-size:12px;">📋 Copia negli appunti</button>';

    document.body.appendChild(coordBox);

    document.getElementById('sr-select').addEventListener('change', renderCoordinates);

    // Chiudi con la X
    document.getElementById('close-btn').addEventListener('click', function () {
      deactivate();
    });

    // Copia tutte le proiezioni
    document.getElementById('copy-btn').addEventListener('click', function () {
      if (!currentCoords) return;
      var latlon = "Lat: " + currentCoords.lat.toFixed(6) + ", Lon: " + currentCoords.lon.toFixed(6) + " (EPSG:4326)";
      var t3003 = transformCoordsFrom4326(currentCoords.lon, currentCoords.lat, "EPSG:3003");
      var xy3003 = "X: " + t3003.x.toFixed(2) + ", Y: " + t3003.y.toFixed(2) + " (EPSG:3003)";
      var t32632 = transformCoordsFrom4326(currentCoords.lon, currentCoords.lat, "EPSG:32632");
      var xy32632 = "X: " + t32632.x.toFixed(2) + ", Y: " + t32632.y.toFixed(2) + " (EPSG:32632)";
      var text = latlon + "\n" + xy3003 + "\n" + xy32632;
      navigator.clipboard.writeText(text).then(function () {
        alert("Coordinate copiate negli appunti:\n\n" + text);
      });
    });
  }

  function renderCoordinates() {
    var el = document.getElementById('coord-values');
    if (!el || !currentCoords) return;
    var sr = document.getElementById('sr-select').value;
    if (sr === 'EPSG:4326') {
      el.innerHTML = "Lat: " + currentCoords.lat.toFixed(6) + "<br>Lon: " + currentCoords.lon.toFixed(6);
    } else {
      var t = transformCoordsFrom4326(currentCoords.lon, currentCoords.lat, sr);
      el.innerHTML = "X: " + t.x.toFixed(2) + "<br>Y: " + t.y.toFixed(2) + " (" + sr + ")";
    }
  }

  function activate() {
    if (active) return;
    active = true;
    map = lizMap.mainLizmap.map;
    ensureCoordBox();
    ensureProj4(function () {});
    clickKey = function (evt) {
      var coords = evt.coordinate;
      var lonlat = mercatorToLonLat(coords[0], coords[1]);
      currentCoords = { lon: lonlat[0], lat: lonlat[1] };
      renderCoordinates();
    };
    map.on('singleclick', clickKey);
    document.addEventListener('keydown', escHandler);
  }

  function deactivate() {
    if (!active) return;
    active = false;
    if (clickKey) { map.un('singleclick', clickKey); clickKey = null; }
    if (coordBox && coordBox.parentNode) { coordBox.parentNode.removeChild(coordBox); coordBox = null; }
    document.removeEventListener('keydown', escHandler);
    $('#mapmenu li.' + TOOL_ID + ' a').css('background', '');
  }

  function escHandler(evt) { if (evt.key === 'Escape') deactivate(); }

  lizMap.events.on({
    uicreated: function () {
      lizMap.addDock(
        TOOL_ID,
        'Cattura coordinate',
        'rightdock',
        '<div style="padding:8px">Clicca il pulsante e poi un punto sulla mappa.</div>',
        'icon-map-marker'
      );
      $('#mapmenu').on('click', 'li.' + TOOL_ID + ' a', function () {
        if (active) { deactivate(); } else { activate(); $(this).css('background', 'blue'); }
      });
    }
  });
})();
