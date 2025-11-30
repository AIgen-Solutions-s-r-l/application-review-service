"""
Redis Cache Adapter Implementation.

Implements the CachePort interface using Redis.
"""
from typing import Optional

import redis.asyncio as redis

from app.domain.ports.cache import CachePort
from app.log.logging import logger


class RedisCacheAdapter(CachePort):
    """
    Redis implementation of the CachePort interface.

    Provides async caching operations using redis.asyncio.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._connection: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self._connection = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=False,
            )
            await self._connection.ping()
            logger.info(
                f"Connected to Redis at {self._host}:{self._port}",
                event_type="REDIS_CONNECTED",
            )
        except redis.ConnectionError as e:
            logger.error(
                f"Failed to connect to Redis: {e}",
                event_type="REDIS_CONNECTION_ERROR",
            )
            self._connection = None

    async def disconnect(self) -> None:
        """Close connection to Redis."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Disconnected from Redis", event_type="REDIS_DISCONNECTED")

    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        if not self._connection:
            await self.connect()
        if not self._connection:
            return None

        try:
            value = await self._connection.get(key)
            if value:
                return value.decode("utf-8")
            return None
        except Exception as e:
            logger.exception(
                f"Error getting key {key} from Redis: {e}",
                event_type="REDIS_GET_ERROR",
            )
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Set a value in cache."""
        if not self._connection:
            await self.connect()
        if not self._connection:
            return False

        try:
            if ttl_seconds:
                await self._connection.setex(key, ttl_seconds, value)
            else:
                await self._connection.set(key, value)
            return True
        except Exception as e:
            logger.exception(
                f"Error setting key {key} in Redis: {e}",
                event_type="REDIS_SET_ERROR",
            )
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self._connection:
            await self.connect()
        if not self._connection:
            return False

        try:
            result = await self._connection.delete(key)
            return result > 0
        except Exception as e:
            logger.exception(
                f"Error deleting key {key} from Redis: {e}",
                event_type="REDIS_DELETE_ERROR",
            )
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self._connection:
            await self.connect()
        if not self._connection:
            return False

        try:
            result = await self._connection.exists(key)
            return result > 0
        except Exception as e:
            logger.exception(
                f"Error checking existence of key {key}: {e}",
                event_type="REDIS_EXISTS_ERROR",
            )
            return False

    async def is_connected(self) -> bool:
        """Check if cache is connected."""
        if not self._connection:
            return False
        try:
            await self._connection.ping()
            return True
        except Exception:
            return False
