from datetime import datetime, timezone
from app.core.mongo import get_mongo_client
from app.log.logging import logger
from bson import ObjectId


class DatabaseWriter:

    def __init__(self):
        self.mongo_client = get_mongo_client()

    async def clean_from_db(self, id: str):
        db = self.mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        await collection.delete_one({"_id": ObjectId(id)})

    async def restore_sent(self, mongo_id: str):
        """
        Attempts to restore the sent status for retry. If no retries remain,
        marks the job as permanently failed.

        Args:
            mongo_id: The MongoDB document ID to restore.
        """
        db = self.mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        # Try to restore for retry (only if retries_left > 0)
        result = await collection.update_one(
            {
                "_id": ObjectId(mongo_id),
                "retries_left": {"$gt": 0}
            },
            {"$set": {"sent": False}}
        )

        # If no document was modified, it means retries are exhausted
        if result.modified_count == 0:
            # Check if the document exists and mark it as permanently failed
            mark_failed_result = await collection.update_one(
                {"_id": ObjectId(mongo_id)},
                {
                    "$set": {
                        "status": "failed",
                        "failed_at": datetime.now(timezone.utc)
                    }
                }
            )
            if mark_failed_result.modified_count > 0:
                logger.error(
                    f"Job {mongo_id} permanently failed after exhausting all retries",
                    event_type="JOB_PERMANENTLY_FAILED",
                    mongo_id=mongo_id
                )


database_writer = DatabaseWriter()
