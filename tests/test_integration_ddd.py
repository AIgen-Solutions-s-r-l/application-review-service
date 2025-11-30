"""
Integration tests for DDD architecture.

Tests the full flow through domain, application, and infrastructure layers.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.domain.value_objects import CorrelationId, ApplicationStatus, JobPortal, PortalType
from app.domain.entities import Application, Job, Resume, CoverLetter
from app.domain.exceptions import (
    ApplicationNotFoundException,
    ApplicationAlreadySentException,
    UserNotFoundException,
)
from app.application.use_cases import (
    GetPendingApplicationsUseCase,
    GetSentApplicationsUseCase,
    GetApplicationDetailsUseCase,
    UpdateApplicationFieldUseCase,
    UpdateResumeUseCase,
    UpdateCoverLetterUseCase,
    SubmitAllApplicationsUseCase,
    SubmitSelectedApplicationsUseCase,
)
from app.infrastructure.container import Container, get_container, reset_container


class TestFullApplicationFlow:
    """Test complete application lifecycle through all layers."""

    def create_mock_user_document(self):
        """Create a realistic user document for testing."""
        return {
            "user_id": "user-123",
            "content": {
                "app-1": {
                    "id": "job-1",
                    "portal": "workday",
                    "title": "Software Engineer",
                    "company_name": "TechCorp",
                    "apply_link": "https://techcorp.com/apply",
                    "location": "Remote",
                    "sent": False,
                    "resume_optimized": {
                        "resume": {
                            "header": {"personal_information": {"name": "John", "surname": "Doe"}},
                            "body": {"experience_details": {}}
                        }
                    },
                    "cover_letter": {
                        "cover_letter": {
                            "body": {"greeting": "Dear Hiring Manager"}
                        }
                    },
                    "style": "professional",
                    "gen_cv": True,
                },
                "app-2": {
                    "id": "job-2",
                    "portal": "greenhouse",
                    "title": "Data Scientist",
                    "company_name": "DataCo",
                    "apply_link": "https://dataco.com/apply",
                    "location": "New York",
                    "sent": False,
                    "resume_optimized": {},
                    "cover_letter": {},
                    "style": "creative",
                    "gen_cv": True,
                },
                "app-3": {
                    "id": "job-3",
                    "portal": "lever",
                    "title": "DevOps Engineer",
                    "company_name": "CloudInc",
                    "apply_link": "https://cloudinc.com/apply",
                    "sent": True,  # Already sent
                    "timestamp": datetime.now(timezone.utc),
                },
            }
        }


class TestGetPendingApplicationsUseCase:
    """Tests for GetPendingApplicationsUseCase."""

    @pytest.mark.asyncio
    async def test_returns_only_pending_applications(self):
        """Test that only non-sent applications are returned."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value={
            "user_id": "user-123",
            "content": {
                "app-1": {"id": "1", "portal": "workday", "title": "Eng", "sent": False},
                "app-2": {"id": "2", "portal": "greenhouse", "title": "Dev", "sent": True},
                "app-3": {"id": "3", "portal": "lever", "title": "SRE", "sent": False},
            }
        })

        use_case = GetPendingApplicationsUseCase(mock_repo)
        result = await use_case.execute("user-123")

        assert len(result) == 2
        assert "app-1" in result
        assert "app-3" in result
        assert "app-2" not in result

    @pytest.mark.asyncio
    async def test_raises_user_not_found_when_no_document(self):
        """Test UserNotFoundException when user has no documents."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value=None)

        use_case = GetPendingApplicationsUseCase(mock_repo)

        with pytest.raises(UserNotFoundException):
            await use_case.execute("nonexistent-user")


class TestGetSentApplicationsUseCase:
    """Tests for GetSentApplicationsUseCase."""

    @pytest.mark.asyncio
    async def test_returns_only_sent_applications(self):
        """Test that only sent applications are returned."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value={
            "user_id": "user-123",
            "content": {
                "app-1": {"id": "1", "portal": "workday", "title": "Eng", "sent": False},
                "app-2": {"id": "2", "portal": "greenhouse", "title": "Dev", "sent": True},
                "app-3": {"id": "3", "portal": "lever", "title": "SRE", "sent": True},
            }
        })

        use_case = GetSentApplicationsUseCase(mock_repo)
        result = await use_case.execute("user-123")

        assert len(result) == 2
        assert "app-2" in result
        assert "app-3" in result
        assert "app-1" not in result


class TestGetApplicationDetailsUseCase:
    """Tests for GetApplicationDetailsUseCase."""

    @pytest.mark.asyncio
    async def test_returns_full_application_details(self):
        """Test that full application details are returned."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "job-1",
            "portal": "workday",
            "title": "Software Engineer",
            "company_name": "TechCorp",
            "apply_link": "https://example.com",
            "resume_optimized": {"resume": {"header": {}}},
            "cover_letter": {"cover_letter": {"body": {}}},
            "sent": False,
            "style": "professional",
        })

        use_case = GetApplicationDetailsUseCase(mock_repo)
        result = await use_case.execute("user-123", "app-1")

        assert result.id == "app-1"
        assert result.job_info["title"] == "Software Engineer"
        assert result.resume_optimized is not None
        assert result.sent is False

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_application(self):
        """Test ApplicationNotFoundException for missing application."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value=None)

        use_case = GetApplicationDetailsUseCase(mock_repo)

        with pytest.raises(ApplicationNotFoundException):
            await use_case.execute("user-123", "nonexistent-app")


class TestUpdateApplicationFieldUseCase:
    """Tests for UpdateApplicationFieldUseCase."""

    @pytest.mark.asyncio
    async def test_updates_field_successfully(self):
        """Test successful field update."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "app-1",
            "sent": False,
            "style": "professional",
        })
        mock_repo.update_application_field = AsyncMock(return_value=True)

        use_case = UpdateApplicationFieldUseCase(mock_repo)
        result = await use_case.execute("user-123", "app-1", {"style": "creative"})

        assert result is True
        mock_repo.update_application_field.assert_called_once_with(
            "user-123", "app-1", "style", "creative"
        )

    @pytest.mark.asyncio
    async def test_raises_error_for_sent_application(self):
        """Test that updating sent application raises error."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "app-1",
            "sent": True,
        })

        use_case = UpdateApplicationFieldUseCase(mock_repo)

        with pytest.raises(ApplicationAlreadySentException):
            await use_case.execute("user-123", "app-1", {"style": "creative"})

    @pytest.mark.asyncio
    async def test_raises_error_for_protected_fields(self):
        """Test that updating protected fields raises error."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "app-1",
            "sent": False,
        })

        use_case = UpdateApplicationFieldUseCase(mock_repo)

        with pytest.raises(ValueError, match="Cannot modify protected fields"):
            await use_case.execute("user-123", "app-1", {"sent": True})


class TestUpdateResumeUseCase:
    """Tests for UpdateResumeUseCase."""

    @pytest.mark.asyncio
    async def test_updates_resume_successfully(self):
        """Test successful resume update."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "app-1",
            "sent": False,
            "resume_optimized": {"resume": {}},
        })
        mock_repo.update_application_field = AsyncMock(return_value=True)

        use_case = UpdateResumeUseCase(mock_repo)
        new_resume = {"header": {"personal_information": {"name": "Jane"}}, "body": {}}
        result = await use_case.execute("user-123", "app-1", new_resume)

        assert result is True

    @pytest.mark.asyncio
    async def test_raises_error_when_sent(self):
        """Test error when trying to update sent application."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "app-1",
            "sent": True,
            "resume_optimized": {},
        })

        use_case = UpdateResumeUseCase(mock_repo)

        with pytest.raises(ApplicationAlreadySentException):
            await use_case.execute("user-123", "app-1", {})


class TestUpdateCoverLetterUseCase:
    """Tests for UpdateCoverLetterUseCase."""

    @pytest.mark.asyncio
    async def test_updates_cover_letter_successfully(self):
        """Test successful cover letter update."""
        mock_repo = AsyncMock()
        mock_repo.get_application_by_id = AsyncMock(return_value={
            "id": "app-1",
            "sent": False,
            "cover_letter": {"cover_letter": {}},
        })
        mock_repo.update_application_field = AsyncMock(return_value=True)

        use_case = UpdateCoverLetterUseCase(mock_repo)
        new_letter = {"body": {"greeting": "Hello"}}
        result = await use_case.execute("user-123", "app-1", new_letter)

        assert result is True


class TestSubmitAllApplicationsUseCase:
    """Tests for SubmitAllApplicationsUseCase."""

    @pytest.mark.asyncio
    async def test_submits_all_pending_applications(self):
        """Test that all pending applications are submitted."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value={
            "user_id": "user-123",
            "content": {
                "app-1": {"sent": False},
                "app-2": {"sent": False},
                "app-3": {"sent": True},  # Already sent, should be ignored
            }
        })
        mock_repo.mark_applications_as_sent = AsyncMock(return_value=2)

        mock_publisher = AsyncMock()
        mock_publisher.publish_data_to_microservices = AsyncMock()

        use_case = SubmitAllApplicationsUseCase(mock_repo, mock_publisher)
        result = await use_case.execute("user-123")

        assert result["submitted_count"] == 2
        mock_publisher.publish_data_to_microservices.assert_called_once()
        mock_repo.mark_applications_as_sent.assert_called_once_with(
            "user-123", ["app-1", "app-2"]
        )

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_pending(self):
        """Test that zero is returned when no pending applications."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value={
            "user_id": "user-123",
            "content": {
                "app-1": {"sent": True},
                "app-2": {"sent": True},
            }
        })

        mock_publisher = AsyncMock()

        use_case = SubmitAllApplicationsUseCase(mock_repo, mock_publisher)
        result = await use_case.execute("user-123")

        assert result["submitted_count"] == 0
        mock_publisher.publish_data_to_microservices.assert_not_called()


class TestSubmitSelectedApplicationsUseCase:
    """Tests for SubmitSelectedApplicationsUseCase."""

    @pytest.mark.asyncio
    async def test_submits_selected_applications(self):
        """Test that only selected applications are submitted."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value={
            "user_id": "user-123",
            "content": {
                "app-1": {"id": "1", "sent": False},
                "app-2": {"id": "2", "sent": False},
                "app-3": {"id": "3", "sent": False},
            }
        })
        mock_repo.mark_applications_as_sent = AsyncMock(return_value=2)

        mock_publisher = AsyncMock()
        mock_publisher.publish_data_to_microservices = AsyncMock()

        use_case = SubmitSelectedApplicationsUseCase(mock_repo, mock_publisher)
        result = await use_case.execute("user-123", ["app-1", "app-3"])

        assert result["submitted_count"] == 2
        assert "app-1" in result["application_ids"]
        assert "app-3" in result["application_ids"]

    @pytest.mark.asyncio
    async def test_raises_error_when_none_found(self):
        """Test error when no valid applications found."""
        mock_repo = AsyncMock()
        mock_repo.get_user_document = AsyncMock(return_value={
            "user_id": "user-123",
            "content": {
                "app-1": {"sent": True},  # Already sent
            }
        })

        mock_publisher = AsyncMock()

        use_case = SubmitSelectedApplicationsUseCase(mock_repo, mock_publisher)

        with pytest.raises(ApplicationNotFoundException):
            await use_case.execute("user-123", ["app-1", "nonexistent"])


class TestDependencyInjectionContainer:
    """Tests for the DI Container."""

    def test_container_singleton(self):
        """Test that get_container returns singleton."""
        reset_container()
        container1 = get_container()
        container2 = get_container()
        assert container1 is container2

    def test_reset_container(self):
        """Test that reset_container creates new instance."""
        container1 = get_container()
        reset_container()
        container2 = get_container()
        assert container1 is not container2

    def test_container_raises_error_when_not_initialized(self):
        """Test that accessing repos without init raises error."""
        reset_container()
        container = get_container()

        with pytest.raises(RuntimeError, match="Container not initialized"):
            _ = container.application_repository

    def test_container_initialization(self):
        """Test container initialization with mock client."""
        reset_container()
        container = get_container()

        mock_mongo_client = MagicMock()
        container.initialize(mongo_client=mock_mongo_client)

        # Should not raise
        repo = container.application_repository
        assert repo is not None


class TestDomainEntityIntegration:
    """Test domain entities work together correctly."""

    def test_application_lifecycle(self):
        """Test complete application lifecycle."""
        # Create entities
        job = Job.from_dict({
            "id": "job-123",
            "portal": "workday",
            "title": "Software Engineer",
            "company_name": "TechCorp",
            "apply_link": "https://example.com",
        })

        resume = Resume.from_dict({
            "header": {"personal_information": {"name": "John", "email": "john@example.com"}},
            "body": {"experience_details": {"default": [{"company": "PrevCo"}]}}
        })

        cover_letter = CoverLetter.from_dict({
            "body": {
                "greeting": "Dear Hiring Manager",
                "opening_paragraph": "I am writing to apply...",
                "body_paragraphs": ["Experience paragraph"],
                "closing_paragraph": "Thank you",
            }
        })

        # Create application
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
            resume=resume,
            cover_letter=cover_letter,
        )

        # Verify initial state
        assert app.is_pending is True
        assert app.can_be_modified is True
        assert app.applier_queue == "providers_queue"  # workday has native provider

        # Update resume while pending
        new_resume = resume.update_personal_info({"surname": "Doe"})
        app.update_resume(new_resume)
        assert app.resume.personal_info.surname == "Doe"

        # Send application
        app.mark_as_sent()
        assert app.is_sent is True
        assert app.sent_at is not None

        # Cannot modify after sent
        with pytest.raises(ApplicationAlreadySentException):
            app.update_resume(resume)

        # Mark as applied
        app.mark_as_applied()
        assert app.is_terminal is True
        assert app.applied_at is not None

    def test_portal_routing_for_different_portals(self):
        """Test that different portals route to correct queues."""
        native_portals = ["workday", "greenhouse", "smartrecruiters", "dice", "lever"]
        browser_portals = ["custom_ats", "unknown_portal", "some_company"]

        for portal_name in native_portals:
            job = Job.from_dict({
                "id": "job-1",
                "portal": portal_name,
                "title": "Eng",
                "company_name": "Co",
                "apply_link": "http://x.com",
            })
            assert job.applier_queue == "providers_queue", f"Failed for {portal_name}"

        for portal_name in browser_portals:
            job = Job.from_dict({
                "id": "job-1",
                "portal": portal_name,
                "title": "Eng",
                "company_name": "Co",
                "apply_link": "http://x.com",
            })
            assert job.applier_queue == "skyvern_queue", f"Failed for {portal_name}"


class TestValueObjectImmutability:
    """Test that value objects are truly immutable."""

    def test_correlation_id_immutable(self):
        """Test CorrelationId cannot be modified."""
        cid = CorrelationId.generate()
        with pytest.raises(Exception):  # frozen dataclass raises FrozenInstanceError
            cid.value = "new-value"

    def test_application_status_immutable(self):
        """Test ApplicationStatus cannot be modified."""
        status = ApplicationStatus.pending()
        with pytest.raises(Exception):
            status.status = "sent"

    def test_job_portal_immutable(self):
        """Test JobPortal cannot be modified."""
        portal = JobPortal.from_string("workday")
        with pytest.raises(Exception):
            portal.name = "greenhouse"
