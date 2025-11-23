import pytest


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", 
                      "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net")
    monkeypatch.setenv("AZURE_CONTAINER_NAME", "test-container")
    monkeypatch.setenv("UPDATE_CHANNEL", "current")
    monkeypatch.setenv("LAG_DAYS", "14")


@pytest.fixture
def temp_manifest(tmp_path):
    return tmp_path / "manifest.json"
