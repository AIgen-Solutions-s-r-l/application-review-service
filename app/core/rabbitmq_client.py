import json
import pika
from loguru import logger
from typing import Optional, Callable


class RabbitMQClient:
    """
    A utility class for managing RabbitMQ connections, channels, and basic message operations.
    """

    def __init__(self, rabbitmq_url: str) -> None:
        """
        Initializes the RabbitMQClient with a connection URL.
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

    def connect(self) -> None:
        """
        Connects to RabbitMQ using the BlockingConnection and opens a channel.
        """
        if not self.connection or self.connection.is_closed:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")

    def ensure_queue(self, queue: str, durable: bool = False) -> None:
        """
        Declares a queue to ensure it exists.

        Parameters:
            queue (str): The queue name.
            durable (bool): If True, makes the queue durable.
        """
        if self.channel and self.channel.is_open:
            self.channel.queue_declare(queue=queue, durable=durable)
            logger.info(f"Queue '{queue}' ensured (declared with durability={durable})")

    def publish_message(self, queue: str, message: dict, persistent: bool = False) -> None:
        """
        Publishes a JSON-encoded message to the specified queue.

        Parameters:
            queue (str): The queue to which the message will be published.
            message (dict): The message content as a dictionary.
            persistent (bool): If True, makes the message persistent.
        """
        self.connect()
        # Set durable=False when ensuring the queue, to match the non-durable configuration
        self.ensure_queue(queue, durable=False)
        message_body = json.dumps(message)
        self.channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message_body,
            properties=pika.BasicProperties(delivery_mode=2 if persistent else 1)
        )
        logger.info(f"Message sent to queue '{queue}': {message}")

    def consume_messages(self, queue: str, callback: Callable, auto_ack: bool = True) -> None:
        """
        Sets up a consumer with the specified callback.

        Parameters:
            queue (str): The queue to consume messages from.
            callback (Callable): The callback function to process each message.
            auto_ack (bool): If True, enables automatic message acknowledgment.
        """
        self.connect()
        self.ensure_queue(queue, durable=False)  # Set durable=False for non-durable queues
        self.channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=auto_ack)
        logger.info(f"Started consuming messages from queue '{queue}'")
        self.channel.start_consuming()

    def close(self) -> None:
        """
        Closes the RabbitMQ connection if it is open.
        """
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")