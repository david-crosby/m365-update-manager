import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    name: str
    app_id: str
    fwlink: str
    bundle_id: str
    blob_name: str


CDN_URLS = {
    "current": "https://res.public.onecdn.static.microsoft/mro1cdnstorage/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/",
    "preview": "https://res.public.onecdn.static.microsoft/mro1cdnstorage/1ac37578-5a24-40fb-892e-b89d85b6dfaa/MacAutoupdate/",
    "beta": "https://res.public.onecdn.static.microsoft/mro1cdnstorage/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/",
}

APPS = {
    "word": AppConfig(
        name="Microsoft Word",
        app_id="MSWD2019",
        fwlink="https://go.microsoft.com/fwlink/?linkid=525134",
        bundle_id="com.microsoft.word",
        blob_name="word.pkg",
    ),
    "excel": AppConfig(
        name="Microsoft Excel",
        app_id="XCEL2019",
        fwlink="https://go.microsoft.com/fwlink/?linkid=525135",
        bundle_id="com.microsoft.excel",
        blob_name="excel.pkg",
    ),
    "powerpoint": AppConfig(
        name="Microsoft PowerPoint",
        app_id="PPT32019",
        fwlink="https://go.microsoft.com/fwlink/?linkid=525136",
        bundle_id="com.microsoft.powerpoint",
        blob_name="powerpoint.pkg",
    ),
    "outlook": AppConfig(
        name="Microsoft Outlook",
        app_id="OPIM2019",
        fwlink="https://go.microsoft.com/fwlink/?linkid=525137",
        bundle_id="com.microsoft.outlook",
        blob_name="outlook.pkg",
    ),
    "onenote": AppConfig(
        name="Microsoft OneNote",
        app_id="ONMC2019",
        fwlink="https://go.microsoft.com/fwlink/?linkid=820886",
        bundle_id="com.microsoft.onenote.mac",
        blob_name="onenote.pkg",
    ),
    "onedrive": AppConfig(
        name="Microsoft OneDrive",
        app_id="ONDR18",
        fwlink="https://go.microsoft.com/fwlink/?linkid=823060",
        bundle_id="com.microsoft.onedrive",
        blob_name="onedrive.pkg",
    ),
    "teams": AppConfig(
        name="Microsoft Teams",
        app_id="TEAMS21",
        fwlink="https://go.microsoft.com/fwlink/?linkid=2249065",
        bundle_id="com.microsoft.teams2",
        blob_name="teams.pkg",
    ),
    "companyportal": AppConfig(
        name="Company Portal",
        app_id="IMCP01",
        fwlink="https://go.microsoft.com/fwlink/?linkid=869655",
        bundle_id="com.microsoft.CompanyPortalMac",
        blob_name="companyportal.pkg",
    ),
    "edge": AppConfig(
        name="Microsoft Edge",
        app_id="EDGE01",
        fwlink="https://go.microsoft.com/fwlink/?linkid=2093504",
        bundle_id="com.microsoft.edgemac",
        blob_name="edge.pkg",
    ),
    "defender": AppConfig(
        name="Microsoft Defender",
        app_id="WDAV00",
        fwlink="https://go.microsoft.com/fwlink/?linkid=2097502",
        bundle_id="com.microsoft.wdav",
        blob_name="defender.pkg",
    ),
    "mau": AppConfig(
        name="Microsoft AutoUpdate",
        app_id="MSau04",
        fwlink="https://go.microsoft.com/fwlink/?linkid=830196",
        bundle_id="com.microsoft.autoupdate",
        blob_name="mau.pkg",
    ),
    "windowsapp": AppConfig(
        name="Windows App",
        app_id="MSRD10",
        fwlink="https://go.microsoft.com/fwlink/?linkid=868963",
        bundle_id="com.microsoft.rdc.macos",
        blob_name="windowsapp.pkg",
    ),
}


class Settings:
    def __init__(self):
        self.azure_storage_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not self.azure_storage_connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required")
        
        self.azure_container_name = os.environ.get("AZURE_CONTAINER_NAME", "m365-updates")
        self.channel = os.environ.get("UPDATE_CHANNEL", "current")
        self.lag_days = int(os.environ.get("LAG_DAYS", "14"))
    
    @property
    def cdn_base_url(self):
        return CDN_URLS.get(self.channel.lower(), CDN_URLS["current"])
