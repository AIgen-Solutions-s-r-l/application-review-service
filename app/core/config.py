import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration class for environment variables and service settings.

    This class defines the settings for the application, including connections
    to external services like RabbitMQ and PostgreSQL. The settings are primarily
    loaded from environment variables, with default values provided for local development
    or testing environments.

    Attributes:
        rabbitmq_url (str): The connection URL for RabbitMQ.
            Default: "amqp://guest:guest@localhost:5672/"
            Example: "amqp://user:password@hostname:port/vhost"

        service_name (str): The name of the service.
            Default: "authService"
            Used for logging, monitoring, and other service identification purposes.

        database_url (str): The connection URL for the main PostgreSQL database.
            Default: "postgresql+asyncpg://user:password@localhost:5432/main_db"
            Example: "postgresql+asyncpg://username:password@hostname:port/dbname"

        test_database_url (str): The connection URL for the test PostgreSQL database.
            Default: "postgresql+asyncpg://user:password@localhost:5432/test_db"
            Used for testing purposes to isolate data changes and run tests against a dedicated
            test database. Automatically used when tests are run.

    Usage:
        The settings can be overridden by creating a `.env` file in the root directory
        with the necessary environment variables. Alternatively, environment variables
        can be set directly in the operating system.

        Example:
            .env file content:
            RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
            DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/main_db"
            TEST_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/test_db"
    """

    service_name: str = "applier_service"
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    career_docs_queue: str = "career_docs_queue"
    career_docs_response_queue: str = "career_docs_response_queue"
    mongodb: str = os.getenv("MONGODB", "mongodb://localhost:27017")

    model_config = SettingsConfigDict(env_file=".env")

    # Authentication settings
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30