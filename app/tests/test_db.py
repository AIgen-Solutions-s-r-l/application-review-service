# applier_service/app/tests/test_db.py
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from httpx import AsyncClient, ASGITransport

# Database test setup
@pytest.fixture(scope="module")
async def db_client():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    client.close()

@pytest.mark.asyncio
async def test_insert_and_retrieve(db_client):
    async for client in db_client:
        db = client["test_db"]
        collection = db["test_collection"]
        
        sample_data = {"_id": 1, "name": "test"}
        await collection.insert_one(sample_data)
        
        retrieved_data = await collection.find_one({"_id": 1})
        assert retrieved_data["name"] == "test"
        
        await collection.delete_one({"_id": 1})  # Clean up