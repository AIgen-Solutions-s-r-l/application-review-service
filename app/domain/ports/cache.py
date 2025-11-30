"""
Cache Port Interface.

Define the contract for caching operations.
Implementations will use Redis or other cache backends.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any
import json


class CachePort(ABC):
    """
    Interface for cache operations.

    Implementations should handle serialization, TTL management,
    and connection pooling.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the cache backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the cache backend."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from cache.

        Args:
            key: The cache key

        Returns:
            The cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl_seconds: Optional time-to-live in seconds

        Returns:
            True if set successfully
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: The cache key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: The cache key

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if cache is connected."""
        pass

    # Convenience methods for JSON serialization

    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get a JSON value from cache.

        Args:
            key: The cache key

        Returns:
            The deserialized value if found, None otherwise
        """
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set a JSON value in cache.

        Args:
            key: The cache key
            value: The value to cache (will be JSON serialized)
            ttl_seconds: Optional time-to-live in seconds

        Returns:
            True if set successfully
        """
        serialized = json.dumps(value)
        return await self.set(key, serialized, ttl_seconds)
