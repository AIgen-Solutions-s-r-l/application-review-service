from unittest.mock import MagicMock
import pytest

from app.core.redis_client import RedisClient

@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for testing Redis operations.
    """
    client = MagicMock(spec=RedisClient)
    client.connect.return_value = True
    client.is_connected.return_value = True
    client.set.return_value = True
    client.get.return_value = '{"key": "value"}'
    client.delete.return_value = True
    yield client
    client.close()


@pytest.mark.asyncio
async def test_redis_operations(mock_redis_client):
    """
    Test basic Redis operations: connect, set, get, and delete.
    """
    # Test connection
    assert mock_redis_client.connect() is True
    assert mock_redis_client.is_connected() is True

    # Test set operation
    key = "test_key"
    value = '{"key": "value"}'
    assert mock_redis_client.set(key, value) is True

    # Test get operation
    retrieved_value = mock_redis_client.get(key)
    assert retrieved_value == value

    # Test delete operation
    assert mock_redis_client.delete(key) is True