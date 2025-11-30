import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client."""
    client = MagicMock()
    db = MagicMock()
    collection = MagicMock()

    client.get_database.return_value = db
    db.get_collection.return_value = collection

    # Make collection methods async
    collection.find_one = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    collection.insert_one = AsyncMock()

    return client, db, collection


@pytest.fixture
def mock_redis_client():
    """Create a mock async Redis client."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.is_connected = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_rabbitmq_client():
    """Create a mock RabbitMQ client."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.publish_message = AsyncMock()
    client.consume_messages = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "title": "Software Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "portal": "workday",
        "url": "https://example.com/job/123"
    }


@pytest.fixture
def sample_career_docs_response():
    """Sample CareerDocs response for testing."""
    return {
        "success": True,
        "user_id": 123,
        "mongo_id": "64cfc7f476071f6557215d57",
        "applications": {
            "corr-id-1": {
                "resume_optimized": {"header": {}, "body": {}},
                "cover_letter": {"header": {}, "body": {}, "footer": {}}
            }
        }
    }


@pytest.fixture
def sample_resume():
    """Sample resume data for testing."""
    return {
        "header": {
            "personal_information": {
                "name": "John",
                "surname": "Doe",
                "email": "john@example.com"
            }
        },
        "body": {
            "education_details": {},
            "experience_details": {}
        }
    }


@pytest.fixture
def sample_cover_letter():
    """Sample cover letter data for testing."""
    return {
        "header": {
            "applicant_details": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "company_details": {
                "name": "Test Corp"
            }
        },
        "body": {
            "greeting": "Dear Hiring Manager,",
            "opening_paragraph": "I am writing to apply...",
            "body_paragraphs": ["First paragraph", "Second paragraph"],
            "closing_paragraph": "Thank you for your consideration."
        },
        "footer": {
            "closing": "Sincerely,",
            "signature": "John Doe"
        }
    }
