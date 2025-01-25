import json
from loguru import logger
from app.core.exceptions import DatabaseOperationError, InvalidRequestError
from app.core.mongo import get_mongo_client
from app.core.redis_client import redis_client
from app.schemas.app_jobs import CareerDocsData, CareerDocsResponse
from app.services.base_consumer import BaseConsumer
from app.core.config import settings
from app.services.career_docs_publisher import career_docs_publisher
from app.services.database_writer import database_writer

mongo_client = get_mongo_client()

class CareerDocsConsumer(BaseConsumer):

    def __init__(self):
        super().__init__()
        self.jobs_redis_client = redis_client
        self.career_docs_publisher = career_docs_publisher
        self.database_writer = database_writer

    
    def get_queue_name(self) -> str:
        return settings.career_docs_response_queue
    

    def _retrieve_content(self, applications: dict[str, CareerDocsData]) -> dict:
        """
        Retrieves immutable data from redis to reconstruct application content (for each application)

        Args:
            message (dict): The message sent by CareerDocs
        """

        content = {}
        correlation_id: str
        job_application: CareerDocsData

        # Loop through both correlation_id (needed for redis) and values ({cv, cover_letter})
        for correlation_id, job_application in applications.items(): 
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

            # We don't delete here on redis, we delete on app failure or success to avoid re-assigning UUID

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
        await self.database_writer.clean_from_db(mongo_id)

    async def _restore_sent_status(self, mongo_id: str):
        logger.warning(f"CareerDocs failed, restoring sent status for entity {mongo_id}")
        await self.database_writer.restore_sent(mongo_id)


    async def process_message(self, message: dict):
        """
        Consumes messages from the career_docs_response_queue.

        """

        job_applications = CareerDocsResponse(**message)

        if job_applications.success:

            content = self._retrieve_content(job_applications.applications)

            await self._update_career_docs_responses(job_applications.user_id, content)

            await self._remove_processed_entry(job_applications.mongo_id)

        else:

            await self._restore_sent_status(job_applications.mongo_id)

        await self.career_docs_publisher.refill_queue()
        

career_docs_consumer = CareerDocsConsumer()