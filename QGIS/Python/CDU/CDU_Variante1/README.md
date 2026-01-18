# GENERAZIONE CDU
La combinazione di questi due script Python permette di eseguire automaticamente   
l'intersezione tra il layer delle particelle catastali e i layer della pianificazione   
e dei vincoli contenuti in uno stesso gruppo (ad esempio "URBANISTICA"):   
1) Il primo esegue le intersezioni e popola la "TabellaCDU";
2) Il secondo estrapola i dati dalla "TabellaCDU" dopo essere stata visionata ed
   eventualmente corretta dall'operatore, e generale il certificato di destinanzione
   urbanistica in formato .doc.

## Versione QGIS testata
Lo script è testato nella versione QGIS 3.28 per le versioni successive potrebbero essere
necessari alcuni aggiustamenti.

## Prerequisiti dei layer
Gli script sono progettati per funzionare con le seguenti caratteristiche dei layer:   
1) Nel progetto deve essere presente il layer poligonale delle particelle catastali
   che deve avere i seguenti campi:
      fid - chiave primaria di tipo integer;   
      COMUNE - nome del comune di tipo string;   
      foglio - numero di foglio di tipo integr;   
      allegato - numero/lettera allegato foglio di tipo string;   
      mappale - numero della particella di tipo string (può contenere anche lettere es. 11a);   
      Area1 - superficie della particella di tipo real (per la massima precisione);   
   2)
