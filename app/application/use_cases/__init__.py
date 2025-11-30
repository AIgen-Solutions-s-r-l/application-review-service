"""
Use Cases - Application services implementing business operations.
"""
from app.application.use_cases.get_applications import (
    GetPendingApplicationsUseCase,
    GetSentApplicationsUseCase,
    GetApplicationDetailsUseCase,
)
from app.application.use_cases.update_application import (
    UpdateApplicationFieldUseCase,
    UpdateResumeUseCase,
    UpdateCoverLetterUseCase,
)
from app.application.use_cases.submit_applications import (
    SubmitAllApplicationsUseCase,
    SubmitSelectedApplicationsUseCase,
)

__all__ = [
    "GetPendingApplicationsUseCase",
    "GetSentApplicationsUseCase",
    "GetApplicationDetailsUseCase",
    "UpdateApplicationFieldUseCase",
    "UpdateResumeUseCase",
    "UpdateCoverLetterUseCase",
    "SubmitAllApplicationsUseCase",
    "SubmitSelectedApplicationsUseCase",
]
