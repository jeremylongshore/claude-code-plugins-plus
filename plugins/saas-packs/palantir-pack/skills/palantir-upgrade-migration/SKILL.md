---
name: palantir-upgrade-migration
description: |
  Upgrade Palantir Foundry SDK versions and handle breaking changes.
  Use when upgrading foundry-platform-sdk, migrating between API versions,
  or detecting deprecations in Foundry integrations.
  Trigger with phrases like "upgrade palantir", "palantir migration",
  "foundry breaking changes", "update foundry SDK".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Bash(git:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, upgrade, migration]
compatible-with: claude-code, codex, openclaw
---

# Palantir Upgrade & Migration

## Overview
Safely upgrade `foundry-platform-sdk` versions, handle breaking changes, and migrate between Foundry API versions. Includes a step-by-step upgrade checklist and rollback procedure.

## Prerequisites
- Current `foundry-platform-sdk` installed
- Git for version control
- Test suite covering Foundry API calls
- Staging environment

## Instructions

### Step 1: Check Current Version and Available Updates
```bash
set -euo pipefail
pip show foundry-platform-sdk | grep -E "^(Name|Version)"
pip index versions foundry-platform-sdk 2>/dev/null | head -3
# Check OSDK version too
npm list @osdk/client 2>/dev/null || echo "OSDK not installed"
```

### Step 2: Review Changelog
```bash
# Check GitHub releases for breaking changes
python -c "
import urllib.request, json
url = 'https://api.github.com/repos/palantir/foundry-platform-python/releases?per_page=5'
releases = json.loads(urllib.request.urlopen(url).read())
for r in releases:
    print(f'{r[\"tag_name\"]:12s} {r[\"published_at\"][:10]}')
    body = r.get('body', '')[:200]
    if 'BREAKING' in body.upper():
        print(f'  *** BREAKING CHANGES DETECTED ***')
    print()
"
```

### Step 3: Create Upgrade Branch and Update
```bash
set -euo pipefail
git checkout -b upgrade/foundry-sdk-$(date +%Y%m%d)
pip install --upgrade foundry-platform-sdk
pip show foundry-platform-sdk | grep Version
```

### Step 4: Run Tests and Fix Breaking Changes
```bash
set -euo pipefail
pytest tests/ -v --tb=short 2>&1 | tee upgrade-test-results.txt
# Review failures for breaking changes
grep -E "FAILED|ERROR" upgrade-test-results.txt
```

Common breaking changes between versions:
```python
# v0.x → v1.x: Client initialization changed
# Before:
client = foundry.FoundryClient(auth=foundry.UserTokenAuth(token="..."))
# After:
client = foundry.FoundryClient(
    auth=foundry.UserTokenAuth(hostname="...", token="..."),
    hostname="...",
)

# v1.x → v2.x: Ontology methods moved
# Before:
client.ontology.list_objects(...)
# After:
client.ontologies.OntologyObject.list(...)
```

### Step 5: Verify in Staging
```bash
# Deploy to staging and run smoke tests
FOUNDRY_HOSTNAME=$STAGING_HOSTNAME pytest tests/integration/ -v
```

### Step 6: Rollback Procedure
```bash
# Pin previous version
pip install foundry-platform-sdk==0.8.0
# Or revert the branch
git checkout main -- requirements.txt
pip install -r requirements.txt
```

## Output
- Updated SDK version with all tests passing
- Breaking changes identified and fixed
- Staging verification completed
- Rollback procedure documented

## Error Handling
| Change Type | Detection | Fix |
|-------------|-----------|-----|
| Renamed method | `AttributeError` in tests | Update method calls |
| Changed parameters | `TypeError` in tests | Update function signatures |
| Removed feature | `ImportError` | Find replacement in changelog |
| New required param | `ApiError: 400` | Add missing parameter |

## Resources
- [foundry-platform-python Releases](https://github.com/palantir/foundry-platform-python/releases)
- [PyPI Package](https://pypi.org/project/foundry-platform-sdk/)
- [API Changelog](https://www.palantir.com/docs/foundry/api/general/overview/introduction)

## Next Steps
For CI integration during upgrades, see `palantir-ci-integration`.
