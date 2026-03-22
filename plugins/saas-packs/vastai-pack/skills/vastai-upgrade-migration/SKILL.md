---
name: vastai-upgrade-migration
description: |
  Upgrade Vast.ai CLI, migrate API versions, and handle breaking changes.
  Use when upgrading vastai CLI, detecting deprecations,
  or migrating between API versions.
  Trigger with phrases like "upgrade vastai", "vastai migration",
  "vastai breaking changes", "update vastai CLI".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(vastai:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api, migration]

---
# Vast.ai Upgrade & Migration

## Current State
!`vastai --version 2>/dev/null || echo 'vastai CLI not installed'`
!`pip show vastai 2>/dev/null | grep -E "^(Name|Version)" || echo 'N/A'`

## Overview
Upgrade the Vast.ai CLI and Python SDK, handle API changes, and migrate between GPU configurations. The CLI is distributed via PyPI as `vastai` and tracks the REST API at `cloud.vast.ai/api/v0`.

## Prerequisites
- Current `vastai` CLI installed
- Active instances inventory documented
- Backup of any custom scripts using the API

## Instructions

### Step 1: Check Current Version and Upgrade

```bash
# Check installed version
vastai --version
pip show vastai | grep Version

# Upgrade to latest
pip install --upgrade vastai

# Verify upgrade
vastai --version
vastai show user  # Verify auth still works
```

### Step 2: Detect Breaking Changes

```python
# Compare CLI help output before and after upgrade
import subprocess

def get_cli_commands():
    result = subprocess.run(["vastai", "--help"], capture_output=True, text=True)
    commands = set()
    for line in result.stdout.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('-') and not stripped.startswith('usage'):
            cmd = stripped.split()[0] if stripped.split() else ""
            if cmd.isalpha():
                commands.add(cmd)
    return commands

# Run before and after upgrade to detect removed commands
```

### Step 3: API Version Migration

```python
# The REST API is at v0 — if Vast.ai introduces v1, update base URL
OLD_BASE = "https://cloud.vast.ai/api/v0"
NEW_BASE = "https://console.vast.ai/api/v0"  # Alternative endpoint

# Test both endpoints
import requests
for base in [OLD_BASE, NEW_BASE]:
    try:
        resp = requests.get(f"{base}/users/current",
                           headers={"Authorization": f"Bearer {api_key}"})
        print(f"{base}: {resp.status_code}")
    except Exception as e:
        print(f"{base}: {e}")
```

### Step 4: Docker Image Updates

```bash
# Update GPU workload images to latest CUDA
# Old: pytorch/pytorch:1.13-cuda11.7-runtime
# New: pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# Test new image locally before deploying
docker pull pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime
docker run --rm pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime python -c "import torch; print(torch.__version__)"

# Verify CUDA compatibility with target GPU hosts
vastai search offers 'cuda_max_good>=12.1 num_gpus=1' --limit 5
```

### Step 5: Post-Upgrade Verification

```bash
#!/bin/bash
set -euo pipefail
echo "Post-upgrade verification..."

vastai show user && echo "  Auth: OK"
vastai search offers 'num_gpus=1 rentable=true' --limit 1 --raw | python3 -c "import sys,json; offers=json.load(sys.stdin); print(f'  Search: OK ({len(offers)} offers)')"
vastai show instances && echo "  Instances: OK"

echo "Upgrade verified."
```

## Output
- CLI upgraded to latest version
- Breaking changes identified
- API endpoint compatibility verified
- Docker images updated to latest CUDA
- Post-upgrade verification passed

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| CLI command removed after upgrade | Breaking change in new version | Pin to previous version: `pip install vastai==0.2.8` |
| Auth fails after upgrade | API key format changed | Re-run `vastai set api-key YOUR_KEY` |
| CUDA mismatch after image update | Host CUDA older than image requires | Filter offers by `cuda_max_good>=VERSION` |

## Resources
- [vastai PyPI](https://pypi.org/project/vastai/)
- [vast-cli GitHub](https://github.com/vast-ai/vast-cli)
- [Vast.ai Documentation](https://docs.vast.ai)

## Next Steps
For CI/CD integration, see `vastai-ci-integration`.

## Examples

**Safe upgrade**: Pin the current version in `requirements.txt`, upgrade in a test environment, run the verification script, then update production.

**CUDA migration**: Move from CUDA 11.7 to 12.1 by updating Docker images and filtering offers with `cuda_max_good>=12.1`.
