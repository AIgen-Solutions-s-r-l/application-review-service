# app/main.py
import logging
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.applier import consume_jobs

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load settings
settings = Settings()

# Initialize shared resources
rabbit_client = RabbitMQClient(rabbitmq_url=settings.rabbitmq_url)
rabbit_client.connect()
mongo_client = AsyncIOMotorClient(settings.mongodb)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for app resources."""
    # Start background task for consuming jobs and sending messages
    job_consumer_task = asyncio.create_task(consume_jobs(mongo_client, rabbit_client, settings))
    logging.info("Job consumer task started")

    try:
        yield
    finally:
        # Stop background tasks
        job_consumer_task.cancel()
        try:
            await job_consumer_task
        except asyncio.CancelledError:
            logging.info("Job consumer task cancelled")

        # Close RabbitMQ client
        rabbit_client.close()

        # Close MongoDB client
        mongo_client.close()
        logging.info("MongoDB client closed")

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)