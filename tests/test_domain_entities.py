"""Tests for Domain Entities."""
import pytest
from datetime import datetime, timezone

from app.domain.entities import Job, Resume, CoverLetter, Application
from app.domain.value_objects import CorrelationId, ApplicationStatus, JobPortal
from app.domain.exceptions import (
    ApplicationAlreadySentException,
    ApplicationInvalidStateException,
)


class TestJob:
    """Tests for Job entity."""

    def test_create_job_from_dict(self):
        """Test creating a Job from dictionary."""
        data = {
            "id": "job-123",
            "portal": "workday",
            "title": "Software Engineer",
            "company_name": "TechCorp",
            "apply_link": "https://example.com/apply",
            "location": "Remote",
        }
        job = Job.from_dict(data)

        assert job.id == "job-123"
        assert job.title == "Software Engineer"
        assert job.company_name == "TechCorp"
        assert job.portal.name == "workday"
        assert job.requires_browser_automation is False

    def test_job_to_dict(self):
        """Test converting Job to dictionary."""
        data = {
            "id": "job-123",
            "portal": "greenhouse",
            "title": "Data Scientist",
            "company_name": "DataCo",
            "apply_link": "https://example.com/apply",
        }
        job = Job.from_dict(data)
        result = job.to_dict()

        assert result["id"] == "job-123"
        assert result["portal"] == "greenhouse"
        assert result["title"] == "Data Scientist"

    def test_job_requires_browser_automation(self):
        """Test that unknown portals require browser automation."""
        data = {
            "id": "job-456",
            "portal": "custom_ats",
            "title": "Engineer",
            "company_name": "Company",
            "apply_link": "https://example.com/apply",
        }
        job = Job.from_dict(data)
        assert job.requires_browser_automation is True
        assert job.applier_queue == "skyvern_queue"

    def test_job_equality_based_on_id(self):
        """Test Job equality is based on ID."""
        job1 = Job.from_dict({"id": "job-1", "portal": "workday", "title": "Eng",
                              "company_name": "Co", "apply_link": "http://x.com"})
        job2 = Job.from_dict({"id": "job-1", "portal": "greenhouse", "title": "Different",
                              "company_name": "Other", "apply_link": "http://y.com"})
        assert job1 == job2

    def test_job_empty_id_raises_error(self):
        """Test that empty job ID raises ValueError."""
        with pytest.raises(ValueError, match="Job ID cannot be empty"):
            Job.from_dict({"id": "", "portal": "workday", "title": "Eng",
                          "company_name": "Co", "apply_link": "http://x.com"})


class TestResume:
    """Tests for Resume entity."""

    def test_create_resume_from_dict(self):
        """Test creating Resume from dictionary."""
        data = {
            "header": {
                "personal_information": {
                    "name": "John",
                    "surname": "Doe",
                    "email": "john@example.com",
                    "phone": "1234567890",
                }
            },
            "body": {
                "education_details": {"default": [{"institution": "MIT"}]},
                "experience_details": {"default": [{"company": "TechCorp"}]},
            }
        }
        resume = Resume.from_dict(data)

        assert resume.personal_info.name == "John"
        assert resume.personal_info.surname == "Doe"
        assert resume.personal_info.full_name == "John Doe"
        assert resume.has_contact_info is True
        assert resume.has_experience is True
        assert resume.has_education is True

    def test_resume_to_dict(self):
        """Test converting Resume to dictionary."""
        data = {
            "header": {
                "personal_information": {
                    "name": "Jane",
                    "email": "jane@example.com",
                }
            },
            "body": {}
        }
        resume = Resume.from_dict(data)
        result = resume.to_dict()

        assert result["header"]["personal_information"]["name"] == "Jane"

    def test_resume_update_personal_info(self):
        """Test updating personal information."""
        resume = Resume.from_dict({
            "header": {"personal_information": {"name": "John", "email": "john@example.com"}},
            "body": {}
        })
        updated = resume.update_personal_info({"surname": "Smith", "phone": "9876543210"})

        assert updated.personal_info.name == "John"  # Unchanged
        assert updated.personal_info.surname == "Smith"  # Added
        assert updated.personal_info.phone == "9876543210"  # Added

    def test_resume_has_contact_info_false(self):
        """Test has_contact_info when no contact info present."""
        resume = Resume.from_dict({"header": {"personal_information": {"name": "John"}}, "body": {}})
        assert resume.has_contact_info is False


class TestCoverLetter:
    """Tests for CoverLetter entity."""

    def test_create_cover_letter_from_dict(self):
        """Test creating CoverLetter from dictionary."""
        data = {
            "header": {
                "applicant_details": {"name": "John Doe", "email": "john@example.com"},
                "company_details": {"name": "TechCorp"},
            },
            "body": {
                "greeting": "Dear Hiring Manager,",
                "opening_paragraph": "I am writing to apply...",
                "body_paragraphs": ["First paragraph", "Second paragraph"],
                "closing_paragraph": "Thank you for your consideration.",
            },
            "footer": {
                "closing": "Sincerely,",
                "signature": "John Doe",
            }
        }
        letter = CoverLetter.from_dict(data)

        assert letter.applicant_details.name == "John Doe"
        assert letter.company_details.name == "TechCorp"
        assert letter.greeting == "Dear Hiring Manager,"
        assert letter.is_complete is True

    def test_cover_letter_word_count(self):
        """Test word count calculation."""
        data = {
            "body": {
                "greeting": "Dear Sir",
                "opening_paragraph": "I am applying for this position",
                "body_paragraphs": ["One two three"],
                "closing_paragraph": "Thank you",
            }
        }
        letter = CoverLetter.from_dict(data)
        # "Dear Sir" (2) + "I am applying for this position" (6) + "One two three" (3) + "Thank you" (2) = 13
        assert letter.word_count == 13

    def test_cover_letter_is_complete_false(self):
        """Test is_complete returns False when sections missing."""
        letter = CoverLetter.from_dict({"body": {"greeting": "Hello"}})
        assert letter.is_complete is False


class TestApplication:
    """Tests for Application aggregate root."""

    def create_test_job(self):
        """Helper to create a test Job."""
        return Job.from_dict({
            "id": "job-123",
            "portal": "workday",
            "title": "Software Engineer",
            "company_name": "TechCorp",
            "apply_link": "https://example.com/apply",
        })

    def test_create_application(self):
        """Test creating a new Application."""
        job = self.create_test_job()
        correlation_id = CorrelationId.generate()

        app = Application.create(
            application_id="app-123",
            correlation_id=correlation_id,
            user_id="user-456",
            job=job,
        )

        assert app.id == "app-123"
        assert app.user_id == "user-456"
        assert app.is_pending is True
        assert app.can_be_modified is True
        assert app.can_be_submitted is True

    def test_mark_as_sent(self):
        """Test marking application as sent."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )

        app.mark_as_sent()

        assert app.is_sent is True
        assert app.is_pending is False
        assert app.can_be_modified is False
        assert app.sent_at is not None

    def test_mark_already_sent_raises_error(self):
        """Test that marking sent application as sent raises error."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )
        app.mark_as_sent()

        with pytest.raises(ApplicationInvalidStateException):
            app.mark_as_sent()

    def test_update_resume_when_pending(self):
        """Test updating resume when application is pending."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )
        resume = Resume.from_dict({"header": {"personal_information": {"name": "John"}}, "body": {}})

        app.update_resume(resume)

        assert app.resume is not None
        assert app.resume.personal_info.name == "John"

    def test_update_resume_when_sent_raises_error(self):
        """Test that updating resume when sent raises error."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )
        app.mark_as_sent()
        resume = Resume.from_dict({"header": {}, "body": {}})

        with pytest.raises(ApplicationAlreadySentException):
            app.update_resume(resume)

    def test_mark_as_applied(self):
        """Test marking application as applied."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )
        app.mark_as_sent()
        app.mark_as_applied()

        assert app.is_terminal is True
        assert app.applied_at is not None

    def test_mark_as_failed(self):
        """Test marking application as failed."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )

        app.mark_as_failed("Network error")

        assert app.is_terminal is True
        assert app.failure_reason == "Network error"
        assert app.failed_at is not None

    def test_applier_queue(self):
        """Test getting the correct applier queue."""
        job = self.create_test_job()
        app = Application.create(
            application_id="app-123",
            correlation_id=CorrelationId.generate(),
            user_id="user-456",
            job=job,
        )

        assert app.applier_queue == "providers_queue"
