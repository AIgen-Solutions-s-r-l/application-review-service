"""
Resume Entity.

Represents a candidate's resume/CV with personal information,
education, experience, and skills.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class PersonalInfo:
    """Personal information section of a resume."""
    name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    phone_prefix: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the full name of the candidate."""
        parts = [p for p in [self.name, self.surname] if p]
        return " ".join(parts)

    @property
    def full_phone(self) -> Optional[str]:
        """Get full phone number with prefix."""
        if self.phone:
            if self.phone_prefix:
                return f"{self.phone_prefix}{self.phone}"
            return str(self.phone)
        return None


@dataclass
class Resume:
    """
    Entity representing a candidate's resume.

    Contains all resume sections and provides methods for
    validation and modification.
    """
    personal_info: Optional[PersonalInfo] = None
    education_details: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    experience_details: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    projects: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    achievements: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    certifications: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    additional_skills: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Resume":
        """Create Resume from dictionary (e.g., from API or database)."""
        header = data.get("header", {})
        body = data.get("body", {})

        personal_info_data = header.get("personal_information", {})
        personal_info = PersonalInfo(
            name=personal_info_data.get("name"),
            surname=personal_info_data.get("surname"),
            date_of_birth=personal_info_data.get("date_of_birth"),
            country=personal_info_data.get("country"),
            city=personal_info_data.get("city"),
            address=personal_info_data.get("address"),
            zip_code=personal_info_data.get("zip_code"),
            phone_prefix=personal_info_data.get("phone_prefix"),
            phone=str(personal_info_data.get("phone", "")) if personal_info_data.get("phone") else None,
            email=personal_info_data.get("email"),
            github=str(personal_info_data.get("github", "")) if personal_info_data.get("github") else None,
            linkedin=str(personal_info_data.get("linkedin", "")) if personal_info_data.get("linkedin") else None,
        ) if personal_info_data else None

        return cls(
            personal_info=personal_info,
            education_details=body.get("education_details", {}),
            experience_details=body.get("experience_details", {}),
            projects=body.get("projects", {}),
            achievements=body.get("achievements", {}),
            certifications=body.get("certifications", {}),
            additional_skills=body.get("additional_skills"),
        )

    def to_dict(self) -> dict:
        """Convert Resume to dictionary for persistence."""
        header = {}
        if self.personal_info:
            header["personal_information"] = {
                "name": self.personal_info.name,
                "surname": self.personal_info.surname,
                "date_of_birth": self.personal_info.date_of_birth,
                "country": self.personal_info.country,
                "city": self.personal_info.city,
                "address": self.personal_info.address,
                "zip_code": self.personal_info.zip_code,
                "phone_prefix": self.personal_info.phone_prefix,
                "phone": self.personal_info.phone,
                "email": self.personal_info.email,
                "github": self.personal_info.github,
                "linkedin": self.personal_info.linkedin,
            }

        body = {
            "education_details": self.education_details,
            "experience_details": self.experience_details,
            "projects": self.projects,
            "achievements": self.achievements,
            "certifications": self.certifications,
            "additional_skills": self.additional_skills,
        }

        return {"header": header, "body": body}

    def update_personal_info(self, updates: Dict[str, Any]) -> "Resume":
        """Create a new Resume with updated personal information."""
        if not self.personal_info:
            self.personal_info = PersonalInfo()

        # Create new PersonalInfo with updates
        new_personal_info = PersonalInfo(
            name=updates.get("name", self.personal_info.name),
            surname=updates.get("surname", self.personal_info.surname),
            date_of_birth=updates.get("date_of_birth", self.personal_info.date_of_birth),
            country=updates.get("country", self.personal_info.country),
            city=updates.get("city", self.personal_info.city),
            address=updates.get("address", self.personal_info.address),
            zip_code=updates.get("zip_code", self.personal_info.zip_code),
            phone_prefix=updates.get("phone_prefix", self.personal_info.phone_prefix),
            phone=updates.get("phone", self.personal_info.phone),
            email=updates.get("email", self.personal_info.email),
            github=updates.get("github", self.personal_info.github),
            linkedin=updates.get("linkedin", self.personal_info.linkedin),
        )

        return Resume(
            personal_info=new_personal_info,
            education_details=self.education_details,
            experience_details=self.experience_details,
            projects=self.projects,
            achievements=self.achievements,
            certifications=self.certifications,
            additional_skills=self.additional_skills,
        )

    @property
    def has_contact_info(self) -> bool:
        """Check if resume has basic contact information."""
        if not self.personal_info:
            return False
        return bool(self.personal_info.email or self.personal_info.phone)

    @property
    def has_experience(self) -> bool:
        """Check if resume has any work experience."""
        return bool(self.experience_details)

    @property
    def has_education(self) -> bool:
        """Check if resume has education details."""
        return bool(self.education_details)
