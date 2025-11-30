"""
Value Objects - Immutable domain primitives.

Value objects are defined by their attributes rather than identity.
They are immutable and equality is based on all attributes.
"""
from app.domain.value_objects.correlation_id import CorrelationId
from app.domain.value_objects.application_status import (
    ApplicationStatus,
    ApplicationStatusType,
)
from app.domain.value_objects.job_portal import (
    JobPortal,
    PortalType,
    NATIVE_PROVIDER_PORTALS,
)

__all__ = [
    "CorrelationId",
    "ApplicationStatus",
    "ApplicationStatusType",
    "JobPortal",
    "PortalType",
    "NATIVE_PROVIDER_PORTALS",
]
