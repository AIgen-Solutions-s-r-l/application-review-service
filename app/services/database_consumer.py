from loguru import logger
import json
from app.core.mongo import get_mongo_client

mongo_client = get_mongo_client()

class DatabaseConsumer:

    def _ensure_dict(data):
        while isinstance(data, str):
            try:
                data = json.loads(data)
            except (ValueError, TypeError, json.JSONDecodeError):
                break

        if isinstance(data, dict):
            return {k: DatabaseConsumer._ensure_dict(v) for k, v in data.items()}

        if isinstance(data, list):
            return [DatabaseConsumer._ensure_dict(item) for item in data]

        return data

    async def retrieve_one_batch_from_db(self) -> tuple[int, list] | None:
        """
        Consumes job data from MongoDB to be sent into CareerDocs queue

        Raises:
            DatabaseOperationError: If there's an error with MongoDB.
        """
        logger.info("Connecting to MongoDB for fetching...")
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        while True:

            user_applications = await collection.find_one({"sent": False})

            if user_applications is None:
                logger.info(f"All jobs have been processed.")
                return None

            await collection.update_one(
                {"_id": user_applications.get("_id")},
                {"$set": {"sent": True}}
            )

            user_id = user_applications.get("user_id")
            jobs_field = user_applications.get("jobs")

            if not user_id or not jobs_field:
                logger.warning("Invalid document structure, skipping.")
                continue

            try:
                if isinstance(jobs_field, list):
                    # Parse each JSON string in the list
                    jobs_field = [DatabaseConsumer._ensure_dict(job) for job in jobs_field]
                else:
                    logger.warning("'jobs' field is not a list, skipping document.")
                    continue
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse 'jobs' JSON: {e}, skipping document.")
                continue

            if not isinstance(jobs_field, list) or not all(isinstance(job, dict) for job in jobs_field):
                logger.warning("'jobs' field does not contain valid job dictionaries, skipping document.")
                continue

            return user_id, jobs_field


database_consumer = DatabaseConsumer()