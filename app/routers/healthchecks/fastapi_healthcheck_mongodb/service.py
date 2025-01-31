import logging
from app.routers.healthchecks.fastapi_healthcheck.service import HealthCheckBase
from app.routers.healthchecks.fastapi_healthcheck.enum import HealthCheckStatusEnum
from app.routers.healthchecks.fastapi_healthcheck.domain import HealthCheckInterface
from typing import List, Optional
from pymongo import AsyncMongoClient

logger = logging.getLogger(__name__)

class HealthCheckMongoDB(HealthCheckBase, HealthCheckInterface):
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
            client = AsyncMongoClient(self._connection_uri, serverSelectionTimeoutMS=5000)
            if await client.server_info():
                res = HealthCheckStatusEnum.HEALTHY
        except Exception as e:
            logger.error(f"Mongo health check failed: {e}")
        return res
