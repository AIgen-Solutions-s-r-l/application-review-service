import asyncio
import logging
import json
import uuid
from fastapi import HTTPException
from aio_pika import IncomingMessage
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.rabbitmq_client import AsyncRabbitMQClient
from app.core.appliers_config import APPLIERS, process_default
from app.core.exceptions import ResumeNotFoundError, JobApplicationError, DatabaseOperationError, InvalidRequestError
from app.core.redis_client import RedisClient

# Initialize Redis clients for different databases
redis_client_jobs = RedisClient(host='localhost', port=6379, db=0)  # For jobs-related data
redis_client_resumes = RedisClient(host='localhost', port=6379, db=1)  # For resumes
redis_client_jobs.connect()
redis_client_resumes.connect()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def generate_unique_uuid():
    """
    Generates a unique UUID that is not already present in the provided mapping.

    Args:
        existing_mapping (dict): The mapping to check for existing UUIDs.

    Returns:
        str: A unique UUID.
    """
    while True:
        unique_uuid = str(uuid.uuid4())
        try:
            if redis_client_jobs.get(unique_uuid) is None:
                return unique_uuid
        except Exception as e:
            logger.error(f"Failed to check for existing UUID: {str(e)}")
            raise JobApplicationError("Failed to generate a unique UUID")

async def notify_career_docs(user_id: str, resume: dict, jobs: list, is_batch: bool, rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Publishes a message to the career_docs queue with the user's resume and jobs list.

    Args:
        user_id (str): User ID.
        resume (dict): User's resume data.
        jobs (list): List of jobs.
        is_batch (bool): Whether the job applications will be processed in batch.
        correlation_id (str): Correlation ID for the message (optimization).
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        settings: Application settings.

    Raises:
        JobApplicationError: If notification fails.
    """

    if not redis_client_jobs.is_connected() or not redis_client_resumes.is_connected():
        logger.error("One or more Redis clients are not connected")
        raise JobApplicationError("Redis client is not connected")

    for job in jobs:
        correlation_id = generate_unique_uuid()
        # add correlation_id to the job data
        job["correlation_id"] = correlation_id

        try:
            # Serialize the dictionary to a JSON string and store in Redis
            redis_value = json.dumps({"job_id": job.get("job_id"), "title": job.get("title"), "description": job.get("description"), "portal": job.get("portal")})
            # Store the correlation ID in Redis (DB 0)
            success = redis_client_jobs.set(correlation_id, redis_value)
            if not success:
                logger.error(f"Failed to store correlation ID '{correlation_id}' in mapping")
                raise JobApplicationError("Failed to store correlation ID in mapping")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data for correlation ID '{correlation_id}': {str(e)}")
            raise JobApplicationError("Failed to serialize data for correlation ID")

    # Store resume in Redis (DB 1)
    redis_client_resumes.set(f"resume:{user_id}", json.dumps(resume))
    logger.info(f"Stored resume for user {user_id} in Redis (DB 1).")

    message = {"user_id": user_id, "is_batch": is_batch, "resume": resume, "jobs": jobs}
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
                is_batch = doc.get("is_batch", False)

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

                await notify_career_docs(user_id, resume, jobs, rabbitmq_client, is_batch, settings)

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

        # Loop through both keys (correlation_id) and values ({cv, cover_letter, responses})
        for correlation_id, job_data in data.items():
            # Get title, description, portal from correlation_mapping
            original_data_json = redis_client_jobs.get(correlation_id)
            if original_data_json:
                # Deserialize the JSON string back into a dictionary
                original_data = json.loads(original_data_json)
                # Update the value (job_data) with the job_id, title, description, portal of that job
                job_data.update(original_data)

                success = redis_client_jobs.delete(correlation_id)
                if not success:
                    logger.warning(f"Failed to delete correlation ID '{correlation_id}' from mapping")

            elif correlation_id != "user_id":
                logger.warning(f"Correlation ID '{correlation_id}' not found in mapping")
                raise InvalidRequestError("Invalid correlation ID in response from career_docs")
        
        # Retrieve resume from Redis (DB 1)
        user_id = data.get("user_id")
        if user_id:
            redis_resume_key = f"resume:{user_id}"
            redis_resume_json = redis_client_resumes.get(redis_resume_key)
            if redis_resume_json:
                resume = json.loads(redis_resume_json)
                data["resume"] = resume  # Add resume to the response data

                # Delete the resume from Redis (DB 1) after processing
                success = redis_client_resumes.delete(redis_resume_key)
                if not success:
                    logger.warning(f"Failed to delete resume for user {user_id} from Redis (DB 1)")
            else:
                logger.warning(f"Resume for user {user_id} not found in Redis (DB 1)")
                raise ResumeNotFoundError(f"Resume for user {user_id} not found in Redis")
        else:
            logger.warning("No user_id provided in the response data")
            raise InvalidRequestError("Missing user_id in response from career_docs")

        # Process the received data and send to other appliers if  it's a batch
        is_batch = data.pop("is_batch", False)
        if is_batch:
            await send_data_to_microservices(data, rabbitmq_client)

            # Acknowledge the message
            await message.ack()

            await rabbitmq_client.consume_messages(
                queue_name=settings.career_docs_response_queue,
                callback=on_message,
                auto_ack=False  # Manually acknowledge after processing
            )
        else: # if not a batch, store the career-docs response in Mongo
            try:
                # Connect to MongoDB
                mongo_client = AsyncIOMotorClient(settings.mongo_url)
                db = mongo_client.get_database("resumes")
                collection = db.get_collection("career_docs_responses")

                # Insert the response data into MongoDB
                result = await collection.insert_one(data)
                if result.acknowledged:
                    logger.info("Successfully stored career_docs response in MongoDB")
                else:
                    logger.error("Failed to store career_docs response in MongoDB")
                    raise DatabaseOperationError("Failed to store career_docs response in MongoDB")
            except Exception as e:
                logger.error(f"Error occurred while storing career_docs response in MongoDB: {str(e)}")
                raise DatabaseOperationError("Error while storing career_docs response in MongoDB")

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