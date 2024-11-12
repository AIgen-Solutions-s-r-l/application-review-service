# tests/test_main.py
import pytest
import sys
from httpx import AsyncClient, ASGITransport
from pathlib import Path

# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.main import app  # Now you can import app

@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "coreService is up and running!"}