import pytest
from src.app import app


@pytest.fixture()
def app_instance():
    yield app


@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()
