"""
Repository Port Interfaces.

Define the contracts for data persistence operations.
Implementations will be provided by infrastructure adapters.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.domain.entities import Application


class ApplicationRepository(ABC):
    """
    Repository interface for Application aggregate persistence.

    Implementations should handle the mapping between domain entities
    and the underlying storage mechanism.
    """

    @abstractmethod
    async def get_by_id(self, application_id: str, user_id: str) -> Optional[Application]:
        """
        Retrieve an application by its ID.

        Args:
            application_id: The unique application identifier
            user_id: The user ID (for access control)

        Returns:
            The Application if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_correlation_id(self, correlation_id: str) -> Optional[Application]:
        """
        Retrieve an application by its correlation ID.

        Args:
            correlation_id: The correlation identifier

        Returns:
            The Application if found, None otherwise
        """
        pass

    @abstractmethod
    async def save(self, application: Application) -> str:
        """
        Persist an application (create or update).

        Args:
            application: The application to save

        Returns:
            The application ID
        """
        pass

    @abstractmethod
    async def delete(self, application_id: str, user_id: str) -> bool:
        """
        Delete an application.

        Args:
            application_id: The application ID
            user_id: The user ID (for access control)

        Returns:
            True if deleted, False if not found
        """
        pass


class UserApplicationsRepository(ABC):
    """
    Repository interface for user-scoped application operations.

    Handles operations on the user's application collection.
    """

    @abstractmethod
    async def get_pending_applications(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Application]:
        """
        Get all pending applications for a user.

        Args:
            user_id: The user identifier
            limit: Optional limit on number of results

        Returns:
            List of pending applications
        """
        pass

    @abstractmethod
    async def get_sent_applications(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Application]:
        """
        Get all sent/processing applications for a user.

        Args:
            user_id: The user identifier
            limit: Optional limit on number of results

        Returns:
            List of sent applications
        """
        pass

    @abstractmethod
    async def get_application_by_id(
        self, user_id: str, application_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific application by ID.

        Args:
            user_id: The user identifier
            application_id: The application identifier

        Returns:
            Application data dict if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_application_field(
        self, user_id: str, application_id: str, field_path: str, value: Any
    ) -> bool:
        """
        Update a specific field in an application.

        Args:
            user_id: The user identifier
            application_id: The application identifier
            field_path: Dot-notation path to the field
            value: The new value

        Returns:
            True if updated, False otherwise
        """
        pass

    @abstractmethod
    async def mark_applications_as_sent(
        self, user_id: str, application_ids: List[str]
    ) -> int:
        """
        Mark multiple applications as sent.

        Args:
            user_id: The user identifier
            application_ids: List of application IDs to mark

        Returns:
            Number of applications marked
        """
        pass

    @abstractmethod
    async def create_or_update_user_document(
        self, user_id: str, application_data: Dict[str, Any]
    ) -> str:
        """
        Create or update a user's application document.

        Args:
            user_id: The user identifier
            application_data: The application data to store

        Returns:
            The document ID
        """
        pass

    @abstractmethod
    async def count_pending(self, user_id: str) -> int:
        """
        Count pending applications for a user.

        Args:
            user_id: The user identifier

        Returns:
            Number of pending applications
        """
        pass

    @abstractmethod
    async def get_user_document(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the entire user document.

        Args:
            user_id: The user identifier

        Returns:
            The user document if found, None otherwise
        """
        pass
