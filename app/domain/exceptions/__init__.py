"""
Domain Exceptions - Business rule violation errors.

These exceptions represent violations of business rules and invariants.
They should be caught and translated to appropriate responses at the adapter layer.
"""
from app.domain.exceptions.application_exceptions import (
    DomainException,
    ApplicationNotFoundException,
    ApplicationAlreadySentException,
    ApplicationInvalidStateException,
    InvalidCorrelationIdException,
    ResumeValidationException,
    CoverLetterValidationException,
    PortalNotSupportedException,
    UserNotFoundException,
    UnauthorizedAccessException,
    MessagePublishException,
    CacheOperationException,
)

__all__ = [
    "DomainException",
    "ApplicationNotFoundException",
    "ApplicationAlreadySentException",
    "ApplicationInvalidStateException",
    "InvalidCorrelationIdException",
    "ResumeValidationException",
    "CoverLetterValidationException",
    "PortalNotSupportedException",
    "UserNotFoundException",
    "UnauthorizedAccessException",
    "MessagePublishException",
    "CacheOperationException",
]
