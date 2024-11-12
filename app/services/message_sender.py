import pika
from loguru import logger
from app.core.config import Settings

settings = Settings()


class MessageSender:
    """
    MessageSender is responsible for managing a connection to RabbitMQ
    and providing methods to send messages to a specified queue.
    """

    def __init__(self) -> None:
        """
        Initializes the MessageSender instance with RabbitMQ URL from settings.
        Sets up placeholders for the connection and channel to RabbitMQ.
        """
        self.rabbitmq_url: str = settings.rabbitmq_url
        self.connection: pika.BlockingConnection | None = None
        self.channel: pika.adapters.blocking_connection.BlockingChannel | None = None

    def connect(self) -> None:
        """
        Connects to RabbitMQ using the provided URL and opens a channel.
        If the connection is successful, the channel is stored for sending messages.

        Raises:
            Exception: If there is an error during connection setup.
        """
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def send_message(self, queue: str, message: str) -> None:
        """
        Sends a message to the specified queue in RabbitMQ.
        If a connection does not exist, it establishes one.

        Parameters:
            queue (str): The name of the RabbitMQ queue where the message will be sent.
            message (str): The content of the message to be sent.

        Raises:
            Exception: If there is an error during message publishing.
        """
        if not self.connection or not self.channel:
            self.connect()

        try:
            # Declare the queue to ensure it exists
            self.channel.queue_declare(queue=queue, durable=True)
            # Publish the message to the specified queue with persistence
            self.channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            logger.info(f"Message sent to queue '{queue}': {message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def close_connection(self) -> None:
        """
        Closes the connection to RabbitMQ if it is open.
        This should be called when the instance is no longer needed.

        Returns:
            None
        """
        if self.connection:
            self.connection.close()
            logger.info("Connection to RabbitMQ closed")
