import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import get_current_user  # Adjust if your code imports from a different place

client = TestClient(app)

@pytest.fixture(scope="function")
def override_user():
    app.dependency_overrides[get_current_user] = lambda: 123
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_mongo():
    with patch("app.core.mongo.get_mongo_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        mock_client.get_database.return_value = mock_db
        mock_db.get_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client
        yield mock_collection

def test_get_career_docs_success(override_user, mock_mongo):
    mock_mongo.find_one.return_value = {
        "user_id": 123,
        "content": {
            "app_1": {
                "id": "job_1",
                "resume_optimized": {"dummy": "remove"},
                "cover_letter": {"dummy": "remove"}
            }
        }
    }
    response = client.get("/apply_content")
    assert response.status_code == 200

def test_get_career_docs_not_found(override_user, mock_mongo):
    mock_mongo.find_one.return_value = None
    response = client.get("/apply_content")
    assert response.status_code == 500

@patch("app.routers.applier_editor.generic_publisher.publish_data_to_microservices", new_callable=AsyncMock)
def test_process_career_docs_success(mock_publish, override_user, mock_mongo):
    mock_mongo.find_one.return_value = {
        "user_id": 123,
        "content": {"some": "data"}
    }
    response = client.post("/apply_all")
    assert response.status_code == 200
    mock_publish.assert_awaited_once()
