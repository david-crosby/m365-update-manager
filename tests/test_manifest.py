from datetime import datetime, timezone

from src.manifest import AppState, ManifestManager, PackageState


def test_creates_new_manifest(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    assert mgr.manifest.last_updated == ""
    assert mgr.manifest.channel == "current"
    assert mgr.manifest.lag_days == 14
    assert len(mgr.manifest.apps) == 0


def test_saves_and_loads(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    mgr.stage_update(
        app_key="word",
        app_id="MSWD2019",
        name="Microsoft Word",
        blob_name="word.pkg",
        version="16.80.123",
        sha256="abc123",
        download_url="https://example.com/word.pkg",
    )
    
    mgr.save()
    
    mgr2 = ManifestManager(temp_manifest)
    state = mgr2.get_app_state("word")
    
    assert state is not None
    assert state.name == "Microsoft Word"
    assert state.staged is not None
    assert state.staged.version == "16.80.123"
    assert state.staged.sha256 == "abc123"


def test_update_available_for_new_app(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    assert mgr.is_update_available("word", "16.80.123", "abc123")


def test_update_not_available_when_staged(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    mgr.stage_update(
        app_key="word",
        app_id="MSWD2019",
        name="Microsoft Word",
        blob_name="word.pkg",
        version="16.80.123",
        sha256="abc123",
        download_url="https://example.com/word.pkg",
    )
    
    assert not mgr.is_update_available("word", "16.80.123", "abc123")


def test_update_available_for_different_version(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    mgr.stage_update(
        app_key="word",
        app_id="MSWD2019",
        name="Microsoft Word",
        blob_name="word.pkg",
        version="16.80.123",
        sha256="abc123",
        download_url="https://example.com/word.pkg",
    )
    
    assert mgr.is_update_available("word", "16.81.0", "def456")


def test_promotion_flow(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    mgr.stage_update(
        app_key="word",
        app_id="MSWD2019",
        name="Microsoft Word",
        blob_name="word.pkg",
        version="16.80.123",
        sha256="abc123",
        download_url="https://example.com/word.pkg",
    )
    
    assert mgr.promote_update("word")
    
    state = mgr.get_app_state("word")
    assert state.staged is None
    assert state.live is not None
    assert state.live.version == "16.80.123"
    assert state.live.promoted_at is not None


def test_not_ready_when_just_staged(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    mgr.stage_update(
        app_key="word",
        app_id="MSWD2019",
        name="Microsoft Word",
        blob_name="word.pkg",
        version="16.80.123",
        sha256="abc123",
        download_url="https://example.com/word.pkg",
    )
    
    assert not mgr.is_ready_for_promotion("word", 14)


def test_ready_after_lag_period(temp_manifest):
    mgr = ManifestManager(temp_manifest)
    
    state = AppState(
        app_id="MSWD2019",
        name="Microsoft Word",
        blob_name="word.pkg",
        staged=PackageState(
            version="16.80.123",
            sha256="abc123",
            download_url="https://example.com/word.pkg",
            staged_at="2024-01-01T00:00:00+00:00",
        )
    )
    mgr.set_app_state("word", state)
    
    assert mgr.is_ready_for_promotion("word", 0)
