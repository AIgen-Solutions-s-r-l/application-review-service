import logging
from contextlib import asynccontextmanager
from threading import Thread
import asyncio
from fastapi import FastAPI
from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.applier import consume_jobs_interleaved

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load settings
settings = Settings()

# RabbitMQ client
rabbit_client = RabbitMQClient(rabbitmq_url=settings.rabbitmq_url)

def rabbitmq_callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        if not isinstance(message, dict):
            raise ValueError("Invalid message format: must be a dictionary")

        logging.info(f"Message received: {message}")
        user_id = message.get("user_id")
        resume = message.get("resume")
        jobs = message.get("jobs")

        if not user_id or not resume or not jobs:
            raise ValueError("Incomplete message: 'user_id', 'resume', and 'jobs' are required")

        # Process the message
        logging.info(f"Processing triple: user_id={user_id}, resume={resume}, jobs={jobs}")

        # Acknowledge only if auto_ack=False
        if not ch.is_closed:  # Ensure the channel is still open
            ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        # Optionally, reject the message
        if not ch.is_closed:
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

# MongoDB client
mongo_client = AsyncIOMotorClient(settings.mongodb)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for app resources."""
    # Start RabbitMQ consumer in a separate thread
    def start_rabbitmq_consumer():
        try:
            rabbit_client.consume_messages(queue=settings.career_docs_queue, callback=rabbitmq_callback)
        except Exception as e:
            logging.error(f"RabbitMQ consumer thread error: {e}")

    rabbit_thread = Thread(target=start_rabbitmq_consumer, daemon=True)
    rabbit_thread.start()
    logging.info("RabbitMQ consumer started")

    # Background task for other services
    job_consumer_task = asyncio.create_task(consume_jobs_interleaved(mongo_client))
    logging.info("Job consumer task started")

    try:
        yield
    finally:
        # Stop RabbitMQ client and background tasks
        rabbit_client.close()
        rabbit_thread.join()
        job_consumer_task.cancel()
        try:
            await job_consumer_task
        except asyncio.CancelledError:
            logging.info("Job consumer task cancelled")

        # Close MongoDB client
        mongo_client.close()
        logging.info("MongoDB client closed")

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)