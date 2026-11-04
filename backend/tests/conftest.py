import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.model_loader import load_all_artifacts

@pytest.fixture(scope="session", autouse=True)
def init_models():
    load_all_artifacts()

@pytest.fixture
def client():
    return TestClient(app)
