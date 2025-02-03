from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class JobData(BaseModel):
    """
    Model for job details in a response.
    """
    id: Optional[int] = Field(None, description="The unique ID of the job record.")
    portal: Optional[str] = Field(None, description="The portal where the job was found.")
    title: Optional[str] = Field(None, description="The title of the job.")
    workplace_type: Optional[str] = Field(None, description="The workplace type, e.g., onsite, remote, or hybrid.")
    posted_date: Optional[str] = Field(None, description="The date the job was posted.")
    job_state: Optional[str] = Field(None, description="The state or status of the job.")
    description: Optional[str] = Field(None, description="A detailed description of the job.")
    apply_link: Optional[str] = Field(None, description="The link to apply for the job.")
    company_name: Optional[str] = Field(None, description="The name of the company offering the job.")
    location: Optional[str] = Field(None, description="The location of the job.")
    short_description: Optional[str] = Field(None, description="A short description of the job.")
    field: Optional[str] = Field(None, description="The field or industry of the job.")
    company_logo: Optional[str] = Field(None, description="The URL of the company logo.")
    experience: Optional[str] = Field(None, description="The required experience for the job.")
    skills_required: Optional[list[str]] = Field(None, description="The required skills for the job.")
    class Config:
        from_attributes = True