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
      * fid - chiave primaria di tipo integer;   
      * COMUNE - nome del comune di tipo string;   
      * foglio - numero di foglio di tipo integr;   
      * allegato - numero/lettera allegato foglio di tipo string;   
      * mappale - numero della particella di tipo string (può contenere anche lettere es. 11a);   
      * Area1 - superficie della particella di tipo real (per la massima precisione);   
2) I laye all'interno del gruppo "URBANISTICA" possono avere qualsiasi nome valido ma campi omogenei:
      * fid - chiave primaria integer;
      * tema - indicazione del piano/programma/vincolo che il layer rappresenta di tipo string;
      * zona - acronimo della zona rappresentata di tipo string;
      * descrizion - descrizione della zona di tipo string;
3) TabellaCDU con i campi strutturati per accogliere le intersezioni:
      * foglio tipo integer;
      * allegato tipo string;
      * mappale tipo string;
      * tema tipo string;
      * zona tipo string;
      * descrizion tipo string;
      * percent che ospiterà la percentuale di sovrapposizione di tipo integer.

## Come installare le azioni
Sul layer "Particelle" va definita una azione Python con lo script "GeneraTabellaCDU.py".
Sul layer "TabellaCDU" va definita una azione Python con lo script "GeneraTabellaCDU.py".

## Anteprima
https://youtu.be/nxNJLOkNjqU
<div style="
  border:1px solid #e0e0e0;
  border-radius:6px;
  padding:12px;
  margin:18px 0;
  box-shadow:0 1px 4px rgba(0,0,0,0.06);
  background:#fafafa;
  max-width:800px;
">

  <h3 style="margin:0 0 10px 0; font-size:18px; font-weight:600;">
    🎥 GENERA CDU VAR. 1
  </h3>

  <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:4px;">
    <iframe 
      src="https://www.youtube.com/embed/nxNJLOkNjqU"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
      style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:4px;">
    </iframe>
  </div>

  <p style="margin-top:8px; font-size:14px;">
    🔗 <a href="" target="_blank">
      Apri su YouTube
    </a>
  </p>

</div>
