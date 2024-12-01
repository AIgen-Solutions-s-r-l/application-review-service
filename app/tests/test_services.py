import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.applier import consume_jobs

#TODO: For now: hanging (infinite loop) in consume_jobs function
@pytest.mark.asyncio
async def test_consume_jobs(mocker):
    # Mock MongoDB client
    mock_mongo_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = AsyncMock()
    mock_mongo_client.get_database.return_value = mock_db
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value = mock_cursor
    mock_cursor.to_list.return_value = [
        {"user_id": "user1", "resume": {}, "jobs": '{"jobs": [{"job_id": "job1"}, {"job_id": "job2"}]}'},
        {"user_id": "user2", "resume": {}, "jobs": '{"jobs": [{"job_id": "job3"}]}'}
    ]
    
    # Mock RabbitMQ client
    mock_rabbitmq_client = MagicMock()
    mock_rabbitmq_client.publish_message = AsyncMock()
    
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.career_docs_queue = "career_docs_queue"
    
    # Run the function
    await consume_jobs(mock_mongo_client, mock_rabbitmq_client, mock_settings)
    
    # Verify RabbitMQ publish calls
    expected_calls = [
        mocker.call(queue_name="career_docs_queue", message={"user_id": "user1", "resume": {}, "jobs": [{"job_id": "job1"}, {"job_id": "job2"}]}),
        mocker.call(queue_name="career_docs_queue", message={"user_id": "user2", "resume": {}, "jobs": [{"job_id": "job3"}]})
    ]
    mock_rabbitmq_client.publish_message.assert_has_calls(expected_calls, any_order=True)