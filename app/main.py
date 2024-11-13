# /app/main.py

import logging
import asyncio
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI

from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient
from app.services.applier import consume_jobs_interleaved

from motor.motor_asyncio import AsyncIOMotorClient

# Configura il logging
logging.basicConfig(level=logging.DEBUG)

# Carica le impostazioni
settings = Settings()

# Crea un'istanza del client RabbitMQ
rabbit_client = RabbitMQClient(
    rabbitmq_url=settings.rabbitmq_url,
    queue="my_queue",
    callback=lambda ch, method, properties, body: print(f"Message: {body.decode()}")
)

# Crea un'istanza del client MongoDB
mongo_client = AsyncIOMotorClient(settings.mongodb)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager per l'avvio e lo spegnimento delle risorse.
    """
    # Avvia il client RabbitMQ in un thread separato
    rabbit_thread = Thread(target=rabbit_client.start, daemon=True)
    rabbit_thread.start()
    logging.info("RabbitMQ client started")

    # Avvia il consumatore di job come task di background
    loop = asyncio.get_event_loop()
    job_consumer_task = asyncio.create_task(consume_jobs_interleaved(mongo_client))
    logging.info("Job consumer started")

    try:
        yield
    finally:
        # Ferma il client RabbitMQ e altre risorse
        rabbit_client.stop()
        rabbit_thread.join()
        logging.info("RabbitMQ client stopped")

        # Cancella il task del consumatore di job
        job_consumer_task.cancel()
        try:
            await job_consumer_task
        except asyncio.CancelledError:
            logging.info("Job consumer task cancelled")
        
        # Chiudi il client MongoDB
        mongo_client.close()
        logging.info("MongoDB client closed")

# Inizializza l'app FastAPI con il context manager di lifespan
app = FastAPI(lifespan=lifespan)

# Non aggiungere route o router
