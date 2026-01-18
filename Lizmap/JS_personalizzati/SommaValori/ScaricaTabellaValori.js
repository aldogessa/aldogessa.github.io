/*
=========================================================================================
VERSIONE PER LIZ 3.8
Scaricare la tabella con il dettaglio del calcolo del valore delle particelle selezionate
(comune di villa san pietro - Mappa IMU)
==========================================================================================
*/

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
    const base = "https://map.gishosting.eu/index.php/lizmap/service";
    let virtidList = [];
    for (let fid of fidList) {
      const params = new URLSearchParams({
        repository: "comunevillasanpietro",
        project: "A11ValoriIMU",
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
            + '?repository=comunevillasanpietro'
            + '&project=A11ValoriIMU'
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
