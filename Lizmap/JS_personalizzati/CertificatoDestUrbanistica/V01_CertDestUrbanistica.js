/*
===============================================================================
VERSIONE PER LIZ 3.8
Realizzazione certificato di destinazione urbanistica di una selezione di
particelle
===============================================================================
*/


/* Snippet_unico.js – versione solo CDN + template in media/99_CodrongianosPUC/
   - Carica librerie dai CDN ufficiali (multi-CDN + fallback JSZip v2)
   - Bottone menu
   - Lettura padre -> virtid
   - Query figlio -> righe ordinate
   - Merge su media/codrongianos/Template_CDU.docx -> download
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
  var TEMPLATE_URL = 'https://map.gishosting.eu/index.php/view/media/getMedia?repository=comunevillasanpietro&project=A03PianoUrbanisticoComunale&path=media%2Fpuc%2F00_CDU_Schema.docx';

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
    const base = "https://map.gishosting.eu/index.php/lizmap/service";
    let virtidList = [];

    for (let fid of fidList) {
      const params = new URLSearchParams({
        repository: "comunevillasanpietro",
        project: "A03PianoUrbanisticoComunale",
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

    let url = 'https://map.gishosting.eu/index.php/lizmap/service'
            + '?repository=comunevillasanpietro'
            + '&project=A03PianoUrbanisticoComunale'
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




