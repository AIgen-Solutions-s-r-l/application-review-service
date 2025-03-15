import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration class for environment variables and service settings!!!.
    """
    # Service settings
    service_name: str = os.getenv("SERVICE_NAME", "applier_service")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    syslog_host: str = os.getenv("SYSLOG_HOST", "172.17.0.1")
    syslog_port: int = int(os.getenv("SYSLOG_PORT", "5141"))
    json_logs: bool = os.getenv("JSON_LOGS", "True").lower() == "true"
    log_retention: str = os.getenv("LOG_RETENTION", "7 days")
    enable_logstash: bool = os.getenv("ENABLE_LOGSTASH", "True").lower() == "true"

    # MongoDB settings
    mongodb: str = os.getenv("MONGODB", "mongodb://localhost:27017")

    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = os.getenv("REDIS_PORT", 6379)
    redis_db: int = os.getenv("REDIS_DB", 0)
    redis_password: str = os.getenv("REDIS_PASSWORD", "")

    # RabbitMQ settings
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    career_docs_queue: str = os.getenv("CAREER_DOCS_QUEUE", "career_docs_queue")
    career_docs_response_queue: str = os.getenv("CAREER_DOCS_RESPONSE_QUEUE", "career_docs_response_queue")
    application_manager_queue: str = os.getenv("APPLICATION_MANAGER_QUEUE", "middleware_notification_queue")

    # Authentication settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Environment-specific logging configuration
    @property
    def logging_config(self) -> dict:
        """
        Returns logging configuration based on environment.
        """
        base_config = {
            "app_name": self.service_name,
            "log_level": self.log_level,
            "syslog_host": self.syslog_host if self.enable_logstash else None,
            "syslog_port": self.syslog_port if self.enable_logstash else None,
            "json_logs": self.json_logs,
            "enable_logstash": self.enable_logstash,
        }

        if self.environment == "development":
            base_config.update({
                "json_logs": False,
                "log_level": "DEBUG" if self.debug else "INFO"
            })

        return base_config

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()