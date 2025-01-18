from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.job import JobData

class JobApplicationRequest(BaseModel):
    """
    Request model for receiving the job application data.
    """
    jobs: list[JobData] = Field(
        ..., description="List of jobs to apply to, each represented as a JobItem."
    )

class DetailedJobData(BaseModel):
    resume_optimized: Optional[Dict[str, Any]] = None
    cover_letter: Optional[Dict[str, Any]] = None