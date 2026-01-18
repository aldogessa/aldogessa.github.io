/*
======================================================================
VERSIONE PER LIZ 3.8
Calcolare il valore ai fini IMU (Comune di Villa San Pietro) delle
particelle selezionate e visualizzarlo sullo schermo
======================================================================
*/

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
    const base = "https://map.gishosting.eu/index.php/lizmap/service";
    let sum2016 = 0, sum2017 = 0, sum2019 = 0;

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
