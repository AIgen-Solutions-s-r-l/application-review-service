"""
Submit Applications Use Cases.

Use cases for submitting applications to the applier queues.
"""
from typing import List, Dict, Any, Protocol

from app.domain.ports import UserApplicationsRepository
from app.domain.exceptions import UserNotFoundException, ApplicationNotFoundException
from app.log.logging import logger


class MessagePublisherProtocol(Protocol):
    """Protocol for message publishing (to avoid circular imports)."""

    async def publish_data_to_microservices(self, data: Dict[str, Any]) -> None:
        """Publish data to the appropriate microservices."""
        ...


class SubmitAllApplicationsUseCase:
    """
    Use case for submitting all pending applications.

    Sends all pending applications to the applier microservices.
    """

    def __init__(
        self,
        repository: UserApplicationsRepository,
        publisher: MessagePublisherProtocol,
    ):
        self._repository = repository
        self._publisher = publisher

    async def execute(self, user_id: str) -> Dict[str, Any]:
        """
        Submit all pending applications for a user.

        Args:
            user_id: The user identifier

        Returns:
            Dictionary with submission results

        Raises:
            UserNotFoundException: If user has no applications
        """
        document = await self._repository.get_user_document(user_id)
        if not document:
            raise UserNotFoundException(user_id)

        content = document.get("content", {})
        pending_app_ids = [
            app_id
            for app_id, app_data in content.items()
            if isinstance(app_data, dict) and app_data.get("sent") is False
        ]

        if not pending_app_ids:
            return {
                "message": "No pending applications to submit",
                "submitted_count": 0,
            }

        # Publish to microservices
        await self._publisher.publish_data_to_microservices(document)

        # Mark all as sent
        marked_count = await self._repository.mark_applications_as_sent(
            user_id, pending_app_ids
        )

        logger.info(
            f"Submitted {marked_count} applications for user {user_id}",
            event_type="ALL_APPLICATIONS_SUBMITTED",
            user_id=user_id,
            count=marked_count,
        )

        return {
            "message": "Career documents processed successfully",
            "submitted_count": marked_count,
        }


class SubmitSelectedApplicationsUseCase:
    """
    Use case for submitting selected applications.

    Sends only the specified applications to the applier microservices.
    """

    def __init__(
        self,
        repository: UserApplicationsRepository,
        publisher: MessagePublisherProtocol,
    ):
        self._repository = repository
        self._publisher = publisher

    async def execute(
        self,
        user_id: str,
        application_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Submit selected applications for a user.

        Args:
            user_id: The user identifier
            application_ids: List of application IDs to submit

        Returns:
            Dictionary with submission results

        Raises:
            UserNotFoundException: If user has no applications
            ApplicationNotFoundException: If none of the IDs were found
        """
        document = await self._repository.get_user_document(user_id)
        if not document:
            raise UserNotFoundException(user_id)

        content = document.get("content", {})

        # Filter to only requested and valid applications
        filtered_content = {}
        for app_id in application_ids:
            if app_id in content:
                app_data = content[app_id]
                if isinstance(app_data, dict) and app_data.get("sent") is False:
                    filtered_content[app_id] = app_data

        if not filtered_content:
            raise ApplicationNotFoundException(
                f"None of the specified application IDs were found or all already sent"
            )

        # Create filtered document for publishing
        filtered_document = {
            "user_id": user_id,
            "content": filtered_content,
        }

        # Publish to microservices
        await self._publisher.publish_data_to_microservices(filtered_document)

        # Mark selected as sent
        marked_count = await self._repository.mark_applications_as_sent(
            user_id, list(filtered_content.keys())
        )

        logger.info(
            f"Submitted {marked_count} selected applications for user {user_id}",
            event_type="SELECTED_APPLICATIONS_SUBMITTED",
            user_id=user_id,
            count=marked_count,
            application_ids=list(filtered_content.keys()),
        )

        return {
            "message": "Selected applications processed successfully",
            "submitted_count": marked_count,
            "application_ids": list(filtered_content.keys()),
        }
