import logging

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192


class AzureStorageClient:
    def __init__(self, settings):
        self.settings = settings
        self.blob_service = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self.container = self.blob_service.get_container_client(
            settings.azure_container_name
        )
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        try:
            self.container.create_container(public_access="blob")
            logger.info(f"Created container: {self.settings.azure_container_name}")
        except ResourceExistsError:
            pass
    
    def _blob_path(self, folder, filename):
        return f"{folder}/{filename}"
    
    def upload_package(self, local_path, folder, filename, overwrite=True):
        blob_path = self._blob_path(folder, filename)
        try:
            blob_client = self.container.get_blob_client(blob_path)
            content_settings = ContentSettings(
                content_type="application/octet-stream",
                content_disposition=f"attachment; filename={filename}",
            )
            with open(local_path, "rb") as data:
                blob_client.upload_blob(
                    data, 
                    overwrite=overwrite, 
                    content_settings=content_settings
                )
            logger.info(f"Uploaded {local_path} to {blob_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Local file not found: {local_path}")
            return False
        except Exception as e:
            logger.error(f"Upload failed for {local_path}: {e}")
            return False
    
    def copy_blob(self, source_folder, source_filename, dest_folder, dest_filename=None):
        dest_filename = dest_filename or source_filename
        source_path = self._blob_path(source_folder, source_filename)
        dest_path = self._blob_path(dest_folder, dest_filename)
        
        try:
            source_client = self.container.get_blob_client(source_path)
            dest_client = self.container.get_blob_client(dest_path)
            dest_client.start_copy_from_url(source_client.url)
            logger.info(f"Copied {source_path} to {dest_path}")
            return True
        except ResourceNotFoundError:
            logger.error(f"Source blob not found: {source_path}")
            return False
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False
    
    def delete_blob(self, folder, filename):
        blob_path = self._blob_path(folder, filename)
        try:
            blob_client = self.container.get_blob_client(blob_path)
            blob_client.delete_blob()
            logger.info(f"Deleted {blob_path}")
            return True
        except ResourceNotFoundError:
            return True
        except Exception as e:
            logger.error(f"Delete failed for {blob_path}: {e}")
            return False
    
    def blob_exists(self, folder, filename):
        blob_path = self._blob_path(folder, filename)
        try:
            blob_client = self.container.get_blob_client(blob_path)
            return blob_client.exists()
        except Exception:
            return False
    
    def get_blob_url(self, folder, filename):
        blob_path = self._blob_path(folder, filename)
        blob_client = self.container.get_blob_client(blob_path)
        return blob_client.url
    
    def promote_package(self, filename):
        logger.info(f"Promoting {filename}")
        
        # Archive current live version
        if self.blob_exists("live", filename):
            if self.blob_exists("previous", filename):
                self.delete_blob("previous", filename)
            if not self.copy_blob("live", filename, "previous", filename):
                return False
            self.delete_blob("live", filename)
        
        # Check staged exists
        if not self.blob_exists("staged", filename):
            logger.error(f"No staged package for {filename}")
            return False
        
        # Promote staged to live
        if not self.copy_blob("staged", filename, "live", filename):
            return False
        
        self.delete_blob("staged", filename)
        logger.info(f"Promoted {filename}")
        return True
    
    def rollback_package(self, filename):
        logger.info(f"Rolling back {filename}")
        
        if not self.blob_exists("previous", filename):
            logger.error(f"No previous version for {filename}")
            return False
        
        # Save current live before rollback
        if self.blob_exists("live", filename):
            self.copy_blob("live", filename, "staged", f"{filename}.rollback")
        
        if not self.copy_blob("previous", filename, "live", filename):
            return False
        
        logger.info(f"Rolled back {filename}")
        return True
