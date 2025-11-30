import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_publish_data_to_microservices_sends_to_all_appliers():
    """Test that publish_data_to_microservices sends data to all configured appliers."""
    from app.services.generic_publisher import GenericPublisher

    mock_rabbit_client = MagicMock()
    mock_rabbit_client.connect = AsyncMock()
    mock_rabbit_client.publish_message = AsyncMock()

    publisher = GenericPublisher()
    publisher.rabbitmq_client = mock_rabbit_client

    # Mock APPLIERS config
    mock_appliers = {
        'test_applier': {
            'queue_name': 'test_queue',
            'process_function': lambda x: x
        }
    }

    data = {
        "user_id": 123,
        "content": {
            "app1": {"title": "Job 1", "portal": "test"}
        }
    }

    with patch("app.services.generic_publisher.APPLIERS", mock_appliers):
        await publisher.publish_data_to_microservices(data)

    mock_rabbit_client.connect.assert_awaited()
    mock_rabbit_client.publish_message.assert_awaited()


@pytest.mark.asyncio
async def test_publish_data_skips_when_process_returns_none():
    """Test that publish_data_to_microservices skips when process_function returns None."""
    from app.services.generic_publisher import GenericPublisher

    mock_rabbit_client = MagicMock()
    mock_rabbit_client.connect = AsyncMock()
    mock_rabbit_client.publish_message = AsyncMock()

    publisher = GenericPublisher()
    publisher.rabbitmq_client = mock_rabbit_client

    # Mock APPLIERS config with process function that returns None
    mock_appliers = {
        'test_applier': {
            'queue_name': 'test_queue',
            'process_function': lambda x: None
        }
    }

    data = {
        "user_id": 123,
        "content": {
            "app1": {"title": "Job 1"}
        }
    }

    with patch("app.services.generic_publisher.APPLIERS", mock_appliers):
        await publisher.publish_data_to_microservices(data)

    # Should not publish when process_function returns None
    mock_rabbit_client.publish_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_data_sends_individual_applications():
    """Test that each application is sent as a separate message."""
    from app.services.generic_publisher import GenericPublisher

    mock_rabbit_client = MagicMock()
    mock_rabbit_client.connect = AsyncMock()
    mock_rabbit_client.publish_message = AsyncMock()

    publisher = GenericPublisher()
    publisher.rabbitmq_client = mock_rabbit_client

    mock_appliers = {
        'test_applier': {
            'queue_name': 'test_queue',
            'process_function': lambda x: x
        }
    }

    data = {
        "user_id": 123,
        "content": {
            "app1": {"title": "Job 1"},
            "app2": {"title": "Job 2"},
            "app3": {"title": "Job 3"}
        }
    }

    with patch("app.services.generic_publisher.APPLIERS", mock_appliers):
        await publisher.publish_data_to_microservices(data)

    # Should be called 3 times (once per application)
    assert mock_rabbit_client.publish_message.await_count == 3
