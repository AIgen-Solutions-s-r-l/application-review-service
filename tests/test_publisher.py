import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.career_docs_publisher import career_docs_publisher
from app.core.exceptions import JobApplicationError
from app.schemas.app_jobs import JobsToApplyInfo

@pytest.mark.asyncio
@patch.object(career_docs_publisher, "jobs_redis_client")
async def test_publish_applications_success(m_redis):
    m_redis.is_connected = AsyncMock(return_value=True)
    m_redis.get = AsyncMock(return_value=None)
    m_redis.set = AsyncMock(return_value=True)
    with patch.object(career_docs_publisher.pdf_resumes_collection, "update_one", new_callable=AsyncMock) as m_up:
        m_up.return_value.modified_count = 1
        info = JobsToApplyInfo(user_id=123, jobs=[{"title": "Job"}], cv_id="64cfc7f476071f6557215d57", mongo_id="abc", style="formal")
        with patch.object(career_docs_publisher, "publish", new_callable=AsyncMock) as m_pub:
            await career_docs_publisher.publish_applications(info)
            m_pub.assert_awaited_once()

@pytest.mark.asyncio
@patch.object(career_docs_publisher, "jobs_redis_client")
async def test_publish_applications_redis_failure(m_redis):
    m_redis.is_connected = AsyncMock(return_value=False)
    info = JobsToApplyInfo(user_id=123, jobs=[{"title": "Job"}], cv_id=None, mongo_id="abc", style="formal")
    with pytest.raises(JobApplicationError, match="Redis client is not connected"):
        await career_docs_publisher.publish_applications(info)

@pytest.mark.asyncio
@patch("app.services.career_docs_publisher.database_consumer.retrieve_one_batch_from_db", new_callable=AsyncMock)
@patch.object(career_docs_publisher, "get_queue_size", new_callable=AsyncMock)
@patch.object(career_docs_publisher, "publish_applications", new_callable=AsyncMock)
async def test_refill_queue_success(m_pub, m_size, m_db):
    m_size.side_effect = [50, 80, 99, 101]
    m_db.side_effect = [
        JobsToApplyInfo(user_id=1, jobs=[], cv_id=None, mongo_id="abc", style="formal"),
        JobsToApplyInfo(user_id=2, jobs=[], cv_id=None, mongo_id="def", style="formal"),
        JobsToApplyInfo(user_id=3, jobs=[], cv_id=None, mongo_id="xyz", style="formal"),
        None
    ]
    await career_docs_publisher.refill_queue()
    assert m_pub.call_count == 3

@pytest.mark.asyncio
async def test_refill_queue_stop_on_none():
    with patch.object(career_docs_publisher, "get_queue_size", new_callable=AsyncMock) as m_size, \
         patch("app.services.career_docs_publisher.database_consumer.retrieve_one_batch_from_db", new_callable=AsyncMock) as m_db, \
         patch.object(career_docs_publisher, "publish_applications", new_callable=AsyncMock) as m_pub:
        m_size.return_value = 30
        m_db.return_value = None
        await career_docs_publisher.refill_queue()
        m_pub.assert_not_awaited()
