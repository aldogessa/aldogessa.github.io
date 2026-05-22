# WORKFLOW QGIS + QGIS SERVER + LIZMAP CON VETTORI GEOPACKAGE

## INTRODUZIONE
Il workflow presentato in questo documento non è un esercizio teorico, ma il risultato di un lavoro concreto, sviluppato e applicato nel Sistema Informativo Territoriale del Comune di Villa San Pietro.
Da oltre due anni le mappe prodotte con questa metodologia sono pubblicate in modo stabile attraverso l’infrastruttura di Gter (servizio GisHosting – Piano Base) e vengono utilizzate quotidianamente sia dagli uffici tecnici sia dai cittadini.
Questa esperienza reale ha permesso di affinare ogni passaggio del processo, rendendolo affidabile, scalabile e facilmente aggiornabile. Il workflow nasce quindi dall’esigenza di costruire un sistema robusto, coerente e replicabile, capace di supportare in modo efficace la gestione dei dati territoriali e la produzione del Certificato di Destinazione Urbanistica.

## PREPARAZIONE DEI DATI

### Curare le prestazioni
La mappa pubblicata in Lizmap adotta il sistema di riferimento della mappa di base (OpenStreetMap o altri servizi), cioè EPSG:3857 – WGS84/Pseudo Mercator. QGIS Server riproietta automaticamente tutti i layer verso questo sistema di riferimento.
Per ridurre il carico computazionale sul server, soprattutto in presenza di molti layer, e per evitare disallineamenti dovuti a riproiezioni dinamiche, è consigliabile che i dati vettoriali e le eventuali altre mappe di base siano già disponibili in EPSG:3857.
Tuttavia, EPSG:3857 non è un sistema adatto all’editing né ai calcoli spaziali, poiché non garantisce coerenza geometrica e metrica. Per tutte le attività tecniche, analitiche e certificative è necessario utilizzare un sistema di riferimento proiettato idoneo.
In Sardegna è possibile utilizzare EPSG:3003 (Roma40 / Monte Mario) oppure EPSG:7791 (ETRF2000 / RDN2008). La mappa deve essere costruita e mantenuta in uno di questi sistemi, e successivamente i layer devono essere riproiettati in EPSG:3857 per la pubblicazione.
È quindi opportuno mantenere due dataset sincronizzati: – uno “master” in EPSG:3003 o EPSG:7791 – uno “di pubblicazione” in EPSG:3857
Le conversioni 3003 <-> 3857 e 7791 <-> 3857 sono standard e non presentano criticità.
La conversione 3003 <-> 7791, invece, non è standard e richiede l’uso dei grigliati IGM per garantire precisione metrica. In assenza dei grigliati è necessario evitare questa trasformazione, poiché comporta errori dell’ordine di diversi metri.

### Layer catastali
L’Agenzia delle Entrate mette a disposizione dei professionisti, tramite accesso con credenziali CIE/SPID/CNS, la fornitura dei dati catastali vettoriali comunali in diversi formati e sistemi di riferimento.
L’utilizzo dei dati è regolato dalla licenza Creative Commons CC BY 4.0, che consente il riuso anche commerciale con obbligo di attribuzione.
Per le attività tecniche e cartografiche è particolarmente indicato il formato GeoJSON, poiché può essere utilizzato direttamente in QGIS senza plugin aggiuntivi ed è disponibile sia in EPSG:3003 sia in EPSG:7791, entrambi idonei all’esecuzione di calcoli metrici e analisi spaziali.
La fornitura GeoJSON contiene tutti gli strati catastali; per ottenere un buon equilibrio tra prestazioni, leggibilità e completezza del dato è consigliabile estrarre e utilizzare principalmente gli strati dei Fogli e delle Particelle, che costituiscono la base delle analisi urbanistiche e delle certificazioni.

#### Normalizzazione della fornitura catastale e struttura dei layer
Per garantire la robustezza delle automazioni e favorire la replicabilità dei processi è necessario stabilire una struttura predefinita della tabella degli attributi. La fornitura dei dati catastali ottenuta dal portale dell’Agenzia delle Entrate può presentare variazioni nella struttura dei campi tra un aggiornamento e l’altro; per questo motivo, anche se la normalizzazione potrebbe essere automatizzata, si suggerisce di eseguirla manualmente, così da mantenere pieno controllo sia sulla struttura originale sia su quella finale.
Una volta verificata e normalizzata la fornitura, si consiglia di adottare le seguenti strutture standardizzate.
Layer Fogli
•	fid — integer, chiave primaria interna.
•	COMUNE — text, nome del Comune.
•	FOGLIO — integer, numero del foglio catastale.
•	COD_CAT — text, codice catastale del Comune.

