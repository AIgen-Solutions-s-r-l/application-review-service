import json
from loguru import logger
import uuid
from app.core.config import settings
from app.core.exceptions import JobApplicationError
from app.core.redis_client import RedisClient
from app.services.base_publisher import BasePublisher

class CareerDocsPublisher(BasePublisher):

    def __init__(self, redis_client_jobs: RedisClient):
        super(self).__init__()
        self.redis_client_jobs = redis_client_jobs

    def get_queue_name(self):
        return settings.career_docs_queue
    

    def _generate_unique_uuid(self):
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
                if self.redis_client_jobs.get(unique_uuid) is None:
                    return unique_uuid
            except Exception as e:
                logger.error(f"Failed to check for existing UUID: {str(e)}")
                raise JobApplicationError("Failed to generate a unique UUID")
            
    
    async def publish_applications(self, user_id: str, jobs: list):
    
        """
        Publishes a message to the career_docs queue with the user_id and jobs list.

        Args:
            user_id (str): User ID.
            jobs (list): List of jobs. -> it is modified by giving each job a correlation_id

        Raises:
            JobApplicationError: If notification fails.
        """

        if not self.redis_client_jobs.is_connected():
            logger.error("One or more Redis clients are not connected")
            raise JobApplicationError("Redis client is not connected")

        for job in jobs:
            correlation_id = self._generate_unique_uuid()
            
            job["correlation_id"] = correlation_id      # add correlation_id to the job data

            try:
                redis_value = {
                    "job_id": job.get("job_id"),
                    "title": job.get("title"),
                    "description": job.get("description"),
                    "portal": job.get("portal"),
                }
                success = self.redis_client_jobs.set(correlation_id, json.dumps(redis_value))

                if not success:
                    logger.error(f"Failed to store correlation ID '{correlation_id}' in mapping")
                    raise JobApplicationError("Failed to store correlation ID in mapping")
                
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize data for correlation ID '{correlation_id}': {str(e)}")
                raise JobApplicationError("Failed to serialize data for correlation ID")

        message = {"user_id": user_id, "jobs": jobs}
        try:
            
            await self.publish(message)

            logger.info(f"Notification sent to career_docs for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to career_docs for user {user_id}: {str(e)}")
            raise JobApplicationError(f"Failed to notify career_docs for user {user_id}")