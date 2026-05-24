/* ============================================================
   Agis -Aldo Gessa
   CDU Particelle – Versione robusta (Maggio 2026)
   – Librerie locali (no CDN)
   – URL centralizzati (BASE_MEDIA_URL + BASE_WFS_URL)
   – Guard anti-doppia inizializzazione
   – Nessuna modifica funzionale
   - Funziona con la struttura dei layer indicata nel worflow
============================================================ */

(function () {

  // ================== GUARD ANTI-DOPPIA INIZIALIZZAZIONE ==================
  if (window.__CDU_TOOL_INITIALIZED__) return;
  window.__CDU_TOOL_INITIALIZED__ = true;

  // ================== LIZMAP READY ==================
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
        console.warn('CDU Tool: Lizmap non inizializzato');
      }

    }, 100);
  }

  // ================== CSS RESPONSIVE ==================
  var style = document.createElement('style');
  style.textContent = `
    @media (max-width: 600px) {
      .ui-dialog {
        width: 95vw !important;
        max-width: 95vw !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
      }
      .ui-dialog .ui-dialog-content {
        max-height: 70vh !important;
        overflow-y: auto !important;
      }
    }
  `;
  document.head.appendChild(style);

  // ================== CONFIG ==================
  var TOOL_ID = 'CDUtool';
  var PADRE_NAMES = ['Particelle'];

  // ================== URL BASE CENTRALIZZATI ==================
  const BASE_MEDIA_URL =
    "https://map.gishosting.eu/index.php/view/media/getMedia" //inserisci qui l'indirizzo di getMedia
    + "?repository=comunevillasanpietro" //inserisci qui il nome del repository
    + "&project=A03CPianoUrbanisticoComunale" //inserisci qui il nome del progetto
    + "&path=";

  const BASE_WFS_URL =
    "https://map.gishosting.eu/index.php/lizmap/service" //inserisci qui l'indirizzo del service
    + "?repository=comunevillasanpietro" //inserisci qui il nome del repository
    + "&project=A03CPianoUrbanisticoComunale" //inserisci qui il nome del progetto
    + "&service=WFS"
    + "&version=1.0.0"
    + "&request=GetFeature";

  // ================== LIBRERIE LOCALI ==================
  const LOCAL_LIBS = [
    BASE_MEDIA_URL + "media/js/A03CPianoUrbanisticoComunale/pizzip.min.js", //URL cartella lizmap
    BASE_MEDIA_URL + "media/js/A03CPianoUrbanisticoComunale/docxtemplater.js", //URL cartella lizmap
    BASE_MEDIA_URL + "media/js/A03CPianoUrbanisticoComunale/FileSaver.min.js" //URL cartella lizmap
  ];

  // ================== TEMPLATE DOCX ==================
  const TEMPLATE_URL =
    BASE_MEDIA_URL + "media/puc/00_CDU_Schema.docx"; //URL cartella lizmap

  // ================== STATE ==================
  var selectedIds = [];
  var ready = false;
  var ZIP_BACKEND = null;

  // ================== UTILS ==================
  function toast(msg, bg) {
    var box = document.createElement('div');
    box.textContent = msg;
    box.style.position = 'absolute';
    box.style.top = '50%';
    box.style.left = '50%';
    box.style.transform = 'translate(-50%, -50%)';
    box.style.padding = '12px 18px';
    box.style.background = bg || 'rgba(31,41,55,0.9)';
    box.style.color = 'white';
    box.style.font = '14px/1.3 sans-serif';
    box.style.borderRadius = '8px';
    box.style.boxShadow = '0 4px 12px rgba(0,0,0,.35)';
    box.style.zIndex = 99999;
    box.style.maxWidth = '70%';
    box.style.textAlign = 'center';
    document.body.appendChild(box);
    setTimeout(function(){ box.remove(); }, 2600);
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

  // ================== TEMPLATE DOCX ==================
  async function fetchTemplateArrayBuffer() {
    const url = TEMPLATE_URL + "&_=" + Date.now();
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("Template non trovato");
    return await resp.arrayBuffer();
  }

  // ================== WFS PADRE ==================
  async function getVirtidFromSelection(fidList) {
    const layerName = "Particelle"; //nome del layer delle particelle registrato nella pubblicazone WFS
    let virtidList = [];

    for (let fid of fidList) {

      const url =
        BASE_WFS_URL
        + "&typeName=" + layerName
        + "&outputFormat=application/json"
        + "&featureid=" + layerName + "." + fid;

      try {
        const resp = await fetch(url);
        const data = await resp.json();
        if (data.features && data.features.length > 0) {
          virtidList.push(data.features[0].properties.VIRTID);
        }
      } catch (err) {
        console.error("Errore WFS padre:", err);
      }
    }

    return virtidList;
  }

  // ================== WFS FIGLIO ==================
  async function queryFiglioDaVirtid(virtidList) {
    if (!virtidList || virtidList.length === 0) return [];

    let orConditions = virtidList.map(v => (
      '<ogc:PropertyIsEqualTo>' +
        '<ogc:PropertyName>VIRTID</ogc:PropertyName>'
        '<ogc:Literal>' + v + '</ogc:Literal>' +
      '</ogc:PropertyIsEqualTo>'
    )).join('');

    let filter = '<ogc:Filter><ogc:Or>' + orConditions + '</ogc:Or></ogc:Filter>';

    const url =
      BASE_WFS_URL
      + "&typeName=Analisi_urbanistica_particella" //nome del layer contenente l'analisi urbanistica - intersezioni - registrato nel pubblicazione WFS
      + "&outputFormat=application/json"
      + "&filter=" + encodeURIComponent(filter);

    try {
      const resp = await fetch(url);
      const data = await resp.json();

      if (!data.features) return [];

      let rows = data.features.map(f => {
        let p = f.properties || {};
        return {
          foglio: String(p.FOGLIO ?? ''),
          allegato: String(p.ALLEGATO ?? ''),
          mappale: String(p.MAPPALE ?? ''),
          tema: String(p.TEMA ?? ''),
          zona: String(p.ZONA ?? ''),
          dettaglio: String(p.DETTAGLIO ?? ''),
          norme: String(p.NORME ?? ''),
          percent: (p.PERCENT === 0 ? '<1' : String(p.PERCENT ?? '')),
          percent_num: (p.PERCENT ?? null)
        };
      });

      // ORDINAMENTO IDENTICO AL PYTHON
      rows.sort((a, b) => {

        let fA = parseInt(a.foglio);
        let fB = parseInt(b.foglio);
        if (fA !== fB) return fA - fB;

        let cmp = a.mappale.localeCompare(b.mappale, 'it', {numeric:true, sensitivity:'base'});
        if (cmp !== 0) return cmp;

        cmp = a.tema.localeCompare(b.tema, 'it', {numeric:true});
        if (cmp !== 0) return cmp;

        cmp = a.zona.localeCompare(b.zona, 'it', {numeric:true});
        if (cmp !== 0) return cmp;

        return (a.percent_num ?? 0) - (b.percent_num ?? 0);
      });

      return rows;

    } catch (err) {
      console.error("Errore fetch figli:", err);
      return [];
    }
  }

  // ================== CARICAMENTO LIBRERIE LOCALI ==================
  function loadLocalLibs() {
    return new Promise(async (resolve, reject) => {
      try {
        for (let url of LOCAL_LIBS) {
          await new Promise((res, rej) => {
            const s = document.createElement("script");
            s.src = url;
            s.onload = res;
            s.onerror = () => rej(new Error("Errore caricamento: " + url));
            document.head.appendChild(s);
          });
        }

        if (typeof window.PizZip === "undefined")
          return reject("PizZip non caricato");

        if (typeof window.docxtemplater === "undefined" &&
            typeof window.Docxtemplater === "undefined")
          return reject("Docxtemplater non caricato");

        if (typeof window.saveAs !== "function")
          return reject("FileSaver non caricato");

        // Normalizzazione nome classe
        if (typeof window.docxtemplater === "undefined")
          window.docxtemplater = window.Docxtemplater;

        ZIP_BACKEND = "pizzip";
        resolve(true);

      } catch (err) {
        console.error(err);
        reject(err);
      }
    });
  }

  async function ensureLibs() {
    try {
      await loadLocalLibs();
      return true;
    } catch (err) {
      console.error("Errore librerie:", err);
      toast("Librerie locali non disponibili", "#dc2626");
      return false;
    }
  }

  // ================== GENERAZIONE DOCX ==================
  async function generaDocx(rows) {
    try {
      var libsOk = await ensureLibs();
      if (!libsOk) {
        toast('Librerie mancanti', '#dc2626');
        return;
      }

      const content = await fetchTemplateArrayBuffer();

      // Sempre PizZip (backend locale)
      var zip = new window.PizZip(content);

      var now = new Date();
      var oggi = String(now.getDate()).padStart(2, '0') + '/'
               + String(now.getMonth() + 1).padStart(2, '0') + '/'
               + now.getFullYear();

      var DocxClass = window.docxtemplater;
      var doc = new DocxClass(zip, { paragraphLoop: true, linebreaks: true });

      doc.render({
        dati: rows,
        data: oggi
      });

      var out = doc.getZip().generate({
        type: 'blob',
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });

      saveAs(out, 'CDU_generato.docx');
      toast('CDU generato!', '#2563eb');

    } catch (err) {
      console.error("Errore generazione DOCX:", err);
      toast('Errore generazione CDU', '#dc2626');
    }
  }

  // ================== UI LIZMAP ==================
  lizmapReady(function () {

    // Dock CDU
    lizMap.addDock(
      TOOL_ID,
      'CDU automatizzato',
      'rightdock',
      '<div style="padding:8px">Seleziona una o più particelle dal layer padre e poi clicca l’icona in alto.</div>',
      'icon-file'
    );

    // Click icona menu CDU
    $('#mapmenu').on('click', 'li.' + TOOL_ID + ' a', async function (e) {
      e.preventDefault();

      if (!ready) {
        toast('Devi selezionare almeno una particella', '#6b7280');
        return;
      }

      // Dialogo scelta tipo CDU
      var html = `
        <div id="cdu-dialog" title="Seleziona il tipo di anteprima certificato">
          <p style="margin-bottom:12px; text-align:justify; font-size:13px; line-height:1.35">
            Puoi scegliere se esportare una <b>anteprima ordinaria</b>, contenente solo i TEMI previsti dalla legge 
            che troveresti nel certificato ufficiale, oppure una <b>anteprima completa</b> contenente anche tutti gli 
            altri TEMI presenti nella mappa.<br><br>
            Questi ulteriori TEMI non compaiono nel certificato ufficiale in quanto riguardano vincoli sovracomunali, 
            la cui attestazione è di competenza delle Autorità preposte alla vigilanza su tali vincoli. Sono comunque 
            molto utili per uno studio preliminare unitario e completo dell'area.<br><br>
            Si ricorda infine che, in ogni caso, le informazioni riportate nell'anteprima sono ricavate con procedure 
            automatizzate in ambiente GIS e hanno carattere puramente indicativo. Non sostituiscono le certificazioni 
            ufficiali che, a seguito dell'istruttoria tecnica dell'Ufficio competente, possono differire anche 
            sostanzialmente.
          </p>

          <div style="text-align:right; margin-top:15px">
            <button id="btn-ordinario" class="ui-button ui-widget ui-corner-all" style="margin-right:10px">
              Ordinario
            </button>
            <button id="btn-completo" class="ui-button ui-widget ui-corner-all" style="margin-right:10px">
              Completo
            </button>
            <button id="btn-annulla" class="ui-button ui-widget ui-corner-all" style="background:#ccc">
              Annulla
            </button>
          </div>
        </div>
      `;

      $('body').append(html);

      $("#cdu-dialog").dialog({
        modal: true,
        width: 520,
        maxWidth: 520,
        resizable: false,
        close: function () { $(this).remove(); }
      });

      // ============================
      // ORDINARIO
      // ============================
      $("#btn-ordinario").on('click', async function () {
        $("#cdu-dialog").dialog('close');
        toast('Generazione CDU ordinario…', '#16a34a');

        const virtidList = await getVirtidFromSelection(selectedIds);
        let rows = await queryFiglioDaVirtid(virtidList);

        // Solo T01, T02, T03
        const prefixList = ['T01.', 'T02.', 'T03.'];
        rows = rows.filter(r => prefixList.some(p => r.tema.startsWith(p)));

        if (rows.length === 0) {
          toast('Nessun dato disponibile', '#f59e0b');
          return;
        }

        let finalRows = [];
        let lastGroup = null;

        for (let r of rows) {

          let foglioNorm = String(r.foglio).trim();
          let mappaleNorm = String(r.mappale).trim().replace(/^0+/, '');
          let group = foglioNorm + "_" + mappaleNorm;

          if (group !== lastGroup) {

            // RIGA FOGLIO–MAPPALE
            finalRows.push({
              isGroup: true,
              isHeader: false,
              isData: false,
              foglio: "FOGLIO",
              allegato: foglioNorm,
              mappale: "MAPPALE",
              tema: mappaleNorm,
              zona: "",
              dettaglio: "",
              norme: "",
              percent: ""
            });

            // RIGA INTESTAZIONE
            finalRows.push({
              isGroup: false,
              isHeader: true,
              isData: false,
              foglio: "Fg.",
              allegato: "All.",
              mappale: "Map.",
              tema: "Tema",
              zona: "Zona",
              dettaglio: "Dettaglio",
              norme: "Norme Specifiche",
              percent: "Q.tà* %"
            });

            lastGroup = group;
          }

          // RIGA DATI
          finalRows.push({
            isGroup: false,
            isHeader: false,
            isData: true,
            foglio: r.foglio,
            allegato: r.allegato,
            mappale: r.mappale,
            tema: r.tema,
            zona: r.zona,
            dettaglio: r.dettaglio,
            norme: r.norme,
            percent: r.percent
          });
        }

        await generaDocx(finalRows);
      });

      // ============================
      // COMPLETO
      // ============================
      $("#btn-completo").on('click', async function () {
        $("#cdu-dialog").dialog('close');
        toast('Generazione CDU completo…', '#16a34a');

        const virtidList = await getVirtidFromSelection(selectedIds);
        let rows = await queryFiglioDaVirtid(virtidList);

        if (rows.length === 0) {
          toast('Nessun dato disponibile', '#f59e0b');
          return;
        }

        let finalRows = [];
        let lastGroup = null;

        for (let r of rows) {

          let foglioNorm = String(r.foglio).trim();
          let mappaleNorm = String(r.mappale).trim().replace(/^0+/, '');
          let group = foglioNorm + "_" + mappaleNorm;

          if (group !== lastGroup) {

            // RIGA FOGLIO–MAPPALE
            finalRows.push({
              isGroup: true,
              isHeader: false,
              isData: false,
              foglio: "FOGLIO",
              allegato: foglioNorm,
              mappale: "MAPPALE",
              tema: mappaleNorm,
              zona: "",
              dettaglio: "",
              norme: "",
              percent: ""
            });

            // RIGA INTESTAZIONE
            finalRows.push({
              isGroup: false,
              isHeader: true,
              isData: false,
              foglio: "Fg.",
              allegato: "All.",
              mappale: "Map.",
              tema: "Tema",
              zona: "Zona",
              dettaglio: "Dettaglio",
              norme: "Norme Specifiche",
              percent: "Q.tà* %"
            });

            lastGroup = group;
          }

          // RIGA DATI
          finalRows.push({
            isGroup: false,
            isHeader: false,
            isData: true,
            foglio: r.foglio,
            allegato: r.allegato,
            mappale: r.mappale,
            tema: r.tema,
            zona: r.zona,
            dettaglio: r.dettaglio,
            norme: r.norme,
            percent: r.percent
          });
        }

        await generaDocx(finalRows);
      });

      // ============================
      // ANNULLA
      // ============================
      $("#btn-annulla").on('click', function () {
        $("#cdu-dialog").dialog('close');
        toast('Operazione annullata', '#6b7280');
      });

    }); // fine click icona menu

    updateMenuButton();

  }); // fine lizmapReady

  // ================== SELEZIONE LAYER ==================
  lizmapReady(function () {

    lizMap.events.on({

      layerSelectionChanged: function (e) {

        if (!e) return;

        if (isPadre(e.featureType)) {

          selectedIds = Array.isArray(e.featureIds)
            ? e.featureIds
            : [];

          ready = selectedIds.length > 0;

          updateMenuButton();
        }
      }

    });

  });

})(); // fine IIFE
