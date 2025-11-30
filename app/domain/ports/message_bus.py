"""
Message Bus Port Interfaces.

Define the contracts for message publishing and consuming.
Implementations will use RabbitMQ or other message brokers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Awaitable


class MessagePublisher(ABC):
    """
    Interface for publishing messages to queues.

    Implementations should handle serialization, routing,
    and delivery guarantees.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass

    @abstractmethod
    async def publish(
        self,
        queue_name: str,
        message: Dict[str, Any],
        correlation_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Publish a message to a queue.

        Args:
            queue_name: The target queue name
            message: The message payload (will be serialized)
            correlation_id: Optional correlation ID for tracking
            headers: Optional message headers

        Returns:
            True if published successfully, False otherwise
        """
        pass

    @abstractmethod
    async def publish_batch(
        self,
        queue_name: str,
        messages: list[Dict[str, Any]],
    ) -> int:
        """
        Publish multiple messages to a queue.

        Args:
            queue_name: The target queue name
            messages: List of message payloads

        Returns:
            Number of messages successfully published
        """
        pass


class MessageConsumer(ABC):
    """
    Interface for consuming messages from queues.

    Implementations should handle deserialization, acknowledgment,
    and error handling.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass

    @abstractmethod
    async def subscribe(
        self,
        queue_name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[bool]],
        prefetch_count: int = 1,
    ) -> None:
        """
        Subscribe to a queue with a message handler.

        Args:
            queue_name: The queue to consume from
            handler: Async function to process messages.
                    Should return True to ack, False to nack.
            prefetch_count: Number of messages to prefetch
        """
        pass

    @abstractmethod
    async def start_consuming(self) -> None:
        """Start consuming messages (blocking)."""
        pass

    @abstractmethod
    async def stop_consuming(self) -> None:
        """Stop consuming messages."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if consumer is connected."""
        pass
