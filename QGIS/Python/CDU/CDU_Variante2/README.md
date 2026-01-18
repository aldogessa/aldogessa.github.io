# GENERAZIONE CDU VERSIONE 2
Script da utilizzare come azione Python definita sul layer delle particelle.
Questa versione sfrutta la preconfigurazione delle intersezioni che sono archiviate
in un apposito layer (DestinazioniUrbanistiche).
Lo script parte dalla selezione delle particelle e recupera con una chiave esterna
le relative intersezioni preconfigurate e archiviate in un apposito layer, trasferendo
i dati in un file .doc, preconfigurato anch'esso, che viene servito come anteprima del certificato
di destinazione urbanistica.

Vantaggi: 
1) minima elaborazione CPU ed elavata velocità di esecuzione, lo script deve solo raccogliere informazioni senza calcolare;
2) libertà di organizzazione dell'albero dei layer;
3) la strategia può essere utilizzata nei WebGis Lizmap, per non caricare il server ed incidere sulle prestazioni,
   perchè non richiede calcoli complessi (intersezioni);
5) la strategia permette di avere coerenza tra QGIS locale e WebGis Lizmap.

Svantaggi:
1) aggiornamenti più onerosi, occorre riprodurre la tabella delle intersezioni (DestinazioniUrbanistiche).

## Versione QGIS testata
Lo script è testato nella versione QGIS 3.40 per le versioni successive potrebbero essere
necessari alcuni aggiustamenti.

## Prerequisiti dei layer
Lo script è progettato per funzionare con le seguenti caratteristiche dei layer:   
1) Nel progetto deve essere presente il layer delle particelle catastali
   che deve avere una chiave esterna predisposta (in questo caso VIRTID);     
2) Nel progetto deve essere presente il layer contenente le inersezioni (in questo caso DestinazioniUrbanistiche)
   con la medesima chiave esterna, da preservare durante l'esecuzione delle intersezioni (in questo caso virtid);
3) Colonne della tabella intersezioni coerente con la tabella del template .doc.

## Come installare l'azione
Sul layer "Particelle" va definita una azione Python con lo script "GeneraCDU.py".

## Anteprima
<a href="https://youtu.be/ZibaKQC1TEM" target="_blank">
  <img src="https://img.youtube.com/vi/ZibaKQC1TEM/0.jpg" alt="Video YouTube">
</a>
