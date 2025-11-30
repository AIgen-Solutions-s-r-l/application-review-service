import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_start_calls_refill_queue():
    """Test that start() calls refill_queue on the publisher."""
    from app.services.timed_queue_refiller import TimedQueueRefiller

    mock_publisher = MagicMock()
    mock_publisher.refill_queue = AsyncMock()

    refiller = TimedQueueRefiller()
    refiller.career_docs_publisher = mock_publisher

    # Run start for a short time then cancel
    async def run_briefly():
        task = asyncio.create_task(refiller.start())
        await asyncio.sleep(0.1)
        refiller.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    with patch.object(TimedQueueRefiller, 'WAIT_TIME', 0.05):
        await run_briefly()

    mock_publisher.refill_queue.assert_awaited()


@pytest.mark.asyncio
async def test_start_continues_after_error():
    """Test that start() continues running after an exception."""
    from app.services.timed_queue_refiller import TimedQueueRefiller

    call_count = 0

    async def mock_refill():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Test error")
        # Second call succeeds

    mock_publisher = MagicMock()
    mock_publisher.refill_queue = mock_refill

    refiller = TimedQueueRefiller()
    refiller.career_docs_publisher = mock_publisher

    async def run_briefly():
        task = asyncio.create_task(refiller.start())
        await asyncio.sleep(0.15)  # Allow time for multiple iterations
        refiller.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    with patch.object(TimedQueueRefiller, 'WAIT_TIME', 0.05):
        await run_briefly()

    # Should have been called multiple times despite the error
    assert call_count >= 2


@pytest.mark.asyncio
async def test_stop_sets_running_false():
    """Test that stop() sets running to False."""
    from app.services.timed_queue_refiller import TimedQueueRefiller

    refiller = TimedQueueRefiller()
    refiller.running = True

    refiller.stop()

    assert refiller.running is False


@pytest.mark.asyncio
async def test_start_handles_cancelled_error():
    """Test that start() properly handles CancelledError."""
    from app.services.timed_queue_refiller import TimedQueueRefiller

    mock_publisher = MagicMock()
    mock_publisher.refill_queue = AsyncMock()

    refiller = TimedQueueRefiller()
    refiller.career_docs_publisher = mock_publisher

    task = asyncio.create_task(refiller.start())
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
