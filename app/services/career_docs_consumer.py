import json
from loguru import logger
from app.core.exceptions import DatabaseOperationError, InvalidRequestError
from app.core.mongo import get_mongo_client
from app.core.redis_client import redis_client
from app.services.base_consumer import BaseConsumer
from app.core.config import settings
from app.services.career_docs_publisher import career_docs_publisher

mongo_client = get_mongo_client()

class CareerDocsConsumer(BaseConsumer):

    def __init__(self):
        super(self).__init__()
        self.jobs_redis_client = redis_client
        self.career_docs_publisher = career_docs_publisher

    def _ensure_dict(data):
        while isinstance(data, str):
            try:
                data = json.loads(data)
            except (ValueError, TypeError, json.JSONDecodeError):
                break

        if isinstance(data, dict):
            return {k: CareerDocsConsumer._ensure_dict(v) for k, v in data.items()}

        if isinstance(data, list):
            return [CareerDocsConsumer._ensure_dict(item) for item in data]

        return data
    
    def get_queue_name(self) -> str:
        return settings.career_docs_response_queue
    

    def _retrieve_content_from_redis(self, message: dict) -> dict:
        """
        Retrieves immutable data from redis to reconstruct application content (for each application)

        Args:
            message (dict): The message sent by CareerDocs
        """
        
        content = {}
        for correlation_id, job_data in message.items():    # Loop through both keys (correlation_id) and values ({cv, cover_letter, responses})
            if correlation_id != "user_id":
                # Get title, description, portal from correlation_mapping
                original_data_json = self.jobs_redis_client.get(correlation_id)
                if original_data_json:
                    # Deserialize the JSON string back into a dictionary
                    original_data = CareerDocsConsumer._ensure_dict(original_data_json)
                    job_data = CareerDocsConsumer._ensure_dict(job_data)

                    # Update the value (job_data) with the job_id, title, description, portal of that job
                    job_data.update(original_data)

                    # TODO: Maybe in future avoid deletion here & keep this for a bit longer to cache (due to non batch processing)
                    success = self.jobs_redis_client.delete(correlation_id)
                    if not success:
                        logger.warning(f"Failed to delete correlation ID '{correlation_id}' from mapping")
                else:
                    logger.warning(f"Correlation ID '{correlation_id}' not found in Redis mapping")
                    raise InvalidRequestError(f"Invalid correlation ID '{correlation_id}' in response from career_docs")
                
                # Add the correlation_id and its updated job_data to the content
                content[correlation_id] = job_data

        return content


    async def _update_career_docs_responses(self, user_id: int, content: dict):
        """
        Writes the produced content into the career_docs_responses collection

        Args:
            user_id (str): User ID.
            content (dict): The content produced by carrer docs + part recovered from redis

        Raises:
            DatabaseOperationError: If mongo fails
        """

        try:
            db = mongo_client.get_database("resumes")
            collection = db.get_collection("career_docs_responses")
            
            filter_query = {"user_id": user_id}
            update_query = {"$setOnInsert": {"user_id": user_id}}

            content_mod = {
                key: {
                    **CareerDocsConsumer._ensure_dict(value),
                    "resume_optimized": CareerDocsConsumer._ensure_dict(value.get("resume_optimized", {})),
                    "cover_letter": CareerDocsConsumer._ensure_dict(value.get("cover_letter", {})),
                    "sent": False
                }
                for key, value in content.items()
            }

            # Merge each entry from the incoming content into the existing content
            for key, value in content_mod.items():
                if isinstance(value, str):
                    # If a nested field is still a string, ensure it's a dictionary
                    content_mod[key] = CareerDocsConsumer._ensure_dict(value)
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


    async def process_message(self, message: dict):
        """
        Consumes messages from the career_docs_response_queue.

        """

        # Extract user_id field
        user_id = message.get("user_id")

        if not user_id:
            logger.warning("No user_id provided in the response data")
            raise InvalidRequestError("Missing user_id in response from career_docs")

        content = self._retrieve_content_from_redis(message)

        await self._update_career_docs_responses(user_id, content)

        await self.career_docs_publisher.refill_queue()
        

career_docs_consumer = CareerDocsConsumer()