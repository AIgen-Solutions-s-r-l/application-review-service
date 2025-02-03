import logging
import redis
from app.routers.healthchecks.fastapi_healthcheck.service import HealthCheckBase
from app.routers.healthchecks.fastapi_healthcheck.enum import HealthCheckStatusEnum
from app.routers.healthchecks.fastapi_healthcheck.domain import HealthCheckInterface
from typing import List, Optional

logger = logging.getLogger(__name__)


class HealthCheckRedis(HealthCheckBase, HealthCheckInterface):
    _host: str
    _port: int
    _message: str

    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        alias: str,
        tags: Optional[List[str]] = None,
    ) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._alias = alias
        self._tags = tags

    async def __checkHealth__(self) -> HealthCheckStatusEnum:
        res: HealthCheckStatusEnum = HealthCheckStatusEnum.UNHEALTHY
        try:
            connection = redis.Redis(
                host=self._host, port=self._port, db=self._db)
            if connection.ping():
                res = HealthCheckStatusEnum.HEALTHY
        except Exception as e:
            logger.error(f"Mongo health check failed: {e}")
        return res
