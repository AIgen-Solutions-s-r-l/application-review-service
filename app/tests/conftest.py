import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from app.core.rabbitmq_client import AsyncRabbitMQClient
from app.core.redis_client import RedisClient

@pytest.fixture
def mock_rabbitmq_client():
    """
    Mock RabbitMQ client for testing RabbitMQ operations.
    """
    # Create an AsyncMock with the same interface as AsyncRabbitMQClient
    client = AsyncMock(spec=AsyncRabbitMQClient)
    # Ensure the publish_message method is mocked
    client.publish_message = AsyncMock(return_value=None)
    return client


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


@pytest.fixture(scope="session", autouse=True)
def cleanup_event_loop():
    """
    Cleanup all pending tasks and close the event loop at the end of the session.
    """
    yield
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
        loop.close()
    except RuntimeError:
        pass  # Skip if no event loop exists
