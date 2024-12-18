import pytest
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture(scope="module")
async def db_client():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    try:
        yield client  # Yield the client instance
    finally:
        client.close()

@pytest.mark.asyncio
async def test_document_deletion(db_client):
    async for client in db_client:
        db = client.get_database("test_db")
        collection = db.get_collection("test_collection")
        await collection.insert_one({"user_id": "123", "data": "test"})
        delete_result = await collection.delete_one({"user_id": "123"})
        assert delete_result.deleted_count == 1
