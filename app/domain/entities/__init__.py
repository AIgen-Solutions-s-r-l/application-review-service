"""
Entities - Domain objects with identity.

Entities are distinguished by their identity, rather than their attributes.
They have a lifecycle and can change over time while maintaining the same identity.
"""
from app.domain.entities.application import Application
from app.domain.entities.resume import Resume
from app.domain.entities.cover_letter import CoverLetter
from app.domain.entities.job import Job

__all__ = [
    "Application",
    "Resume",
    "CoverLetter",
    "Job",
]
