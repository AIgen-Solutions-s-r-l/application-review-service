import logging
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI

from core.config import Settings
from core.rabbitmq_client import RabbitMQClient
from routers.example_router import router as example_router

logging.basicConfig(level=logging.DEBUG)

# Load settings
settings = Settings()


def message_callback(ch, method, properties, body):
    """
    Callback function to process each message from RabbitMQ.

    Parameters:
    - ch: Channel - The RabbitMQ channel
    - method: - RabbitMQ method frame
    - properties: - RabbitMQ properties
    - body: bytes - The message content
    """
    try:
        logging.info(f"Received message: {body.decode()}")
        # Custom message processing logic here
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        # Optionally, add message requeue logic here


# Global instance of RabbitMQClient
rabbit_client = RabbitMQClient(
    rabbitmq_url=settings.rabbitmq_url,
    queue="my_queue",
    callback=message_callback
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to manage the startup and shutdown events for FastAPI.
    Starts and stops the RabbitMQ client connection.
    """
    # Start the RabbitMQ client I/O loop in a separate thread
    rabbit_thread = Thread(target=rabbit_client.start)
    rabbit_thread.start()
    logging.info("RabbitMQ client started in background thread")

    yield  # Application will run while paused here

    # Stop the RabbitMQ client I/O loop and wait for thread to join
    rabbit_client.stop()
    rabbit_thread.join()
    logging.info("RabbitMQ client connection closed")


# Initialize FastAPI with the lifespan manager
app = FastAPI(lifespan=lifespan)


# Example FastAPI route for testing
@app.get("/")
async def root():
    """
    Basic root endpoint to test if the service is running.
    """
    return {"message": "coreService is up and running!"}


app.include_router(example_router)
