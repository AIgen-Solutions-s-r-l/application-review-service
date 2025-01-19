from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.job import JobData

class ApplyContent(BaseModel):
    jobs: Dict[str, JobData]

class DetailedJobData(BaseModel):
    resume_optimized: Optional[Dict[str, Any]] = None
    cover_letter: Optional[Dict[str, Any]] = None