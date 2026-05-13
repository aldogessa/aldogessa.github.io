# AZIONI QGIS PER LA GENERAZIONE DEL CERTIFICATO DI DESTINAZIONE URBANISTICA VERSIONE 7
Versione di QGIS: 3.44.9   
Formato layer: Geopackage

## DESCRZIONE
Gli script V7_CDU_RealTime_Intersezioni.py e V7_CDU_RealTime_GeneraCDU.py fanno parte di un unico workflow suddiviso in due operazioni.   
La prima operazione (V7_CDU_RealTime_Intersezioni.py) esegue le intersezioni tra le particelle catastali e i layer selezionati, calcola la superficie di sovrapposizione e la relativa percentuale, trasferisce i dati nel layer dell'analisi urbanistica predisposto per lo scopo.   
La seconda operazione (V7_CDU_RealTime_GeneraCDU.py) estrae dalla tabella dell'analisi urbanistica, sopra descritta, il risultato dell'intersezione e popola il template.doc precedentemente predisposto.   
Lo script V7_CDU_TabellaPrecalcolata.py funziona in autonomia lavorando su due layer: layer delle particelle catastali e layer dell'analisi urbanistica ove sono precalcolate le intersezioni (che eventualmente possono essere calcolate con V_CDU_RealTime_Intersezioni).   
Entrambe le soluzioni richiedono che i layer abbiano la struttura indicata negli script.   
- V7_CDU_RealTime_Intersezioni.py va intallata come azione nel layer delle particelle;
- V7_CDU_RealTime_GeneraVDU.py va installata come azione nel layer dell'analisi urbanistica;
- V7_CDU_TabellaPrecalcolata.py va installata come azione nel layer delle particelle.

## Vantaggi e svantaggi delle due soluzioni
La soluzione V7_TabellaPrecalcolata.py ha il vantaggio della leggerezza e della velocità. Inoltre permette di mettere in relazione le particelle con le relative destinazioni urbanistiche. Lo svantaggio sta nell'aggiornamento: al variare del layer particelle o dei layer di sovrapposizione (puc, vincoli, etc.) è necessario ricalcolare la tabella dell'analisi urbanistica (per questa operazione può essere usato lo script V7_CDU_RealTime_Intersezioni.py con le raccomandazioni che seguiranno).   
La soluzione V7_CDU_RealTime_Intersezioni.py + V7_CDU_RealTime_GeneraCDU.py ha l'enorme vantaggio di non risentire degli aggiornamenti dei layer coinvolti nelle intersezioni perchè le intersezioni sono sempre ricalcolate. Lo svantaggio sta nel processamento che, per un numero ragionevole di particelle è comunque molto veloce. La CPU tende a soffrire quando si cerca di elaborare centinaia di particelle contemporaneamente su decine di layer di soprapposizione, ma questa è una condizione inverosimile. Tuttavia la scelta di trasferire i dati dell'elaborazione in una tabella fisica (layer dell'analisi urbanistica) permette l'incrementalità e duqnue di procedere, in casi limite, con l'elaborazione per blocchi. In questo modo è dunque possibile realizzare l'analisi urbanistica (per blocchi consecutivi) dell'intero dataset catastale.   
Le due soluzioni possono coesistere nello stesso ecosistema QGIS ed essere utilizzate in dipendenza delle circostanze di lavoro.

## Prerequisiti dei layer
Le azioni per funzionare correttamente richiedono che i layer abbiano struttura omogenea che nel caso degli script qui pubblicati è la seguente.   
.   
Layer delle particelle:   
fid	FOGLIO	ALLEGATO	MAPPALE	SUPVIDEO  SUPCALC  VIRTID   
.   
Layer di sovrapposizione (puc, vincoli, etc.):   
fid CODTEMA	DESCTEMA	TEMA	ZONA	DETTAGLIO	NORME	IMGZONA	DESCRIZ_A	LINK_A	DESLINK_A	LINK_B	DESLINK_B	LINK_C	DESLINK_C	LINK_D	DESLINK_D	LINK_E	DESLINK_E	LINK_F	DESLINK_F	LINK_G	DESLINK_G   
.   
Layer dell'analisi urbanistica (che riceve il risultato dell'intersezione):   
fid	FOGLIO	ALLEGATO	MAPPALE	TEMA	ZONA	DETTAGLIO	NORME	PERCENT	PERCENT_V	IMGZONA	DESCRIZ_A	DESCRIZ_B	DESCRIZ_C	LINK_A	DESLINK_A	LINK_B	DESLINK_B	LINK_C	DESLINK_C	LINK_D	DESLINK_D	LINK_E	DESLINK_E	LINK_F	DESLINK_F	LINK_G	DESLINK_G	ORD	FK_CAT	VIRTID.

## Template
Il template utilizzato deve essere conforme a quello pubblicato qui:
