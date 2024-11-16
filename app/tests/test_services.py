import logging
import pytest
from unittest.mock import call
from motor.motor_asyncio import AsyncIOMotorClient  # Import AsyncIOMotorClient
from app.services.applier import consume_jobs_interleaved

# Define MockCursor to mock MongoDB cursor behavior
class MockCursor:
    async def to_list(self, length=None):
        # Sample job data to return
        return [
            {"_id": "1", "user_id": "user1", "jobs": [{"job_id": "job1"}, {"job_id": "job2"}]},
            {"_id": "2", "user_id": "user2", "jobs": [{"job_id": "job3"}]},
        ]

@pytest.mark.asyncio
async def test_consume_jobs_interleaved(mocker):
    # Configure logging
    logger = logging.getLogger("test_consume_jobs_interleaved")
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting test_consume_jobs_interleaved")

    # Mock the MongoDB client, database, and collection
    mock_mongo_client = mocker.Mock(spec=AsyncIOMotorClient)
    mock_db = mocker.Mock()
    mock_collection = mocker.Mock()

    # Use get_database and get_collection instead of subscripting
    mock_mongo_client.get_database.return_value = mock_db
    mock_db.get_collection.return_value = mock_collection

    # Set `find` to return an instance of MockCursor
    mock_collection.find.return_value = MockCursor()

    # Mock `notify_career_docs` and `process_job` as AsyncMock
    mock_notify = mocker.patch("app.services.applier.notify_career_docs", new_callable=mocker.AsyncMock)
    mock_process_job = mocker.patch("app.services.applier.process_job", new_callable=mocker.AsyncMock)

    # Mock `delete_one` to ensure it behaves as expected in the loop
    mock_collection.delete_one = mocker.AsyncMock()

    # Execute the function
    await consume_jobs_interleaved(mock_mongo_client)
    logger.info("consume_jobs_interleaved executed")

    # Verify `notify_career_docs` calls with detailed logging
    notify_calls = [(call.args[0], call.args[1]) for call in mock_notify.call_args_list]
    logger.info(f"notify_career_docs calls: {notify_calls}")

    # Verify the calls without requiring a specific order
    expected_calls = {("user1", "job1"), ("user1", "job2"), ("user2", "job3")}
    assert set(notify_calls) == expected_calls, f"Expected calls: {expected_calls}, but got: {notify_calls}"