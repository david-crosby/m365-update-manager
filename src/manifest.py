import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PackageState:
    version: str
    sha256: str
    download_url: str
    staged_at: str = None
    promoted_at: str = None
    file_size: int = None
    min_os: str = None


@dataclass
class AppState:
    app_id: str
    name: str
    blob_name: str
    staged: PackageState = None
    live: PackageState = None
    previous: PackageState = None


@dataclass
class Manifest:
    last_updated: str = ""
    channel: str = "current"
    lag_days: int = 14
    apps: dict = field(default_factory=dict)


class ManifestManager:
    def __init__(self, manifest_path):
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load()
    
    def _load(self):
        if not self.manifest_path.exists():
            return Manifest()
        
        try:
            with open(self.manifest_path) as f:
                data = json.load(f)
            return self._parse(data)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to load manifest: {e}")
            return Manifest()
    
    def _parse(self, data):
        manifest = Manifest(
            last_updated=data.get("last_updated", ""),
            channel=data.get("channel", "current"),
            lag_days=data.get("lag_days", 14),
        )
        
        for key, app_data in data.get("apps", {}).items():
            app = AppState(
                app_id=app_data.get("app_id", ""),
                name=app_data.get("name", ""),
                blob_name=app_data.get("blob_name", ""),
            )
            
            for tier in ["staged", "live", "previous"]:
                tier_data = app_data.get(tier)
                if tier_data:
                    pkg = PackageState(
                        version=tier_data.get("version", ""),
                        sha256=tier_data.get("sha256", ""),
                        download_url=tier_data.get("download_url", ""),
                        staged_at=tier_data.get("staged_at"),
                        promoted_at=tier_data.get("promoted_at"),
                        file_size=tier_data.get("file_size"),
                        min_os=tier_data.get("min_os"),
                    )
                    setattr(app, tier, pkg)
            
            manifest.apps[key] = app
        
        return manifest
    
    def save(self):
        self.manifest.last_updated = datetime.now(timezone.utc).isoformat()
        
        data = {
            "last_updated": self.manifest.last_updated,
            "channel": self.manifest.channel,
            "lag_days": self.manifest.lag_days,
            "apps": {},
        }
        
        for key, app in self.manifest.apps.items():
            app_data = {
                "app_id": app.app_id,
                "name": app.name,
                "blob_name": app.blob_name,
            }
            
            for tier in ["staged", "live", "previous"]:
                pkg = getattr(app, tier)
                if pkg:
                    app_data[tier] = asdict(pkg)
            
            data["apps"][key] = app_data
        
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info("Saved manifest")
    
    def get_app_state(self, app_key):
        return self.manifest.apps.get(app_key)
    
    def set_app_state(self, app_key, state):
        self.manifest.apps[app_key] = state
    
    def stage_update(self, app_key, app_id, name, blob_name, version, 
                     sha256, download_url, file_size=None, min_os=None):
        state = self.get_app_state(app_key)
        if not state:
            state = AppState(app_id=app_id, name=name, blob_name=blob_name)
        
        state.staged = PackageState(
            version=version,
            sha256=sha256,
            download_url=download_url,
            staged_at=datetime.now(timezone.utc).isoformat(),
            file_size=file_size,
            min_os=min_os,
        )
        
        self.set_app_state(app_key, state)
        logger.info(f"Staged {name} {version}")
    
    def promote_update(self, app_key):
        state = self.get_app_state(app_key)
        if not state or not state.staged:
            logger.error(f"No staged update for {app_key}")
            return False
        
        state.previous = state.live
        state.live = state.staged
        state.live.promoted_at = datetime.now(timezone.utc).isoformat()
        state.staged = None
        
        self.set_app_state(app_key, state)
        logger.info(f"Promoted {state.name}")
        return True
    
    def is_update_available(self, app_key, new_version, new_sha256):
        state = self.get_app_state(app_key)
        if not state:
            return True
        
        new_hash = new_sha256.lower()
        if state.staged and state.staged.sha256.lower() == new_hash:
            return False
        if state.live and state.live.sha256.lower() == new_hash:
            return False
        
        return True
    
    def is_ready_for_promotion(self, app_key, lag_days):
        state = self.get_app_state(app_key)
        if not state or not state.staged or not state.staged.staged_at:
            return False
        
        staged = datetime.fromisoformat(state.staged.staged_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_waiting = (now - staged).days
        
        return days_waiting >= lag_days
    
    def get_apps_ready_for_promotion(self, lag_days):
        ready = []
        for key in self.manifest.apps:
            if self.is_ready_for_promotion(key, lag_days):
                ready.append(key)
        return ready
