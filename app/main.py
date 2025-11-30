from app.log.logging import logger
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from app.routers.applier_editor import router as applier_editor_router
from app.core.rabbitmq_client import rabbit_client
from app.services.career_docs_consumer import career_docs_consumer
from app.services.application_manager_consumer import application_manager_consumer
from app.services.timed_queue_refiller import timed_queue_refiller

# Initialize FastAPI app
app = FastAPI()

# Initialize shared resources outside lifespan to avoid re-initialization
mongo_client = AsyncIOMotorClient(settings.mongodb)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for app resources."""
    logger.info("Starting application lifespan...", event_type="lifespan.start")
    
    try:
        await rabbit_client.connect()
        logger.info("Connected to RabbitMQ", event_type="lifespan.rabbitmq.connect")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", event_type="lifespan.rabbitmq.connect.error")
        raise

    # Start background tasks
    try:
        career_docs_response_task = asyncio.create_task(career_docs_consumer.start())
        application_manager_notification_task = asyncio.create_task(application_manager_consumer.start())
        timed_queue_refiller_task = asyncio.create_task(timed_queue_refiller.start())
        logger.info("Career docs response consumer task started", event_type="lifespan.career_docs_response.start")
        logger.info("Application manager consumer task started", event_type="lifespan.application_manager.start")
        logger.info("Timed queue refiller task started", event_type="lifespan.timed_queue_refiller.start")
    except Exception as e:
        logger.exception(
            f"Failed to start background tasks: {e}",
            event_type="lifespan.background_tasks.start.error",
            error_type=type(e).__name__,
            error_details=str(e))
        raise

    try:
        yield
    finally:
        # Stop background tasks
        application_manager_notification_task.cancel()
        career_docs_response_task.cancel()
        timed_queue_refiller_task.cancel()
        try:
            await application_manager_notification_task
            await career_docs_response_task
            await timed_queue_refiller_task
        except asyncio.CancelledError:
            logger.info("Background tasks cancelled")
        except Exception as e:
            logger.exception(
                f"Error while stopping background tasks: {e}",
                event_type="lifespan.background_tasks.stop.error",
                error_type=type(e).__name__,
                error_details=str(e))

        # Close RabbitMQ client
        try:
            await rabbit_client.close()
            logger.info("RabbitMQ client closed", event_type="lifespan.rabbitmq.close")
        except Exception as e:
            logger.exception(
                f"Error while stopping background tasks: {e}",
                event_type="lifespan.background_tasks.stop.error",
                error_type=type(e).__name__,
                error_details=str(e))

        # Close MongoDB client
        try:
            mongo_client.close()
            logger.info("MongoDB client closed", event_type="lifespan.mongodb.close")
        except Exception as e:
            logger.exception(
                f"Error while closing MongoDB client: {e}",
                event_type="lifespan.mongodb.close.error",
                error_type=type(e).__name__,
                error_details=str(e))

    logger.info("Application lifespan ended", event_type="lifespan.end")


# Assign the lifespan function to the app
app.router.lifespan_context = lifespan

# include the router
app.include_router(applier_editor_router)
from app.routers.healthcheck_router import router as healthcheck_router
app.include_router(healthcheck_router)