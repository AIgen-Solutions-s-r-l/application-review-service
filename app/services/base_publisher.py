from abc import ABC, abstractmethod
from app.core.rabbitmq_client import AsyncRabbitMQClient
from app.core.config import Settings


class BasePublisher(ABC):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.rabbitmq_client = AsyncRabbitMQClient(settings.rabbitmq_url)
        self.queue_name = self.get_queue_name()

    @abstractmethod
    def get_queue_name(self) -> str:
        """Return the RabbitMQ queue name."""
        pass

    async def publish(self, message: dict, persistent: bool = False) -> None:
        """Publishes the message on the queue"""
        await self.rabbitmq_client.connect()
        await self.rabbitmq_client.publish_message(self.queue_name, message, persistent)
