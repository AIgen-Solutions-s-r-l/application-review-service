"""
Application Domain Exceptions.

Custom exceptions for business rule violations in the application domain.
"""
from typing import Optional


class DomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class ApplicationNotFoundException(DomainException):
    """Raised when an application cannot be found."""

    def __init__(self, application_id: str):
        super().__init__(
            message=f"Application not found: {application_id}",
            code="APPLICATION_NOT_FOUND"
        )
        self.application_id = application_id


class ApplicationAlreadySentException(DomainException):
    """Raised when attempting to modify an already sent application."""

    def __init__(self, application_id: str):
        super().__init__(
            message=f"Application already sent and cannot be modified: {application_id}",
            code="APPLICATION_ALREADY_SENT"
        )
        self.application_id = application_id


class ApplicationInvalidStateException(DomainException):
    """Raised when an application is in an invalid state for the requested operation."""

    def __init__(self, application_id: str, current_state: str, required_state: str):
        super().__init__(
            message=f"Application {application_id} is in state '{current_state}', "
                    f"but '{required_state}' is required for this operation",
            code="APPLICATION_INVALID_STATE"
        )
        self.application_id = application_id
        self.current_state = current_state
        self.required_state = required_state


class InvalidCorrelationIdException(DomainException):
    """Raised when a correlation ID is invalid or malformed."""

    def __init__(self, correlation_id: str, reason: str = "Invalid format"):
        super().__init__(
            message=f"Invalid correlation ID '{correlation_id}': {reason}",
            code="INVALID_CORRELATION_ID"
        )
        self.correlation_id = correlation_id
        self.reason = reason


class ResumeValidationException(DomainException):
    """Raised when resume data fails validation."""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Resume validation failed for field '{field}': {reason}",
            code="RESUME_VALIDATION_ERROR"
        )
        self.field = field
        self.reason = reason


class CoverLetterValidationException(DomainException):
    """Raised when cover letter data fails validation."""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Cover letter validation failed for field '{field}': {reason}",
            code="COVER_LETTER_VALIDATION_ERROR"
        )
        self.field = field
        self.reason = reason


class PortalNotSupportedException(DomainException):
    """Raised when a job portal is not supported."""

    def __init__(self, portal_name: str):
        super().__init__(
            message=f"Job portal '{portal_name}' is not supported",
            code="PORTAL_NOT_SUPPORTED"
        )
        self.portal_name = portal_name


class UserNotFoundException(DomainException):
    """Raised when a user cannot be found."""

    def __init__(self, user_id: str):
        super().__init__(
            message=f"User not found: {user_id}",
            code="USER_NOT_FOUND"
        )
        self.user_id = user_id


class UnauthorizedAccessException(DomainException):
    """Raised when access to a resource is denied."""

    def __init__(self, resource: str, user_id: str):
        super().__init__(
            message=f"User '{user_id}' is not authorized to access '{resource}'",
            code="UNAUTHORIZED_ACCESS"
        )
        self.resource = resource
        self.user_id = user_id


class MessagePublishException(DomainException):
    """Raised when message publishing fails."""

    def __init__(self, queue: str, reason: str):
        super().__init__(
            message=f"Failed to publish message to queue '{queue}': {reason}",
            code="MESSAGE_PUBLISH_ERROR"
        )
        self.queue = queue
        self.reason = reason


class CacheOperationException(DomainException):
    """Raised when a cache operation fails."""

    def __init__(self, operation: str, key: str, reason: str):
        super().__init__(
            message=f"Cache {operation} failed for key '{key}': {reason}",
            code="CACHE_OPERATION_ERROR"
        )
        self.operation = operation
        self.key = key
        self.reason = reason
