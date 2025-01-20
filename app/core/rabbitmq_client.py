# app/core/async_rabbitmq_client.py

import json
import aio_pika
import asyncio
from loguru import logger
from typing import Callable, Optional
from app.core.config import settings

class AsyncRabbitMQClient:
    """
    An asynchronous RabbitMQ client using aio_pika.
    """

    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None

    async def connect(self) -> None:
        """Establishes a connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            return  # Connection is already open
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            logger.info("RabbitMQ connection established")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def ensure_queue(self, queue_name: str, durable: bool = False) -> aio_pika.Queue:
        """Ensures that a queue exists."""
        await self.connect()
        try:
            queue = await self.channel.declare_queue(queue_name, durable=durable)
            logger.info(f"Queue '{queue_name}' ensured (durability={durable})")
            return queue
        except Exception as e:
            logger.error(f"Failed to ensure queue '{queue_name}': {e}")
            raise

    async def publish_message(self, queue_name: str, message: dict, persistent: bool = False) -> None:
        """Publishes a message to the queue."""
        try:
            await self.connect()
            await self.ensure_queue(queue_name, durable=False)
            message_body = json.dumps(message).encode()
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else aio_pika.DeliveryMode.NOT_PERSISTENT,
                ),
                routing_key=queue_name,
            )
            logger.info(f"Message published to queue '{queue_name}': {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to queue '{queue_name}': {e}")
            raise

    async def consume_messages(self, queue_name: str, callback: Callable, auto_ack: bool = False) -> None:
        """Consumes messages from the queue asynchronously."""
        while True:
            try:
                await self.connect()
                queue = await self.ensure_queue(queue_name, durable=False)
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        await callback(message)
                        if auto_ack:
                            await message.ack()
            except Exception as e:
                logger.error(f"Error consuming messages from queue '{queue_name}': {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def close(self) -> None:
        """Closes the RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error while closing RabbitMQ connection: {e}")

    async def get_queue_size(self, queue_name: str) -> int:
        try:
            queue = await self.channel.declare_queue(queue_name, passive=True)
            return queue.declaration_result.message_count
        except aio_pika.exceptions.QueueNotFoundEntity as e:
            return 0 # non-existent queue is an empty queue

rabbit_client = AsyncRabbitMQClient(rabbitmq_url=settings.rabbitmq_url)