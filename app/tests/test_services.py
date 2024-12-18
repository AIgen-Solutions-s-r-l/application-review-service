import asyncio
import json
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.applier import notify_career_docs, consume_jobs

@pytest.mark.asyncio
async def test_notify_career_docs(mock_rabbitmq_client):
    """
    Test the notify_career_docs function with mocked dependencies.
    """
    mock_settings = MagicMock()
    mock_settings.career_docs_queue = "career_docs"

    user_id = "123"
    jobs = [{"title": "Engineer", "description": "Engineering job", "portal": "Job Portal"}]

    # Call the function
    await notify_career_docs(user_id, jobs, mock_rabbitmq_client, mock_settings)

    # Assert that RabbitMQ was called correctly
    mock_rabbitmq_client.publish_message.assert_called_once_with(
        queue_name="career_docs",
        message={"user_id": user_id, "jobs": jobs},
    )
    
'''@pytest.mark.asyncio
async def test_consume_jobs(caplog):
    caplog.set_level(logging.DEBUG)

    # Mock MongoDB and its methods
    mock_mongo_client = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = AsyncMock()

    # Ensure the document structure matches what `consume_jobs` expects
    mock_cursor.to_list.return_value = [
        {
            "user_id": "123",
            "jobs": json.dumps({"jobs": [{"title": "Engineer", "description": "Engineering job", "portal": "Job Portal"}]}),
        }
    ]
    mock_collection.find.return_value = mock_cursor
    mock_mongo_client.get_database.return_value.get_collection.return_value = mock_collection

    # Mock RabbitMQ and settings
    mock_rabbitmq_client = AsyncMock()
    mock_settings = MagicMock()

    # Mock `notify_career_docs`
    with patch("app.services.applier.notify_career_docs", new_callable=AsyncMock) as mock_notify:
        mock_notify.return_value = None

        # Patch `asyncio.sleep` to prevent delay
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # Run the task
            task = asyncio.create_task(
                consume_jobs(mock_mongo_client, mock_rabbitmq_client, mock_settings)
            )

            # Let it process briefly
            await asyncio.sleep(0.1)

            # Cancel the task after confirming it runs
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    # Output all logs for debugging purposes
    print("\nCaptured Logs:")
    for record in caplog.records:
        print(f"{record.levelname}: {record.message}")

    # Ensure `notify_career_docs` was called
    try:
        mock_notify.assert_awaited_once()
    except AssertionError as e:
        print("\nAssertion Error: `notify_career_docs` was not called.")
        raise e
'''