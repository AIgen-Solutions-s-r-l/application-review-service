import logging
import aio_pika
from app.routers.healthchecks.fastapi_healthcheck.service import HealthCheckBase
from app.routers.healthchecks.fastapi_healthcheck.enum import HealthCheckStatusEnum
from app.routers.healthchecks.fastapi_healthcheck.domain import HealthCheckInterface
from typing import List, Optional

logger = logging.getLogger(__name__)


class HealthCheckRabbitMQ(HealthCheckBase, HealthCheckInterface):
    _connection_uri: str
    _message: str

    def __init__(
        self,
        connection_uri: str,
        alias: str,
        tags: Optional[List[str]] = None,
    ) -> None:
        self._connection_uri = connection_uri
        self._alias = alias
        self._tags = tags

    async def __checkHealth__(self) -> HealthCheckStatusEnum:
        res: HealthCheckStatusEnum = HealthCheckStatusEnum.UNHEALTHY
        try:
            connection = await aio_pika.connect_robust(self._connection_uri)
            if connection and not connection.is_closed:
                res = HealthCheckStatusEnum.HEALTHY
        except Exception as e:
            logger.error(f"Mongo health check failed: {e}")
        return res
