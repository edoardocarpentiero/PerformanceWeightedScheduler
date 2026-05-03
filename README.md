# PerformanceWeightedScheduler

PerformanceWeightedScheduler è un plugin sperimentale per **OpenStack Cinder** progettato per migliorare la selezione dei backend durante la creazione dei volumi.

Nel funzionamento standard di Cinder, lo scheduler seleziona il backend principalmente sulla base di parametri statici, come lo spazio disponibile e le capabilities esposte dai driver. Questo approccio può rappresentare un limite in ambienti con risorse di storage eterogenee.

Negli scenari basati su **thick provisioning**, una decisione errata dello scheduler può avere effetti persistenti, poiché il volume viene allocato immediatamente sul backend selezionato e rimane vincolato a quella scelta. Questo può causare:

- degrado delle prestazioni;
- saturazione precoce dei backend più performanti;
- scarso bilanciamento del carico;
- utilizzo inefficiente dell’infrastruttura di storage.

PerformanceWeightedScheduler introduce un meccanismo di pesatura avanzata, basato non solo sulla capacità disponibile, ma anche su indicatori prestazionali reali dei backend, tra cui:

- IOPS;
- latenza;
- throughput;
- tipologia di storage;
- livello di saturazione.

---

## Obiettivi

Il plugin ha l’obiettivo di migliorare:

- il bilanciamento del carico;
- la distribuzione dei volumi tra backend differenti;
- la prevedibilità delle prestazioni;
- la capacità di evitare la saturazione precoce delle risorse più performanti;
- l’efficienza del processo di selezione dei backend in scenari di thick provisioning.

---

## Architettura Plugin
<img width="1003" height="595" alt="image" src="https://github.com/user-attachments/assets/c559e77a-86c9-428d-a018-f739fe1bd453" />

Il plugin è suddiviso in due componenti principali.

### 1. Performance Collector

Integrato in `cinder-volume`, questo modulo si occupa di:

- raccogliere le metriche prestazionali dei backend;
- acquisire informazioni sulla tipologia di storage;
- pubblicare le metriche verso `cinder-scheduler` tramite RPC/AMQP.

#### Struttura del modulo

- **collector_daemon.py**  
  Processo periodico che avvia automaticamente la raccolta delle metriche.

- **collector_service.py**  
  Coordina la raccolta, identifica i backend configurati e associa i dispositivi fisici o virtuali da monitorare.

- **performance_metrics.py**  
  Utilizza `iostat` per raccogliere metriche quali:
  - IOPS
  - throughput
  - latenza
  - saturazione

- **scheduler_rpc_api.py**  
  Trasmette le metriche raccolte al modulo scheduler tramite RPC.

---

### 2. Weigher Extension

Integrato in `cinder-scheduler`, questo modulo si occupa di:

- ricevere le metriche da `cinder-volume`;
- memorizzarle in una cache interna;
- estendere lo scheduler con un custom weigher;
- calcolare un punteggio per ciascun backend.

Se le metriche richieste non sono presenti o risultano obsolete, lo scheduler può attivare una richiesta RPC on-demand verso `cinder-volume` per aggiornare i dati prima della fase di weighing.

#### Struttura del modulo

- **performance_weigher.py**  
  Implementa il custom weigher e calcola lo score finale dei backend.

- **scheduler_bootstrap.py**  
  Inizializza il sistema RPC lato scheduler.

- **scheduler_metrics_endpoint.py**  
  Endpoint RPC che riceve e aggiorna le metriche.

- **metrics_cache.py**  
  Gestisce la cache locale delle metriche dei backend.

- **performance_storage_bonus.json** (`/etc/cinder/`)  
  File di configurazione che consente di associare bonus differenti a specifiche tecnologie di storage (SSD, HDD, NVMe).

---


## Struttura del progetto

```text
PerformanceWeightedScheduler/
│
├── devstack/
│   ├── plugin.sh
│   ├── module1_collector.sh
│   └── module2_weigher.sh
│
├── modulo_1_performance_collector/
│   ├── collector_daemon.py
│   ├── collector_service.py
│   ├── performance_metrics.py
│   └── scheduler_rpc_api.py
│
├── modulo_2_weigher_extension/
│   ├── performance_weigher.py
│   ├── scheduler_bootstrap.py
│   ├── scheduler_metrics_endpoint.py
│   └── metrics_cache.py
│
├── test_env/
│   └── local.conf
│
├── test_script/
    ├── setup_env.sh
    └── simulate_io.sh


```



## Ambiente di test

### Cartella `test_env`

Contiene il file di configurazione DevStack utilizzato per predisporre l’ambiente di test in modo da fornire una configurazione completa e facilmente replicabile dell’ambiente sperimentale.

- **local.conf**
  - credenziali DevStack;
  - configurazione servizi OpenStack;
  - attivazione del plugin;
  - configurazione Cinder multi-backend;
  - backend `low_cap`, `mid_cap`, `high_cap`;
  - tipologia di storage e volume type;
  - parametri di test.

---

### Cartella `test_script`

Contiene gli script utilizzati per predisporre e validare l’ambiente di test in modo da simulare tre backend distinti con capacità differenti su una singola macchina.

#### `setup_env.sh`

- crea i Volume Group LVM:
  - `vg-low`
  - `vg-mid`
  - `vg-high`
- associa i file a loop device Linux;


#### `simulate_io.sh`

- genera operazioni di lettura e scrittura sul backend selezionato;
- produce carico reale;
- consente di verificare:
  - raccolta metriche via `iostat`;
  - aggiornamento dinamico delle metriche;
  - comportamento dello scheduler sotto carico.

---

## Workflow di installazione e test

### 1. Installazione DevStack

```bash
sudo apt update
sudo apt install -y git
git clone https://opendev.org/openstack/devstack
cd devstack
```

Copiare il file:

```text
PerformanceWeightedScheduler/test_env/local.conf
```

Eseguire:

```bash
./stack.sh
```

---

### 2. Setup e validazione ambiente di test

```bash
cd /opt/stack/performance-weighted-scheduler/test_script
chmod +x setup_env.sh
./setup_env.sh
```

Eseguire il comando di autenticazione
```bash
source openrc admin admin
```

2.1 Verifica disponibilità servizi:
```bash
openstack volume service list
```
<img width="1004" height="143" alt="image" src="https://github.com/user-attachments/assets/7d3b63b1-3cb3-4df6-bd99-9d35836a9727" />

2.2 Verifica capacità BE e loop device attivi:
```bash
sudo vgs
```
<img width="745" height="169" alt="image" src="https://github.com/user-attachments/assets/0c2274f8-e10c-4b5f-957d-b24eb287e1f3" />

2.3 Creazione volume:

```bash
openstack volume create --size <size_GB> <nome_volume>
```
Esempio:

```bash
openstack volume create --size 3 volume_1
```
<img width="407" height="390" alt="image" src="https://github.com/user-attachments/assets/b920ac29-17a0-4efa-b596-d82a91c2bb97" />

2.4 Verifica disponibilità volumi VL:

```bash
openstack volume list
```
<img width="592" height="74" alt="image" src="https://github.com/user-attachments/assets/455e2160-68e6-4ab0-94e8-a1bd8f496816" />

---

### 3. Simulazione I/O
Lo script `simulate_io.sh` viene utilizzato per generare artificialmente carico di lettura e scrittura su uno specifico Volume Group LVM. Riceve in input il nome del `Volume Group`, crea al suo interno un volume logico temporaneo da 512 MB e avvia un ciclo continuo di operazioni di scrittura e lettura tramite il comando dd.

Lo script rimane attivo fino all’interruzione manuale dell’utente tramite `CTRL+C`. Alla chiusura, rimuove automaticamente il volume temporaneo creato, evitando di lasciare risorse inutilizzate nel sistema. Questo strumento è stato utilizzato per produrre attività reale sui backend e verificare la corretta raccolta delle metriche da parte di `iostat`, come IOPS, throughput, latenza e utilizzo del dispositivo.

```bash
chmod +x simulate_io.sh
./simulate_io.sh <nome_VG>
```

Esempio:

```bash
./simulate_io.sh vg-high
```

## Note finali

- Il plugin è attualmente progettato principalmente per ambienti LVM-based.
- Il sistema è facilmente estendibile verso altri driver di storage.
- Il file JSON di bonus consente una gestione dinamica delle preferenze hardware.
- Per la verifica delle attività eseguite dallo scheduler: `sudo journalctl -u devstack@c-sch -f > test.txt`
