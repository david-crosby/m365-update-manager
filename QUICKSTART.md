# Quick Start Guide

Get up and running with M365 Update Manager in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Azure Storage account
- Git

## 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Set Up Project

```bash
# Clone repository
git clone https://github.com/david-crosby/m365-update-manager.git
cd m365-update-manager

# Install dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install
```

## 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your details
nano .env  # or use your preferred editor
```

Required environment variables:
```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net
AZURE_CONTAINER_NAME=m365-updates
UPDATE_CHANNEL=current
LAG_DAYS=14
```

## 4. Test Locally

```bash
# Check for updates (dry-run)
uv run python check_updates.py --dry-run --verbose

# Test promotion (dry-run)
uv run python promote.py --dry-run --verbose

# Run tests
make test
```

## 5. Deploy to GitHub

```bash
# Push to GitHub
git add .
git commit -m "feat: initial setup of m365 update manager"
git push origin main
```

Configure GitHub secrets (Settings → Secrets and variables → Actions):
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_CONTAINER_NAME`

Configure GitHub variables:
- `UPDATE_CHANNEL` (optional, defaults to 'current')
- `LAG_DAYS` (optional, defaults to '14')

## 6. Monitor

Workflows will run automatically:
- **Update checks:** Every 6 hours
- **Promotions:** Daily at 8 AM

Manual triggers available in Actions tab.

## Common Commands

```bash
make test           # Run tests
make lint           # Check code quality
make format         # Format code
make check-updates  # Check for updates (dry-run)
make promote        # Promote updates (dry-run)
make clean          # Clean build artifacts
```

## Troubleshooting

### Import errors
Ensure you're running scripts with `uv run`:
```bash
uv run python check_updates.py
```

### Azure authentication fails
Verify connection string format:
```bash
echo $AZURE_STORAGE_CONNECTION_STRING
```

### Tests fail
Install dev dependencies:
```bash
uv sync --all-extras --dev
```

## Next Steps

1. Review `CODE_REVIEW.md` for detailed findings
2. Read `CONTRIBUTING.md` for development guidelines
3. Check `SUMMARY.md` for architecture overview
4. Set up monitoring and alerting

## Support

- Documentation: See README.md (to be created)
- Issues: GitHub Issues
- Contact: https://www.linkedin.com/in/david-bing-crosby/

## Quick Reference

### File Locations
- Source code: `src/`
- Tests: `tests/`
- Scripts: `check_updates.py`, `promote.py`
- Config: `.env`, `pyproject.toml`
- CI/CD: `.github/workflows/`

### Azure Blob Structure
```
m365-updates/
├── staged/        # New updates waiting
├── live/          # Production updates
└── previous/      # Rollback versions
```

### Supported Applications
Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Teams, Company Portal, Edge, Defender, MAU, Windows App

### Update Channels
- `current` - Production channel (recommended)
- `preview` - Preview/Beta channel
- `beta` - Insider/Beta channel
