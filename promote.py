#!/usr/bin/env python3

import argparse
import logging
import sys

from src.azure_storage import AzureStorageClient
from src.config import Settings
from src.manifest import ManifestManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def promote_updates(settings, manifest_mgr, storage, dry_run=False, 
                     force=False, app_filter=None):
    promoted = []
    
    # Determine which apps are ready
    if force and app_filter:
        ready = app_filter
    elif force:
        ready = [k for k, s in manifest_mgr.manifest.apps.items() if s.staged]
    else:
        ready = manifest_mgr.get_apps_ready_for_promotion(settings.lag_days)
    
    if app_filter and not force:
        ready = [app for app in ready if app in app_filter]
    
    if not ready:
        logger.info("No updates ready for promotion")
        return []
    
    logger.info(f"Ready: {', '.join(ready)}")
    
    for key in ready:
        state = manifest_mgr.get_app_state(key)
        
        if not state or not state.staged:
            logger.warning(f"No staged update for {key}")
            continue
        
        logger.info(f"Promoting {state.name}: {state.staged.version}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would promote {state.name}")
            promoted.append(key)
            continue
        
        if not storage.promote_package(state.blob_name):
            logger.error(f"Storage promotion failed for {state.name}")
            continue
        
        if not manifest_mgr.promote_update(key):
            logger.error(f"Manifest update failed for {state.name}")
            continue
        
        promoted.append(key)
        logger.info(f"Promoted {state.name}")
    
    return promoted


def rollback_update(manifest_mgr, storage, app_key, dry_run=False):
    state = manifest_mgr.get_app_state(app_key)
    
    if not state:
        logger.error(f"Unknown app: {app_key}")
        return False
    
    if not state.previous:
        logger.error(f"No previous version for {state.name}")
        return False
    
    logger.info(
        f"Rolling back {state.name} from "
        f"{state.live.version if state.live else 'none'} "
        f"to {state.previous.version}"
    )
    
    if dry_run:
        logger.info(f"[DRY RUN] Would rollback {state.name}")
        return True
    
    if not storage.rollback_package(state.blob_name):
        logger.error(f"Storage rollback failed for {state.name}")
        return False
    
    # Swap versions in manifest
    state.live, state.previous = state.previous, state.live
    manifest_mgr.set_app_state(app_key, state)
    
    logger.info(f"Rolled back {state.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Promote M365 updates to live")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--apps", nargs="*")
    parser.add_argument("--rollback", metavar="APP")
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
    storage = AzureStorageClient(settings)
    
    if args.rollback:
        success = rollback_update(manifest_mgr, storage, args.rollback, args.dry_run)
        if success and not args.dry_run:
            manifest_mgr.save()
        return 0 if success else 1
    
    promoted = promote_updates(
        settings, 
        manifest_mgr, 
        storage,
        args.dry_run,
        args.force,
        args.apps
    )
    
    if promoted:
        logger.info(f"Promoted: {', '.join(promoted)}")
        if not args.dry_run:
            manifest_mgr.save()
    else:
        logger.info("No updates promoted")
    
    print(f"::set-output name=promoted_count::{len(promoted)}")
    print(f"::set-output name=promoted_apps::{','.join(promoted)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
