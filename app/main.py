# app/main.py

import logging
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.core.config import Settings
from app.core.rabbitmq_client import AsyncRabbitMQClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.applier import consume_jobs, consume_career_docs_responses

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI()

# Initialize shared resources outside lifespan to avoid re-initialization
mongo_client = AsyncIOMotorClient(settings.mongodb)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for app resources."""
    # Initialize RabbitMQ client
    rabbit_client = AsyncRabbitMQClient(rabbitmq_url=settings.rabbitmq_url)
    await rabbit_client.connect()

    # Start background tasks
    job_consumer_task = asyncio.create_task(consume_jobs(mongo_client, rabbit_client, settings))
    career_docs_response_task = asyncio.create_task(consume_career_docs_responses(rabbit_client, settings))
    logging.info("Job consumer task started")
    logging.info("Career docs response consumer task started")

    try:
        yield
    finally:
        # Stop background tasks
        job_consumer_task.cancel()
        career_docs_response_task.cancel()
        try:
            await job_consumer_task
            await career_docs_response_task
        except asyncio.CancelledError:
            logging.info("Background tasks cancelled")

        # Close RabbitMQ client
        await rabbit_client.close()

        # Close MongoDB client
        mongo_client.close()
        logging.info("MongoDB client closed")


# Assign the lifespan function to the app
app.router.lifespan_context = lifespan