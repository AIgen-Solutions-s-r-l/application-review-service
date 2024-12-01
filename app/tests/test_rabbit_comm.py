import pytest
from app.core.rabbitmq_client import AsyncRabbitMQClient
from aio_pika import connect_robust
import asyncio

@pytest.mark.asyncio
async def test_publish_message():
    rabbitmq_url = "amqp://guest:guest@localhost/"
    queue_name = "test_queue"
    message = {"content": "test_message"}
    
    # Initialize AsyncRabbitMQClient
    rabbitmq_client = AsyncRabbitMQClient(rabbitmq_url=rabbitmq_url)
    
    # Publish a test message
    await rabbitmq_client.publish_message(queue_name=queue_name, message=message)
    
    # Verify the message in RabbitMQ
    connection = await connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name)
        async with queue.iterator() as queue_iter:
            async for msg in queue_iter:
                assert msg.body.decode() == '{"content": "test_message"}'
                await msg.ack()
                break