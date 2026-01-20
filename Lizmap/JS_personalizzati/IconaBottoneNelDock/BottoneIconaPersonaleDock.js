/*
============================================================================
BOTTONE CON IMMAGINE PNG NEL DOCK
VERSIONE TESTATA LIZMAP 3.9
Questo Script crea un bottone nel Dock con immagine png personalizzata
e deve essere usato in associazione con il relativo CSS
===========================================================================
*/

lizMap.events.on({
  uicreated: function(e) {

    lizMap.addDock(
      'Tutorial',
      'HELP - Tutorial',
      'bottomdook',
      '',
      'icon-book'// icona predefinita che sarà sovrascritta, serve per non perdere le caratteristiche di default di Lizmap in particolare nel mobile
    );

    let $i = 0;

    $(function () {
      const $tutorialBtn = $('#mapmenu li.Tutorial a');

      // Aggiungiamo la classe solo se siamo in layout desktop
     if (!lizMap.isMobile) {
      $tutorialBtn.addClass('agis-desktop');   // aggiungi stile solo su desktop
      $tutorialBtn.find('span.icon').hide();   // nascondi icon-book su desktop (in realtà non funziona, la nasconde anche sul mobile)
}


      $tutorialBtn.click(function () {
        if ($i === 0) {
          $i = 1;
          $('#right-dock-close').click();
          $('#mapmenu li.Tutorial a').click();
          window.open('****URL_della_pagina_o_documento_da_richiamare');
        } else {
          $i = 0;
        }
      });
    });
  }
});
