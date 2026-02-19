# GENERAZIONE CDU VERSIONE 4
Script da utilizzare come azione Python definita sul layer delle particelle.
Questa versione è identica alla versione 3 salvo che permette, nella finestra di dialogo, la scelta del layer "Particelle" e del Layer "Intersezioni", al fine di rendere lo script indipendente dal nome del layer scelto dall'utente così da non dover ricorrere alla preventiva manipolazione del codice.

Lo script:
1) Verifica la struttura del layer particelle selezionato che deve rispondere ai prerequisiti stabiliti;
2) Verifica la struttura del layer intersezioni, selezionato per ricevere il risultato, che deve rispondere ai prerequisiti stabiliti;
3) Parte dalla selezione delle particelle sul layer selezionato;   
4) Esegue le intersezioni tra le particelle selezionate e tutti i layer polgonali scelti nella finestra di dialogo;     
5) Calcola le percentuali di sovrapposizione;   
6) Trasferisce il risultato all'interno del layer selezionato per accogliere le intersezioni.
Se le colonne del layer delle particelle e dei layer delle intersezioni contengono la struttura del layer preimpostato che accoglie il risultato, tutte le colonne risulteranno popolate, altrimenti alcune colonne saranno vuote.

Vantaggi: 
1) Lo script lavora con qualsiasi layer poligonale, aggiornando le mappe è possibile ottenere intersezioni sempre aggiornate anche in tempo reale;
2) E' possibile impostare e scegliere diversi layer particelle (per operazioni storiche per esempio) e diversi layer per accogliere i risultati delle intersezioni (per costruire più tabelle per esempio);

Svantaggi:
1) L'elaborazione richiede CPU (ma non troppa);   
2) Per un risultato ottimale e ottenere una tabella dell'intersezione completamente popolata i layer particelle e di intersezione devono rispettare la struttura preimpostata e dunque necessaria una loro preimpostazione;
3) Lo script non è progettato per attivare una azione sul layer, proprio perchè funziona su qualsiasi layer particelle selezionato, per partire ha bisogno di essere lanciato da qualche opzione, dunque se si definisce su un layer, può essere lanciato solo da quel layer, mentre funziona universalmente sulla consolle python. Questo comportamento perchè è un progetto in evoluzione destinato allo sviluppo ebentuale di un plugin. E' dunque una versione ancora instabile non consigliata. Come azione di layer meglio utilizzare la versione 5.

## Versione QGIS testata
Lo script è testato nella versione QGIS 3.40 per le versioni successive potrebbero essere
necessari alcuni aggiustamenti.

## Prerequisiti dei layer
Lo script è progettato per funzionare con le seguenti caratteristiche dei layer:   
1) Nel progetto deve essere presente il layer delle particelle catastali;
2) Nel progetto deve essee presente il layer che accoglie il risultato delle intersezioni;
3) Il layer delle particelle deve avere la seguente struttura:
   id (chiave primaria); foglio (integr); allegato (string); mappale (string); Area1 (Real);
4) I layer da intersecare devono avere la seguente struttura:
   id (chiave primaria); tema (string); zona (string); descrizion (string); J_norme (string)
   tema: descrive lo strato informativi (ad esempio: T01 PUC; T02 PAI; T03 VINCOLO FRANA etc.);   
   zona: descrive l'acronimo della zona di solito riportato in legenda (ad esempio zona A; B; C etc.);
   descrizion: descrive il significato dell'acronimo di zona (ad esempio: CENTRO STORICO; COMPLETAMENTO ect.);
   J_norme: contiene i riferimenti normativi (ad esempio: Artt: 25, 27 e 29 delle NTA del PUC);
6) Il layer di destinazione delle intersezioni deve avere la seguente struttura:
   foglio (integer); allegato (string); mappale (string); tema (string); zona (string); descrizion (string); J_norme (string); percent (integer);   

E' possibile assegnare al nome dei campi qualsiasi alias.

## Come installare l'azione
Sul layer delle particelle va definita una azione Python con lo script "EseguiIntersezioniV4.py".   
Sul layer del risultato delle intersezioni va definita una azione Python con lo script "GeneraCDU_da_IntersezioniV4.py".
Deve essere raggiungibile dal progetto QGIS un template .doc con una tabella coerente con quella del layer "Intersezioni".

## Anteprima
Vedi Variante 2, il funzionamento è analogo cambia solo la gestione del processo.

