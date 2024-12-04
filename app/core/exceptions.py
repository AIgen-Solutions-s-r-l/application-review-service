from fastapi import HTTPException, status

class MiddlewareApplierException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail={
            "error": self.__class__.__name__,
            "message": detail
        })


class ResumeNotFoundError(MiddlewareApplierException):
    """Raised when a resume is not found in the database."""

    def __init__(self, user_id: int):
        super().__init__(
            detail=f"Resume not found for user_id: {user_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class JobApplicationError(MiddlewareApplierException):
    """Raised when there is an error in the job application process."""

    def __init__(self, detail: str):
        super().__init__(
            detail=f"Job application error: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class DatabaseOperationError(MiddlewareApplierException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str):
        super().__init__(
            detail=f"Database operation failed: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class InvalidRequestError(MiddlewareApplierException):
    """Raised when an invalid request is received."""

    def __init__(self, detail: str):
        super().__init__(
            detail=f"Invalid request id: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST
        )