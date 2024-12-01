import asyncio
import logging
import json
from fastapi import HTTPException
from aio_pika import IncomingMessage
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.rabbitmq_client import AsyncRabbitMQClient
from app.core.appliers_config import APPLIERS, process_default
from app.core.exceptions import ResumeNotFoundError, JobApplicationError, DatabaseOperationError

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def notify_career_docs(user_id: str, resume: dict, jobs: list, rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Publishes a message to the career_docs queue with the user's resume and jobs list.

    Args:
        user_id (str): User ID.
        resume (dict): User's resume data.
        jobs (list): List of jobs.
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        settings: Application settings.

    Raises:
        JobApplicationError: If notification fails.
    """
    message = {"user_id": user_id, "resume": resume, "jobs": jobs}
    try:
        await rabbitmq_client.publish_message(queue_name=settings.career_docs_queue, message=message)
        logger.info(f"Notification sent to career_docs for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to career_docs for user {user_id}: {str(e)}")
        raise JobApplicationError(f"Failed to notify career_docs for user {user_id}")

async def consume_jobs(mongo_client: AsyncIOMotorClient, rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Consumes job data from MongoDB and processes job applications.

    Args:
        mongo_client (AsyncIOMotorClient): MongoDB client instance.
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        settings: Application settings.

    Raises:
        DatabaseOperationError: If there's an error with MongoDB.
    """
    while True:
        try:
            logger.info("Connecting to MongoDB...")
            db = mongo_client.get_database("resumes")
            collection = db.get_collection("jobs_to_apply_per_user")

            logger.info("Fetching job lists from MongoDB...")
            cursor = collection.find({}, {"_id": 0})
            job_lists = await cursor.to_list(length=None)

            for doc in job_lists:
                user_id = doc.get("user_id")
                resume = doc.get("resume", {})
                jobs_field = doc.get("jobs")

                if not user_id or not resume or not jobs_field:
                    logger.warning("Invalid document structure, skipping.")
                    continue

                try:
                    jobs_field = json.loads(jobs_field) if isinstance(jobs_field, str) else jobs_field
                except json.JSONDecodeError:
                    logger.warning("Failed to parse 'jobs' JSON, skipping document.")
                    continue

                jobs = jobs_field.get("jobs", [])
                if not isinstance(jobs, list):
                    logger.warning("'jobs' field is not a list, skipping document.")
                    continue

                await notify_career_docs(user_id, resume, jobs, rabbitmq_client, settings)

                #TOENABLE then: Remove the processed document from MongoDB
                '''result = await collection.delete_one({"user_id": user_id})
                if result.deleted_count > 0:
                    print(f"Successfully deleted document for user_id: {user_id}")
                else:
                    print(f"Failed to delete document for user_id: {user_id}")'''

            # TODO: wait for frontend for actual rate-limiting logic
            logger.info("All jobs have been processed. Sleeping before the next iteration.")
            await asyncio.sleep(999)
            
        except Exception as e:
            logger.error(f"Error occurred in the processing loop: {str(e)}")
            raise DatabaseOperationError("Error while processing jobs from MongoDB")

async def consume_career_docs_responses(rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Consumes messages from the career_docs_response_queue.

    Args:
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        settings: Application settings.
    """
    async def on_message(message: IncomingMessage):
        body = message.body.decode()
        data = json.loads(body)
        logger.info(f"Received response from career_docs: {data}")

        # Process the received data and send to other appliers
        # TODO: Uncomment when other appliers are implemented.
        # await send_data_to_microservices(data, rabbitmq_client)

        # Acknowledge the message
        await message.ack()

    await rabbitmq_client.consume_messages(
        queue_name=settings.career_docs_response_queue,
        callback=on_message,
        auto_ack=False  # Manually acknowledge after processing
    )

async def send_data_to_microservices(data, rabbitmq_client: AsyncRabbitMQClient):
    """
    Processes the received data and sends it to different microservices via their queues.

    Args:
        data (dict): Data to send.
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
    """
    for microservice_name, microservice_info in APPLIERS.items():
        queue_name = microservice_info['queue_name']
        process_function = microservice_info.get('process_function', process_default)

        microservice_data = process_function(data)
        await rabbitmq_client.publish_message(queue_name=queue_name, message=microservice_data)
        logger.info(f"Sent data to microservice '{microservice_name}' via queue '{queue_name}'")