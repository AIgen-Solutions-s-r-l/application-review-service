"""
Job Portal Value Object.

Represents the target job portal/ATS system for an application.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Set


class PortalType(str, Enum):
    """Known ATS/Portal types with native provider support."""
    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    SMARTRECRUITERS = "smartrecruiters"
    DICE = "dice"
    APPLYTOJOB = "applytojob"
    LEVER = "lever"
    WORKABLE = "workable"
    BAMBOOHR = "bamboohr"
    BREEZYHR = "breezyhr"
    INFOJOBS = "infojobs"
    INFOJOBS_NET = "infojobs_net"
    TOTALJOBS = "totaljobs"
    UNKNOWN = "unknown"


# Portals that have native provider integrations
NATIVE_PROVIDER_PORTALS: Set[str] = {
    PortalType.WORKDAY.value,
    PortalType.GREENHOUSE.value,
    PortalType.SMARTRECRUITERS.value,
    PortalType.DICE.value,
    PortalType.APPLYTOJOB.value,
    PortalType.LEVER.value,
    PortalType.WORKABLE.value,
    PortalType.BAMBOOHR.value,
    PortalType.BREEZYHR.value,
    PortalType.INFOJOBS.value,
    PortalType.INFOJOBS_NET.value,
    PortalType.TOTALJOBS.value,
}


@dataclass(frozen=True)
class JobPortal:
    """
    Value Object representing a job portal/ATS system.

    Encapsulates portal identification and routing logic.
    """
    name: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Portal name cannot be empty")

    @classmethod
    def from_string(cls, portal_name: str) -> "JobPortal":
        """Create JobPortal from string, normalizing to lowercase."""
        return cls(name=portal_name.lower().strip())

    @property
    def has_native_provider(self) -> bool:
        """Check if this portal has a native provider integration."""
        return self.name in NATIVE_PROVIDER_PORTALS

    @property
    def requires_browser_automation(self) -> bool:
        """Check if this portal requires Skyvern browser automation."""
        return not self.has_native_provider

    @property
    def portal_type(self) -> PortalType:
        """Get the PortalType enum value."""
        try:
            return PortalType(self.name)
        except ValueError:
            return PortalType.UNKNOWN

    def get_applier_queue(self) -> str:
        """Determine which applier queue should handle this portal."""
        if self.has_native_provider:
            return "providers_queue"
        return "skyvern_queue"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, JobPortal):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)
