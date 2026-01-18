/*
==============================================================================
VERSIONE PER LIZ 3.8
Espandere e comprimere i popup dei figli anche quando sono realizzati con HTML
Deve essere accopiato con il relatico CSS
==============================================================================
 */

(function ($) {
    'use strict';

    /**
     * Utility: ottiene il popup corrente (solo per il padre)
     */
    function getPopupContext(el) {
        const popup = $(el).closest('.lizmapPopupDiv');
        return popup.length ? popup : $(document);
    }

    /**
     * ========================================================
     * BOTTONE PADRE – .toggle-children
     * ========================================================
     */

    $('body').on('click', '.toggle-children', function (event) {

        event.stopImmediatePropagation(); // blocca refresh Lizmap

        const btn = $(this);
        const popup = getPopupContext(btn);

        const label = btn.find('.label');
        const children = popup.find('.lizmapPopupChildren .lizmapPopupSingleFeature');
        const dataviz = popup.find('.lizdataviz, .lizmapDataviz, .plotly-graph-div');

        const isOpen = btn.hasClass('open');

        // --- COLLASSA ---
        if (isOpen) {

            children.slideUp(200);
            dataviz.slideUp(200, function () {
                label.html('<b>VEDI ANALISI URBANISTICA</b>');
                btn.removeClass('open');
            });

            return;
        }

        // --- ESPANDI ---
        children.slideDown(200);
        dataviz.slideDown(200, function () {

            label.html('<b>CHIUDI ANALISI URBANISTICA</b>');
            btn.addClass('open');

            // Resize DataViz
            if (lizMap?.dataViz?.resizeAll) {
                lizMap.dataViz.resizeAll();
            }

            // Forza resize finestra (utile per grafici Plotly)
            setTimeout(() => window.dispatchEvent(new Event('resize')), 80);

            // Reposition popup
            setTimeout(() => {
                if (lizMap?.popup?.updatePosition) {
                    lizMap.popup.updatePosition();
                }
            }, 250);
        });
    });

    /**
     * ========================================================
     * BOTTONE FIGLIO – .close-analysis-child
     * ========================================================
     */

    $('body').on('click', '.close-analysis-child', function (event) {

        event.stopImmediatePropagation(); // blocca refresh Lizmap

        /**
         * RISALITA CORRETTA:
         *
         * Bottone figlio → dentro popup figlio:
         *
         * .lizmapPopupChildren
         *    └── .lizmapPopupSingleFeature
         *            └── .lizmapPopupDiv   ← popup figlio
         *
         * Popup principale è 3 livelli sopra.
         */

        const popup = $(this)
            .closest('.lizmapPopupDiv')   // popup del figlio
            .parent()                     // .lizmapPopupSingleFeature
            .parent()                     // .lizmapPopupChildren
            .parent()                     // popup principale
            .closest('.lizmapPopupDiv');  // popup principale

        const btnParent = popup.find('.toggle-children').first();
        const label = btnParent.find('.label');

        const children = popup.find('.lizmapPopupChildren .lizmapPopupSingleFeature');
        const dataviz = popup.find('.lizdataviz, .lizmapDataviz, .plotly-graph-div');

        // Chiusura
        children.slideUp(200);
        dataviz.slideUp(200, function () {

            // Sincronizzazione bottone padre
            label.html('<b>VEDI ANALISI URBANISTICA</b>');
            btnParent.removeClass('open');
        });
    });

})(jQuery);
