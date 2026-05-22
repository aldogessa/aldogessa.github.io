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
<br>
Layer Fogli
- fid — integer, chiave primaria interna.
- COMUNE — text, nome del Comune.
- FOGLIO — integer, numero del foglio catastale.
- COD_CAT — text, codice catastale del Comune.
<br>

Layer Particelle
- fid — integer, chiave primaria interna.
- FOGLIO — integer, numero del foglio catastale.
- ALLEGATO — text, indicativo dell’allegato.
- MAPPALE — text, numero della particella (può contenere lettere).
- SUPCALC — real, area della particella utilizzata per i calcoli metrici.
- SUPVIDEO — text, area formattata per la visualizzazione (migliaia + due decimali).
- VIRTID — text, identificativo univoco della particella ottenuto concatenando: LPAD(FOGLIO, 5, '0') || LPAD(MAPPALE, 15, '0') Questo garantisce un codice univoco, ordinabile e privo di ambiguità (es. distingue correttamente 1/11 da 11/1).
- id — integer, numero progressivo generato con row_number() utile per verifiche interne e per controllare la corrispondenza con fid.
- layer — text, campo derivato dalla fornitura per verificare che siano state estratte solo le particelle.
- anno — text, anno della fornitura catastale.
- agg — text, data di aggiornamento della fornitura.
<br>

#### Perché non automatizzare la normalizzazione
Le forniture catastali dell’Agenzia delle Entrate non sono completamente uniformi nel tempo: possono variare nella denominazione dei campi, nella presenza di attributi aggiuntivi o nella struttura interna dei layer. Automatizzare la normalizzazione significherebbe assumere che la struttura sia sempre identica, con il rischio di introdurre errori silenziosi difficili da individuare.
L’esecuzione manuale della normalizzazione consente invece di verificare ogni volta la coerenza della fornitura, garantendo che i dati siano correttamente allineati alla struttura standard adottata dal progetto.

### Layer Tematici
I layer tematici rappresentano gli strati informativi che descrivono il territorio e che si sovrappongono alla cartografia catastale e alle mappe di base. Possono essere numerosi e molto eterogenei tra loro; per questo motivo è opportuno organizzarli in una struttura logica e gerarchica che ne faciliti la gestione, la lettura e l’utilizzo nelle automazioni.
Si suggerisce di suddividere i layer in temi principali, identificati da un codice numerico progressivo, e in sotto temi, anch’essi codificati in modo coerente.   
Esempio di organizzazione dei temi:
- T01 – Piano urbanistico Comunale;
- T02 – Piano di assetto idrogeologico;
- ...
<br>

Esempio di organizzazione dei sotto temi:   
T01 – Piano urbanistico comunale
- T01.01 - Zonizzazione;
- T01.02 – Variante strada;
- T01.03 – Variante localizzazione ospedale;
- T01.04 - ...

T02 – Piano di assetto idrogeologico
- T02.01 – Pericolosità idraulica;
- T02.02 – Pericolosità geologica;
- ...
<br>

La codifica dei temi non deve essere casuale, ma definita in base all’ordine con cui si desidera che i layer compaiano nella tabella del Certificato di Destinazione Urbanistica.
In questo modo, ad esempio, il Piano Urbanistico Comunale (T01) verrà riportato per primo, seguito dalle sue varianti (T01.xx), e successivamente dalle informazioni relative alla pericolosità idraulica e geologica (T02.xx).   
Questa struttura garantisce:
- coerenza tra progetto QGIS, Lizmap e CDU;
- ordinamento stabile e prevedibile;
- facilità di manutenzione nel tempo;
- maggiore leggibilità per tecnici e cittadini;
- automazioni più robuste e meno soggette a errori.

#### Normalizzazione dei layer tematici e loro struttura
Per facilitare e velocizzare le automazioni, le intersezioni vettoriali e la produzione del Certificato di Destinazione Urbanistica, è consigliabile normalizzare i layer tematici adottando una struttura uniforme e stabile nel tempo.
La normalizzazione deve tenere conto dei contenuti della pubblicazione che si intende realizzare e deve garantire che ogni layer tematico disponga degli attributi necessari per essere correttamente interpretato dal sistema.
Una struttura particolarmente solida e flessibile è la seguente:
- fid: integer – chiave primaria;
- CODTEMA: text – contiene il codice tema (esempio T01.01);
- DESCTEMA: text – contiene la descrizione del tema (esempio PIANO URBANISTICO);
- TEMA: text – contiene per esteso “CODTEMA”||’ ‘||”DESCTEMA” (esempio T01.01 PIANO URBANISTICO);
- ZONA: text – contiene l’etichetta della zona rappresentata dalla geometria (esempio A o B o C);
- DETTAGLIO: text – contiene la descrizione della zona (esempio CENTRO STORICO o COMPLETAMENTO);
- NORME: text – contiene i riferimenti normativi (esempio Artt. da 32 a 44 delle NTA del PUC);
- IMGZONA: text – contiene l’URL ad una immagine sulla cartella media che caratterizza la zona;
- DESCRIZ_A: text – contiene una descrizione più estesa e completa della zona;
- DESCRIZ_B: text – contiene una seconda descrizione più estesa della zona per ulteriori approfondimenti;
- DESCRIZ_C: text – contiene una terza descrizione se necessaria;
- LINK_A: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_A: text – contiene la descrizione dell’URL A (es: Vedi NTA del PUC);
- LINK_B: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_B: text – contiene la descrizione dell’URL B (es: Vedi NTA del PAI);
- LINK_C: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_C: text – contiene la descrizione dell’URL C (es: Vai a sito regionale);
- LINK_D: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_D: text – contiene la descrizione dell’URL D (es: Vedi documento);
- LINK_E: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_E: text – contiene la descrizione dell’URL E (es: Scarica file);
- LINK_F: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_F: text – contiene la descrizione dell’URL F (es: Approfondimento);
- LINK_G: text – contiene l’URL a un documento o risorsa esterna;
- DESLINK_G: text – contiene la descrizione dell’URL G (es: Vai al Piano Particolareggiato).

#### Campi obbligatori e campi opzionali
- Obbligatori: CODTEMA, DESCTEMA, TEMA, ZONA, DETTAGLIO, NORME → senza questi campi, il CDU risulterà incompleto o vuoto nelle parti essenziali.
- Opzionali: tutti i campi successivi a NORME → Lizmap li ignora se vuoti, quindi possono essere popolati solo quando necessari.
Questa scelta rende la struttura estremamente flessibile: puoi avere layer molto semplici (solo i campi essenziali) o layer molto ricchi (descrizioni, immagini, link, approfondimenti).

#### Perchè questa struttura
- Uniforma tutti i layer tematici, anche se provengono da fonti diverse.
- Stabilizza le automazioni (intersezioni, merge, CDU).
- Riduce gli errori dovuti a campi mancanti o denominazioni incoerenti.
- Permette aggiornamenti periodici senza dover riscrivere script o modelli.
- Supporta Lizmap in modo nativo (popup, media, immagini, link, descrizioni).
- Rende il CDU leggibile e completo, con testi e riferimenti normativi.

### Analisi urbanistica: intersezione tra particelle e layer tematici
Una volta predisposti i layer catastali e i layer tematici normalizzati, è possibile eseguire l’analisi urbanistica mediante l’intersezione tra le particelle e i layer tematici, calcolando per ciascuna particella le percentuali di sovrapposizione e preservando tutte le informazioni provenienti dai diversi temi.
Esistono diverse strategie per eseguire questa analisi. La più diffusa consiste nel reiterare l’intersezione tra le particelle e ciascun layer tematico, producendo tanti risultati quante sono le sorgenti informative. Tuttavia, la normalizzazione eseguita sui layer tematici non è stata introdotta solo per uniformare la struttura dei dati, ma anche per rendere più efficiente l’intero processo di analisi.
Poiché tutti i layer tematici condividono la stessa struttura, è possibile eseguire un merge tra essi, ottenendo un unico layer tematico che contiene al suo interno tutte le zone rilevanti ai fini dell’analisi urbanistica, con una struttura perfettamente coerente con quella di ciascun layer di origine.
In questo modo, anziché eseguire tante intersezioni quante sono le sorgenti tematiche, è sufficiente eseguire una sola intersezione tra le particelle catastali e il layer tematico unificato.
Questa strategia comporta un vantaggio significativo in termini di prestazioni, velocità e stabilità del processo, soprattutto in presenza di numerosi layer tematici o di geometrie complesse.
L’intero procedimento può essere automatizzato tramite uno script Python, sviluppato con l’assistenza dell’Intelligenza Artificiale, che consente di selezionare i layer tematici da includere nel merge e di eseguire automaticamente l’intersezione con le particelle, scrivendo i risultati in un layer appositamente predisposto.
Il layer di destinazione, se si segue lo schema dei layer catastali e tematici fin qui descritto, deve avere la seguente struttura:
- fid — integer, chiave primaria intern;
- FOGLIO — integer, deriva dal layer particelle;
- ALLEGATO — text, deriva dal layer particelle;
- MAPPALE — text, deriva dal layer particelle;
- TEMA: text – deriva dal layer tematico;
- ZONA: text – deriva dal layer tematico;
- DETTAGLIO: text – deriva dal layer tematico;
- NORME: text – deriva dal layer tematico;
- PERCENT: integer - percentuale calcolata dall’algoritrmo;
- PERCENT_V: text – percentuale da visualizzare calcolata dall’algoritmo che gestisce le percentuali pari a zero;
- IMGZONA: text – deriva dal layer tematico;
- DESCRIZ_A: text – deriva dal layer tematico;
- DESCRIZ_B: text – deriva dal layer tematico;
- DESCRIZ_C: text – deriva dal layer tematico;
- LINK_A: text – deriva dal layer tematico;
- DESLINK_A: text – deriva dal layer tematico;
- LINK_B: text – deriva dal layer tematico;
- DESLINK_B: text – deriva dal layer tematico;
- LINK_C: text – deriva dal layer tematico;
- DESLINK_C: text – deriva dal layer tematico;
- LINK_D: text – deriva dal layer tematico;
- DESLINK_D: text – deriva dal layer tematico;
- LINK_E: text – deriva dal layer tematico;
- DESLINK_E: text – deriva dal layer tematico;
- LINK_F: text – deriva dal layer tematico;
- DESLINK_F: text – deriva dal layer tematico;
- LINK_G: text – deriva dal layer tematico;
- DESLINK_G: text – deriva dal layer tematico;
- ORD: text – campo libero da popolare successivamente sulla base dell’ordinamento che si intende ottenere;
- FK_CAT: integer – preservato dall’algoritmo che associa ad ogni intersezione la chiave primaria della particella;
- VIRTID: text – derivata dal layer particelle.

#### Ordinamento della tabella analisi urbanistica
Per ottenere un ordinamento stabile e coerente dei risultati dell’analisi urbanistica è necessario definire l’ordinamento   
<br>
“TEMA”||”ZONA”||”DETTAGLIO”||Lpad(“PERCENT”, ‘0’,3)   
<br>
Questa concatenazione garantisce un ordinamento logico e prevedibile tra temi, sotto‑temi, zone e percentuali di sovrapposizione, assicurando che la tabella finale rispetti la gerarchia definita nella codifica dei layer tematici.
Il campo ORD riveste un ruolo fondamentale perché deve essere utilizzato per costruire i valori del campo fid del GeoPackage prima della scrittura finale. Lizmap, infatti, ordina i “figli” sulla base del loro fid in ordine decrescente; pertanto, se si mantengono i fid generati automaticamente dall’algoritmo, non vi è alcuna garanzia che i risultati vengano visualizzati nell’ordine desiderato.
Una volta definito l’ordinamento corretto tramite il campo ORD, è necessario procedere alla rigenerazione dei fid secondo tale ordine.   
La procedura consigliata è la seguente:
- ordinare la tabella dell’analisi urbanistica in base al campo ORD (in cima il tema che si vuole visualizzare per ultimo);
- copiare e incollare tutti i record in un layer temporaneo;
- applicare al campo fid la funzione row_number() per generare una numerazione progressiva coerente con l’ordinamento desiderato;
- utilizzare il layer temporaneo per sovrascrivere il layer dell’analisi urbanistica nel GeoPackage (se già esistente) oppure per crearlo ex novo se si tratta della prima generazione.

Questa procedura garantisce che Lizmap visualizzi i risultati dell’analisi urbanistica nell’ordine corretto, rispettando la gerarchia dei temi e la struttura del Certificato di Destinazione Urbanistica.

#### Automazione delle intersezioni
Lo script Python è progettato come azione associata al layer delle particelle, in modo da ridurre al minimo la possibilità di errore da parte dell’operatore.   
Lo script:
- individua automaticamente il layer delle particelle, evitando selezioni errate;
- permette di selezionare il layer predisposto per accogliere l’analisi urbanistica e mantiene in memoria tale scelta per le esecuzioni successive;
- consente di selezionare i layer tematici da includere nell’intersezione e ricorda anche questa selezione;
- per dataset molto estesi, supporta la modalità incrementale, elaborando blocchi consecutivi di particelle e salvando progressivamente i risultati nella stessa tabella, senza sovrascrivere i dati già presenti.

Questa modalità incrementale è particolarmente utile quando si lavora con:
- migliaia di particelle selezionate;
- layer tematici complessi;
- server o workstation con risorse limitate.

In questo modo l’analisi rimane robusta, scalabile e ripetibile, senza rischiare blocchi o perdita di dati.

#### Perché non automatizzare l’ordinamento
L’ordinamento finale dell’analisi urbanistica è un’operazione:
- semplice;
- veloce;
- soggetta a possibili variazioni a ogni aggiornamento dei dati.
- 
Automatizzarlo all’interno dello script significherebbe:
- irrigidire il processo;
- dover modificare lo script ogni volta che cambia una regola di ordinamento;
- introdurre potenziali fragilità in un componente che deve rimanere stabile.

Mantenendo l’ordinamento come fase manuale, si ottengono due vantaggi fondamentali:
- Lo script rimane sempre coerente e robusto, perché lavora solo su dati stabili e consolidati.
- L’operatore mantiene il controllo su eventuali modifiche da apportare all’ordinamento in occasione di aggiornamenti, varianti o nuove esigenze di pubblicazione.

In altre parole lo script automatizza ciò che deve essere stabile, mentre l’ordinamento rimane flessibile e sotto controllo umano.













