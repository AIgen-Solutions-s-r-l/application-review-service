import json
import pika
from loguru import logger
from typing import Callable, Optional

class RabbitMQClient:
    """
    A robust RabbitMQ client with reconnection logic and improved error handling.
    """

    def __init__(self, rabbitmq_url: str) -> None:
        """Initializes the RabbitMQ client."""
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

    def connect(self) -> None:
        """Establishes a connection to RabbitMQ."""
        try:
            if not self.connection or self.connection.is_closed:
                parameters = pika.URLParameters(self.rabbitmq_url)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def ensure_queue(self, queue: str, durable: bool = True) -> None:
        """Ensures that a queue exists."""
        self.connect()
        try:
            self.channel.queue_declare(queue=queue, durable=durable)
            logger.info(f"Queue '{queue}' ensured (durability={durable})")
        except Exception as e:
            logger.error(f"Failed to ensure queue '{queue}': {e}")
            raise

    def publish_message(self, queue: str, message: dict, persistent: bool = True) -> None:
        """Publishes a message to the queue."""
        try:
            self.connect()
            self.ensure_queue(queue, durable=True)
            message_body = json.dumps(message)
            self.channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2 if persistent else 1),
            )
            logger.info(f"Message published to queue '{queue}': {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to queue '{queue}': {e}")
            raise

    def consume_messages(self, queue: str, callback: Callable, auto_ack: bool = True) -> None:
        """Consumes messages from the queue with enhanced error handling."""
        while True:  # Infinite loop to ensure reconnection
            try:
                self.connect()
                self.ensure_queue(queue, durable=False)
                self.channel.basic_consume(
                    queue=queue,
                    on_message_callback=callback,
                    auto_ack=auto_ack,
                )
                logger.info(f"Started consuming messages from queue '{queue}'")
                self.channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker as e:
                logger.error(f"Connection closed by broker: {e}")
                self.connect()
            except pika.exceptions.AMQPChannelError as e:
                logger.error(f"AMQP channel error: {e}")
                self.close()
                break  # Exit on unrecoverable errors
            except Exception as e:
                logger.error(f"Error consuming messages from queue '{queue}': {e}")
                break  # Exit on unrecoverable errors


    def close(self) -> None:
        """Closes the RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error while closing RabbitMQ connection: {e}")
