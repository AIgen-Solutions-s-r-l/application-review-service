
# Documentazione del Progetto CoreService

Benvenuti nella documentazione del progetto **CoreService**. Questa documentazione fornisce una panoramica completa del progetto, incluse le istruzioni per l'installazione, l'uso, e la manutenzione.

## Indice

- [Introduzione](#introduzione)
- [Installazione](#installazione)
- [Guida Rapida](#guida-rapida)
- [Struttura del Progetto](#struttura-del-progetto)
- [Configurazione](#configurazione)
- [Esecuzione dei Test](#esecuzione-dei-test)
- [Docker](#docker)
- [Contributi](#contributi)
- [Licenza](#licenza)

## Introduzione

CoreService è un'applicazione progettata per gestire messaggi asincroni tramite RabbitMQ e fornire un'interfaccia API costruita con FastAPI. Questa soluzione è costruita utilizzando Python e offre funzionalità per il processamento e la gestione dei messaggi.

## Installazione

Per installare il progetto, segui questi passaggi:

1. Clonare il repository:
    ```sh
    git clone <repository-url>
    cd coreService
    ```

2. Creare un ambiente virtuale e attivarlo:
    ```sh
    python -m venv venv
    source venv/bin/activate  # Su Windows usare `venv\Scripts\activate`
    ```

3. Installare le dipendenze:
    ```sh
    pip install -r requirements.txt
    ```

## Guida Rapida

Per avviare l'applicazione in locale:

1. Esegui il file principale:
    ```sh
    python app/main.py
    ```

2. Apri il browser e vai a `http://localhost:8000` per vedere l'applicazione in esecuzione.

## Struttura del Progetto

Ecco una panoramica della struttura del progetto:
```
coreService/ 
├── .gitignore 
├── Dockerfile 
├── README.md 
├── requirements.txt 
├── docs/ 
│   └── index.md
├── app/ 
│   ├── routers/ 
│   │   └── example_router.py 
│   ├── core/ 
│   │   └── config.py 
│   ├── models/
│   │   └── __init__.py
│   ├── services/
│   │   └── message_sender.py
│   ├── tests/ 
│   │   ├── test_example_router.py 
│   │   └── test_main.py 
│   ├── rabbitmq_client.py 
│   └── main.py 
└── pytest.ini
```

## Configurazione

Le configurazioni principali del progetto si trovano in `app/core/config.py`. Assicurati di impostare le variabili di ambiente richieste, inclusi i dettagli per la connessione a RabbitMQ.

## Esecuzione dei Test

Per eseguire i test, puoi utilizzare `pytest`:

```sh
pytest
```

## Docker

Per costruire l'immagine Docker ed eseguire il container:

1. Costruzione dell'immagine:
    ```sh
    docker build -t coreservice .
    ```

2. Esecuzione del container:
    ```sh
    docker run -d -p 8000:8000 coreservice
    ```

## Contributi

Siamo aperti ai contributi! Segui questi passaggi per contribuire:

1. Fai un fork del repository.
2. Crea un nuovo branch (`git checkout -b feature/nome-feature`).
3. Esegui i tuoi cambiamenti e committali (`git commit -am 'Aggiunta nuova feature'`).
4. Push del branch (`git push origin feature/nome-feature`).
5. Crea una Pull Request.

## Licenza

Questo progetto è rilasciato sotto la licenza [Nome Licenza]. Vedi il file [LICENSE](./LICENSE) per più dettagli.
