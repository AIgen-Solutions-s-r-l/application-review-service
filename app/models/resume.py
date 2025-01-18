from pydantic import BaseModel, EmailStr, AnyUrl, Field, field_serializer
from typing import Optional, List, Dict, Union
from pydantic_core import Url


class PersonalInformation(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = Field(None, max_length=10)
    phone_prefix: Optional[str] = None
    phone: Optional[Union[str, int]] = None
    email: Optional[EmailStr] = None
    github: Optional[Union[AnyUrl, str]] = None
    linkedin: Optional[Union[AnyUrl, str]] = None

    @field_serializer("github", "linkedin")
    def url2str(self, val) -> Optional[str]:
        if isinstance(val, Url):
            return str(val)
        return val


class RelevantModule(BaseModel):
    module: Optional[str] = None
    grade: Optional[str] = None


class ExamDetails(BaseModel):
    relevant_modules: Optional[List[RelevantModule]] = None


class EducationDetail(BaseModel):
    education_level: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    final_evaluation_grade: Optional[str] = None
    start_date: Optional[int] = None
    year_of_completion: Optional[int] = None
    exam: Optional[Dict[str, Union[float, int]]] = None


class ExperienceDetail(BaseModel):
    position: Optional[str] = None
    company: Optional[str] = None
    employment_period: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    key_responsibilities: Optional[List[str]] = None
    skills_acquired: Optional[List[str]] = None


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    link: Optional[Union[AnyUrl, str]] = None

    @field_serializer("link")
    def url2str(self, val) -> Optional[str]:
        if isinstance(val, Url):
            return str(val)
        return val


class Achievement(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Language(BaseModel):
    language: Optional[str] = None
    proficiency: Optional[str] = None


class Availability(BaseModel):
    notice_period: Optional[str] = None


class SalaryExpectations(BaseModel):
    salary_range_usd: Optional[str] = None


class SelfIdentification(BaseModel):
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    veteran: Optional[str] = None
    disability: Optional[str] = None
    ethnicity: Optional[str] = None


class WorkPreferences(BaseModel):
    remote_work: Optional[str] = None
    in_person_work: Optional[str] = None
    open_to_relocation: Optional[str] = None
    willing_to_complete_assessments: Optional[str] = None
    willing_to_undergo_drug_tests: Optional[str] = None
    willing_to_undergo_background_checks: Optional[str] = None


class LegalAuthorization(BaseModel):
    eu_work_authorization: Optional[str] = None
    us_work_authorization: Optional[str] = None
    requires_us_visa: Optional[str] = None
    legally_allowed_to_work_in_us: Optional[str] = None
    requires_us_sponsorship: Optional[str] = None
    requires_eu_visa: Optional[str] = None
    legally_allowed_to_work_in_eu: Optional[str] = None
    requires_eu_sponsorship: Optional[str] = None
    canada_work_authorization: Optional[str] = None
    requires_canada_visa: Optional[str] = None
    legally_allowed_to_work_in_canada: Optional[str] = None
    requires_canada_sponsorship: Optional[str] = None
    uk_work_authorization: Optional[str] = None
    requires_uk_visa: Optional[str] = None
    legally_allowed_to_work_in_uk: Optional[str] = None
    requires_uk_sponsorship: Optional[str] = None


class AdditionalSkills(BaseModel):
    additional_skills: Optional[List[str]] = None
    languages: Optional[List[Language]] = None


class SideProject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None


class ResumeBody(BaseModel):
    education_details: Optional[Dict[str, List[EducationDetail]]] = None
    experience_details: Optional[Dict[str, List[ExperienceDetail]]] = None
    side_projects: Optional[List[SideProject]] = None
    achievements: Optional[Dict[str, List[Achievement]]] = None
    certifications: Optional[Dict[str, List[Certification]]] = None
    additional_skills: Optional[AdditionalSkills] = None


class ResumeHeader(BaseModel):
    personal_information: Optional[PersonalInformation] = None


class Resume(BaseModel):
    header: Optional[ResumeHeader] = None
    body: Optional[ResumeBody] = None