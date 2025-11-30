import json
from bson import ObjectId
from app.log.logging import logger
import uuid
from app.core.config import settings
from app.core.exceptions import JobApplicationError
from app.core.redis_client import redis_client
from app.schemas.app_jobs import JobsToApplyInfo
from app.services.database_consumer import database_consumer
from app.services.base_publisher import BasePublisher
from app.core.mongo import get_mongo_client

mongo_client = get_mongo_client()
class CareerDocsPublisher(BasePublisher):

    MAX_QUEUE_SIZE: int = 100

    def __init__(self):
        super().__init__()
        self.jobs_redis_client = redis_client
        self.pdf_resumes_collection = mongo_client.get_database("resumes").get_collection("pdf_resumes")

    def get_queue_name(self):
        return settings.career_docs_queue
    
    async def _generate_unique_uuid(self):
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
                if await self.jobs_redis_client.get(unique_uuid) is None:
                    return unique_uuid
            except Exception as e:
                logger.exception(
                    "Failed to check for existing UUID",
                    event_type="generate_unique_uuid",
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
                raise JobApplicationError("Failed to generate a unique UUID")
            
    
    async def publish_applications(self, jobsToApplyInfo: JobsToApplyInfo):
    
        """
        Publishes a message to the career_docs queue with the user_id and jobs list.

        Args:
            user_id (str): User ID.
            jobs (list): List of jobs. -> it is modified by giving each job a correlation_id

        Raises:
            JobApplicationError: If notification fails.
        """

        if not await self.jobs_redis_client.is_connected():
            logger.error("One or more Redis clients are not connected", event_type="publish_applications")
            raise JobApplicationError("Redis client is not connected")

        correlation_ids = []
        style_for_all = jobsToApplyInfo.style

        for job in jobsToApplyInfo.jobs:
            correlation_id = await self._generate_unique_uuid()
            job["correlation_id"] = correlation_id
            job["style"] = style_for_all
            correlation_ids.append(correlation_id)

            try:
                redis_value = {key: value for key, value in job.items() if value is not None}
                success = await self.jobs_redis_client.set(correlation_id, json.dumps(redis_value))

                if not success:
                    logger.error(f"Failed to store correlation ID {correlation_id} in mapping", event_type="publish_applications")
                    raise JobApplicationError("Failed to store correlation ID in mapping")

            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize data for correlation ID {correlation_id}", event_type="publish_applications")
                raise JobApplicationError("Failed to serialize data for correlation ID")
            
        cv_id = jobsToApplyInfo.cv_id
        if cv_id is not None:
            try:
                update_result = await self.pdf_resumes_collection.update_one(
                    {"_id": ObjectId(cv_id)},
                    {"$push": {"app_ids": {"$each": correlation_ids}}}
                )
                if update_result.modified_count == 0:
                    logger.info(f"No document found with _id {cv_id} in pdf_resumes or nothing was updated.", event_type="publish_applications")
            except Exception as e:
                logger.error(f"Failed to update 'app_ids' for cv_id {cv_id}", event_type="publish_applications")
                raise JobApplicationError("Failed to update 'app_ids' in pdf_resumes collection")

        message = {"user_id": jobsToApplyInfo.user_id, "jobs": jobsToApplyInfo.jobs, "mongo_id": str(jobsToApplyInfo.mongo_id)}
        try:
            await self.publish(message, True)

            logger.info(f"Notification sent to career_docs for user {jobsToApplyInfo.user_id}", event_type="publish_applications")
        except Exception as e:
            logger.error(f"Failed to send notification to career_docs for user {jobsToApplyInfo.user_id}", event_type="publish_applications")
            raise JobApplicationError(f"Failed to notify career_docs for user {jobsToApplyInfo.user_id}")
        
    async def refill_queue(self):
        """
        Continuously checks the queue size and pushes new application batches onto it until it is full:
        it is kind of slow as it keeps querying the queue size and extracting one batch at a time from
        the db, however it should be still faster than CareerDocs and ensures consistency in the workload
        
        """
        queue_size = await self.get_queue_size()

        while queue_size < CareerDocsPublisher.MAX_QUEUE_SIZE:
            jobsToApplyInfo = await database_consumer.retrieve_one_batch_from_db()
            if jobsToApplyInfo is None:
                break
            await self.publish_applications(jobsToApplyInfo)
            queue_size = await self.get_queue_size()
        
career_docs_publisher = CareerDocsPublisher()