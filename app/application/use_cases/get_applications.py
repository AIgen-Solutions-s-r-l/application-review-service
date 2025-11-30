"""
Get Applications Use Cases.

Use cases for retrieving application data.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from app.domain.ports import UserApplicationsRepository
from app.domain.exceptions import ApplicationNotFoundException, UserNotFoundException
from app.log.logging import logger


@dataclass
class ApplicationSummary:
    """Summary of an application (without resume/cover letter)."""
    id: str
    portal: Optional[str]
    title: Optional[str]
    company_name: Optional[str]
    location: Optional[str]
    workplace_type: Optional[str]
    posted_date: Optional[str]
    job_state: Optional[str]
    description: Optional[str]
    apply_link: Optional[str]
    short_description: Optional[str]
    company_logo: Optional[str]
    field: Optional[str]
    experience: Optional[str]
    skills_required: Optional[List[str]]
    sent: bool
    style: Optional[str]
    gen_cv: Optional[bool]
    timestamp: Optional[str]


@dataclass
class ApplicationDetails:
    """Full application details including resume and cover letter."""
    id: str
    resume_optimized: Optional[Dict[str, Any]]
    cover_letter: Optional[Dict[str, Any]]
    job_info: Dict[str, Any]
    style: Optional[str]
    sent: bool
    gen_cv: Optional[bool]


class GetPendingApplicationsUseCase:
    """
    Use case for retrieving pending applications.

    Returns applications that have not been sent yet.
    """

    def __init__(self, repository: UserApplicationsRepository):
        self._repository = repository

    async def execute(self, user_id: str) -> Dict[str, ApplicationSummary]:
        """
        Get all pending applications for a user.

        Args:
            user_id: The user identifier

        Returns:
            Dictionary mapping application IDs to summaries

        Raises:
            UserNotFoundException: If user has no applications
        """
        document = await self._repository.get_user_document(user_id)
        if not document:
            raise UserNotFoundException(user_id)

        content = document.get("content", {})
        result = {}

        for app_id, app_data in content.items():
            if isinstance(app_data, dict) and app_data.get("sent") is False:
                result[app_id] = self._to_summary(app_id, app_data)

        logger.info(
            f"Retrieved {len(result)} pending applications for user {user_id}",
            event_type="PENDING_APPLICATIONS_RETRIEVED",
            user_id=user_id,
            count=len(result),
        )

        return result

    def _to_summary(self, app_id: str, data: Dict[str, Any]) -> ApplicationSummary:
        """Convert raw data to ApplicationSummary."""
        return ApplicationSummary(
            id=app_id,
            portal=data.get("portal"),
            title=data.get("title"),
            company_name=data.get("company_name"),
            location=data.get("location"),
            workplace_type=data.get("workplace_type"),
            posted_date=data.get("posted_date"),
            job_state=data.get("job_state"),
            description=data.get("description"),
            apply_link=data.get("apply_link"),
            short_description=data.get("short_description"),
            company_logo=data.get("company_logo"),
            field=data.get("field"),
            experience=data.get("experience"),
            skills_required=data.get("skills_required"),
            sent=data.get("sent", False),
            style=data.get("style"),
            gen_cv=data.get("gen_cv"),
            timestamp=str(data.get("timestamp")) if data.get("timestamp") else None,
        )


class GetSentApplicationsUseCase:
    """
    Use case for retrieving sent/processing applications.

    Returns applications that have been submitted and are being processed.
    """

    def __init__(self, repository: UserApplicationsRepository):
        self._repository = repository

    async def execute(self, user_id: str) -> Dict[str, ApplicationSummary]:
        """
        Get all sent applications for a user.

        Args:
            user_id: The user identifier

        Returns:
            Dictionary mapping application IDs to summaries

        Raises:
            UserNotFoundException: If user has no applications
        """
        document = await self._repository.get_user_document(user_id)
        if not document:
            raise UserNotFoundException(user_id)

        content = document.get("content", {})
        result = {}

        for app_id, app_data in content.items():
            if isinstance(app_data, dict) and app_data.get("sent") is True:
                result[app_id] = self._to_summary(app_id, app_data)

        logger.info(
            f"Retrieved {len(result)} sent applications for user {user_id}",
            event_type="SENT_APPLICATIONS_RETRIEVED",
            user_id=user_id,
            count=len(result),
        )

        return result

    def _to_summary(self, app_id: str, data: Dict[str, Any]) -> ApplicationSummary:
        """Convert raw data to ApplicationSummary."""
        return ApplicationSummary(
            id=app_id,
            portal=data.get("portal"),
            title=data.get("title"),
            company_name=data.get("company_name"),
            location=data.get("location"),
            workplace_type=data.get("workplace_type"),
            posted_date=data.get("posted_date"),
            job_state=data.get("job_state"),
            description=data.get("description"),
            apply_link=data.get("apply_link"),
            short_description=data.get("short_description"),
            company_logo=data.get("company_logo"),
            field=data.get("field"),
            experience=data.get("experience"),
            skills_required=data.get("skills_required"),
            sent=data.get("sent", True),
            style=data.get("style"),
            gen_cv=data.get("gen_cv"),
            timestamp=str(data.get("timestamp")) if data.get("timestamp") else None,
        )


class GetApplicationDetailsUseCase:
    """
    Use case for retrieving full application details.

    Returns complete application data including resume and cover letter.
    """

    def __init__(self, repository: UserApplicationsRepository):
        self._repository = repository

    async def execute(self, user_id: str, application_id: str) -> ApplicationDetails:
        """
        Get full details of a specific application.

        Args:
            user_id: The user identifier
            application_id: The application identifier

        Returns:
            ApplicationDetails with full data

        Raises:
            ApplicationNotFoundException: If application not found
        """
        app_data = await self._repository.get_application_by_id(user_id, application_id)

        if not app_data:
            raise ApplicationNotFoundException(application_id)

        logger.info(
            f"Retrieved details for application {application_id}",
            event_type="APPLICATION_DETAILS_RETRIEVED",
            user_id=user_id,
            application_id=application_id,
        )

        return ApplicationDetails(
            id=application_id,
            resume_optimized=app_data.get("resume_optimized"),
            cover_letter=app_data.get("cover_letter"),
            job_info={
                "id": app_data.get("id"),
                "portal": app_data.get("portal"),
                "title": app_data.get("title"),
                "workplace_type": app_data.get("workplace_type"),
                "posted_date": app_data.get("posted_date"),
                "job_state": app_data.get("job_state"),
                "description": app_data.get("description"),
                "apply_link": app_data.get("apply_link"),
                "company_name": app_data.get("company_name"),
                "location": app_data.get("location"),
                "short_description": app_data.get("short_description"),
                "company_logo": app_data.get("company_logo"),
                "field": app_data.get("field"),
                "experience": app_data.get("experience"),
                "skills_required": app_data.get("skills_required"),
            },
            style=app_data.get("style"),
            sent=app_data.get("sent", False),
            gen_cv=app_data.get("gen_cv"),
        )
