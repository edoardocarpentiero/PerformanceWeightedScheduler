# PerformanceWeightedScheduler

PerformanceWeightedScheduler è un plugin sperimentale per OpenStack Cinder progettato per migliorare la selezione dei backend durante la creazione dei volumi.

Nel funzionamento standard di Cinder, lo scheduler seleziona principalmente un backend sulla base di parametri statici, come lo spazio disponibile e le capabilities esposte dai driver. Questo approccio può rappresentare un limite in ambienti con risorse di storage eterogenee, dove coesistono backend SSD e HDD.

Negli scenari basati su thick provisioning, una decisione errata dello scheduler può avere effetti persistenti, poiché il volume viene allocato immediatamente sul backend selezionato e rimane vincolato a quella scelta. Questo può causare:

- degrado delle prestazioni;
- saturazione precoce dei backend più performanti;
- scarso bilanciamento del carico;
- utilizzo inefficiente dell’infrastruttura di storage disponibile.

PerformanceWeightedScheduler introduce un meccanismo di pesatura più avanzato, basato non solo sulla capacità disponibile, ma anche su indicatori prestazionali dei backend, come:

- IOPS
- latenza
- throughput
- tipologia di storage
- livello di saturazione

## Architettura

Il plugin è suddiviso in due componenti principali:

### 1. Performance Collector

Integrato in `cinder-volume`, questo modulo si occupa di:

- raccogliere le metriche prestazionali dei backend;
- acquisire informazioni sulla tipologia di storage;
- pubblicare le metriche tramite RPC/AMQP;
- supportare richieste di fallback provenienti dallo scheduler.

### 2. Weigher Extension

Integrato in `cinder-scheduler`, questo modulo si occupa di:

- ricevere le metriche da `cinder-volume`;
- memorizzarle in una cache interna;
- estendere lo scheduler con un custom weigher;
- calcolare un punteggio per ciascun backend;
- selezionare il backend più adatto.

Se le metriche richieste non sono presenti o risultano obsolete, lo scheduler può attivare una richiesta RPC on-demand verso `cinder-volume` per aggiornare i dati prima di eseguire la fase di weighing.

## Obiettivi

Il plugin ha l’obiettivo di migliorare:

- il bilanciamento del carico;
- la distribuzione dei volumi tra backend differenti;
- la prevedibilità delle prestazioni;
- la capacità di evitare la saturazione precoce delle risorse più performanti;
- l’efficienza del processo di selezione dei backend in scenari di thick provisioning.

## Struttura del progetto

```text
modulo_1_performance_collector/
├── ....py

modulo_2_weigher_extension/
├── ....py
```

