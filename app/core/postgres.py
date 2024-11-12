# app/core/database.py

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import Settings
from app.models.user import User

# Set up logger
logger = logging.getLogger(__name__)

# Load settings from the configuration file
settings = Settings()

# Determine the database URL based on the environment
# Use test_database_url if the `PYTEST_RUNNING` environment variable is set
database_url = settings.test_database_url if os.getenv("PYTEST_RUNNING") == "true" else settings.database_url
logger.info(f"Using database URL: {database_url}")

# Create the asynchronous engine for connecting to the PostgreSQL database
engine = create_async_engine(database_url, echo=True)

# Define the base class for ORM models
Base = declarative_base()

# Define an asynchronous session factory bound to the engine
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False  # Prevents objects from expiring after each commit
)

async def get_db():
    """
    Dependency to obtain a new database session for each request.

    `get_db` is an asynchronous function that provides a new database session
    using the `AsyncSessionLocal` factory, which is automatically closed after use.

    Yields:
        AsyncSession: An asynchronous database session for interacting with the database.
    """
    async with AsyncSessionLocal() as session:
        yield session