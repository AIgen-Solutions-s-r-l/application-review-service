from pydantic import BaseModel, EmailStr
from typing import Optional, List


class ApplicantDetails(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city_state_zip: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class CompanyDetails(BaseModel):
    name: Optional[str] = None


class CoverLetterHeader(BaseModel):
    applicant_details: Optional[ApplicantDetails] = None
    company_details: Optional[CompanyDetails] = None


class CoverLetterBody(BaseModel):
    greeting: Optional[str] = None
    opening_paragraph: Optional[str] = None
    body_paragraphs: Optional[List[str]] = None
    closing_paragraph: Optional[str] = None


class CoverLetterFooter(BaseModel):
    closing: Optional[str] = None
    signature: Optional[str] = None
    date: Optional[str] = None


class CoverLetter(BaseModel):
    header: Optional[CoverLetterHeader] = None
    body: Optional[CoverLetterBody] = None
    footer: Optional[CoverLetterFooter] = None
