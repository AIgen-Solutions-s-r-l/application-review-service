"""
Update Application Use Cases.

Use cases for modifying application data.
"""
from typing import Dict, Any

from app.domain.ports import UserApplicationsRepository
from app.domain.exceptions import (
    ApplicationNotFoundException,
    ApplicationAlreadySentException,
)
from app.log.logging import logger


class UpdateApplicationFieldUseCase:
    """
    Use case for updating specific fields in an application.

    Can update any field except protected ones like 'sent'.
    """

    # Fields that cannot be directly modified
    PROTECTED_FIELDS = {"sent", "timestamp", "created_at"}

    def __init__(self, repository: UserApplicationsRepository):
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        application_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update specific fields in an application.

        Args:
            user_id: The user identifier
            application_id: The application identifier
            updates: Dictionary of field names to new values

        Returns:
            True if update was successful

        Raises:
            ApplicationNotFoundException: If application not found
            ApplicationAlreadySentException: If application already sent
            ValueError: If trying to update protected fields
        """
        # Check for protected fields
        protected_in_updates = set(updates.keys()) & self.PROTECTED_FIELDS
        if protected_in_updates:
            raise ValueError(
                f"Cannot modify protected fields: {protected_in_updates}"
            )

        # Check application exists and is not sent
        app_data = await self._repository.get_application_by_id(user_id, application_id)
        if not app_data:
            raise ApplicationNotFoundException(application_id)

        if app_data.get("sent", False):
            raise ApplicationAlreadySentException(application_id)

        # Apply updates
        for field, value in updates.items():
            success = await self._repository.update_application_field(
                user_id, application_id, field, value
            )
            if not success:
                logger.warning(
                    f"Failed to update field {field} for application {application_id}",
                    event_type="FIELD_UPDATE_FAILED",
                )

        logger.info(
            f"Updated {len(updates)} fields for application {application_id}",
            event_type="APPLICATION_FIELDS_UPDATED",
            application_id=application_id,
            fields=list(updates.keys()),
        )

        return True


class UpdateResumeUseCase:
    """
    Use case for replacing the entire resume of an application.
    """

    def __init__(self, repository: UserApplicationsRepository):
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        application_id: str,
        resume_data: Dict[str, Any],
    ) -> bool:
        """
        Replace the entire resume for an application.

        Args:
            user_id: The user identifier
            application_id: The application identifier
            resume_data: The new resume data (validated by Pydantic before this)

        Returns:
            True if update was successful

        Raises:
            ApplicationNotFoundException: If application not found
            ApplicationAlreadySentException: If application already sent
        """
        # Check application exists and is not sent
        app_data = await self._repository.get_application_by_id(user_id, application_id)
        if not app_data:
            raise ApplicationNotFoundException(application_id)

        if app_data.get("sent", False):
            raise ApplicationAlreadySentException(application_id)

        # Check resume_optimized section exists
        if "resume_optimized" not in app_data:
            raise ApplicationNotFoundException(
                f"{application_id} (missing resume_optimized section)"
            )

        # Update the resume
        success = await self._repository.update_application_field(
            user_id,
            application_id,
            "resume_optimized.resume",
            resume_data,
        )

        if success:
            logger.info(
                f"Updated resume for application {application_id}",
                event_type="RESUME_UPDATED",
                application_id=application_id,
            )

        return success


class UpdateCoverLetterUseCase:
    """
    Use case for replacing the entire cover letter of an application.
    """

    def __init__(self, repository: UserApplicationsRepository):
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        application_id: str,
        cover_letter_data: Dict[str, Any],
    ) -> bool:
        """
        Replace the entire cover letter for an application.

        Args:
            user_id: The user identifier
            application_id: The application identifier
            cover_letter_data: The new cover letter data (validated by Pydantic before this)

        Returns:
            True if update was successful

        Raises:
            ApplicationNotFoundException: If application not found
            ApplicationAlreadySentException: If application already sent
        """
        # Check application exists and is not sent
        app_data = await self._repository.get_application_by_id(user_id, application_id)
        if not app_data:
            raise ApplicationNotFoundException(application_id)

        if app_data.get("sent", False):
            raise ApplicationAlreadySentException(application_id)

        # Check cover_letter section exists
        if "cover_letter" not in app_data:
            raise ApplicationNotFoundException(
                f"{application_id} (missing cover_letter section)"
            )

        # Update the cover letter
        success = await self._repository.update_application_field(
            user_id,
            application_id,
            "cover_letter.cover_letter",
            cover_letter_data,
        )

        if success:
            logger.info(
                f"Updated cover letter for application {application_id}",
                event_type="COVER_LETTER_UPDATED",
                application_id=application_id,
            )

        return success
