import logging
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from app.routers.applier_editor import router as applier_editor_router
from app.core.rabbitmq_client import rabbit_client
from app.services.career_docs_consumer import career_docs_consumer
from app.services.application_manager_consumer import application_manager_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize shared resources outside lifespan to avoid re-initialization
mongo_client = AsyncIOMotorClient(settings.mongodb)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for app resources."""
    logger.info("Starting application lifespan...")
    
    try:
        await rabbit_client.connect()
        logger.info("Connected to RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise

    # Start background tasks
    try:
        #job_consumer_task = asyncio.create_task(consume_jobs(mongo_client, rabbit_client, settings))
        career_docs_response_task = asyncio.create_task(career_docs_consumer.start())
        application_manager_notification_task = asyncio.create_task(application_manager_consumer.start())
        logger.info("Job consumer task started")
        logger.info("Career docs response consumer task started")
    except Exception as e:
        logger.error(f"Failed to start background tasks: {e}")
        raise

    try:
        yield
    finally:
        # Stop background tasks
        application_manager_notification_task.cancel()
        career_docs_response_task.cancel()
        try:
            await application_manager_notification_task
            await career_docs_response_task
        except asyncio.CancelledError:
            logger.info("Background tasks cancelled")
        except Exception as e:
            logger.error(f"Error while stopping background tasks: {e}")

        # Close RabbitMQ client
        try:
            await rabbit_client.close()
            logger.info("RabbitMQ client closed")
        except Exception as e:
            logger.error(f"Error while closing RabbitMQ client: {e}")

        # Close MongoDB client
        try:
            mongo_client.close()
            logger.info("MongoDB client closed")
        except Exception as e:
            logger.error(f"Error while closing MongoDB client: {e}")

    logger.info("Application lifespan ended")


# Assign the lifespan function to the app
app.router.lifespan_context = lifespan

# include the router
app.include_router(applier_editor_router)