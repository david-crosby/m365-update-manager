#!/usr/bin/env python3

import argparse
import logging
import sys

from config import Settings
from azure_storage import AzureStorageClient
from manifest import ManifestManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def promote_updates(
    settings: Settings,
    manifest_manager: ManifestManager,
    storage_client: AzureStorageClient,
    dry_run: bool = False,
    force: bool = False,
    app_filter: list[str] = None,
) -> list[str]:

    promoted = []
    
    # Get apps ready for promotion based on lag period
    if force and app_filter:
        ready_apps = app_filter
    elif force:
        ready_apps = [
            key for key, state in manifest_manager.manifest.apps.items()
            if state.staged is not None
        ]
    else:
        ready_apps = manifest_manager.get_apps_ready_for_promotion(settings.lag_days)
    
    # Apply filter if specified
    if app_filter and not force:
        ready_apps = [app for app in ready_apps if app in app_filter]
    
    if not ready_apps:
        logger.info("No updates ready for promotion")
        return []
    
    logger.info(f"Updates ready for promotion: {', '.join(ready_apps)}")
    
    for app_key in ready_apps:
        state = manifest_manager.get_app_state(app_key)
        
        if not state or not state.staged:
            logger.warning(f"No staged update for {app_key}")
            continue
        
        logger.info(
            f"Promoting {state.name}: {state.staged.version}"
        )
        
        if dry_run:
            logger.info(f"[DRY RUN] Would promote {state.name}")
            promoted.append(app_key)
            continue
        
        # Promote in storage first
        if not storage_client.promote_package(state.blob_name):
            logger.error(f"Failed to promote {state.name} in storage")
            continue
        
        # Update manifest
        if not manifest_manager.promote_update(app_key):
            logger.error(f"Failed to update manifest for {state.name}")
            continue
        
        promoted.append(app_key)
        logger.info(f"Successfully promoted {state.name}")
    
    return promoted


def rollback_update(
    manifest_manager: ManifestManager,
    storage_client: AzureStorageClient,
    app_key: str,
    dry_run: bool = False,
) -> bool:
    """Roll back an app to its previous version."""
    state = manifest_manager.get_app_state(app_key)
    
    if not state:
        logger.error(f"Unknown app: {app_key}")
        return False
    
    if not state.previous:
        logger.error(f"No previous version available for {state.name}")
        return False
    
    logger.info(
        f"Rolling back {state.name} from "
        f"{state.live.version if state.live else 'none'} "
        f"to {state.previous.version}"
    )
    
    if dry_run:
        logger.info(f"[DRY RUN] Would rollback {state.name}")
        return True
    
    # Rollback in storage
    if not storage_client.rollback_package(state.blob_name):
        logger.error(f"Failed to rollback {state.name} in storage")
        return False
    
    # Swap in manifest
    state.live, state.previous = state.previous, state.live
    manifest_manager.set_app_state(app_key, state)
    
    logger.info(f"Successfully rolled back {state.name}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Promote staged M365 updates to live"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check what would be promoted without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force promotion regardless of lag period",
    )
    parser.add_argument(
        "--apps",
        nargs="*",
        help="Only promote specific apps (by key)",
    )
    parser.add_argument(
        "--rollback",
        metavar="APP",
        help="Roll back a specific app to its previous version",
    )
    parser.add_argument(
        "--manifest",
        default="manifest.json",
        help="Path to the manifest file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        settings = Settings()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    manifest_manager = ManifestManager(args.manifest)
    storage_client = AzureStorageClient(settings)
    
    if args.rollback:
        success = rollback_update(
            manifest_manager=manifest_manager,
            storage_client=storage_client,
            app_key=args.rollback,
            dry_run=args.dry_run,
        )
        
        if success and not args.dry_run:
            manifest_manager.save()
        
        sys.exit(0 if success else 1)
    
    promoted = promote_updates(
        settings=settings,
        manifest_manager=manifest_manager,
        storage_client=storage_client,
        dry_run=args.dry_run,
        force=args.force,
        app_filter=args.apps,
    )
    
    if promoted:
        logger.info(f"Promoted: {', '.join(promoted)}")
        
        if not args.dry_run:
            manifest_manager.save()
    else:
        logger.info("No updates promoted")
    
    # Output for GitHub Actions
    print(f"::set-output name=promoted_count::{len(promoted)}")
    print(f"::set-output name=promoted_apps::{','.join(promoted)}")


if __name__ == "__main__":
    main()
