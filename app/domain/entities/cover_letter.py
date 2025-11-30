"""
Cover Letter Entity.

Represents a cover letter for a job application.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ApplicantDetails:
    """Applicant contact details for cover letter header."""
    name: Optional[str] = None
    address: Optional[str] = None
    city_state_zip: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None


@dataclass
class CompanyDetails:
    """Company details for cover letter header."""
    name: Optional[str] = None


@dataclass
class CoverLetter:
    """
    Entity representing a cover letter.

    Contains header (applicant/company details), body (letter content),
    and footer (closing/signature).
    """
    applicant_details: Optional[ApplicantDetails] = None
    company_details: Optional[CompanyDetails] = None
    greeting: Optional[str] = None
    opening_paragraph: Optional[str] = None
    body_paragraphs: Optional[List[str]] = None
    closing_paragraph: Optional[str] = None
    closing: Optional[str] = None
    signature: Optional[str] = None
    date: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CoverLetter":
        """Create CoverLetter from dictionary."""
        header = data.get("header", {})
        body = data.get("body", {})
        footer = data.get("footer", {})

        applicant_data = header.get("applicant_details", {})
        applicant_details = ApplicantDetails(
            name=applicant_data.get("name"),
            address=applicant_data.get("address"),
            city_state_zip=applicant_data.get("city_state_zip"),
            email=applicant_data.get("email"),
            phone_number=applicant_data.get("phone_number"),
        ) if applicant_data else None

        company_data = header.get("company_details", {})
        company_details = CompanyDetails(
            name=company_data.get("name"),
        ) if company_data else None

        return cls(
            applicant_details=applicant_details,
            company_details=company_details,
            greeting=body.get("greeting"),
            opening_paragraph=body.get("opening_paragraph"),
            body_paragraphs=body.get("body_paragraphs"),
            closing_paragraph=body.get("closing_paragraph"),
            closing=footer.get("closing"),
            signature=footer.get("signature"),
            date=footer.get("date"),
        )

    def to_dict(self) -> dict:
        """Convert CoverLetter to dictionary for persistence."""
        header = {}
        if self.applicant_details:
            header["applicant_details"] = {
                "name": self.applicant_details.name,
                "address": self.applicant_details.address,
                "city_state_zip": self.applicant_details.city_state_zip,
                "email": self.applicant_details.email,
                "phone_number": self.applicant_details.phone_number,
            }
        if self.company_details:
            header["company_details"] = {
                "name": self.company_details.name,
            }

        body = {
            "greeting": self.greeting,
            "opening_paragraph": self.opening_paragraph,
            "body_paragraphs": self.body_paragraphs,
            "closing_paragraph": self.closing_paragraph,
        }

        footer = {
            "closing": self.closing,
            "signature": self.signature,
            "date": self.date,
        }

        return {"header": header, "body": body, "footer": footer}

    def update_body(
        self,
        greeting: Optional[str] = None,
        opening_paragraph: Optional[str] = None,
        body_paragraphs: Optional[List[str]] = None,
        closing_paragraph: Optional[str] = None,
    ) -> "CoverLetter":
        """Create a new CoverLetter with updated body content."""
        return CoverLetter(
            applicant_details=self.applicant_details,
            company_details=self.company_details,
            greeting=greeting if greeting is not None else self.greeting,
            opening_paragraph=opening_paragraph if opening_paragraph is not None else self.opening_paragraph,
            body_paragraphs=body_paragraphs if body_paragraphs is not None else self.body_paragraphs,
            closing_paragraph=closing_paragraph if closing_paragraph is not None else self.closing_paragraph,
            closing=self.closing,
            signature=self.signature,
            date=self.date,
        )

    @property
    def is_complete(self) -> bool:
        """Check if cover letter has all essential sections."""
        return bool(
            self.greeting
            and self.opening_paragraph
            and self.body_paragraphs
            and self.closing_paragraph
        )

    @property
    def word_count(self) -> int:
        """Get approximate word count of the cover letter body."""
        total = 0
        if self.greeting:
            total += len(self.greeting.split())
        if self.opening_paragraph:
            total += len(self.opening_paragraph.split())
        if self.body_paragraphs:
            for para in self.body_paragraphs:
                total += len(para.split())
        if self.closing_paragraph:
            total += len(self.closing_paragraph.split())
        return total
