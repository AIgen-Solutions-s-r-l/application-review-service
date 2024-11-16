# applier_service/app/tests/test_rabbitmq_communication.py
import pytest
import aio_pika
from app.core.rabbitmq_client import RabbitMQClient

@pytest.mark.asyncio
async def test_publish_message():
    rabbitmq_url = "amqp://guest:guest@localhost/"
    queue_name = "test_queue"
    
    # Initialize RabbitMQClient without the queue argument
    rabbitmq_client = RabbitMQClient(rabbitmq_url=rabbitmq_url)
    message = {"content": "test_message"}
    
    # Publish a test message, specifying the queue here
    rabbitmq_client.publish_message(queue=queue_name, message=message)
    
    # Verify the message in RabbitMQ without auto_delete
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    assert message.body.decode() == '{"content": "test_message"}'
                    break