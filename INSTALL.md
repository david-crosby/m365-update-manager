# Installation Guide

## Prerequisites

- Python 3.11+
- Azure Storage account
- Git

## Local Setup

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone Repository

```bash
git clone https://github.com/david-crosby/m365-update-manager.git
cd m365-update-manager
```

### 3. Install Dependencies

```bash
uv sync --all-extras --dev
uv run pre-commit install
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net
AZURE_CONTAINER_NAME=m365-updates
UPDATE_CHANNEL=current
LAG_DAYS=14
```

### 5. Test

```bash
uv run python check_updates.py --dry-run --verbose
uv run python promote.py --dry-run --verbose
make test
```

## Azure Setup

### Create Storage Account

```bash
az storage account create \
  --name your-storage-name \
  --resource-group your-rg \
  --location uksouth \
  --sku Standard_LRS

az storage container create \
  --name m365-updates \
  --account-name your-storage-name \
  --public-access blob
```

### Get Connection String

```bash
az storage account show-connection-string \
  --name your-storage-name \
  --resource-group your-rg
```

## GitHub Actions Setup

### 1. Push to GitHub

```bash
git remote add origin https://github.com/your-username/m365-update-manager.git
git push -u origin main
```

### 2. Configure Secrets

Go to repository Settings → Secrets and variables → Actions

Add secrets:
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_CONTAINER_NAME`

Add variables (optional):
- `UPDATE_CHANNEL` (default: current)
- `LAG_DAYS` (default: 14)

### 3. Enable Workflows

The workflows will run automatically:
- Check updates: Every 6 hours
- Promote updates: Daily at 8 AM

Manual triggers available in Actions tab.

## Verification

Check the Azure container:

```bash
az storage blob list \
  --container-name m365-updates \
  --account-name your-storage-name \
  --output table
```

Check manifest.json in your repository after first run.

## Uninstall

```bash
# Remove Azure resources
az storage container delete \
  --name m365-updates \
  --account-name your-storage-name

# Remove local files
cd ..
rm -rf m365-update-manager
```

## Troubleshooting

**Command not found after installing uv:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

**Azure authentication errors:**
- Check connection string format
- Verify storage account exists
- Confirm container permissions

**Import errors:**
- Ensure you're using `uv run python script.py`
- Check Python version is 3.11+

**Workflow failures:**
- Verify GitHub secrets are set
- Check workflow logs in Actions tab
- Ensure Azure credentials are valid

## Next Steps

- Review README.md for usage
- Check CONTRIBUTING.md for development
- Read CODE_REVIEW.md for implementation details
