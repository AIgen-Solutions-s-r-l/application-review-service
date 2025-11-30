"""
MongoDB Application Repository Implementation.

Implements the ApplicationRepository interface for MongoDB.
"""
from typing import Optional
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.domain.entities import Application
from app.domain.ports.repositories import ApplicationRepository
from app.log.logging import logger


class MongoApplicationRepository(ApplicationRepository):
    """
    MongoDB implementation of the ApplicationRepository.

    Handles persistence of Application aggregates to MongoDB.
    """

    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        database_name: str = "resumes",
        collection_name: str = "jobs_to_apply_per_user",
    ):
        self._client = mongo_client
        self._database_name = database_name
        self._collection_name = collection_name

    @property
    def _collection(self):
        """Get the MongoDB collection."""
        return self._client[self._database_name][self._collection_name]

    async def get_by_id(
        self, application_id: str, user_id: str
    ) -> Optional[Application]:
        """Retrieve an application by its ID."""
        try:
            document = await self._collection.find_one({
                "_id": ObjectId(application_id),
                "user_id": user_id,
            })
            if document:
                document["id"] = str(document.pop("_id"))
                return Application.from_dict(document)
            return None
        except Exception as e:
            logger.exception(
                f"Error fetching application {application_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return None

    async def get_by_correlation_id(
        self, correlation_id: str
    ) -> Optional[Application]:
        """Retrieve an application by its correlation ID."""
        try:
            document = await self._collection.find_one({
                "correlation_id": correlation_id,
            })
            if document:
                document["id"] = str(document.pop("_id"))
                return Application.from_dict(document)
            return None
        except Exception as e:
            logger.exception(
                f"Error fetching application by correlation_id {correlation_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return None

    async def save(self, application: Application) -> str:
        """Persist an application (create or update)."""
        try:
            data = application.to_dict()
            data["updated_at"] = datetime.now(timezone.utc)

            if application.id and application.id != "":
                # Update existing
                try:
                    object_id = ObjectId(application.id)
                    data.pop("id", None)
                    await self._collection.update_one(
                        {"_id": object_id},
                        {"$set": data},
                        upsert=True,
                    )
                    return str(object_id)
                except Exception:
                    # If ID is not a valid ObjectId, create new
                    pass

            # Create new
            data.pop("id", None)
            data["created_at"] = datetime.now(timezone.utc)
            result = await self._collection.insert_one(data)
            return str(result.inserted_id)

        except Exception as e:
            logger.exception(
                f"Error saving application: {e}",
                event_type="REPOSITORY_ERROR",
            )
            raise

    async def delete(self, application_id: str, user_id: str) -> bool:
        """Delete an application."""
        try:
            result = await self._collection.delete_one({
                "_id": ObjectId(application_id),
                "user_id": user_id,
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.exception(
                f"Error deleting application {application_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return False

    async def restore_sent_status(self, application_id: str) -> bool:
        """
        Restore sent status for retry. Returns False if retries exhausted.

        This is a specific MongoDB operation for the retry mechanism.
        """
        try:
            # Try to restore for retry (only if retries_left > 0)
            result = await self._collection.update_one(
                {
                    "_id": ObjectId(application_id),
                    "retries_left": {"$gt": 0}
                },
                {"$set": {"sent": False}}
            )

            if result.modified_count > 0:
                return True

            # No retries left, mark as failed
            await self._collection.update_one(
                {"_id": ObjectId(application_id)},
                {
                    "$set": {
                        "status": "failed",
                        "failed_at": datetime.now(timezone.utc)
                    }
                }
            )
            logger.error(
                f"Application {application_id} permanently failed after exhausting retries",
                event_type="APPLICATION_PERMANENTLY_FAILED",
                application_id=application_id,
            )
            return False

        except Exception as e:
            logger.exception(
                f"Error restoring sent status for {application_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return False
