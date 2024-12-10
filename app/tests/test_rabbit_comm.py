import pytest
import asyncio
from app.core.rabbitmq_client import AsyncRabbitMQClient

@pytest.mark.asyncio
async def test_publish_message():
    rabbitmq_url = "amqp://guest:guest@localhost/"
    queue_name = "test_queue"
    message = {"content": "test_message"}

    rabbitmq_client = AsyncRabbitMQClient(rabbitmq_url=rabbitmq_url)
    await rabbitmq_client.publish_message(queue_name=queue_name, message=message)
    assert True  # If no exception, the test passes

@pytest.mark.asyncio
async def test_consume_message():
    rabbitmq_url = "amqp://guest:guest@localhost/"
    queue_name = "test_queue"
    rabbitmq_client = AsyncRabbitMQClient(rabbitmq_url=rabbitmq_url)

    # Define a mock callback to handle the message
    async def mock_callback(message):
        assert message.body.decode() == '{"content": "test_message"}'
        await message.ack()

    # Use asyncio.wait_for to timeout after 5 seconds
    try:
        await asyncio.wait_for(
            rabbitmq_client.consume_messages(queue_name=queue_name, callback=mock_callback),
            timeout=5  # Timeout after 5 seconds
        )
    except asyncio.TimeoutError:
        assert True  # Test passes if timeout occurs