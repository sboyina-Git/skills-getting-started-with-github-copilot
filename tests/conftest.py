import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture providing FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def sample_email():
    """Fixture providing a unique test email not in pre-populated data"""
    return "test_student@mergington.edu"


@pytest.fixture
def sample_activity():
    """Fixture providing a valid activity name"""
    return "Chess Club"


@pytest.fixture
def nonexistent_activity():
    """Fixture providing an invalid activity name"""
    return "Nonexistent Activity"
