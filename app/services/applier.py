import asyncio
import logging
import json
import uuid
from aio_pika import IncomingMessage
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.rabbitmq_client import AsyncRabbitMQClient
from app.core.appliers_config import APPLIERS, process_default
from app.core.exceptions import JobApplicationError, DatabaseOperationError, InvalidRequestError
from app.core.redis_client import RedisClient

# Initialize Redis clients for different databases
redis_client_jobs = RedisClient(host='localhost', port=6379, db=0)  # For jobs-related data
redis_client_jobs.connect()

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

async def notify_career_docs(user_id: str, jobs: list, rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Publishes a message to the career_docs queue with the user_id and jobs list.

    Args:
        user_id (str): User ID.
        jobs (list): List of jobs.
        correlation_id (str): Correlation ID for the message (optimization).
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        settings: Application settings.

    Raises:
        JobApplicationError: If notification fails.
    """

    if not redis_client_jobs.is_connected():
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

    message = {"user_id": user_id, "jobs": jobs}
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
            # TODO: Implement priority of users here, maybe based on pricing plan (?)
            # TODO: Implement rate-limiting logic here
            # TODO: Decomment deletion of job to apply lists
            # TODO: Implement a recovery process (thanks to redis) in case of failures in career_docs
            await asyncio.sleep(10)
            logger.info("Connecting to MongoDB for fetching...")
            db = mongo_client.get_database("resumes")
            collection = db.get_collection("jobs_to_apply_per_user")

            logger.info("Fetching job lists from MongoDB...")
            cursor = collection.find({}, {"_id": 0})
            job_lists = await cursor.to_list(length=None)

            for doc in job_lists:
                user_id = doc.get("user_id")
                jobs_field = doc.get("jobs")

                if not user_id or not jobs_field:
                    logger.warning("Invalid document structure, skipping.")
                    continue

                try:
                    # Parse each JSON string in the list
                    if isinstance(jobs_field, list):
                        jobs_field = [json.loads(job) if isinstance(job, str) else job for job in jobs_field]
                    else:
                        logger.warning("'jobs' field is not a list, skipping document.")
                        continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse 'jobs' JSON: {e}, skipping document.")
                    continue

                if not isinstance(jobs_field, list) or not all(isinstance(job, dict) for job in jobs_field):
                    logger.warning("'jobs' field does not contain valid job dictionaries, skipping document.")
                    continue

                await notify_career_docs(user_id, jobs_field, rabbitmq_client, settings)

                # Clear the "jobs" field after successfully notifying career docs
                # TODO: see above! 
                '''
                    result = await collection.update_one(
                        {"user_id": user_id},
                        {"$set": {"jobs": []}}
                    )
                    if result.modified_count > 0:
                        logger.info(f"Cleared 'jobs' field for user_id {user_id}.")
                    else:
                        logger.warning(f"Failed to clear 'jobs' field for user_id {user_id}.")
                '''

            # TODO: wait for frontend for actual rate-limiting logic
            logger.info("All jobs have been processed. Sleeping before the next iteration.")
            await asyncio.sleep(999)
            
        except Exception as e:
            logger.error(f"Error occurred in the processing loop: {str(e)}")
            raise DatabaseOperationError("Error while processing jobs from MongoDB")

async def consume_career_docs_responses(mongo_client: AsyncIOMotorClient, rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Consumes messages from the career_docs_response_queue.

    Args:
        rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        settings: Application settings.
    """
    async def on_message(message: IncomingMessage):
        body = message.body.decode()
        data = json.loads(body)
        logger.info(f"Received response from career_docs 1: {data}")

        # Extract user_id field
        user_id = data.get("user_id")

        if not user_id:
            logger.warning("No user_id provided in the response data")
            raise InvalidRequestError("Missing user_id in response from career_docs")

        # Loop through both keys (correlation_id) and values ({cv, cover_letter, responses})
        content = {}
        for correlation_id, job_data in data.items():
            if correlation_id != "user_id":
                # Get title, description, portal from correlation_mapping
                original_data_json = redis_client_jobs.get(correlation_id)
                if original_data_json:
                    # Deserialize the JSON string back into a dictionary
                    original_data = json.loads(original_data_json)
                    # Update the value (job_data) with the job_id, title, description, portal of that job
                    job_data.update(original_data)

                    # TODO: Maybe in future avoid deletion here & keep this for a bit longer to cache (due to non batch processing)
                    success = redis_client_jobs.delete(correlation_id)
                    if not success:
                        logger.warning(f"Failed to delete correlation ID '{correlation_id}' from mapping")
                else:
                    logger.warning(f"Correlation ID '{correlation_id}' not found in Redis mapping")
                    raise InvalidRequestError(f"Invalid correlation ID '{correlation_id}' in response from career_docs")
                
                # Add the correlation_id and its updated job_data to the content
                content[correlation_id] = job_data

        try:
            db = mongo_client.get_database("resumes")
            collection = db.get_collection("career_docs_responses")
            
            filter_query = {"user_id": user_id}
            update_query = {"$setOnInsert": {"user_id": user_id}}

            # Add a "sent" field to each job data entry (to track if it has been sent to the applier)
            content_mod = {key: {**value, "sent": False} for key, value in content.items()}

            logger.info(f"Received response from career_docs 2: {content_mod}")

            # Merge each entry from the incoming content into the existing content
            for key, value in content_mod.items():
                update_query.setdefault("$set", {})[f"content.{key}"] = value

            # Use upsert to insert a new document if it doesn't exist, or update the existing one
            result = await collection.update_one(filter_query, update_query, upsert=True)

            if result.upserted_id:
                logger.info("Successfully inserted new document for user_id: %s", user_id)
            elif result.modified_count > 0:
                logger.info("Successfully updated existing document for user_id: %s", user_id)
            else:
                logger.error("Failed to insert or update document for user_id: %s", user_id)
                raise DatabaseOperationError("Failed to insert or update document in MongoDB")
        except Exception as e:
            logger.error(f"Error occurred while storing career_docs response in MongoDB: {str(e)}")
            raise DatabaseOperationError("Error while storing career_docs response in MongoDB")
        finally:
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
        logger.info("----------------------------------")
        logger.info(microservice_data)
        await rabbitmq_client.publish_message(queue_name=queue_name, message=microservice_data)
        logger.info(f"Sent data to microservice '{microservice_name}' via queue '{queue_name}'")
        logger.info("----------------------------------")