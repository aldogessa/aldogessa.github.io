# GENERAZIONE CDU VERSIONE 5
Questa è la versione più evoluta, lo script per le intersezioni è da utilizzare come azione Python definita sul layer delle particelle catastali.
Lo script riconosce automaticamente il layer su cui è definita l'azione, nella finestra di dialogo sarà impedita la modifica del layer particelle. Dalla finestra di dialogo sarà possibile invece selezionare il layer destinato alle intersezioni. Con questa versione non è più necessario manipolare il codice, le azioni dell'utente sono tutte guidate nella finestra di dialogo.   

Anche lo script da definire come azione Python sul layer destinato alle intersezioni, riconoscerà automaticamente il layer, inoltre permetterà di selezionare il template .doc da utilizzare per la generazione del CDU. Anche in questo caso lo script è stato progettato per non essere manipolato dall'utente che dovrà seguire esclusivamente le opzioni guidate dalla finestra di dialogo.   

Lo script dedicato alle intersezioni:
1) Verifica la struttura del layer particelle su cui è stata definita l'azione che deve rispondere ai prerequisiti stabiliti;
2) Verifica la struttura del layer intersezioni, selezionato per ricevere il risultato, che deve rispondere ai prerequisiti stabiliti;
3) Parte dalla selezione delle particelle;   
4) Esegue le intersezioni tra le particelle selezionate e tutti i layer polgonali scelti nella finestra di dialogo;     
5) Calcola le percentuali di sovrapposizione;   
6) Trasferisce il risultato all'interno del layer selezionato per accogliere le intersezioni.
Se le colonne del layer delle particelle e dei layer delle intersezioni contengono la struttura del layer preimpostato che accoglie il risultato, tutte le colonne risulteranno popolate, altrimenti alcune colonne saranno vuote.

Vantaggi: 
1) Lo script per le intersezioni lavora con qualsiasi layer poligonale, aggiornando le mappe è possibile ottenere intersezioni sempre aggiornate anche in tempo reale;
2) Non è più necessario selezionare il layer delle particelle, viene riconosciuto automaticamente;
3) Non è richiesta nessuna manipolazione del codice al variare dei nomi dei layer;
4) Lo script per la generazione del CDU riconosce automaticamente il layer delle intersezioni in cui è definita l'azione, permette inoltre di selezionare il template da utilizzare: utile se occorrono diverse versioni del certificato e nel caso in cui il template debba essere sopostato da una cartella ad un altra del computer - non occorre manipolare il codice per definire il nuovo percorso.

Svantaggi:
1) L'elaborazione richiede CPU (ma non troppa);   
2) Per un risultato ottimale e ottenere una tabella dell'intersezione completamente popolata i layer particelle e di intersezione devono rispettare la struttura preimpostata e dunque necessaria una loro preimpostazione;

## Versione QGIS testata
Lo script è testato nella versione QGIS 3.40 per le versioni successive potrebbero essere
necessari alcuni aggiustamenti.

## Prerequisiti dei layer
Lo script è progettato per funzionare con le seguenti caratteristiche dei layer:   
1) Nel progetto deve essere presente il layer delle particelle catastali;
2) Nel progetto deve essee presente il layer che accoglie il risultato delle intersezioni;
3) Il layer delle particelle deve avere la seguente struttura:
   id (chiave primaria); foglio (integer); allegato (string); mappale (string); Area1 (Real);
4) I layer da intersecare devono avere la seguente struttura:
   id (chiave primaria); tema (string); zona (string); descrizion (string); J_norme (string)
   tema: descrive lo strato informativi (ad esempio: T01 PUC; T02 PAI; T03 VINCOLO FRANA etc.);   
   zona: descrive l'acronimo della zona di solito riportato in legenda (ad esempio zona A; B; C etc.);
   descrizion: descrive il significato dell'acronimo di zona (ad esempio: CENTRO STORICO; COMPLETAMENTO ect.);
   J_norme: contiene i riferimenti normativi (ad esempio: Artt: 25, 27 e 29 delle NTA del PUC);
6) Il layer di destinazione delle intersezioni deve avere la seguente struttura:
   foglio (integer); allegato (string); mappale (string); tema (string); zona (string); descrizion (string); J_norme (string); percent (integer).   

E' possibile assegnare al nome dei campi qualsiasi alias.   
Se la struttura dei layer di intersezione non è rispettata le intersezioni vengono comunque eseguite ma alcuni campi del risultato dell'intersezione potrebbero essere vuoti.

## Come installare l'azione
Sul layer delle particelle va definita una azione Python con lo script "EseguiIntersezioniV5.py".   
Sul layer del risultato delle intersezioni va definita una azione Python con lo script "GeneraCDU_da_IntersezioniV5.py".
Deve essere raggiungibile dal progetto QGIS un template .doc con una tabella coerente con quella del layer "Intersezioni".

## Anteprima
Il funzionamento è analogo alla versione 3, dunque si propone la stessa anteprima, cambia solo la selezione dei layer coinvolti nel processo e la possibilità di scegliere la posizione di salvataggio del template CDU.
<a href="https://youtu.be/ijOvWNzAK3o" target="_blank">
  <img src="https://img.youtube.com/vi/ijOvWNzAK3o/0.jpg" alt="Video YouTube">
</a>


