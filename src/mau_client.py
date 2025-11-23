import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192
REQUEST_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 600


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
        logger.info(f"Checking {app.name}")
        
        try:
            response = self.session.get(manifest_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            info = self._parse_manifest(root, app.app_id)
            if info:
                return info
        except (requests.RequestException, ET.ParseError) as e:
            logger.debug(f"Manifest fetch failed: {e}")
        
        return self._get_from_fwlink(app)
    
    def _parse_manifest(self, root, app_id):
        version = None
        url = None
        sha = None
        size = None
        min_os = None
        
        for tag in ["CFBundleVersion", "Version", "version"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                version = elem.text.strip()
                break
        
        for tag in ["FullUpdaterLocation", "Location", "PkgLocation"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                url = elem.text.strip()
                break
        
        for tag in ["FullUpdaterSHA256", "SHA256", "Hash"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                sha = elem.text.strip()
                break
        
        for tag in ["FullUpdaterSize", "Size"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                try:
                    size = int(elem.text.strip())
                except ValueError:
                    pass
                break
        
        for tag in ["MinimumOSVersion", "MinOS"]:
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                min_os = elem.text.strip()
                break
        
        if version and url:
            return UpdateInfo(
                app_id=app_id,
                version=version,
                download_url=url,
                sha256=sha,
                file_size=size,
                min_os=min_os,
            )
        return None
    
    def _get_from_fwlink(self, app):
        try:
            response = self.session.head(
                app.fwlink, 
                allow_redirects=True, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            url = response.url
            content_length = response.headers.get("Content-Length")
            version = self._extract_version(url) or "unknown"
            size = int(content_length) if content_length else None
            
            return UpdateInfo(
                app_id=app.app_id,
                version=version,
                download_url=url,
                file_size=size,
            )
        except requests.RequestException as e:
            logger.error(f"FWLink failed for {app.name}: {e}")
            return None
    
    def _extract_version(self, url):
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
    
    def download_package(self, url, dest, expected_sha=None):
        try:
            logger.info(f"Downloading {url}")
            response = self.session.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            sha_hash = hashlib.sha256()
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
                    sha_hash.update(chunk)
            
            computed = sha_hash.hexdigest()
            logger.info(f"Downloaded, SHA256: {computed}")
            
            if expected_sha and computed.lower() != expected_sha.lower():
                logger.error(f"Hash mismatch: expected {expected_sha}, got {computed}")
                return False
            
            return True
        except (requests.RequestException, IOError) as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def compute_file_hash(self, filepath):
        sha_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha_hash.update(chunk)
        return sha_hash.hexdigest()
