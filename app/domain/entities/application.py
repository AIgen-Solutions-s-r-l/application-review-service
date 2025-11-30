"""
Application Aggregate Root.

The Application is the central aggregate that brings together
Job, Resume, and CoverLetter entities along with application state.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.domain.value_objects import (
    CorrelationId,
    ApplicationStatus,
    ApplicationStatusType,
)
from app.domain.entities.job import Job
from app.domain.entities.resume import Resume
from app.domain.entities.cover_letter import CoverLetter
from app.domain.exceptions import (
    ApplicationAlreadySentException,
    ApplicationInvalidStateException,
)


@dataclass
class Application:
    """
    Aggregate Root for job applications.

    This is the main entity that coordinates the application process,
    containing the job, optimized resume, and cover letter.

    Business Rules:
    - Applications can only be modified when in PENDING status
    - Applications can only be submitted when in PENDING status
    - Once sent, applications cannot be rolled back
    """
    id: str
    correlation_id: CorrelationId
    user_id: str
    job: Job
    status: ApplicationStatus
    resume: Optional[Resume] = None
    cover_letter: Optional[CoverLetter] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            raise ValueError("Application ID cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")

    @classmethod
    def create(
        cls,
        application_id: str,
        correlation_id: CorrelationId,
        user_id: str,
        job: Job,
        resume: Optional[Resume] = None,
        cover_letter: Optional[CoverLetter] = None,
    ) -> "Application":
        """Factory method to create a new pending application."""
        return cls(
            id=application_id,
            correlation_id=correlation_id,
            user_id=user_id,
            job=job,
            status=ApplicationStatus.pending(),
            resume=resume,
            cover_letter=cover_letter,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Application":
        """Reconstruct Application from dictionary (e.g., from database)."""
        job_data = data.get("job_data", {})
        resume_data = data.get("resume_optimized", {})
        cover_letter_data = data.get("cover_letter", {})

        status_value = data.get("status", "pending")
        if isinstance(status_value, str):
            try:
                status_type = ApplicationStatusType(status_value)
            except ValueError:
                status_type = ApplicationStatusType.PENDING
            status = ApplicationStatus(status=status_type, reason=data.get("failure_reason"))
        else:
            status = ApplicationStatus.pending()

        return cls(
            id=data.get("id", data.get("_id", "")),
            correlation_id=CorrelationId.from_string(data.get("correlation_id", "")),
            user_id=data.get("user_id", ""),
            job=Job.from_dict(job_data) if job_data else None,
            status=status,
            resume=Resume.from_dict(resume_data) if resume_data else None,
            cover_letter=CoverLetter.from_dict(cover_letter_data) if cover_letter_data else None,
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            updated_at=data.get("updated_at", datetime.now(timezone.utc)),
            sent_at=data.get("sent_at"),
            applied_at=data.get("applied_at"),
            failed_at=data.get("failed_at"),
            failure_reason=data.get("failure_reason"),
        )

    def to_dict(self) -> dict:
        """Convert Application to dictionary for persistence."""
        return {
            "id": self.id,
            "correlation_id": str(self.correlation_id),
            "user_id": self.user_id,
            "job_data": self.job.to_dict() if self.job else {},
            "resume_optimized": self.resume.to_dict() if self.resume else {},
            "cover_letter": self.cover_letter.to_dict() if self.cover_letter else {},
            "status": self.status.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sent_at": self.sent_at,
            "applied_at": self.applied_at,
            "failed_at": self.failed_at,
            "failure_reason": self.failure_reason,
        }

    # State Transition Methods (Business Logic)

    def update_resume(self, resume: Resume) -> None:
        """Update the resume. Only allowed when pending."""
        self._ensure_can_modify()
        self.resume = resume
        self._touch()

    def update_cover_letter(self, cover_letter: CoverLetter) -> None:
        """Update the cover letter. Only allowed when pending."""
        self._ensure_can_modify()
        self.cover_letter = cover_letter
        self._touch()

    def mark_as_sent(self) -> None:
        """Mark application as sent to applier queue."""
        self._ensure_can_submit()
        self.status = ApplicationStatus.sent()
        self.sent_at = datetime.now(timezone.utc)
        self._touch()

    def mark_as_applied(self) -> None:
        """Mark application as successfully applied."""
        if not self.status.is_sent:
            raise ApplicationInvalidStateException(
                self.id, self.status.status.value, "sent"
            )
        self.status = ApplicationStatus.applied()
        self.applied_at = datetime.now(timezone.utc)
        self._touch()

    def mark_as_failed(self, reason: str) -> None:
        """Mark application as failed."""
        self.status = ApplicationStatus.failed(reason)
        self.failed_at = datetime.now(timezone.utc)
        self.failure_reason = reason
        self._touch()

    def mark_as_rejected(self, reason: str) -> None:
        """Mark application as rejected by the portal."""
        self.status = ApplicationStatus.rejected(reason)
        self.failed_at = datetime.now(timezone.utc)
        self.failure_reason = reason
        self._touch()

    # Query Methods

    @property
    def is_pending(self) -> bool:
        """Check if application is pending review."""
        return self.status.is_pending

    @property
    def is_sent(self) -> bool:
        """Check if application has been sent."""
        return self.status.is_sent

    @property
    def is_terminal(self) -> bool:
        """Check if application is in a terminal state."""
        return self.status.is_terminal

    @property
    def can_be_modified(self) -> bool:
        """Check if application can be modified."""
        return self.status.can_be_modified

    @property
    def can_be_submitted(self) -> bool:
        """Check if application can be submitted."""
        return self.status.can_be_submitted

    @property
    def applier_queue(self) -> str:
        """Get the appropriate applier queue for this application."""
        return self.job.applier_queue if self.job else "skyvern_queue"

    # Private Helper Methods

    def _ensure_can_modify(self) -> None:
        """Raise exception if application cannot be modified."""
        if not self.can_be_modified:
            raise ApplicationAlreadySentException(self.id)

    def _ensure_can_submit(self) -> None:
        """Raise exception if application cannot be submitted."""
        if not self.can_be_submitted:
            raise ApplicationInvalidStateException(
                self.id, self.status.status.value, "pending"
            )

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Application):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
