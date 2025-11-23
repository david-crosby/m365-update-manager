#!/usr/bin/env python3

import argparse
import logging
import sys
import tempfile
from pathlib import Path

from src.azure_storage import AzureStorageClient
from src.config import APPS, Settings
from src.manifest import ManifestManager
from src.mau_client import MAUClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_for_updates(settings, manifest_mgr, mau, storage, dry_run=False):
    updated = []
    
    for app_key, app_cfg in APPS.items():
        logger.info(f"Checking {app_cfg.name}")
        
        try:
            info = mau.get_update_info(app_cfg)
            if not info:
                logger.warning(f"Could not get update info for {app_cfg.name}")
                continue
            
            with tempfile.NamedTemporaryFile(suffix=".pkg", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            try:
                # Get hash if not in manifest
                if not info.sha256:
                    logger.info("Downloading to compute hash")
                    if not mau.download_package(info.download_url, tmp_path):
                        logger.error(f"Download failed for {app_cfg.name}")
                        continue
                    info.sha256 = mau.compute_file_hash(tmp_path)
                
                # Check if we already have this version
                if not manifest_mgr.is_update_available(app_key, info.version, info.sha256):
                    logger.info(f"{app_cfg.name} is up to date")
                    continue
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would stage {app_cfg.name} {info.version}")
                    updated.append(app_key)
                    continue
                
                # Download if needed
                if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                    if not mau.download_package(info.download_url, tmp_path, info.sha256):
                        logger.error(f"Download failed for {app_cfg.name}")
                        continue
                
                # Upload to Azure
                if not storage.upload_package(str(tmp_path), "staged", app_cfg.blob_name):
                    logger.error(f"Upload failed for {app_cfg.name}")
                    continue
                
                # Update manifest
                manifest_mgr.stage_update(
                    app_key=app_key,
                    app_id=app_cfg.app_id,
                    name=app_cfg.name,
                    blob_name=app_cfg.blob_name,
                    version=info.version,
                    sha256=info.sha256,
                    download_url=info.download_url,
                    file_size=info.file_size,
                    min_os=info.min_os,
                )
                
                updated.append(app_key)
                logger.info(f"Staged {app_cfg.name} {info.version}")
            
            finally:
                tmp_path.unlink(missing_ok=True)
        
        except Exception as e:
            logger.error(f"Error processing {app_cfg.name}: {e}")
            continue
    
    return updated


def main():
    parser = argparse.ArgumentParser(description="Check for M365 updates")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        settings = Settings()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        return 1
    
    manifest_mgr = ManifestManager(args.manifest)
    manifest_mgr.manifest.channel = settings.channel
    manifest_mgr.manifest.lag_days = settings.lag_days
    
    mau = MAUClient(settings)
    storage = AzureStorageClient(settings)
    
    logger.info(f"Checking for updates (channel: {settings.channel})")
    
    updated = check_for_updates(settings, manifest_mgr, mau, storage, args.dry_run)
    
    if updated:
        logger.info(f"Staged: {', '.join(updated)}")
        if not args.dry_run:
            manifest_mgr.save()
    else:
        logger.info("No updates available")
    
    print(f"::set-output name=updated_count::{len(updated)}")
    print(f"::set-output name=updated_apps::{','.join(updated)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
