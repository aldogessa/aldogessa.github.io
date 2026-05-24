/*
=================================================
AGis - Aldo Gessa
Script per selezionare tutto velocemente senza
utilizzare lo strumento nativa di Lizmap.
Versione più robusta e sicura.
Nessuna modifica funzionale.
Maggio 2026.
=================================================
*/
(function () {

  if (window.__CLEAR_SELECTION_INITIALIZED__) return;
  window.__CLEAR_SELECTION_INITIALIZED__ = true;

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

    const i = setInterval(() => {

      if (window.lizMap && lizMap.mainLizmap?.map) {

        clearInterval(i);

        // evento ufficiale
        lizMap.events.on({ uicreated: run });

        // fallback se evento già passato
        setTimeout(run, 500);
      }

    }, 100);
  }

  /* ---------------------------------------------------------
     SCRIPT PRINCIPALE
  --------------------------------------------------------- */
  lizmapReady(function () {

    const TOOL_ID = 'ClearSelection';
    const activeSelections = {}; // layer -> featureIds

    /* ---------------------------------------------------------
       TOAST
    --------------------------------------------------------- */
    function toast(msg, bg) {

      const box = document.createElement('div');

      box.textContent = msg;

      Object.assign(box.style, {
        position: 'absolute',
        top: '10px',
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '8px 12px',
        background: bg || '#1f2937',
        color: '#fff',
        font: '12px/1.2 sans-serif',
        borderRadius: '6px',
        boxShadow: '0 2px 6px rgba(0,0,0,.25)',
        zIndex: 99999
      });

      document.body.appendChild(box);

      setTimeout(() => {
        if (box.parentNode) {
          box.parentNode.removeChild(box);
        }
      }, 2000);
    }

    /* ---------------------------------------------------------
       TITOLI LAYER
    --------------------------------------------------------- */
    function getLayerTitle(featureType) {

      const cfg = lizMap.config?.layers?.[featureType];

      return cfg?.title || featureType;
    }

    /* ---------------------------------------------------------
       DIALOGO CONFERMA
    --------------------------------------------------------- */
    function showConfirmDialog(layerNames, onConfirm) {

      const overlay = document.createElement('div');

      Object.assign(overlay.style, {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: 'rgba(0,0,0,0.4)',
        zIndex: 100000
      });

      const dialog = document.createElement('div');

      Object.assign(dialog.style, {
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        background: '#fff',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,.3)',
        minWidth: '320px',
        textAlign: 'center'
      });

      const listHtml = layerNames.map(function (n) {

        const title = getLayerTitle(n);
        const count = activeSelections[n].length;

        return '<li>' + title + ' (' + count + ' selezioni)</li>';

      }).join('');

      dialog.innerHTML = `
        <p style="margin-bottom:12px; font-weight:bold;">
          Desideri deselezionare tutto dai seguenti layer?
        </p>

        <ul style="margin:0 0 16px; padding:0; list-style:none;">
          ${listHtml}
        </ul>

        <div>
          <button id="btnSi"
            style="
              margin:0 8px;
              padding:6px 12px;
              background:#16a34a;
              color:#fff;
              border:none;
              border-radius:4px;
            ">
            Si
          </button>

          <button id="btnNo"
            style="
              margin:0 8px;
              padding:6px 12px;
              background:#6b7280;
              color:#fff;
              border:none;
              border-radius:4px;
            ">
            Annulla
          </button>
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

    /* ---------------------------------------------------------
       UI LIZMAP
    --------------------------------------------------------- */
    lizMap.addDock(
      TOOL_ID,
      'Deseleziona tutto',
      'rightdock',
      '<div style="padding:8px">Clicca la stella per svuotare la selezione.</div>',
      'icon-remove'
    );

    /* ---------------------------------------------------------
       EVENTO CAMBIO SELEZIONE
    --------------------------------------------------------- */
    lizMap.events.on({

      layerSelectionChanged: function (e) {

        if (!e || !e.featureType) return;

        activeSelections[e.featureType] =
          Array.isArray(e.featureIds)
            ? e.featureIds
            : [];

        const btn = document.querySelector('li.' + TOOL_ID + ' a');

        if (!btn) return;

        const hasSelection = Object.values(activeSelections)
          .some(function (arr) {
            return arr.length > 0;
          });

        if (hasSelection) {

          btn.style.backgroundColor = '#16a34a';
          btn.style.color = '#fff';

        } else {

          btn.style.backgroundColor = '';
          btn.style.color = '';
        }
      }
    });

    /* ---------------------------------------------------------
       CLICK BOTTONE
    --------------------------------------------------------- */
    $(document).on('click', 'li.' + TOOL_ID + ' a', function (e) {

      e.preventDefault();

      const layerKeys = Object.keys(activeSelections)
        .filter(function (k) {
          return activeSelections[k].length > 0;
        });

      if (layerKeys.length === 0) {

        toast('Nessuna selezione attiva', '#6b7280');

        return;
      }

      showConfirmDialog(layerKeys, function () {

        try {

          layerKeys.forEach(function (ftype) {

            lizMap.events.triggerEvent(
              'layerfeatureunselectall',
              {
                featureType: ftype,
                updateDrawing: true
              }
            );

            activeSelections[ftype] = [];
          });

          toast(
            'Selezioni svuotate su tutti i layer!',
            '#16a34a'
          );

        } catch (err) {

          console.error(
            '❌ Errore unselect all:',
            err
          );

          toast(
            'Errore nel deselezionare',
            '#dc2626'
          );
        }
      });
    });

  }); // fine lizmapReady

})(); // fine IIFE
