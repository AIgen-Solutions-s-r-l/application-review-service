# app/core/mongodb.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Load MongoDB settings
MONGO_DETAILS = settings.mongodb

# Create the MongoDB client
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.resumes

def get_mongo_client() -> AsyncIOMotorClient:
    """Return the MongoDB client instance."""
    return client