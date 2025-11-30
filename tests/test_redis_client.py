import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_connect_success():
    """Test successful Redis connection."""
    from app.core.redis_client import AsyncRedisClient

    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock()

    client = AsyncRedisClient(host='localhost', port=6379)

    with patch('app.core.redis_client.redis.Redis', return_value=mock_redis):
        await client.connect()

    assert client.connection is not None
    mock_redis.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_failure():
    """Test Redis connection failure handling."""
    import redis.asyncio as redis
    from app.core.redis_client import AsyncRedisClient

    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(side_effect=redis.ConnectionError("Connection refused"))

    client = AsyncRedisClient(host='localhost', port=6379)

    with patch('app.core.redis_client.redis.Redis', return_value=mock_redis):
        await client.connect()

    assert client.connection is None


@pytest.mark.asyncio
async def test_get_returns_value():
    """Test getting a value from Redis."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.get = AsyncMock(return_value=b'test_value')

    result = await client.get('test_key')

    assert result == 'test_value'
    client.connection.get.assert_awaited_once_with('test_key')


@pytest.mark.asyncio
async def test_get_returns_none_when_key_not_found():
    """Test getting a non-existent key returns None."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.get = AsyncMock(return_value=None)

    result = await client.get('nonexistent_key')

    assert result is None


@pytest.mark.asyncio
async def test_get_auto_connects():
    """Test that get() auto-connects if not connected."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = None

    with patch.object(client, 'connect', new_callable=AsyncMock) as mock_connect:
        # After connect, still no connection (simulating failure)
        result = await client.get('test_key')

    mock_connect.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_set_success():
    """Test setting a value in Redis."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.set = AsyncMock()

    result = await client.set('test_key', 'test_value')

    assert result is True
    client.connection.set.assert_awaited_once_with('test_key', 'test_value')


@pytest.mark.asyncio
async def test_delete_success():
    """Test deleting a key from Redis."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.delete = AsyncMock(return_value=1)

    result = await client.delete('test_key')

    assert result is True
    client.connection.delete.assert_awaited_once_with('test_key')


@pytest.mark.asyncio
async def test_delete_nonexistent_key():
    """Test deleting a non-existent key returns False."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.delete = AsyncMock(return_value=0)

    result = await client.delete('nonexistent_key')

    assert result is False


@pytest.mark.asyncio
async def test_is_connected_true():
    """Test is_connected returns True when connected."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.ping = AsyncMock()

    result = await client.is_connected()

    assert result is True


@pytest.mark.asyncio
async def test_is_connected_false_when_no_connection():
    """Test is_connected returns False when not connected."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = None

    result = await client.is_connected()

    assert result is False


@pytest.mark.asyncio
async def test_close():
    """Test closing Redis connection."""
    from app.core.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    client.connection = MagicMock()
    client.connection.close = AsyncMock()

    await client.close()

    client.connection.close.assert_awaited_once()
