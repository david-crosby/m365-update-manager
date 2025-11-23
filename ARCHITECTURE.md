# M365 Update Manager - Architecture Diagram

## System Overview

```
┌───────────────────────────────────────────────────────────────┐
│                      GitHub Actions                            │
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │  Check Updates   │         │  Promote Updates │           │
│  │  (Every 6 hours) │         │  (Daily 8am)     │           │
│  └────────┬─────────┘         └────────┬─────────┘           │
└───────────┼──────────────────────────────┼────────────────────┘
            │                              │
            ↓                              ↓
┌───────────────────────────────────────────────────────────────┐
│                  Python Application                            │
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │ check_updates.py │         │   promote.py     │           │
│  │                  │         │                  │           │
│  │ • Fetch manifest │         │ • Check lag      │           │
│  │ • Check for new  │         │ • Move blobs     │           │
│  │ • Download PKGs  │         │ • Update state   │           │
│  │ • Upload to blob │         │ • Commit changes │           │
│  │ • Update state   │         │                  │           │
│  └────────┬─────────┘         └────────┬─────────┘           │
└───────────┼──────────────────────────────┼────────────────────┘
            │                              │
            ↓                              ↓
┌───────────────────────────────────────────────────────────────┐
│                   Core Components                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  MAUClient   │  │   Manifest   │  │ AzureStorage │       │
│  │              │  │   Manager    │  │   Client     │       │
│  │ • Fetch XML  │  │              │  │              │       │
│  │ • Follow FW  │  │ • Track state│  │ • Upload     │       │
│  │ • Download   │  │ • Validate   │  │ • Copy       │       │
│  │ • Hash check │  │ • Promote    │  │ • Delete     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
┌───────────────────────────────────────────────────────────────┐
│                    External Services                           │
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │   Microsoft      │         │  Azure Blob      │           │
│  │   CDN (MAU)      │         │    Storage       │           │
│  │                  │         │                  │           │
│  │ • Update XMLs    │         │ ├── staged/      │           │
│  │ • Package URLs   │         │ ├── live/        │           │
│  │ • Version info   │         │ └── previous/    │           │
│  └──────────────────┘         └──────────────────┘           │
└───────────────────────────────────────────────────────────────┘
```

## Data Flow - Update Check

```
1. GitHub Actions triggers check_updates.py
                │
                ↓
2. Load manifest.json from repository
                │
                ↓
3. For each app in config:
   ├── Fetch update manifest from Microsoft CDN
   ├── Extract version, URL, SHA256
   ├── Compare with manifest state
   └── If new version:
       ├── Download PKG file
       ├── Verify SHA256 hash
       ├── Upload to Azure (staged/)
       └── Update manifest (staged state)
                │
                ↓
4. Commit updated manifest.json
                │
                ↓
5. Create GitHub issue notification
```

## Data Flow - Promotion

```
1. GitHub Actions triggers promote.py
                │
                ↓
2. Load manifest.json from repository
                │
                ↓
3. Check which apps are ready (lag period elapsed)
                │
                ↓
4. For each ready app:
   ├── Copy live/ → previous/
   ├── Copy staged/ → live/
   ├── Delete staged/ version
   └── Update manifest (promote state)
                │
                ↓
5. Commit updated manifest.json
                │
                ↓
6. Create GitHub issue notification
```

## State Transitions

```
New Update Detected
        │
        ↓
[STAGED] ─────────> Wait lag_days
        │
        ↓
[LIVE] ─────────> Currently deployed
        │
        ↓
[PREVIOUS] ─────> Available for rollback
```

## Rollback Flow

```
Issue Detected
        │
        ↓
Run: promote.py --rollback <app>
        │
        ↓
Swap live ↔ previous in manifest
        │
        ↓
Copy previous/ → live/ in blob storage
        │
        ↓
Update complete
```

## File Relationships

```
Repository Structure:
.
├── src/
│   ├── config.py           (Apps, CDN URLs, Settings)
│   ├── mau_client.py       (Microsoft CDN client)
│   ├── azure_storage.py    (Blob operations)
│   └── manifest.py         (State management)
│
├── check_updates.py        (Main update script)
├── promote.py              (Promotion script)
│
├── manifest.json           (Current state)
│   └── tracks: staged, live, previous per app
│
└── .github/workflows/
    ├── check-updates.yml   (Automated checks)
    └── promote-updates.yml (Automated promotions)
```

## Blob Storage Structure

```
Azure Container: m365-updates/

staged/
├── word.pkg           (Waiting for promotion)
├── excel.pkg
├── powerpoint.pkg
└── ...

live/
├── word.pkg           (Currently deployed)
├── excel.pkg
├── powerpoint.pkg
└── ...

previous/
├── word.pkg           (Available for rollback)
├── excel.pkg
├── powerpoint.pkg
└── ...
```

## Manifest Structure

```json
{
  "last_updated": "2024-11-23T14:30:00Z",
  "channel": "current",
  "lag_days": 14,
  "apps": {
    "word": {
      "app_id": "MSWD2019",
      "name": "Microsoft Word",
      "blob_name": "word.pkg",
      "staged": {
        "version": "16.81.0",
        "sha256": "abc123...",
        "download_url": "https://...",
        "staged_at": "2024-11-20T10:00:00Z"
      },
      "live": {
        "version": "16.80.0",
        "sha256": "def456...",
        "download_url": "https://...",
        "promoted_at": "2024-11-10T08:00:00Z"
      },
      "previous": {
        "version": "16.79.0",
        "sha256": "ghi789...",
        "download_url": "https://...",
        "promoted_at": "2024-10-28T08:00:00Z"
      }
    }
  }
}
```

## Security Flow

```
Secrets Management:
    GitHub Secrets
         │
         ↓
    Environment Variables
         │
         ↓
    Settings Class
         │
         ↓
    Azure/MAU Clients
```

## Testing Flow

```
Developer
    │
    ↓
git commit
    │
    ↓
Pre-commit Hooks
    ├── Ruff format
    ├── Ruff lint
    └── MyPy type check
    │
    ↓
git push
    │
    ↓
GitHub Actions CI
    ├── Test Python 3.11
    ├── Test Python 3.12
    ├── Test Python 3.13
    ├── Run all tests
    ├── Check coverage
    └── Type checking
    │
    ↓
Merge to main
```

## Integration Points

```
┌─────────────┐
│   Jamf Pro  │ ← Can pull from live/ URLs
└─────────────┘

┌─────────────┐
│  Munki      │ ← Can reference blob URLs
└─────────────┘

┌─────────────┐
│  AutoPkg    │ ← Can check manifest for versions
└─────────────┘

┌─────────────┐
│  Dashboard  │ ← Could read manifest.json
└─────────────┘
```

## Monitoring Points

```
✓ Check Updates Success/Failure
✓ Download Success/Failure
✓ Upload Success/Failure
✓ Promotion Success/Failure
✓ Manifest Commit Success/Failure
✓ Time spent in each tier
✓ Storage costs
✓ Network bandwidth
```
