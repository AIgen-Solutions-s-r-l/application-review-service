import json
import aio_pika
import asyncio
from app.log.logging import logger
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

    async def connect(self, max_retries: int = 5, retry_delay: int = 5) -> None:
        """Establishes a connection to RabbitMQ with retry logic."""
        if self.connection and not self.connection.is_closed:
            return  # Connection is already open

        retries = 0
        while retries < max_retries:
            try:
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
                self.channel = await self.connection.channel()
                logger.info(
                    "RabbitMQ connection established",
                    event_type="rabbitmq_connection_established"
                )
                return
            except Exception as e:
                retries += 1
                logger.error(
                    "Failed to connect to RabbitMQ: {error}",
                    error=str(e),
                    event_type="rabbitmq_connection_failed"
                )
                if retries < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. RabbitMQ connection could not be established.")

    async def ensure_queue(self, queue_name: str, durable: bool = True) -> aio_pika.Queue:
        """Ensures that a queue exists."""
        await self.connect()
        try:
            queue = await self.channel.declare_queue(queue_name, durable=durable)
            logger.info(
                "Queue {queue_name} ensured (durability={durable})",
                queue_name=queue_name,
                durable=durable,
                event_type="queue_ensured"
            )
            return queue
        except Exception as e:
            logger.exception(
                "Failed to ensure queue {queue_name}: {error}",
                queue_name=queue_name,
                error=str(e),
                event_type="queue_ensure_failed",
                error_type=type(e).__name__,
                error_details=str(e)
            )
            raise

    async def publish_message(self, queue_name: str, message: dict, persistent: bool = True) -> None:
        """Publishes a message to the queue."""
        try:
            await self.connect()
            await self.ensure_queue(queue_name, durable=True)
            message_body = json.dumps(message).encode()
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else aio_pika.DeliveryMode.NOT_PERSISTENT,
                ),
                routing_key=queue_name,
            )
            logger.info(
                "Message published to queue {queue_name}",
                queue_name=queue_name,
                event_type="message_published"
            )
        except Exception as e:
            logger.exception(
                "Failed to publish message to queue {queue_name}: {error}",
                queue_name=queue_name,
                error=str(e),
                event_type="message_publish_failed"
            )
            raise

    async def consume_messages(
        self, queue_name: str, callback: Callable, auto_ack: bool = False
    ) -> None:
        """Consumes messages from the queue asynchronously."""
        while True:
            try:
                await self.connect()
                queue = await self.ensure_queue(queue_name, durable=True)
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        try:
                            await callback(message)
                            if auto_ack:
                                await message.ack()
                        except asyncio.CancelledError:
                            logger.error(
                                "Received CancelledError while processing message",
                                event_type="callback_error",
                            )
                            await message.nack(requeue=True)
                            logger.info(
                                "Message rejected and requeued with queue status with message",
                                event_type="message_rejected",
                            )
                            break
                        except Exception as e:
                            logger.exception(
                                "Error processing message: {error}",
                                error=str(e),
                                event_type="callback_error",
                            )
                            await message.nack(requeue=False)
            
            except Exception as e:
                logger.exception(
                    "Error consuming messages from queue {queue_name}: {error}",
                    queue_name=queue_name,
                    error=str(e),
                )
                await asyncio.sleep(5)  # Wait before reconnecting
                    
    async def close(self) -> None:
        """Closes the RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
                logger.info(
                    "RabbitMQ connection closed",
                    event_type="rabbitmq_connection_closed"
                )
            except Exception as e:
                logger.exception(
                    "Error while closing RabbitMQ connection: {error}",
                    error=str(e),
                    event_type="rabbitmq_connection_close_error",
                    error_type=type(e).__name__,
                    error_details=str(e)
                )

    async def get_queue_size(self, queue_name: str) -> int:
        try:
            queue = await self.channel.declare_queue(queue_name, passive=True)
            return queue.declaration_result.message_count
        except Exception as e:
            logger.info("Queue {queue_name} does not exist: {e}", queue_name=queue_name, e=str(e), event_type="queue_not_found")
            return 0  # Non-existent queue is an empty queue

rabbit_client = AsyncRabbitMQClient(rabbitmq_url=settings.rabbitmq_url)