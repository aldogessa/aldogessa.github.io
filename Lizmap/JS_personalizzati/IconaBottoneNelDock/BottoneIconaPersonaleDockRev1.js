/*
======================================================
AGis - Aldo Gessa
Bottone personalizzato con CSS separato
Versione più stabile e robusta
Nessuna modifica funzionale
Maggio 2026
======================================================
*/

(function () {

  if (window.__TUTORIAL_TOOL_INITIALIZED__) return;
  window.__TUTORIAL_TOOL_INITIALIZED__ = true;

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

        lizMap.events.on({ uicreated: run });

        setTimeout(run, 500);
      }

    }, 100);
  }

  function waitButton(selector, cb) {

    const i = setInterval(() => {

      const $btn = $(selector);

      if ($btn.length) {
        clearInterval(i);
        cb($btn);
      }

    }, 100);
  }

  lizmapReady(function () {

    const TOOL_ID = 'Tutorial';

    /* ---------------------------------------------------------
       CREAZIONE DOCK (necessario in Lizmap 3.9.x)
       MA NON LO FAREMO APRIRE
    --------------------------------------------------------- */
    lizMap.addDock(
      TOOL_ID,
      'HELP - Tutorial',
      'rightdock',
      '',          // contenuto vuoto
      'icon-book'
    );

    /* ---------------------------------------------------------
       ASPETTA IL BOTTONE
    --------------------------------------------------------- */
    waitButton('#mapmenu li.Tutorial a', function ($tutorialBtn) {

      /* -------------------------------------------------------
         STILE DESKTOP
      ------------------------------------------------------- */
      if (!lizMap.isMobile) {
        $tutorialBtn.addClass('agis-desktop');
        $tutorialBtn.find('span.icon').hide();
      }

      /* -------------------------------------------------------
         BLOCCA L’APERTURA DEL DOCK
      ------------------------------------------------------- */
      $tutorialBtn.off('click').on('click', function (e) {

        e.preventDefault();
        e.stopImmediatePropagation(); // <-- questo è il segreto
        e.stopPropagation();

        // chiude eventuali dock aperti
        $('#right-dock-close').click();

        // apre il tutorial in nuova scheda (_blank)
        window.open(
          'https://aldogessa.github.io/#/comuni/villa_san_pietro',
          '_blank',
          'noopener'
        );
      });

    });

  });

})();
