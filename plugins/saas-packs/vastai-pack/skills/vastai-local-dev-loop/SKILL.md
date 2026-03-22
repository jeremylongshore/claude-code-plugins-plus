---
name: vastai-local-dev-loop
description: |
  Configure Vast.ai local development with testing and fast iteration.
  Use when setting up a development environment, testing instance provisioning,
  or building a fast iteration cycle for GPU workloads.
  Trigger with phrases like "vastai dev setup", "vastai local development",
  "vastai dev environment", "develop with vastai".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(pip:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, testing, workflow]

---
# Vast.ai Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Vast.ai GPU workloads. Test Docker images locally, mock API responses for CI, and minimize cloud GPU costs during development.

## Prerequisites
- Completed `vastai-install-auth` setup
- Docker installed locally
- Python 3.8+ with pytest

## Instructions

### Step 1: Project Structure

```
vastai-project/
  src/
    vastai_client.py      # API client wrapper
    job_runner.py          # Job orchestration logic
    instance_manager.py   # Instance lifecycle management
  docker/
    Dockerfile            # GPU workload image
    requirements.txt      # Python dependencies for GPU job
  tests/
    test_client.py        # Unit tests with mocked API
    test_job_runner.py    # Integration tests
    conftest.py           # Shared fixtures and mocks
  scripts/
    test-connection.sh    # Quick API verification
    benchmark-gpu.py      # GPU benchmark script
  .env.development        # Dev API key (low spending limit)
  .env.production         # Prod API key (gitignored)
```

### Step 2: Mock the Vast.ai API for Testing

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_vast_client():
    client = MagicMock()
    client.search_offers.return_value = {
        "offers": [
            {"id": 12345, "gpu_name": "RTX_4090", "gpu_ram": 24,
             "dph_total": 0.22, "reliability2": 0.99,
             "inet_down": 500, "ssh_host": "test.host", "ssh_port": 22},
        ]
    }
    client.create_instance.return_value = {"new_contract": 67890}
    client.show_instances.return_value = [
        {"id": 67890, "actual_status": "running",
         "ssh_host": "test.host", "ssh_port": 22}
    ]
    return client
```

### Step 3: Test Docker Images Locally

```bash
# Build and test your GPU image locally (CPU mode)
docker build -t my-training:dev -f docker/Dockerfile .
docker run --rm my-training:dev python -c "import torch; print('OK')"

# Test training script in CPU mode
docker run --rm -v $(pwd)/data:/workspace/data my-training:dev \
  python train.py --epochs 1 --batch-size 4 --device cpu --dry-run
```

### Step 4: Quick Connection Test Script

```bash
#!/bin/bash
set -euo pipefail
echo "Testing Vast.ai connection..."
vastai show user 2>/dev/null && echo "  CLI auth: OK" || echo "  CLI auth: FAIL"
BALANCE=$(vastai show user --raw 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('balance',0))")
echo "  Balance: \$$BALANCE"
echo "Connection verified."
```

### Step 5: Development Workflow

```bash
# 1. Edit Docker image and training code locally
# 2. Test locally with CPU mode
docker build -t my-training:dev . && docker run --rm my-training:dev python train.py --dry-run
# 3. Push image to registry
docker tag my-training:dev ghcr.io/yourorg/training:dev && docker push ghcr.io/yourorg/training:dev
# 4. Rent cheapest GPU for real test
vastai create instance OFFER_ID --image ghcr.io/yourorg/training:dev --disk 20
# 5. Monitor, verify, destroy
vastai show instances && vastai destroy instance INSTANCE_ID
```

## Output
- Project structure with client, tests, and Docker setup
- Mocked Vast.ai client for unit tests (no API calls)
- Local Docker testing workflow (CPU mode)
- Connection verification script

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Docker build fails | Missing CUDA locally | Use CPU-compatible base image for local testing |
| Mock assertions fail | API interface changed | Update mock return values to match current API |
| Balance too low for testing | Dev account underfunded | Add $5 credits for dev testing |
| Image push rejected | Registry auth missing | Run `docker login ghcr.io` first |

## Resources
- [Vast.ai CLI](https://docs.vast.ai/cli/get-started)
- [vast-cli GitHub](https://github.com/vast-ai/vast-cli)

## Next Steps
Proceed to `vastai-sdk-patterns` for production-ready API patterns.

## Examples

**TDD workflow**: Write tests that mock `search_offers` and `create_instance`, implement the job runner to pass tests, then run one real integration test against the API.

**Cost-controlled dev**: Set `dph_total<=0.10` in search queries and auto-destroy after 30 minutes to keep testing costs under $0.05.
