import json
from loguru import logger
from app.core.exceptions import DatabaseOperationError, InvalidRequestError
from app.core.mongo import get_mongo_client
from app.core.redis_client import redis_client
from app.schemas.app_jobs import CareerDocsData, CareerDocsResponse
from app.services.base_consumer import BaseConsumer
from app.core.config import settings
from app.services.career_docs_publisher import career_docs_publisher
from app.services.database_cleaner import database_cleaner

mongo_client = get_mongo_client()

class CareerDocsConsumer(BaseConsumer):

    def __init__(self):
        super().__init__()
        self.jobs_redis_client = redis_client
        self.career_docs_publisher = career_docs_publisher
        self.database_cleaner = database_cleaner

    
    def get_queue_name(self) -> str:
        return settings.career_docs_response_queue
    

    def _retrieve_content(self, message: dict) -> dict:
        """
        Retrieves immutable data from redis to reconstruct application content (for each application)

        Args:
            message (dict): The message sent by CareerDocs
        """

        content = {}

        job_applications =  CareerDocsResponse(**message)

        correlation_id: str
        job_application: CareerDocsData

        # Loop through both correlation_id (needed for redis) and values ({cv, cover_letter})
        for correlation_id, job_application in job_applications.applications.items(): 
            original_data_json: str | None = self.jobs_redis_client.get(correlation_id) 

            if original_data_json is None: 
                logger.warning(f"Correlation ID '{correlation_id}' not found in Redis mapping")
                raise InvalidRequestError(f"Invalid correlation ID '{correlation_id}' in response from career_docs")

            original_data: dict = json.loads(original_data_json)

            # recover json data from Career Docs message
            complete_job_application = {
                **original_data,
                "resume_optimized": job_application.resume_optimized,
                "cover_letter": job_application.cover_letter,
                "sent": False     # signals this application has not been sent to the applier yet
            }

            content[correlation_id] = complete_job_application

            # TODO: Lorenzo wants to move this after the applier response: I don't care
            success = self.jobs_redis_client.delete(correlation_id)
            if not success:
                logger.warning(f"Failed to delete correlation ID '{correlation_id}' from mapping")

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

            # Merge each entry from the incoming content into the existing content
            for key, value in content.items():
                update_query.setdefault("$set", {})[f"content.{key}"] = value

            # Use upsert to insert a new document if it doesn't exist, or update the existing one
            result = await collection.update_one(filter_query, update_query, upsert=True)

            if result.upserted_id:
                logger.info(f"Successfully inserted new document for user_id: {user_id}")
            elif result.modified_count > 0:
                logger.info(f"Successfully updated existing document for user_id: {user_id}")
            else:
                logger.error(f"Failed to insert or update document for user_id: {user_id}")
                raise DatabaseOperationError("Failed to insert or update document in MongoDB")
        except Exception as e:
            logger.error(f"Error occurred while storing career_docs response in MongoDB: {str(e)}")
            raise DatabaseOperationError("Error while storing career_docs response in MongoDB")
        

    async def _remove_processed_entry(self, mongo_id: str):
        logger.info(f"removing processed entity with id: {mongo_id}")
        await self.database_cleaner.clean_from_db(mongo_id)


    async def process_message(self, message: dict):
        """
        Consumes messages from the career_docs_response_queue.

        """

        # Extract user_id field
        user_id = message.get("user_id")

        if not user_id:
            logger.warning("No user_id provided in the response data")
            raise InvalidRequestError("Missing user_id in response from career_docs")

        content = self._retrieve_content(message)

        await self._update_career_docs_responses(user_id, content)

        mongo_id = message.get("mongo_id")

        if not mongo_id is None:
            await self._remove_processed_entry(mongo_id)

        await self.career_docs_publisher.refill_queue()
        

career_docs_consumer = CareerDocsConsumer()