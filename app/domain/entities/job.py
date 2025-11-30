"""
Job Entity.

Represents a job posting that an application targets.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from app.domain.value_objects import JobPortal


@dataclass
class Job:
    """
    Entity representing a job posting.

    Jobs have identity (via id) and contain information about the position,
    company, and application requirements.
    """
    id: str
    portal: JobPortal
    title: str
    company_name: str
    apply_link: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    posted_date: Optional[str] = None
    job_state: Optional[str] = None
    field_of_work: Optional[str] = None
    company_logo: Optional[str] = None
    experience: Optional[str] = None
    skills_required: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Job ID cannot be empty")
        if not self.title:
            raise ValueError("Job title cannot be empty")
        if not self.company_name:
            raise ValueError("Company name cannot be empty")

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create Job from dictionary (e.g., from API response or database)."""
        portal_name = data.get("portal", "unknown")
        return cls(
            id=data.get("id", ""),
            portal=JobPortal.from_string(portal_name),
            title=data.get("title", ""),
            company_name=data.get("company_name", ""),
            apply_link=data.get("apply_link", ""),
            description=data.get("description"),
            short_description=data.get("short_description"),
            location=data.get("location"),
            workplace_type=data.get("workplace_type"),
            posted_date=data.get("posted_date"),
            job_state=data.get("job_state"),
            field_of_work=data.get("field"),
            company_logo=data.get("company_logo"),
            experience=data.get("experience"),
            skills_required=data.get("skills_required") or [],
        )

    def to_dict(self) -> dict:
        """Convert Job to dictionary for persistence."""
        return {
            "id": self.id,
            "portal": str(self.portal),
            "title": self.title,
            "company_name": self.company_name,
            "apply_link": self.apply_link,
            "description": self.description,
            "short_description": self.short_description,
            "location": self.location,
            "workplace_type": self.workplace_type,
            "posted_date": self.posted_date,
            "job_state": self.job_state,
            "field": self.field_of_work,
            "company_logo": self.company_logo,
            "experience": self.experience,
            "skills_required": self.skills_required,
        }

    @property
    def requires_browser_automation(self) -> bool:
        """Check if this job requires browser automation to apply."""
        return self.portal.requires_browser_automation

    @property
    def applier_queue(self) -> str:
        """Get the appropriate applier queue for this job."""
        return self.portal.get_applier_queue()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
