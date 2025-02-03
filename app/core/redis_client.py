# app/core/redis_client.py
"""
Redis client module for handling Redis connections and operations.

This module provides a RedisClient class that encapsulates Redis functionality
with proper error handling and logging. It supports basic Redis operations
like connecting, getting/setting values, and managing the connection lifecycle.

Example:
    client = RedisClient(host='localhost', port=6379)
    client.connect()
    client.set('key', 'value')
    value = client.get('key')

Attributes:
    logger: The logger instance for this module
"""


from typing import Optional
import redis
from loguru import logger
from app.core.config import settings


class RedisClient:
    """
    A class to handle Redis connections and operations with strong error handling and logging.

    Attributes:
        host (str): The Redis server host.
        port (int): The Redis server port.
        db (int): The Redis database number.
        connection (Optional[redis.Redis]): The Redis connection object.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0) -> None:
        """
        Initializes the RedisClient with the specified host, port, and database.

        Args:
            host (str): The Redis server host. Defaults to 'localhost'.
            port (int): The Redis server port. Defaults to 6379.
            db (int): The Redis database number. Defaults to 0.
        """
        self.host = host
        self.port = port
        self.db = db
        self.connection: Optional[redis.Redis] = None

    def connect(self) -> None:
        """
        Establishes a connection to the Redis server.

        Logs an error if the connection fails.
        """
        try:
            self.connection = redis.Redis(
                host=self.host, port=self.port, db=self.db)
            # Test the connection
            self.connection.ping()
            logger.info("Connected to Redis successfully.")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connection = None

    def get(self, key: str) -> Optional[str]:
        """
        Retrieves a value from Redis by key.

        Args:
            key (str): The key to retrieve from Redis.

        Returns:
            Optional[str]: The value associated with the key, or None if not found or on error.
        """
        if not self.connection:
            logger.error("No Redis connection available.")
            return None
        try:
            value = self.connection.get(key)
            return value.decode('utf-8') if value else None
        except redis.RedisError as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None

    def set(self, key: str, value: str) -> bool:
        """
        Sets a value in Redis for a given key.

        Args:
            key (str): The key to set in Redis.
            value (str): The value to associate with the key.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if not self.connection:
            logger.error("No Redis connection available.")
            return False
        try:
            self.connection.set(key, value)
            logger.info(f"Key {key} set successfully.")
            return True
        except redis.RedisError as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False
        
    def delete(self, key: str) -> bool:
        """
        Deletes a key from Redis.

        Args:
            key (str): The key to delete from Redis.

        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        if not self.connection:
            logger.error("No Redis connection available.")
            return False
        try:
            result = self.connection.delete(key)
            if result == 1:
                logger.info(f"Key {key} deleted successfully.")
                return True
            else:
                logger.warning(f"Key {key} does not exist in Redis.")
                return False
        except redis.RedisError as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
        
    def is_connected(self) -> bool:
        """
        Checks if the Redis client is connected to the Redis server.

        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.connection:
            return False
        try:
            # Attempt to ping the Redis server
            self.connection.ping()
            return True
        except redis.RedisError as e:
            logger.error(f"Redis connection lost: {e}")
            self.connection = None
            return False

    def close(self) -> None:
        """
        Closes the Redis connection.

        Logs an error if closing the connection fails.
        """
        if self.connection:
            try:
                self.connection.close()
                logger.info("Redis connection closed.")
            except redis.RedisError as e:
                logger.error(f"Error closing Redis connection: {e}")


redis_client = RedisClient(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)
redis_client.connect()