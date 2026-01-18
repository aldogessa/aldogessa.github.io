/*
=======================================================================================
VERSIONE PER LIZ 3.8
Deselezionare tutto velocemente con un bottone senza utilizzare lo strumento di default
=======================================================================================
*/

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
