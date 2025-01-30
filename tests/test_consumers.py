import pytest
from unittest.mock import patch, AsyncMock
from app.services.career_docs_consumer import career_docs_consumer
from app.services.application_manager_consumer import application_manager_consumer
from app.services.base_consumer import BaseConsumer

@pytest.mark.asyncio
@patch("app.services.database_consumer.database_consumer.retrieve_one_batch_from_db", new_callable=AsyncMock)
@patch("app.services.career_docs_publisher.career_docs_publisher.get_queue_size", new_callable=AsyncMock)
async def test_career_docs_consumer_process_message_failure(mock_get_size, mock_db):
    mock_get_size.return_value = 0
    mock_db.return_value = None
    with patch.object(career_docs_consumer, "_retrieve_content"), \
         patch.object(career_docs_consumer, "_update_career_docs_responses"), \
         patch.object(career_docs_consumer, "_remove_processed_entry"), \
         patch.object(career_docs_consumer, "_restore_sent_status", new_callable=AsyncMock) as mock_restore:
        msg = {"success": False, "applications": {}, "user_id": 123, "mongo_id": "abc"}
        await career_docs_consumer.process_message(msg)
        mock_restore.assert_awaited_once()

@pytest.mark.asyncio
@patch("app.services.database_consumer.database_consumer.retrieve_one_batch_from_db", new_callable=AsyncMock)
@patch("app.services.career_docs_publisher.career_docs_publisher.get_queue_size", new_callable=AsyncMock)
async def test_career_docs_consumer_process_message_success(mock_get_size, mock_db):
    mock_get_size.return_value = 0
    mock_db.return_value = None
    with patch.object(career_docs_consumer, "_retrieve_content", return_value={"app_1": {}}), \
         patch.object(career_docs_consumer, "_update_career_docs_responses", new_callable=AsyncMock), \
         patch.object(career_docs_consumer, "_remove_processed_entry", new_callable=AsyncMock) as mock_remove, \
         patch.object(career_docs_consumer, "_restore_sent_status", new_callable=AsyncMock) as mock_restore:
        msg = {"success": True, "applications": {}, "user_id": 123, "mongo_id": "abc"}
        await career_docs_consumer.process_message(msg)
        mock_remove.assert_awaited_once()
        mock_restore.assert_not_awaited()

@pytest.mark.asyncio
async def test_application_manager_consumer_process_message():
    with patch("app.services.application_manager_consumer.career_docs_publisher.refill_queue", new_callable=AsyncMock) as mock_refill:
        msg = {"some_key": "some_value"}
        await application_manager_consumer.process_message(msg)
        mock_refill.assert_awaited_once()

@pytest.mark.asyncio
async def test_consume_method():
    with patch.object(BaseConsumer, "_message_handler", new_callable=AsyncMock), \
         patch("app.services.base_consumer.rabbit_client.connect", new_callable=AsyncMock), \
         patch("app.services.base_consumer.rabbit_client.consume_messages", new_callable=AsyncMock) as mock_consume:
        class DummyConsumer(BaseConsumer):
            def get_queue_name(self):
                return "dummy_queue"
            async def process_message(self, message: dict):
                pass
        consumer = DummyConsumer()
        await consumer.consume()
        mock_consume.assert_awaited_once()