# AZIONE QGIS PER LA GENERAZIONE DEL CERTIFICATO DI DESTINAZIONE URBANISTICA IN TEMPO REALE
Versione di QGIS: 3.44.15   
Formato layer: Geopackage

## PREREQUISITI
Azione Python da installare sul layer delle particelle catastali.   
Preferibilmente renderlo attivo su Layer e Mappa.   
L'azione agisce sul layer delle particelle catastali e sui layer tematici che rappresentano la zonizzazione del PUC e i diversi vincoli che interessano il territorio.   
L'azione funziona solamente se i layer coinvolti nel processo hanno una precisa struttura e a condizione che sia installata la libreria Python-docx.   
La libreria Python-docx viene installata automaticamente dall'azione al primo avvio se non presente (può essere necessario il riavvio di QGIS la prima volta).   

### Struttura del Layer particelle
- fid (chiave primaria);
- FOGLIO (integer);
- ALLEGATO (text);
- MAPPALE (text);
- SUPCALC (real deve contenere la superficie della particella);
- SUPVIDEO (text contiene la superficie formattata tipo 1.000,00);
- VIRTID (text contiene un identificativo univoco di ciascuna particella utilizzando i campi FOGLIO e MAPPALE);
- AGG (text contiene la data di aggiornamento della cartografia).

### Struttura dei layer tematici
- fid (chiave primaria);
- CODTEMA (text contiene un codice per ordinare e individuare il tema rappresentato dal vettore);
- DESCTEMA (text contiene una descrizione del tema);
- TEMA (text contiene l'unione dei campi CODTEMA e DESCTEMA);
- ZONA (text contiene l'etichetta della zona rappresentata dalla geometria);
- DETTAGLIO (text contiene la descrizione della zona rappresentata dalla geometria);
- NORME (text contiene il riferimento alle norme relative alla zona rappresentata dalla geometria);
- IMGZONA (text contiene un link ad una immagine da associare alla zona);
- DESCRIZ_A (text contiene una descrizione estesa della zona);
- DESCRIZ_B (text contiene una descrizione ulteriore);
- DESCRIZ_C (text contiene una descrizione ulteriore);
- LINK_A (text contiene un link a norme ed altre risorse);
- DESLINK_A (text contiene la descrizione del link);
- LINK_B (text contiene un link a norme ed altre risorse);
- DESLINK_B (text contiene la descrizione del link);
- LINK_C (text contiene un link a norme ed altre risorse);
- DESLINK_C (text contiene la descrizione del link);
- LINK_D (text contiene un link a norme ed altre risorse);
- DESLINK_D (text contiene la descrizione del link);
- LINK_E (text contiene un link a norme ed altre risorse);
- DESLINK_E (text contiene la descrizione del link);
- LINK_F (text contiene un link a norme ed altre risorse);
- DESLINK_F (text contiene la descrizione del link);
- LINK_G (text contiene un link a norme ed altre risorse);
- DESLINK_G (text contiene la descrizione del link);

### Template
I dati ricavati dall'azione vengono salvati su una tabella preimpostata su un template docx che viene recuperato dall'azione stessa, il template deve essere salvato all'interno della cartella che contiene il progetto QGIS, nella sottocartella \media e deve essere chiamato 00_CDU_Schema.docx (...\media\00_Schema.docx). La tabella vuota nel template deve avere 8 colonne ed una sola riga.
Il template utilizzato deve essere conforme a quello pubblicato qui:   
[Scarica il modello CDU (DOCX)](https://raw.githubusercontent.com/aldogessa/aldogessa.github.io/main/docs/risorse/documenti/00_CDU_Schema.docx)

## DESCRIZIONE DELL'AZIONE
L'azione esegue l'intersezione delle particelle selezionate con i layer tematici indicati nella finestra di dialogo e riporta i dati in un template preimpostato docx, permettendo il suo salvataggio nella posizione desiderata del computer, senza utilizzare tabelle di supporto. I dati sono ricavato in tempo reale ad ogni processo.

## Vantaggi e svantaggi
Il vantaggio si concretizza con minima necessità di manutenzione. Le modifiche apportate sui file coinvolti vengono immediatamente processate dall'azione, non è necessario elaborare alcuna tabella intermedia. Lo svantaggio è che la produzione in tempo reale non è consigliata lato browser e dunque non è replicabile (in javascript), da sola, in contesti webgis come, per esempio Lizmap, poichè le prestazioni potrebbero essere severamente compromesse ed è più opportuno utilizzare tabelle delle intersezioni precalcolate.

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
    🎥 GENERAZIONE CDU CON AZIONE PYTHON
  </h3>

  <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:4px;">
    <iframe 
      src="https://www.youtube.com/embed/ubHVhScl8Ic"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
      style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:4px;">
    </iframe>
  </div>

  <p style="margin-top:8px; font-size:14px;">
    🔗 <a href="https://www.youtube.com/watch?v=8x1fqWXyqyQ" target="_blank">
      Apri su YouTube
    </a>
  </p>

</div>
<br>
