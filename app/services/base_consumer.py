import json
from abc import ABC, abstractmethod
from aio_pika import IncomingMessage
from app.core.rabbitmq_client import rabbit_client


class BaseConsumer(ABC):
    def __init__(self):
        self.rabbitmq_client = rabbit_client
        self.queue_name = self.get_queue_name()

    @abstractmethod
    def get_queue_name(self) -> str:
        """Return the RabbitMQ queue name."""
        pass

    @abstractmethod
    async def process_message(self, message: dict) -> None:
        """Process the received message."""
        pass

    async def consume(self):
        """Consume messages from the queue."""
        await self.rabbitmq_client.connect()
        await self.rabbitmq_client.consume_messages(self.queue_name, self._message_handler, True)

    async def _message_handler(self, message: IncomingMessage):
        """Handle incoming RabbitMQ messages."""
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await self.process_message(data)
            except Exception as e:
                print(f"Failed to process message: {e}")

    async def start(self):
        """Start the applier service."""
        print(f"Starting {self.queue_name} consumer...")
        await self.consume()