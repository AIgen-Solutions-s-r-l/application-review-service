from loguru import logger
from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient


class MessageSender:
    """
    MessageSender is responsible for managing a RabbitMQ client
    and providing methods to send messages to a specified queue.
    """

    def __init__(self) -> None:
        """
        Initializes the MessageSender instance with RabbitMQ URL from settings.
        """
        settings = Settings()
        self.rabbitmq_client = RabbitMQClient(rabbitmq_url=settings.rabbitmq_url)

    def send_message(self, queue: str, message: dict) -> None:
        """
        Sends a message to the specified queue in RabbitMQ.
        
        Parameters:
            queue (str): The name of the RabbitMQ queue where the message will be sent.
            message (dict): The content of the message to be sent as a dictionary.
        """
        try:
            self.rabbitmq_client.publish_message(queue, message)
            logger.info(f"Message sent to queue '{queue}': {message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def close_connection(self) -> None:
        """
        Closes the RabbitMQ connection by using the client.
        """
        self.rabbitmq_client.close()