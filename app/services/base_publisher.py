from abc import ABC, abstractmethod
from app.core.rabbitmq_client import rabbit_client


class BasePublisher(ABC):
    def __init__(self):
        self.rabbitmq_client = rabbit_client
        self.queue_name = self.get_queue_name()

    @abstractmethod
    def get_queue_name(self) -> str:
        """Return the RabbitMQ queue name."""
        pass

    async def publish(self, message: dict, persistent: bool = False) -> None:
        """Publishes the message on the queue"""
        await self.rabbitmq_client.connect()
        await self.rabbitmq_client.publish_message(self.queue_name, message, persistent)

    async def get_queue_size(self) -> int:
        await self.rabbitmq_client.connect()
        queue_size = await self.rabbitmq_client.get_queue_size(self.queue_name)
        return queue_size
            
