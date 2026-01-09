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

<div style="
  border:1px solid #e0e0e0;
  border-radius:6px;
  padding:12px;
  margin:18px 0;
  box-shadow:0 1px 4px rgba(0,0,0,0.06);
  background:#fafafa;
  max-width:800px;
">

  <h3 style="margin:0 0 10px 0; font-size:18px; font-weight:600;">
    🎥 TOOL CATTURA COORDINATE
  </h3>

  <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:4px;">
    <iframe 
      src="https://www.youtube.com/embed/zfuS4VJMftI"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
      style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:4px;">
    </iframe>
  </div>

  <p style="margin-top:8px; font-size:14px;">
    🔗 <a href="https://www.youtube.com/watch?v=zfuS4VJMftI" target="_blank">
      Apri su YouTube
    </a>
  </p>

</div>

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

---

## Deseleziona tutto velocemente
Questo script permette di deselezionare tutti gli elementi con il click di un bottone posto nel Dock senza avviare il Tool di selezione nativo di Lizmap:

<div style="
  border:1px solid #e0e0e0;
  border-radius:6px;
  padding:12px;
  margin:18px 0;
  box-shadow:0 1px 4px rgba(0,0,0,0.06);
  background:#fafafa;
  max-width:800px;
">

  <h3 style="margin:0 0 10px 0; font-size:18px; font-weight:600;">
    🎥 DESELEZIONARE TUTTO VELOCEMENTE
  </h3>

  <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:4px;">
    <iframe 
      src="https://www.youtube.com/embed/LJF1PaDt6UI"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
      style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:4px;">
    </iframe>
  </div>

  <p style="margin-top:8px; font-size:14px;">
    🔗 <a href="https://www.youtube.com/watch?v=LJF1PaDt6UI" target="_blank">
      Apri su YouTube
    </a>
  </p>

</div>

```javascript
/* DeselezionaTutto.js – bottone con conferma multi-layer con titoli leggibili e stato attivo */
(function () {
  var TOOL_ID = 'ClearSelection';
  var activeSelections = {}; // dizionario layer -> featureIds

  function toast(msg, bg) {
    var box = document.createElement('div');
    box.textContent = msg;
    box.style.position = 'absolute';
    box.style.top = '10px'; box.style.left = '50%';
    box.style.transform = 'translateX(-50%)';
    box.style.padding = '8px 12px';
    box.style.background = bg || '#1f2937';
    box.style.color = '#fff';
    box.style.font = '12px/1.2 sans-serif';
    box.style.borderRadius = '6px';
    box.style.boxShadow = '0 2px 6px rgba(0,0,0,.25)';
    box.style.zIndex = 99999;
    document.body.appendChild(box);
    setTimeout(function(){ box.remove(); }, 2000);
  }

  // Recupera il titolo leggibile del layer dalla configurazione Lizmap
  function getLayerTitle(featureType) {
    if (lizMap.config && lizMap.config.layers && lizMap.config.layers[featureType]) {
      return lizMap.config.layers[featureType].title || featureType;
    }
    return featureType;
  }

  function showConfirmDialog(layerNames, onConfirm) {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = 0; overlay.style.left = 0;
    overlay.style.width = '100%'; overlay.style.height = '100%';
    overlay.style.background = 'rgba(0,0,0,0.4)';
    overlay.style.zIndex = 100000;

    const dialog = document.createElement('div');
    dialog.style.position = 'absolute';
    dialog.style.top = '50%'; dialog.style.left = '50%';
    dialog.style.transform = 'translate(-50%, -50%)';
    dialog.style.background = '#fff';
    dialog.style.padding = '20px';
    dialog.style.borderRadius = '8px';
    dialog.style.boxShadow = '0 4px 12px rgba(0,0,0,.3)';
    dialog.style.minWidth = '320px';
    dialog.style.textAlign = 'center';

    const listHtml = layerNames.map(n => {
      const title = getLayerTitle(n);
      const count = activeSelections[n].length;
      return `<li>${title} (${count} selezioni)</li>`;
    }).join('');

    dialog.innerHTML = `
      <p style="margin-bottom:12px; font-weight:bold;">
        Desideri deselezionare tutto dai seguenti layer?
      </p>
      <ul style="margin:0 0 16px; padding:0; list-style:none;">
        ${listHtml}
      </ul>
      <div>
        <button id="btnSi" style="margin:0 8px; padding:6px 12px; background:#16a34a; color:#fff; border:none; border-radius:4px;">Si</button>
        <button id="btnNo" style="margin:0 8px; padding:6px 12px; background:#6b7280; color:#fff; border:none; border-radius:4px;">Annulla</button>
      </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    dialog.querySelector('#btnSi').onclick = function () {
      overlay.remove();
      onConfirm();
    };
    dialog.querySelector('#btnNo').onclick = function () {
      overlay.remove();
    };
  }

  lizMap.events.on({
    uicreated: function () {
      lizMap.addDock(
        TOOL_ID, 'Deseleziona tutto', 'rightdock',
        '<div style="padding:8px">Clicca la stella per svuotare la selezione.</div>',
        'icon-remove'
      );
    },

    // 👉 intercetta ogni cambiamento di selezione
    layerSelectionChanged: function (e) {
      if (!e || !e.featureType) return;
      activeSelections[e.featureType] = Array.isArray(e.featureIds) ? e.featureIds : [];

      // aggiorna stato bottone
      const btn = document.querySelector('li.' + TOOL_ID + ' a');
      if (!btn) return;

      const hasSelection = Object.values(activeSelections).some(arr => arr.length > 0);
      if (hasSelection) {
        btn.style.backgroundColor = '#16a34a';
        btn.style.color = '#fff';
      } else {
        btn.style.backgroundColor = '';
        btn.style.color = '';
      }
    }
  });

  // click sul bottone
  $(document).on('click', 'li.' + TOOL_ID + ' a', function (e) {
    e.preventDefault();

    let layerKeys = Object.keys(activeSelections).filter(k => activeSelections[k].length > 0);

    if (layerKeys.length === 0) {
      toast('Nessuna selezione attiva', '#6b7280');
      return;
    }

    showConfirmDialog(layerKeys, function () {
      try {
        layerKeys.forEach(function (ftype) {
          lizMap.events.triggerEvent('layerfeatureunselectall', {
            featureType: ftype,
            updateDrawing: true
          });
          activeSelections[ftype] = []; // reset
        });
        toast('Selezioni svuotate su tutti i layer!', '#16a34a');
      } catch (err) {
        console.error("❌ Errore unselect all:", err);
        toast('Errore nel deselezionare', '#dc2626');
      }
    });
  });
})();
```

---

## Genera CDU
Questo script permette di generare l'anteprima del certificato di destinazione urbanistica in formato doc e di scaricarlo sul proprio computer. Lo script recupera i dati da una tabella precedentemente predisposta e li copia all'interno di un file preconfigurato:

```javascript
/* Versione solo CDN + template
   - Carica librerie dai CDN ufficiali (multi-CDN + fallback JSZip v2)
   - Bottone menu
   - Lettura padre -> virtid
   - Query figlio -> righe ordinate
   - Merge su .../Template_CDU.docx -> download
*/

(function () {
  // ================== CONFIG ==================
  var TOOL_ID = 'CDUtool';
  var PADRE_NAMES = ['T0B_Particelle', 'T0B_PARTICELLE_CATASTALI_3857'];

  // CDN (multi-fallback)
  var CDN_LIBS = {
    // Proviamo più CDN/versioni per PizZip (3.x)
    pizzip: [
      'https://cdnjs.cloudflare.com/ajax/libs/pizzip/3.2.0/pizzip.min.js',
      'https://cdn.jsdelivr.net/npm/pizzip@3.2.0/dist/pizzip.min.js',
      'https://unpkg.com/pizzip@3.2.0/dist/pizzip.min.js',
      'https://cdnjs.cloudflare.com/ajax/libs/pizzip/3.1.7/pizzip.min.js',
      'https://cdn.jsdelivr.net/npm/pizzip@3.1.7/dist/pizzip.min.js',
      'https://unpkg.com/pizzip@3.1.7/dist/pizzip.min.js'
    ],
    // Docxtemplater
    docxtemplater: [
      'https://cdnjs.cloudflare.com/ajax/libs/docxtemplater/3.42.2/docxtemplater.min.js',
      'https://cdn.jsdelivr.net/npm/docxtemplater@3.42.2/build/docxtemplater.js',
      'https://unpkg.com/docxtemplater@3.42.2/build/docxtemplater.js'
    ],
    // FileSaver
    filesaver: [
      'https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js',
      'https://cdn.jsdelivr.net/npm/file-saver@2.0.5/dist/FileSaver.min.js',
      'https://unpkg.com/file-saver@2.0.5/dist/FileSaver.min.js'
    ],
    // Fallback: JSZip v2 (docxtemplater supporta jszip v2)
    jszip2: [
      'https://cdnjs.cloudflare.com/ajax/libs/jszip/2.7.0/jszip.min.js',
      'https://cdn.jsdelivr.net/npm/jszip@2.7.0/dist/jszip.min.js',
      'https://unpkg.com/jszip@2.7.0/dist/jszip.min.js'
    ]
  };

  // Template unico pubblicato tramite Lizmap getMedia (stessa origin)
  var TEMPLATE_URL = 'https://....inserisci URL al file.....esempio_F00_CDU_Schema.docx';

  // ================== STATE ==================
  var selectedIds = [];
  var ready = false;
  var ZIP_BACKEND = null; // 'pizzip' | 'jszip2' | null

  // ================== UTILS ==================
  function toast(msg, bg) {
    var box = document.createElement('div');
    box.textContent = msg;
    box.style.position = 'absolute';
    box.style.top = '10px';
    box.style.left = '50%';
    box.style.transform = 'translateX(-50%)';
    box.style.padding = '8px 12px';
    box.style.background = bg || '#1f2937';
    box.style.color = 'white';
    box.style.font = '12px/1.2 sans-serif';
    box.style.borderRadius = '6px';
    box.style.boxShadow = '0 2px 6px rgba(0,0,0,.25)';
    box.style.zIndex = 99999;
    document.body.appendChild(box);
    setTimeout(function(){ box.remove(); }, 2500);
  }

  function normalizeLayerName(n) {
    if (!n) return '';
    var out = n.split(':').pop();
    out = out.split('@')[0];
    return out;
  }
  function isPadre(n) { return PADRE_NAMES.indexOf(normalizeLayerName(n)) !== -1; }

  function updateMenuButton() {
    var $a = $('#mapmenu li.' + TOOL_ID + ' a');
    if (!$a.length) return;
    $a.css('background', ready ? '#28a745' : '');
    $a.attr('title', ready ? ('Genera CDU (' + selectedIds.length + ' selezionate)') : 'Seleziona almeno una particella');
  }

  function loadScriptOnce(url) {
    return new Promise(function (resolve, reject) {
      var found = Array.prototype.slice.call(document.getElementsByTagName('script')).some(function(s){
        return s.src && s.src.indexOf(url) !== -1;
      });
      if (found) return resolve();

      var s = document.createElement('script');
      s.src = url;
      s.async = true;
      s.onload = function(){ resolve(); };
      s.onerror = function(){ reject(new Error('load error: ' + url)); };
      document.head.appendChild(s);
    });
  }

  async function tryLoadAny(name, urls, checkFn) {
    for (var i=0;i<urls.length;i++){
      try {
        await loadScriptOnce(urls[i]);
        if (checkFn()) {
          console.log('✅ ' + name + ' caricato:', urls[i]);
          return true;
        }
      } catch (e) {
        console.warn('⚠️ Fallito ' + name + ':', urls[i], e);
      }
    }
    console.error('❌ Impossibile caricare', name);
    return false;
  }

  function ab2bin(ab) {
    // ArrayBuffer -> binary string (per JSZip v2)
    var u8 = new Uint8Array(ab);
    var CHUNK = 0x8000;
    var parts = [];
    for (var i = 0; i < u8.length; i += CHUNK) {
      parts.push(String.fromCharCode.apply(null, u8.subarray(i, i + CHUNK)));
    }
    return parts.join('');
  }

  async function ensureLibs() {
    // Docxtemplater + FileSaver prima (sono indipendenti)
    var okDocx = await tryLoadAny('Docxtemplater', CDN_LIBS.docxtemplater, function(){
      return typeof window.docxtemplater !== 'undefined' || typeof window.Docxtemplater !== 'undefined';
    });
    var okSaver = await tryLoadAny('FileSaver', CDN_LIBS.filesaver, function(){
      return typeof window.saveAs === 'function';
    });

    if (typeof window.docxtemplater === 'undefined' && typeof window.Docxtemplater !== 'undefined') {
      window.docxtemplater = window.Docxtemplater;
    }

    // PizZip (preferito)
    var okPiz = await tryLoadAny('PizZip', CDN_LIBS.pizzip, function(){
      return typeof window.PizZip !== 'undefined';
    });

    if (okPiz) {
      ZIP_BACKEND = 'pizzip';
      console.log('🔧 ZIP backend:', ZIP_BACKEND);
      return okDocx && okSaver;
    }

    console.error('❌ PizZip non disponibile, provo fallback JSZip v2…');
    // Fallback JSZip v2 (docxtemplater supporta solo v2, NON v3)
    var okJS2 = await tryLoadAny('JSZip v2', CDN_LIBS.jszip2, function(){
      return typeof window.JSZip !== 'undefined' && !window.JSZip.prototype.loadAsync; // assicura v2
    });

    if (okJS2) {
      ZIP_BACKEND = 'jszip2';
      console.log('🔧 ZIP backend (fallback):', ZIP_BACKEND);
      return okDocx && okSaver;
    }

    toast('Librerie DOCX non disponibili (PizZip/JSZip)', '#dc2626');
    return false;
  }

  async function fetchTemplateArrayBuffer() {
    var url = TEMPLATE_URL + (TEMPLATE_URL.indexOf('?')>-1 ? '&' : '?') + '_=' + Date.now(); // cache-buster
    console.log('🧩 Carico template:', url);

    var resp = await fetch(url, { credentials: 'same-origin' });
    if (!resp.ok) {
      console.warn('⚠️ Template status:', resp.status, resp.statusText);
      throw new Error('Template CDU non trovato');
    }

    // Se Content-Type è sospetto (es. text/html), mostriamo anteprima testo per debug
    var ctype = (resp.headers.get('content-type') || '').toLowerCase();
    if (ctype && (ctype.indexOf('text/html') !== -1 || ctype.indexOf('text/plain') !== -1)) {
      var preview = await resp.text();
      console.error('❌ Template ha restituito testo/HTML, primi 200 char:\n', preview.slice(0,200));
      throw new Error('Il template non è accessibile (permessi/path).');
    }

    return await resp.arrayBuffer();
  }

  // ================== WFS ==================
  async function getVirtidFromSelection(fidList) {
    const layerName = "T0B_PARTICELLE_CATASTALI_3857";
    const base = "https://...metti_qui_server_hosting/index.php/lizmap/service";
    let virtidList = [];

    for (let fid of fidList) {
      const params = new URLSearchParams({
        repository: "...inserisci_qui_nome_repository...",
        project: "...inserisci_qui_nome_progetto...",
        service: "WFS",
        version: "1.0.0",
        request: "GetFeature",
        typeName: layerName,
        outputFormat: "application/json",
        featureid: `${layerName}.${fid}`
      });

      const url = `${base}?${params}`;
      console.log("🌐 Richiesta WFS (padre):", url);

      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        if (data.features && data.features.length > 0) {
          const virt = data.features[0].properties.VIRTID;
          console.log("🎯 VIRTID per FID", fid, ":", virt);
          virtidList.push(virt);
        } else {
          console.warn("⚠️ Nessuna feature per FID:", fid);
        }
      } catch (err) {
        console.error("❌ Errore WFS padre:", err);
      }
    }

    return virtidList;
  }

  async function queryFiglioDaVirtid(virtidList) {
    if (!virtidList || virtidList.length === 0) return [];

    let orConditions = virtidList.map(function(v){
      return (
        '<ogc:PropertyIsEqualTo>' +
          '<ogc:PropertyName>VIRTID</ogc:PropertyName>' +
          '<ogc:Literal>' + v + '</ogc:Literal>' +
        '</ogc:PropertyIsEqualTo>'
      );
    }).join('');

    let filter = '<ogc:Filter><ogc:Or>' + orConditions + '</ogc:Or></ogc:Filter>';

    let url = 'https://...inserisci_server_hosting.../index.php/lizmap/service'
            + '?repository=...inserisci_nome_repository...'
            + '&project=...inserisci_nome_progetto...'
            + '&service=WFS&version=1.0.0'
            + '&request=GetFeature'
            + '&typeName=T99_DEST_URBANISTICHE_GROUP_3857'
            + '&outputFormat=application/json'
            + '&filter=' + encodeURIComponent(filter);

    console.log("🌐 Richiesta WFS al figlio:", url);

    try {
      const resp = await fetch(url);
      const data = await resp.json();
      console.log("📦 Risposta layer figlio:", data);

      if (data.features && data.features.length > 0) {
        let rows = data.features.map(function(f){
          let p = f.properties || {};
          return {
            foglio: String(p.FOGLIO || ''),
            allegato: String(p.Allegato || ''),
            mappale: String(p.MAPPALE || ''),
            tema: String(p.TEMA || ''),
            zona: String(p.ZONA || ''),
            dettaglio: String(p.DESCRIZIONE || ''),
            norme: String(p.Norme || ''),
            percent: String(p.PERCENTUALE || '')
          };
        });

        // Ordinamento
        rows.sort(function(a, b){
          var ka = a.foglio + a.allegato + a.mappale + a.tema + a.zona + a.percent;
          var kb = b.foglio + b.allegato + b.mappale + b.tema + b.zona + b.percent;
          return ka.localeCompare(kb, 'it', {numeric:true});
        });

        console.log("📊 Dati ordinati:", rows);
        return rows;
      } else {
        console.warn("⚠️ Nessun dato urbanistico trovato per i VIRTID:", virtidList);
        return [];
      }
    } catch (err) {
      console.error("❌ Errore fetch layer figlio:", err);
      return [];
    }
  }

  // ================== DOCX ==================
  async function generaDocx(rows) {
    try {
      var libsOk = await ensureLibs();
      if (!libsOk) {
        console.error('⛔ Librerie mancanti, annullo generazione');
        toast('Librerie mancanti (PizZip/JSZip)', '#dc2626');
        return;
      }

      const content = await fetchTemplateArrayBuffer();

      var zip;
      if (ZIP_BACKEND === 'pizzip' && typeof window.PizZip !== 'undefined') {
        // PizZip accetta ArrayBuffer / Uint8Array
        zip = new window.PizZip(content);
      } else if (ZIP_BACKEND === 'jszip2' && typeof window.JSZip !== 'undefined') {
        // JSZip v2 richiede binary string
        var bin = ab2bin(content);
        zip = new window.JSZip(bin);
      } else {
        toast('Nessuna libreria ZIP disponibile', '#dc2626');
        return;
      }
	  
	  // Calcolo data corrente (formato gg/mm/aaaa)
	  var now = new Date();
      var oggi = String(now.getDate()).padStart(2, '0') + '/' +
               String(now.getMonth() + 1).padStart(2, '0') + '/' +
               now.getFullYear();

      var DocxClass = (typeof window.docxtemplater !== 'undefined') ? window.docxtemplater : window.Docxtemplater;
      var doc = new DocxClass(zip, { paragraphLoop: true, linebreaks: true });

      // Aggiunta della data ai dati
      doc.render({
        dati: rows,
        data: oggi
      });

      var out = doc.getZip().generate({
        type: 'blob',
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      saveAs(out, 'CDU_generato.docx');
      toast('CDU generato con successo!', '#2563eb');
    } catch (err) {
      console.error("❌ Errore generazione DOCX:", err);
      toast('Errore generazione CDU', '#dc2626');
    }
  }

  // ================== UI LIZMAP ==================
  lizMap.events.on({
    uicreated: function () {
      lizMap.addDock(
        TOOL_ID,
        'CDU automatizzato',
        'rightdock',
        '<div style="padding:8px">Seleziona una o più particelle dal layer padre e poi clicca l’icona in alto.</div>',
        'icon-file'
      );

      // Click icona
      $('#mapmenu').on('click', 'li.' + TOOL_ID + ' a', async function (e) {
        e.preventDefault();
        if (!ready) {
          toast('Devi selezionare almeno una particella', '#6b7280');
          return;
        }
        toast('Generazione CDU avviata!', '#16a34a');

        const virtidList = await getVirtidFromSelection(selectedIds);
        console.log("📌 Lista VIRTID:", virtidList);
        const rows = await queryFiglioDaVirtid(virtidList);

        if (rows.length > 0) {
          await generaDocx(rows);
        } else {
          toast('Nessun dato disponibile per CDU', '#f59e0b');
        }
      });

      updateMenuButton();
    },

    // Aggiorna selezione
    layerSelectionChanged: function (e) {
      if (!e) return;
      if (isPadre(e.featureType)) {
        selectedIds = Array.isArray(e.featureIds) ? e.featureIds : [];
        ready = selectedIds.length > 0;
        updateMenuButton();
        console.log("👉 Selezione aggiornata:", selectedIds);
      }
    }
  });

})();
```

---

## Vedi somma valori
Questo script esegue la somma dei valori delle particelle catastali selezionate e gli stampa a video:

```javascript
/* SommaValori.js – calcola totali per V2016, V2017_2018, V2019_2020 */
(function () {
  var TOOL_ID = 'SommaValori';
  var PADRE_NAMES = ['Particelle'];
  var selectedIds = [];
  var ready = false;

// 👉 Funzione di formattazione valuta (in cima)
  function formatEuro(value) {
    return value.toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });
  }

  function toast(msg, bg) {
    var box = document.createElement('div');
    box.textContent = msg;
    box.style.position = 'absolute';
    box.style.top = '10px'; box.style.left = '50%';
    box.style.transform = 'translateX(-50%)';
    box.style.padding = '8px 12px';
    box.style.background = bg || '#1f2937';
    box.style.color = '#fff';
    box.style.font = '12px/1.2 sans-serif';
    box.style.borderRadius = '6px';
    box.style.boxShadow = '0 2px 6px rgba(0,0,0,.25)';
    box.style.zIndex = 99999;
    document.body.appendChild(box);
    setTimeout(function(){ box.remove(); }, 2500);
  }

  function normalizeLayerName(n) {
    if (!n) return '';
    var out = n.split(':').pop();
    out = out.split('@')[0];
    return out;
  }
  function isPadre(n) { return PADRE_NAMES.indexOf(normalizeLayerName(n)) !== -1; }

  function updateMenuButton() {
    var $a = $('#mapmenu li.' + TOOL_ID + ' a');
    if (!$a.length) return;
    $a.css('background', ready ? '#28a745' : '');
    $a.attr('title', ready ? ('Calcola totali (' + selectedIds.length + ' selezionate)') : 'Seleziona almeno una particella');
  }

 // 👉 Finestra modale con i totali (versione con righe)
function showTotalsDialog(sum2016, sum2017, sum2019) {
  const overlay = document.createElement('div');
  overlay.style.position = 'fixed';
  overlay.style.top = 0; overlay.style.left = 0;
  overlay.style.width = '100%'; overlay.style.height = '100%';
  overlay.style.background = 'rgba(0,0,0,0.4)';
  overlay.style.zIndex = 100000;

  const dialog = document.createElement('div');
  dialog.style.position = 'absolute';
  dialog.style.top = '50%'; dialog.style.left = '50%';
  dialog.style.transform = 'translate(-50%, -50%)';
  dialog.style.background = '#fff';
  dialog.style.padding = '20px';
  dialog.style.borderRadius = '8px';
  dialog.style.boxShadow = '0 4px 12px rgba(0,0,0,.3)';
  dialog.style.minWidth = '300px';

  dialog.innerHTML = `
    <div style="text-align:right;">
      <span id="closeBtn" style="cursor:pointer; font-weight:bold;">✖</span>
    </div>
    <h3 style="margin-top:0">Particelle selezionate</h3>
    <table style="width:100%; border-collapse:collapse; border:1px solid #ccc;">
      <tr>
        <td style="padding:6px; font-weight:bold; border:1px solid #ccc;">VALORE TOTALE 2016:</td>
        <td style="padding:6px; text-align:right; border:1px solid #ccc;">${formatEuro(sum2016)}</td>
      </tr>
      <tr>
        <td style="padding:6px; font-weight:bold; border:1px solid #ccc;">VALORE TOTALE 2017/2018:</td>
        <td style="padding:6px; text-align:right; border:1px solid #ccc;">${formatEuro(sum2017)}</td>
      </tr>
      <tr>
        <td style="padding:6px; font-weight:bold; border:1px solid #ccc;">VALORE TOTALE 2019/2020:</td>
        <td style="padding:6px; text-align:right; border:1px solid #ccc;">${formatEuro(sum2019)}</td>
      </tr>
    </table>
  `;

  overlay.appendChild(dialog);
  document.body.appendChild(overlay);

  dialog.querySelector('#closeBtn').onclick = () => overlay.remove();
}


  // 👉 Calcola le somme dai dati selezionati
  async function calcolaTotali(fidList) {
    const layerName = "Particelle";
    const base = "https://...inserisci_server_hosting/index.php/lizmap/service";
    let sum2016 = 0, sum2017 = 0, sum2019 = 0;

    for (let fid of fidList) {
      const params = new URLSearchParams({
        repository: "...inserisci_nome_repository...",
        project: "...inserisci_nome_progetto...",
        service: "WFS", version: "1.0.0",
        request: "GetFeature",
        typeName: layerName,
        outputFormat: "application/json",
        featureid: `${layerName}.${fid}`
      });
      const url = `${base}?${params}`;
      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (data.features && data.features.length > 0) {
          const props = data.features[0].properties;
          sum2016 += Number(props.V2016) || 0;
          sum2017 += Number(props.V2017_2018) || 0;
          sum2019 += Number(props.V2019_2020) || 0;
        }
      } catch (err) { console.error("❌ Errore WFS:", err); }
    }

    showTotalsDialog(sum2016, sum2017, sum2019);
  }

  lizMap.events.on({
    uicreated: function () {
      lizMap.addDock(
        TOOL_ID, 'Vedi Somma Valori', 'rightdock',
        '<div style="padding:8px">Seleziona una o più particelle dal layer padre e poi clicca l’icona in alto.</div>',
        'icon-cog'
      );

      $('#mapmenu').on('click', 'li.' + TOOL_ID + ' a', async function (e) {
        e.preventDefault();
        if (!ready) { toast('Devi selezionare almeno una particella', '#6b7280'); return; }
        await calcolaTotali(selectedIds);
      });

      updateMenuButton();
    },

    layerSelectionChanged: function (e) {
      if (!e) return;
      if (isPadre(e.featureType)) {
        selectedIds = Array.isArray(e.featureIds) ? e.featureIds : [];
        ready = selectedIds.length > 0;
        updateMenuButton();
        console.log("👉 Selezione aggiornata:", selectedIds);
      }
    }
  });

})();
```

---

## Esporta Tabella valori
Questo script esporta i dati da una tabella correlata agli elementi selezionati su di un altra tabella, in questo caso specifico esporta il dettaglio del calcolo del valore delle particelle catastali selezionate:

```javascript
/* EsportaDatiMultiDialog.js – Excel con finestra di dialogo */
(function () {
  var TOOL_ID = 'TabelleValori';
  var PADRE_NAMES = ['Particelle'];
  var selectedIds = [];
  var ready = false;

  var CDN_LIBS = {
    sheetjs: [
      'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'
    ],
    filesaver: [
      'https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js'
    ]
  };

  function toast(msg, bg) {
    var box = document.createElement('div');
    box.textContent = msg;
    box.style.position = 'absolute';
    box.style.top = '10px'; box.style.left = '50%';
    box.style.transform = 'translateX(-50%)';
    box.style.padding = '8px 12px';
    box.style.background = bg || '#1f2937';
    box.style.color = '#fff';
    box.style.font = '12px/1.2 sans-serif';
    box.style.borderRadius = '6px';
    box.style.boxShadow = '0 2px 6px rgba(0,0,0,.25)';
    box.style.zIndex = 99999;
    document.body.appendChild(box);
    setTimeout(function(){ box.remove(); }, 2500);
  }

  function normalizeLayerName(n) {
    if (!n) return '';
    var out = n.split(':').pop();
    out = out.split('@')[0];
    return out;
  }
  function isPadre(n) { return PADRE_NAMES.indexOf(normalizeLayerName(n)) !== -1; }

  function updateMenuButton() {
    var $a = $('#mapmenu li.' + TOOL_ID + ' a');
    if (!$a.length) return;
    $a.css('background', ready ? '#28a745' : '');
    $a.attr('title', ready ? ('Genera Excel (' + selectedIds.length + ' selezionate)') : 'Seleziona almeno una particella');
  }

  async function loadScriptOnce(url) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = url; s.async = true;
      s.onload = function(){ resolve(); };
      s.onerror = function(){ reject(new Error('load error: ' + url)); };
      document.head.appendChild(s);
    });
  }

  async function ensureLibs() {
    await loadScriptOnce(CDN_LIBS.sheetjs[0]);
    await loadScriptOnce(CDN_LIBS.filesaver[0]);
    return (typeof XLSX !== 'undefined' && typeof saveAs === 'function');
  }

  // 👉 Finestra di dialogo con select e pulsanti
  function showExportDialog() {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = 0; overlay.style.left = 0;
    overlay.style.width = '100%'; overlay.style.height = '100%';
    overlay.style.background = 'rgba(0,0,0,0.4)';
    overlay.style.zIndex = 100000;

    const dialog = document.createElement('div');
    dialog.style.position = 'absolute';
    dialog.style.top = '50%'; dialog.style.left = '50%';
    dialog.style.transform = 'translate(-50%, -50%)';
    dialog.style.background = '#fff';
    dialog.style.padding = '20px';
    dialog.style.borderRadius = '8px';
    dialog.style.boxShadow = '0 4px 12px rgba(0,0,0,.3)';
    dialog.style.minWidth = '300px';

    dialog.innerHTML = `
      <h3 style="margin-top:0">Esporta tabella valori</h3>
      <label for="tabellaSelect">Scegli tabella:</label><br>
      <select id="tabellaSelect" style="width:100%; margin:10px 0;">
        <option value="VALORI_2016_3857">VALORI 2016</option>
        <option value="VALORI_2017_2018_3857">VALORI 2017-2018</option>
        <option value="VALORI_2019_2020_3857">VALORI 2019-2020</option>
      </select>
      <button id="exportBtn" style="padding:6px 12px; background:#2563eb; color:#fff; border:none; border-radius:4px; cursor:pointer;">
        Esporta Excel
      </button>
      <button id="cancelBtn" style="padding:6px 12px; margin-left:8px; background:#6b7280; color:#fff; border:none; border-radius:4px; cursor:pointer;">
        Annulla
      </button>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    dialog.querySelector('#cancelBtn').onclick = () => overlay.remove();

    dialog.querySelector('#exportBtn').onclick = async () => {
      const layerFiglio = dialog.querySelector('#tabellaSelect').value;
      overlay.remove();
      toast('Generazione Excel avviata!', '#16a34a');
      const virtidList = await getVirtidFromSelection(selectedIds);
      const rows = await queryFiglioDaVirtid(virtidList, layerFiglio);
      if (rows.length > 0) {
        await generaExcel(rows, layerFiglio);
      } else {
        toast('Nessun dato disponibile per Excel', '#f59e0b');
      }
    };
  }
  async function getVirtidFromSelection(fidList) {
    const layerName = "Particelle";
    const base = "https://...inserisci_server_hosting.../index.php/lizmap/service";
    let virtidList = [];
    for (let fid of fidList) {
      const params = new URLSearchParams({
        repository: "...inserisci_repository...",
        project: "...inserisci_nome_progetto...",
        service: "WFS", version: "1.0.0",
        request: "GetFeature",
        typeName: layerName,
        outputFormat: "application/json",
        featureid: `${layerName}.${fid}`
      });
      const url = `${base}?${params}`;
      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (data.features && data.features.length > 0) {
          virtidList.push(data.features[0].properties.VIRTID);
        }
      } catch (err) { console.error("❌ Errore WFS padre:", err); }
    }
    return virtidList;
  }

  async function queryFiglioDaVirtid(virtidList, layerFiglio) {
    if (!virtidList || virtidList.length === 0) return [];
    let orConditions = virtidList.map(v =>
      `<ogc:PropertyIsEqualTo><ogc:PropertyName>VIRTID</ogc:PropertyName><ogc:Literal>${v}</ogc:Literal></ogc:PropertyIsEqualTo>`
    ).join('');
    let filter = `<ogc:Filter><ogc:Or>${orConditions}</ogc:Or></ogc:Filter>`;
    let url = 'https://map.gishosting.eu/index.php/lizmap/service'
            + '?repository=...inserisci_repository...'
            + '&project=...inserisci_progetto...'
            + '&service=WFS&version=1.0.0'
            + '&request=GetFeature'
            + '&typeName=' + layerFiglio
            + '&outputFormat=application/json'
            + '&filter=' + encodeURIComponent(filter);
    try {
      const resp = await fetch(url);
      const data = await resp.json();
      if (data.features && data.features.length > 0) {
        return data.features.map(f => f.properties || {});
      } else return [];
    } catch (err) { console.error("❌ Errore fetch figlio:", err); return []; }
  }

  async function generaExcel(rows, nomeTabella) {
    try {
      var libsOk = await ensureLibs();
      if (!libsOk) { toast('Librerie Excel non disponibili', '#dc2626'); return; }

      const headers = [
        "FOGLIO","MAPPALE","PUC","DESCRIZION","FASCE_RISP","URBANO","STRUM_ATTU",
        "PERICOLO_I","DESCR_PERI","PERICOLO_F","DESCR_PE_1","VALORE_A_M","SUP_PARZIA","VALORE_PAR","PERIODO"
      ];

      const headerLabels = {
        FOGLIO: "FOGLIO",
        MAPPALE: "MAPPALE",
        PUC: "PUC",
        DESCRIZION: "DESCRIZIONE",
        FASCE_RISP: "FASCE RISP",
        URBANO: "URBANO",
        STRUM_ATTU: "STRUM ATT",
        PERICOLO_I: "PER IDRAULICO",
        DESCR_PERI: "DESC PI",
        PERICOLO_F: "PER FRANA",
        DESCR_PE_1: "DESC PF",
        VALORE_A_M: "VALORE MQ",
        SUP_PARZIA: "SUP PARZIALE",
        VALORE_PAR: "VALORE PARZIALE",
	PERIODO: "PERIODO"
      };

      const filteredRows = rows.map(r => {
        let obj = {};
        headers.forEach(h => { obj[h] = r[h]; });
        return obj;
      });

      const ws = XLSX.utils.json_to_sheet(filteredRows, { header: headers });
      headers.forEach((h,i) => {
        const cell = XLSX.utils.encode_cell({ r:0, c:i });
        if (ws[cell]) ws[cell].v = headerLabels[h];
      });

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, nomeTabella);

      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([wbout], { type: 'application/octet-stream' });
      saveAs(blob, nomeTabella + '.xlsx');
      toast('Excel generato con successo!', '#2563eb');
    } catch (err) { console.error("❌ Errore Excel:", err); toast('Errore generazione Excel', '#dc2626'); }
  }

  lizMap.events.on({
    uicreated: function () {
      lizMap.addDock(
        TOOL_ID, 'Esporta Tabelle Valori', 'rightdock',
        '<div style="padding:8px">Seleziona una o più particelle dal layer padre e poi clicca l’icona in alto.</div>',
        'icon-file'
      );

      // 👉 Click sul bottone apre la finestra di dialogo
      $('#mapmenu').on('click', 'li.' + TOOL_ID + ' a', function (e) {
        e.preventDefault();
        if (!ready) { toast('Devi selezionare almeno una particella', '#6b7280'); return; }
        showExportDialog();
      });

      updateMenuButton();
    },

    layerSelectionChanged: function (e) {
      if (!e) return;
      if (isPadre(e.featureType)) {
        selectedIds = Array.isArray(e.featureIds) ? e.featureIds : [];
        ready = selectedIds.length > 0;
        updateMenuButton();
        console.log("👉 Selezione aggiornata:", selectedIds);
      }
    }
  });

})();
```
</div>

<br>




