"""
MongoDB User Applications Repository Implementation.

Handles user-scoped application operations on the career_docs_responses collection.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.domain.entities import Application
from app.domain.ports.repositories import UserApplicationsRepository
from app.log.logging import logger


class MongoUserApplicationsRepository(UserApplicationsRepository):
    """
    MongoDB implementation of UserApplicationsRepository.

    Operates on the career_docs_responses collection where applications
    are stored nested under user documents.
    """

    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        database_name: str = "resumes",
        collection_name: str = "career_docs_responses",
    ):
        self._client = mongo_client
        self._database_name = database_name
        self._collection_name = collection_name

    @property
    def _collection(self):
        """Get the MongoDB collection."""
        return self._client[self._database_name][self._collection_name]

    async def get_pending_applications(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Application]:
        """Get all pending (not sent) applications for a user."""
        try:
            document = await self._collection.find_one(
                {"user_id": user_id},
                {"_id": 0, "content": 1}
            )
            if not document:
                return []

            content = document.get("content", {})
            applications = []

            for app_id, app_data in content.items():
                if isinstance(app_data, dict) and app_data.get("sent") is False:
                    app_data["id"] = app_id
                    try:
                        applications.append(Application.from_dict(app_data))
                    except Exception:
                        # Skip invalid application data
                        continue

            if limit:
                applications = applications[:limit]

            return applications

        except Exception as e:
            logger.exception(
                f"Error fetching pending applications for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return []

    async def get_sent_applications(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Application]:
        """Get all sent/processing applications for a user."""
        try:
            document = await self._collection.find_one(
                {"user_id": user_id},
                {"_id": 0, "content": 1}
            )
            if not document:
                return []

            content = document.get("content", {})
            applications = []

            for app_id, app_data in content.items():
                if isinstance(app_data, dict) and app_data.get("sent") is True:
                    app_data["id"] = app_id
                    try:
                        applications.append(Application.from_dict(app_data))
                    except Exception:
                        continue

            if limit:
                applications = applications[:limit]

            return applications

        except Exception as e:
            logger.exception(
                f"Error fetching sent applications for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return []

    async def get_application_by_id(
        self, user_id: str, application_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific application by ID."""
        try:
            document = await self._collection.find_one(
                {"user_id": user_id, f"content.{application_id}": {"$exists": True}},
                {"_id": 0, f"content.{application_id}": 1}
            )
            if document and "content" in document:
                return document["content"].get(application_id)
            return None

        except Exception as e:
            logger.exception(
                f"Error fetching application {application_id} for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return None

    async def update_application_field(
        self, user_id: str, application_id: str, field_path: str, value: Any
    ) -> bool:
        """Update a specific field in an application."""
        try:
            result = await self._collection.update_one(
                {"user_id": user_id, f"content.{application_id}": {"$exists": True}},
                {"$set": {f"content.{application_id}.{field_path}": value}}
            )
            return result.modified_count > 0

        except Exception as e:
            logger.exception(
                f"Error updating field {field_path} for application {application_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return False

    async def mark_applications_as_sent(
        self, user_id: str, application_ids: List[str]
    ) -> int:
        """Mark multiple applications as sent."""
        try:
            marked_count = 0
            now = datetime.now(timezone.utc)

            for app_id in application_ids:
                result = await self._collection.update_one(
                    {"user_id": user_id, f"content.{app_id}": {"$exists": True}},
                    {
                        "$set": {
                            f"content.{app_id}.sent": True,
                            f"content.{app_id}.timestamp": now,
                        }
                    }
                )
                if result.modified_count > 0:
                    marked_count += 1

            logger.info(
                f"Marked {marked_count} applications as sent for user {user_id}",
                event_type="APPLICATIONS_MARKED_SENT",
                user_id=user_id,
                count=marked_count,
            )
            return marked_count

        except Exception as e:
            logger.exception(
                f"Error marking applications as sent for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return 0

    async def create_or_update_user_document(
        self, user_id: str, application_data: Dict[str, Any]
    ) -> str:
        """Create or update a user's application document."""
        try:
            correlation_id = application_data.get("correlation_id", "")
            app_id = application_data.get("id", correlation_id)

            # Prepare the content entry
            content_entry = {
                **application_data,
                "sent": False,
                "created_at": datetime.now(timezone.utc),
            }

            result = await self._collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {f"content.{app_id}": content_entry},
                    "$setOnInsert": {"user_id": user_id}
                },
                upsert=True,
            )

            if result.upserted_id:
                return str(result.upserted_id)
            return app_id

        except Exception as e:
            logger.exception(
                f"Error creating/updating document for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            raise

    async def count_pending(self, user_id: str) -> int:
        """Count pending applications for a user."""
        try:
            document = await self._collection.find_one(
                {"user_id": user_id},
                {"_id": 0, "content": 1}
            )
            if not document:
                return 0

            content = document.get("content", {})
            count = sum(
                1 for app_data in content.values()
                if isinstance(app_data, dict) and app_data.get("sent") is False
            )
            return count

        except Exception as e:
            logger.exception(
                f"Error counting pending applications for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return 0

    async def get_user_document(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the entire user document."""
        try:
            document = await self._collection.find_one(
                {"user_id": user_id},
                {"_id": 0}
            )
            return document
        except Exception as e:
            logger.exception(
                f"Error fetching document for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return None

    async def get_filtered_applications(
        self, user_id: str, application_ids: List[str]
    ) -> Dict[str, Any]:
        """Get specific applications by their IDs."""
        try:
            document = await self._collection.find_one(
                {"user_id": user_id},
                {"_id": 0, "content": 1}
            )
            if not document:
                return {}

            content = document.get("content", {})
            return {
                app_id: content[app_id]
                for app_id in application_ids
                if app_id in content
            }

        except Exception as e:
            logger.exception(
                f"Error fetching filtered applications for user {user_id}: {e}",
                event_type="REPOSITORY_ERROR",
            )
            return {}
