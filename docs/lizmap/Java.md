<div style="display:flex; align-items:center; gap:15px;">

  <img src="../risorse/immagini/Icona.png" alt="AGis" width="60">

  <h1 style="margin:0;">AMPLIARE LIZMAP CON JAVASCRIPT</h1>

</div>

<div style="max-width:800px; width:100%;">

## Cosa si può fare con JavaScript
Lizmap è un progetto open sourse con codice aperto e può essere manipolato e ampliato anche con codice Javascript. Dalla documentazione ufficiale si possono cogliere gli elementi essenziali per manipolare Lizmap con JavaScript. La sezione del manuale di Lizmap dedicata al JavaScript è raggiungibile al seguente link:

<a href="https://docs.lizmap.com/current/it/publish/customization/javascript.html" target="_blank"
   style="display:inline-block; padding:10px 15px; background:#2c7be5; color:white; border-radius:6px; text-decoration:none;">
 🌍 Manuale Lizmap - JavaScrip
</a>

---

## Il mio JavaScript
Con il tempo, e con l'aiuto dell'intelligenza artificiale ho realizzato alcuni JavaScript che permettono di aggiungere diverse funzionalità alle mappe:

- Street View in una nuova finestra del browser;
- Cattura coordinate;
- Deseleziona tutto velocemente;
- Genera CDU automatizzato;
- Vedi somma valori;
- Esporta Tabella valori.

---

## Street View in una nuova finestra
Questo script crea un Tool che al click sulla mappa apre, in una nuova finestra del browser, Strett View alle coordinate del punto cliccato:

```javascript
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
```

---

## Cattura coordinate
Questo script cattura le coordinate del punto cliccato e le salva negli appunti per poterle copiare in un qualsiasi file di testo:

```javascript
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
```







</div>




