import pytest

from src.config import APPS, CDN_URLS, Settings


def test_settings_needs_connection_string(monkeypatch):
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)
    
    with pytest.raises(ValueError, match="AZURE_STORAGE_CONNECTION_STRING"):
        Settings()


def test_settings_loads_from_env(mock_env):
    settings = Settings()
    
    assert settings.azure_container_name == "test-container"
    assert settings.channel == "current"
    assert settings.lag_days == 14


def test_settings_rejects_bad_channel(mock_env, monkeypatch):
    monkeypatch.setenv("UPDATE_CHANNEL", "invalid")
    
    with pytest.raises(ValueError, match="UPDATE_CHANNEL"):
        Settings()


def test_settings_rejects_negative_lag(mock_env, monkeypatch):
    monkeypatch.setenv("LAG_DAYS", "-5")
    
    with pytest.raises(ValueError, match="LAG_DAYS"):
        Settings()


def test_cdn_url_for_channel(mock_env):
    settings = Settings()
    assert settings.cdn_base_url == CDN_URLS["current"]


def test_all_apps_present():
    expected = [
        "word", "excel", "powerpoint", "outlook", "onenote",
        "onedrive", "teams", "companyportal", "edge", "defender",
        "mau", "windowsapp"
    ]
    
    for app in expected:
        assert app in APPS
        cfg = APPS[app]
        assert cfg.name
        assert cfg.app_id
        assert cfg.fwlink
        assert cfg.bundle_id
        assert cfg.blob_name
