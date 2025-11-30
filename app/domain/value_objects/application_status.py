"""
Application Status Value Object.

Represents the lifecycle state of a job application.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ApplicationStatusType(str, Enum):
    """Enumeration of possible application statuses."""
    PENDING = "pending"          # Generated, awaiting user review
    SENT = "sent"                # Sent to applier, processing
    APPLIED = "applied"          # Successfully applied
    FAILED = "failed"            # Application failed permanently
    REJECTED = "rejected"        # Application rejected by portal


@dataclass(frozen=True)
class ApplicationStatus:
    """
    Value Object representing the status of a job application.

    Immutable - state transitions create new instances.
    """
    status: ApplicationStatusType
    reason: Optional[str] = None

    @classmethod
    def pending(cls) -> "ApplicationStatus":
        """Create a pending status."""
        return cls(status=ApplicationStatusType.PENDING)

    @classmethod
    def sent(cls) -> "ApplicationStatus":
        """Create a sent status."""
        return cls(status=ApplicationStatusType.SENT)

    @classmethod
    def applied(cls) -> "ApplicationStatus":
        """Create an applied status."""
        return cls(status=ApplicationStatusType.APPLIED)

    @classmethod
    def failed(cls, reason: str) -> "ApplicationStatus":
        """Create a failed status with reason."""
        return cls(status=ApplicationStatusType.FAILED, reason=reason)

    @classmethod
    def rejected(cls, reason: str) -> "ApplicationStatus":
        """Create a rejected status with reason."""
        return cls(status=ApplicationStatusType.REJECTED, reason=reason)

    @property
    def is_pending(self) -> bool:
        return self.status == ApplicationStatusType.PENDING

    @property
    def is_sent(self) -> bool:
        return self.status == ApplicationStatusType.SENT

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no more transitions possible)."""
        return self.status in (
            ApplicationStatusType.APPLIED,
            ApplicationStatusType.FAILED,
            ApplicationStatusType.REJECTED
        )

    @property
    def can_be_modified(self) -> bool:
        """Check if application can still be modified."""
        return self.status == ApplicationStatusType.PENDING

    @property
    def can_be_submitted(self) -> bool:
        """Check if application can be submitted."""
        return self.status == ApplicationStatusType.PENDING

    def __str__(self) -> str:
        if self.reason:
            return f"{self.status.value}: {self.reason}"
        return self.status.value
