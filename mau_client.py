import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urljoin

import requests

from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class UpdateInfo:
    app_id: str
    version: str
    download_url: str
    sha256: str = None
    file_size: int = None
    min_os: str = None


class MAUClient:
    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "M365UpdateManager/1.0"})
    
    def get_update_info(self, app):
        manifest_url = urljoin(self.settings.cdn_base_url, f"0409{app.app_id}.xml")
        logger.info(f"Fetching manifest for {app.name}")
        
        try:
            response = self.session.get(manifest_url, timeout=30)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            info = self._parse_manifest(root, app.app_id)
            if info:
                return info
        except Exception as e:
            logger.debug(f"Manifest fetch failed: {e}")
        
        return self._get_info_from_fwlink(app)
    
    def _parse_manifest(self, root, app_id):
        version = None
        download_url = None
        sha256 = None
        file_size = None
        min_os = None
        
        for tag in ["CFBundleVersion", "Version", "version"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                version = elem.text.strip()
                break
        
        for tag in ["FullUpdaterLocation", "Location", "PkgLocation"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                download_url = elem.text.strip()
                break
        
        for tag in ["FullUpdaterSHA256", "SHA256", "Hash"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                sha256 = elem.text.strip()
                break
        
        for tag in ["FullUpdaterSize", "Size"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                try:
                    file_size = int(elem.text.strip())
                except ValueError:
                    pass
                break
        
        for tag in ["MinimumOSVersion", "MinOS"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                min_os = elem.text.strip()
                break
        
        if version and download_url:
            return UpdateInfo(
                app_id=app_id,
                version=version,
                download_url=download_url,
                sha256=sha256,
                file_size=file_size,
                min_os=min_os,
            )
        return None
    
    def _get_info_from_fwlink(self, app):
        try:
            response = self.session.head(app.fwlink, allow_redirects=True, timeout=30)
            response.raise_for_status()
            
            final_url = response.url
            content_length = response.headers.get("Content-Length")
            version = self._extract_version_from_url(final_url) or "unknown"
            file_size = int(content_length) if content_length else None
            
            return UpdateInfo(
                app_id=app.app_id,
                version=version,
                download_url=final_url,
                file_size=file_size,
            )
        except requests.RequestException as e:
            logger.error(f"Failed to resolve FWLink for {app.name}: {e}")
            return None
    
    def _extract_version_from_url(self, url):
        patterns = [
            r"(\d+\.\d+\.\d{8,})",
            r"(\d+\.\d+\.\d+)",
            r"_(\d+\.\d+)_",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download_package(self, url, destination, expected_sha256=None):
        try:
            logger.info(f"Downloading {url}")
            response = self.session.get(url, stream=True, timeout=600)
            response.raise_for_status()
            
            sha256_hash = hashlib.sha256()
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    sha256_hash.update(chunk)
            
            computed_hash = sha256_hash.hexdigest()
            logger.info(f"Downloaded, SHA256: {computed_hash}")
            
            if expected_sha256 and computed_hash.lower() != expected_sha256.lower():
                logger.error(f"Hash mismatch: expected {expected_sha256}, got {computed_hash}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def compute_file_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
