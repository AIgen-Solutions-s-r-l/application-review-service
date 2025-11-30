"""
Correlation ID Value Object.

Immutable identifier used to correlate job applications across services.
"""
from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass(frozen=True)
class CorrelationId:
    """
    Value Object representing a unique correlation identifier.

    Used to track job applications across:
    - Redis cache (job data storage)
    - RabbitMQ messages (CareerDocs requests/responses)
    - MongoDB documents (application storage)
    """
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("CorrelationId cannot be empty")
        # Validate UUID format
        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError(f"Invalid CorrelationId format: {self.value}")

    @classmethod
    def generate(cls) -> "CorrelationId":
        """Generate a new unique CorrelationId."""
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> "CorrelationId":
        """Create CorrelationId from string."""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CorrelationId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
