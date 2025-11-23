# M365 Update Manager

Lagged deployment system for Microsoft 365 apps on macOS. Downloads updates from Microsoft's CDN, stages them in Azure Blob Storage, and promotes them to production after a configurable waiting period.

## Why This Exists

Enterprise environments need time to test updates before rolling them out. This tool:

- Automatically checks for new M365 updates
- Stages them in Azure for testing
- Waits a configurable period (default 14 days)
- Promotes to production when ready
- Maintains rollback capability

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/david-crosby/m365-update-manager.git
cd m365-update-manager
uv sync --all-extras --dev

# Configure
cp .env.example .env
# Edit .env with your Azure credentials

# Test locally
uv run python check_updates.py --dry-run
uv run python promote.py --dry-run
```

## How It Works

```
Microsoft CDN → Check Updates → Azure Staged → Wait 14 Days → Azure Live → Your MDM
                                    ↓
                              Previous (Rollback)
```

## Configuration

Set these environment variables:

```bash
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_CONTAINER_NAME=m365-updates
UPDATE_CHANNEL=current  # current, preview, or beta
LAG_DAYS=14            # Days to wait before promotion
```

## Usage

### Check for Updates

```bash
python check_updates.py --dry-run --verbose
```

### Promote Updates

```bash
python promote.py --dry-run --verbose
```

### Rollback an Update

```bash
python promote.py --rollback word
```

### Force Promotion

```bash
python promote.py --force --apps word excel
```

## GitHub Actions

Workflows run automatically:
- Update checks: Every 6 hours
- Promotions: Daily at 8 AM

Configure these secrets in GitHub:
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_CONTAINER_NAME`

## Supported Applications

Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Teams, Company Portal, Edge, Defender, AutoUpdate, Windows App

## Development

```bash
make test         # Run tests
make lint         # Check code
make format       # Format code
make clean        # Clean artifacts
```

## Deployment

The manifest.json tracks state. Azure Blob Storage has three folders:
- `staged/` - New updates waiting
- `live/` - Production updates
- `previous/` - Rollback versions

## Azure Storage Structure

```
m365-updates/
├── staged/
│   ├── word.pkg
│   ├── excel.pkg
│   └── ...
├── live/
│   ├── word.pkg
│   ├── excel.pkg
│   └── ...
└── previous/
    ├── word.pkg
    ├── excel.pkg
    └── ...
```

## Integration

Use the blob URLs from the `live/` folder in your MDM (Jamf, Munki, etc).

Example Jamf policy:
```
https://your-storage.blob.core.windows.net/m365-updates/live/word.pkg
```

## Cost

Azure Blob Storage costs roughly £1-2/month for this use case (12 apps × 3 tiers).

## Troubleshooting

**Import errors:** Run scripts with `uv run python script.py`

**Auth failures:** Check your connection string format

**Updates not promoting:** Check lag days and staged timestamps

## License

MIT - See LICENSE file

## Author

David Crosby (Bing)  
[LinkedIn](https://www.linkedin.com/in/david-bing-crosby/)  
[GitHub](https://github.com/david-crosby)
