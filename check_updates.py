#!/usr/bin/env python3

import argparse
import logging
import sys
import tempfile
from pathlib import Path

from config import APPS, Settings
from azure_storage import AzureStorageClient
from manifest import ManifestManager
from mau_client import MAUClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_for_updates(settings, manifest_manager, mau_client, storage_client, dry_run=False):
    updated = []
    
    for app_key, app_config in APPS.items():
        logger.info(f"Checking {app_config.name}")
        
        try:
            update_info = mau_client.get_update_info(app_config)
            if not update_info:
                logger.warning(f"Could not get update info for {app_config.name}")
                continue
            
            with tempfile.NamedTemporaryFile(suffix=".pkg", delete=False) as tmp:
                tmp_path = tmp.name
            
            if not update_info.sha256:
                logger.info(f"Downloading to compute hash")
                if not mau_client.download_package(update_info.download_url, tmp_path):
                    logger.error(f"Failed to download {app_config.name}")
                    Path(tmp_path).unlink(missing_ok=True)
                    continue
                update_info.sha256 = mau_client.compute_file_hash(tmp_path)
            
            if not manifest_manager.is_update_available(app_key, update_info.version, update_info.sha256):
                logger.info(f"{app_config.name} is up to date")
                Path(tmp_path).unlink(missing_ok=True)
                continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Would stage {app_config.name} {update_info.version}")
                Path(tmp_path).unlink(missing_ok=True)
                updated.append(app_key)
                continue
            
            if not Path(tmp_path).exists() or Path(tmp_path).stat().st_size == 0:
                if not mau_client.download_package(update_info.download_url, tmp_path, update_info.sha256):
                    logger.error(f"Failed to download {app_config.name}")
                    Path(tmp_path).unlink(missing_ok=True)
                    continue
            
            if not storage_client.upload_package(tmp_path, "staged", app_config.blob_name):
                logger.error(f"Failed to upload {app_config.name}")
                Path(tmp_path).unlink(missing_ok=True)
                continue
            
            Path(tmp_path).unlink(missing_ok=True)
            
            manifest_manager.stage_update(
                app_key=app_key,
                app_id=app_config.app_id,
                name=app_config.name,
                blob_name=app_config.blob_name,
                version=update_info.version,
                sha256=update_info.sha256,
                download_url=update_info.download_url,
                file_size=update_info.file_size,
                min_os=update_info.min_os,
            )
            
            updated.append(app_key)
            logger.info(f"Staged {app_config.name} {update_info.version}")
            
        except Exception as e:
            logger.error(f"Error processing {app_config.name}: {e}")
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
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    manifest_manager = ManifestManager(args.manifest)
    manifest_manager.manifest.channel = settings.channel
    manifest_manager.manifest.lag_days = settings.lag_days
    
    mau_client = MAUClient(settings)
    storage_client = AzureStorageClient(settings)
    
    logger.info(f"Checking for updates (channel: {settings.channel})")
    
    updated = check_for_updates(
        settings=settings,
        manifest_manager=manifest_manager,
        mau_client=mau_client,
        storage_client=storage_client,
        dry_run=args.dry_run,
    )
    
    if updated:
        logger.info(f"Staged: {', '.join(updated)}")
        if not args.dry_run:
            manifest_manager.save()
    else:
        logger.info("No updates available")
    
    print(f"::set-output name=updated_count::{len(updated)}")
    print(f"::set-output name=updated_apps::{','.join(updated)}")


if __name__ == "__main__":
    main()
