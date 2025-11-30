"""
Ports - Interfaces for external adapters.

Ports define the contracts that adapters must implement.
This allows the domain to remain independent of infrastructure concerns.

- Repository Ports: Define data access patterns
- Message Bus Ports: Define messaging patterns
- Cache Ports: Define caching patterns
"""
from app.domain.ports.repositories import (
    ApplicationRepository,
    UserApplicationsRepository,
)
from app.domain.ports.message_bus import (
    MessagePublisher,
    MessageConsumer,
)
from app.domain.ports.cache import CachePort

__all__ = [
    "ApplicationRepository",
    "UserApplicationsRepository",
    "MessagePublisher",
    "MessageConsumer",
    "CachePort",
]
