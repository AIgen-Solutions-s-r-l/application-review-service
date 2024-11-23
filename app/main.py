# /app/main.py

import logging
import asyncio
import json
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI

from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient
from app.services.applier import consume_jobs_interleaved, handle_career_docs_response

from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load settings
settings = Settings()

# Create an instance of the RabbitMQ client without 'queue'
rabbit_client = RabbitMQClient(rabbitmq_url=settings.rabbitmq_url)

# Define the callback for career_docs queue
def rabbitmq_callback(ch, method, properties, body):
    """
    Callback to process messages from the career_docs_queue.
    """
    try:
        message = body.decode()
        print(f"Received message from career_docs_queue: {message}")
    except Exception as e:
        logging.error(f"Error in rabbitmq_callback: {e}")

# Define the callback for career_docs_response queue
def career_docs_response_callback(ch, method, properties, body):
    """
    Callback to process responses from the career_docs_response_queue.
    """
    try:
        message = json.loads(body.decode())
        asyncio.run(handle_career_docs_response(message))
    except Exception as e:
        logging.error(f"Error in career_docs_response_callback: {e}")

# Create an instance of the MongoDB client
mongo_client = AsyncIOMotorClient(settings.mongodb)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for starting and stopping resources.
    """
    # Start the RabbitMQ client in separate threads for different queues
    rabbit_thread = Thread(
        target=lambda: rabbit_client.consume_messages(
            queue=settings.career_docs_queue,
            callback=rabbitmq_callback
        ),
        daemon=True
    )
    response_thread = Thread(
        target=lambda: rabbit_client.consume_messages(
            queue=settings.career_docs_response_queue,
            callback=career_docs_response_callback
        ),
        daemon=True
    )

    rabbit_thread.start()
    response_thread.start()
    logging.info("RabbitMQ clients started for both queues")

    # Start the job consumer as a background task
    loop = asyncio.get_event_loop()
    job_consumer_task = asyncio.create_task(consume_jobs_interleaved(mongo_client))
    logging.info("Job consumer started")

    try:
        yield
    finally:
        # Stop the RabbitMQ clients and other resources
        rabbit_client.close()
        rabbit_thread.join()
        response_thread.join()
        logging.info("RabbitMQ clients stopped")

        # Cancel the job consumer task
        job_consumer_task.cancel()
        try:
            await job_consumer_task
        except asyncio.CancelledError:
            logging.info("Job consumer task cancelled")

        # Close the MongoDB client
        mongo_client.close()
        logging.info("MongoDB client closed")

# Initialize the FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)