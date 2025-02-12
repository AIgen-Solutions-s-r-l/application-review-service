from app.log.logging import logger
import json

from pydantic import ValidationError
from app.core.mongo import get_mongo_client
from app.schemas.app_jobs import JobsToApplyInfo

mongo_client = get_mongo_client()

class DatabaseConsumer:

    async def retrieve_one_batch_from_db(self) -> JobsToApplyInfo | None:
        """
        Consumes job data from MongoDB to be sent into CareerDocs queue

        Raises:
            DatabaseOperationError: If there's an error with MongoDB.
        """
        logger.info("Connecting to MongoDB for fetching...", event_type="database_consumer")
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        while True:

            user_applications = await collection.find_one({"sent": False})

            if user_applications is None:
                logger.info(f"All jobs have been processed.", event_type="database_consumer")
                return None

            await collection.update_one(
                {"_id": user_applications.get("_id")},
                {
                    "$set": {
                        "sent": True, 
                        "retries_left": user_applications.get("retries_left") - 1
                    }
                }
            )

            try:
                apply_info = JobsToApplyInfo(
                    user_id = user_applications.get("user_id"),
                    jobs = user_applications.get("jobs"),
                    cv_id = user_applications.get("cv_id"),
                    mongo_id = str(user_applications.get("_id")),
                    style= user_applications.get("style")
                )

                return apply_info

            except ValidationError:
                logger.error("Invalid document structure, skipping.", event_type="database_consumer")
                continue
            

database_consumer = DatabaseConsumer()