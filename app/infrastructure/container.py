"""
Dependency Injection Container.

Central configuration for dependency injection using a simple container pattern.
This follows the Composition Root pattern - all dependencies are wired up here.
"""
from typing import Optional
from dataclasses import dataclass, field
from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.domain.ports import (
    ApplicationRepository,
    UserApplicationsRepository,
    CachePort,
)
from app.infrastructure.repositories import (
    MongoApplicationRepository,
    MongoUserApplicationsRepository,
)
from app.infrastructure.cache import RedisCacheAdapter


@dataclass
class Container:
    """
    Dependency Injection Container.

    Holds all application dependencies and provides access to them.
    Uses lazy initialization for services.
    """

    # Core clients (set externally or via initialize())
    _mongo_client: Optional[AsyncIOMotorClient] = None
    _redis_cache: Optional[CachePort] = None

    # Repositories (lazily created)
    _application_repository: Optional[ApplicationRepository] = None
    _user_applications_repository: Optional[UserApplicationsRepository] = None

    def initialize(
        self,
        mongo_client: Optional[AsyncIOMotorClient] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
    ) -> None:
        """
        Initialize the container with external clients.

        Args:
            mongo_client: Pre-configured MongoDB client
            redis_host: Redis host (defaults to settings)
            redis_port: Redis port (defaults to settings)
        """
        if mongo_client:
            self._mongo_client = mongo_client

        # Initialize Redis cache
        self._redis_cache = RedisCacheAdapter(
            host=redis_host or settings.redis_host,
            port=redis_port or settings.redis_port,
        )

    def set_mongo_client(self, client: AsyncIOMotorClient) -> None:
        """Set the MongoDB client."""
        self._mongo_client = client
        # Reset repositories to use new client
        self._application_repository = None
        self._user_applications_repository = None

    # Repository Properties (Lazy Initialization)

    @property
    def application_repository(self) -> ApplicationRepository:
        """Get the Application Repository."""
        if self._application_repository is None:
            if self._mongo_client is None:
                raise RuntimeError(
                    "Container not initialized. Call initialize() first."
                )
            self._application_repository = MongoApplicationRepository(
                mongo_client=self._mongo_client,
            )
        return self._application_repository

    @property
    def user_applications_repository(self) -> UserApplicationsRepository:
        """Get the User Applications Repository."""
        if self._user_applications_repository is None:
            if self._mongo_client is None:
                raise RuntimeError(
                    "Container not initialized. Call initialize() first."
                )
            self._user_applications_repository = MongoUserApplicationsRepository(
                mongo_client=self._mongo_client,
            )
        return self._user_applications_repository

    @property
    def cache(self) -> CachePort:
        """Get the Cache service."""
        if self._redis_cache is None:
            self._redis_cache = RedisCacheAdapter(
                host=settings.redis_host,
                port=settings.redis_port,
            )
        return self._redis_cache

    # Factory Methods for creating new instances

    def create_application_repository(
        self,
        database_name: str = "resumes",
        collection_name: str = "jobs_to_apply_per_user",
    ) -> ApplicationRepository:
        """Create a new Application Repository with custom settings."""
        if self._mongo_client is None:
            raise RuntimeError("Container not initialized. Call initialize() first.")
        return MongoApplicationRepository(
            mongo_client=self._mongo_client,
            database_name=database_name,
            collection_name=collection_name,
        )

    def create_user_applications_repository(
        self,
        database_name: str = "resumes",
        collection_name: str = "career_docs_responses",
    ) -> UserApplicationsRepository:
        """Create a new User Applications Repository with custom settings."""
        if self._mongo_client is None:
            raise RuntimeError("Container not initialized. Call initialize() first.")
        return MongoUserApplicationsRepository(
            mongo_client=self._mongo_client,
            database_name=database_name,
            collection_name=collection_name,
        )


# Global container instance (singleton)
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.

    Returns:
        The singleton Container instance.
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None


# FastAPI Dependency Functions

async def get_application_repository() -> ApplicationRepository:
    """FastAPI dependency for ApplicationRepository."""
    return get_container().application_repository


async def get_user_applications_repository() -> UserApplicationsRepository:
    """FastAPI dependency for UserApplicationsRepository."""
    return get_container().user_applications_repository


async def get_cache() -> CachePort:
    """FastAPI dependency for CachePort."""
    return get_container().cache
