import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId


@pytest.mark.asyncio
async def test_clean_from_db_deletes_document():
    """Test that clean_from_db deletes the correct document."""
    from app.services.database_writer import DatabaseWriter

    mock_collection = MagicMock()
    mock_collection.delete_one = AsyncMock()

    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.get_database.return_value = mock_db

    writer = DatabaseWriter()
    writer.mongo_client = mock_client

    test_id = "64cfc7f476071f6557215d57"
    await writer.clean_from_db(test_id)

    mock_collection.delete_one.assert_awaited_once()
    call_args = mock_collection.delete_one.call_args[0][0]
    assert call_args["_id"] == ObjectId(test_id)


@pytest.mark.asyncio
async def test_restore_sent_restores_when_retries_available():
    """Test that restore_sent sets sent=False when retries are available."""
    from app.services.database_writer import DatabaseWriter

    mock_result = MagicMock()
    mock_result.modified_count = 1

    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock(return_value=mock_result)

    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.get_database.return_value = mock_db

    writer = DatabaseWriter()
    writer.mongo_client = mock_client

    test_id = "64cfc7f476071f6557215d57"
    await writer.restore_sent(test_id)

    # Should only call once (for restore, not for marking failed)
    assert mock_collection.update_one.await_count == 1


@pytest.mark.asyncio
async def test_restore_sent_marks_failed_when_no_retries():
    """Test that restore_sent marks job as failed when no retries left."""
    from app.services.database_writer import DatabaseWriter

    # First call returns 0 (no retries left), second call marks as failed
    mock_result_no_match = MagicMock()
    mock_result_no_match.modified_count = 0

    mock_result_failed = MagicMock()
    mock_result_failed.modified_count = 1

    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock(
        side_effect=[mock_result_no_match, mock_result_failed]
    )

    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.get_database.return_value = mock_db

    writer = DatabaseWriter()
    writer.mongo_client = mock_client

    test_id = "64cfc7f476071f6557215d57"

    with patch("app.services.database_writer.logger") as mock_logger:
        await writer.restore_sent(test_id)

        # Should call twice: once for restore attempt, once for marking failed
        assert mock_collection.update_one.await_count == 2

        # Verify the second call sets status to failed
        second_call_args = mock_collection.update_one.call_args_list[1]
        update_query = second_call_args[0][1]
        assert update_query["$set"]["status"] == "failed"
        assert "failed_at" in update_query["$set"]

        # Verify error was logged
        mock_logger.error.assert_called_once()
