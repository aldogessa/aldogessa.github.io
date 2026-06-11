# Conversione coordinate tra EPSG:3003 ↔ EPSG:7791 tramite API IGM (Verto Online)

L’Istituto Geografico Militare ha recentemente rilasciato un servizio API che consente di convertire con precisione, gratuitamente e in tempo reale, le coordinate tra i principali sistemi di riferimento utilizzati in Italia: **Roma40**, **ED50** ed **ETRS89** (nelle realizzazioni **ETRF89** ed **ETRF2000**).

Il servizio permette di eseguire le trasformazioni ufficiali **senza disporre localmente dei grigliati NTv2**, poiché questi vengono applicati direttamente dal server IGM.  
Questo rende possibile effettuare conversioni tramite chiamate API, senza dover caricare manualmente file sul portale web.

Lo script sviluppato sfrutta questo servizio per risolvere la delicata questione della trasformazione tra **EPSG:3003** (Monte Mario / Italy zone 1) ed **EPSG:7791** (RDN2008 / TM32), che risulta troppo imprecisa se eseguita senza i grigliati ufficiali.

Tuttavia, dalle specifiche delle API si apprende che **la conversione diretta 3003 ↔ 7791 non è supportata**.

---

## Problemi affrontati

- **Il servizio non supporta la conversione diretta tra EPSG:3003 ed EPSG:7791.**  
  È quindi necessario utilizzare un sistema di riferimento intermedio supportato dall’API.

- La pipeline corretta prevede due passaggi:

### 1. Conversione 3003 → 6706 (API IGM)
Trasformazione dal sistema proiettato Monte Mario al sistema geografico **RDN2008 (EPSG:6706)** utilizzando i grigliati ufficiali.

### 2. Proiezione 6706 → 7791 (PROJ)
Proiezione dal sistema geografico RDN2008 al sistema proiettato **RDN2008 / TM32 (EPSG:7791)** tramite l’algoritmo nativo di QGIS (PROJ).

---

## Flusso inverso (7791 → 3003)

La trasformazione inversa segue la pipeline speculare:

### 1. 7791 → 6706 (PROJ)
De-proiezione TM32 → RDN2008 geografico.

### 2. 6706 → 3003 (API IGM)
Conversione ufficiale RDN2008 → Monte Mario tramite grigliati IGM.

---

## Note operative

- La trasformazione sembra **molto precisa**: gli scarti rispetto a Convergo sono dell’ordine del millimetro.
- È **sconsigliato** eseguire cicli ripetuti avanti–indietro (3003 → 7791 → 3003 → …), poiché ogni ciclo introduce un rumore numerico fisiologico.
- Lo script implementa un controllo **STRICT** di validità delle geometrie: se una geometria è invalida, l’elaborazione viene interrotta.

---

## Obiettivo dello script

Lo script vuole fornire una trasformazione affidabile tra 3003 e 7791, utilizzando:

- **API IGM** per il cambio di datum (Monte Mario ↔ RDN2008)
- **PROJ/QGIS** per la proiezione (RDN2008 geografico ↔ TM32)

Garantendo così risultati coerenti con gli standard istituzionali.

---

## Come si utilizza

Lo script è progettato per funzionare come script di processing, dunque il file.py deve essere salvato nell'apposita cartella .../processing/script/ e utilizzato dagli strumenti personalizzati di processing.
