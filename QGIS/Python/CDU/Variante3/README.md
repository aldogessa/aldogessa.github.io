# GENERAZIONE CDU VERSIONE 3
Script da utilizzare come azione Python definita sul layer delle particelle.
Questa versione permette di scegliere i layer poligonali da sottoporre all'intersezione.   
Lo script:   
1) parte dalla selezione delle particelle;   
2) esegue le intersezioni tra le particelle selezionate e tutti i layer polgonali scelti nella finestra di dialogo;       
3) calcola le percentuali di sovrapposizione;   
4) trasferisce il risultato all'interno di un layer preimpostato.
Se le colonne del layer delle particelle e dei layer delle intersezioni contengono la struttura del layer preimpostato che accoglie il risultato, tutte le colonne risulteranno popolate, altrimenti alcune colonne saranno vuote.

Vantaggi: 
1) Lo script lavora con qualsiasi layer poligonale, aggiornando le mappe è possibile ottenere intersezioni sempre aggiornate anche in tempo reale.

Svantaggi:
1) L'elaborazione richiede CPU (ma non troppa);   
2) Per un risultato ottimale e ottenere una tabella dell'intersezione completamente popolata i layer particelle e di intersezione devono rispettare la struttura preimpostata e dunque necessaria una loro preimpostazione.

## Versione QGIS testata
Lo script è testato nella versione QGIS 3.40 per le versioni successive potrebbero essere
necessari alcuni aggiustamenti.

## Prerequisiti dei layer
Lo script è progettato per funzionare con le seguenti caratteristiche dei layer:   
1) Nel progetto deve essere presente il layer delle particelle catastali (chiamato nello script "ParticelleRAS");
2) Nel progetto deve essee presente il layer che accoglie il risultato delle intersezioni (chiamato nell script "IntersezioniCATRAS");
3) Il layer delle particelle deve avere la seguente struttura:
   id (chiave primaria); foglio (integr); allegato (string); mappale (string); Area1 (Real);
4) I layer da intersecare devono avere la seguente struttura:
   id (chiave primaria); tema (string); zona (string); descrizion (string); J_norme (string)
   tema: descrive lo strato informativi (ad esempio: T01 PUC; T02 PAI; T03 VINCOLO FRANA etc.);
5) Il layer di destinazione delle intersezioni deve avere la seguente struttura:
   foglio (integer); allegato (string); mappale (string); tema (string); zona (string); descrizion (string); 

   ) Nel progetto deve essere presente il layer contenente le intersezioni (in questo caso DestinazioniUrbanistiche)
   con la medesima chiave esterna, da preservare durante l'esecuzione delle intersezioni (in questo caso virtid); J_norme (string); percent (integer);   

E' possibile assegnare al nome dei campi qualsiasi alias.
Solo i layer "ParticelleRAS" e "IntersezioniCATRAS" devo avere lo stesso nome riportato nello script, se gli si vuole cambiare il nome sarà sufficiente aggiornare il nuovo nome nella variabile dello script.

## Come installare l'azione
Sul layer "Particelle" va definita una azione Python con lo script "EseguiIntersezioni.py".

## Anteprima
<a href="https://youtu.be/ijOvWNzAK3o" target="_blank">
  <img src="https://img.youtube.com/vi/ijOvWNzAK3o/0.jpg" alt="Video YouTube">
</a>
