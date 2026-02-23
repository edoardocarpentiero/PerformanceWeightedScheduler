# Cinder-Compliance

Il presente progetto propone lo sviluppo di un Compliance-Aware Storage Plugin per il servizio Cinder all’interno di OpenStack.
Il plugin estende il Cinder Scheduler introducendo un filtro e un weigher personalizzati, in grado di allocare i volumi in base a policy di conformità dichiarate dall’utente al momento della creazione, ad esempio vincoli geografici o normativi (EU-only, GDPR).

Attualmente, Cinder effettua l’allocazione dei volumi solo in base a parametri tecnici come capacità, disponibilità e caratteristiche dei backend, senza considerare vincoli di compliance. Il plugin proposto aggiunge una logica policy-aware, separando i backend conformi da quelli non conformi, garantendo che le risorse vengano allocate esclusivamente sui backend che rispettano le regole definite.
