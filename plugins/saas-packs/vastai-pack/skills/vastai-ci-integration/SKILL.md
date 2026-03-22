---
name: vastai-ci-integration
description: |
  Configure Vast.ai CI/CD integration with GitHub Actions and automated GPU testing.
  Use when setting up automated testing on GPU instances,
  or integrating Vast.ai provisioning into CI/CD pipelines.
  Trigger with phrases like "vastai CI", "vastai github actions",
  "vastai automated testing", "vastai pipeline".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, ci-cd]

---
# Vast.ai CI Integration

## Overview
Integrate Vast.ai GPU provisioning into CI/CD pipelines. Run GPU-accelerated tests, model validation, and benchmarks as part of your automated workflow using GitHub Actions with the Vast.ai CLI.

## Prerequisites
- GitHub repository with Actions enabled
- `VASTAI_API_KEY` stored as GitHub Actions secret
- Docker image for GPU workload published to a registry

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/gpu-test.yml
name: GPU Tests
on:
  push:
    branches: [main]
  pull_request:

jobs:
  gpu-test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - name: Install Vast.ai CLI
        run: |
          pip install vastai
          vastai set api-key ${{ secrets.VASTAI_API_KEY }}

      - name: Provision GPU Instance
        id: provision
        run: |
          # Search for cheapest reliable GPU
          OFFER_ID=$(vastai search offers \
            'num_gpus=1 gpu_ram>=8 reliability>0.95 dph_total<=0.25' \
            --order dph_total --raw --limit 1 \
            | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

          # Create instance
          INSTANCE_ID=$(vastai create instance $OFFER_ID \
            --image ghcr.io/${{ github.repository }}/gpu-test:latest \
            --disk 20 --raw \
            | python3 -c "import sys,json; print(json.load(sys.stdin)['new_contract'])")

          echo "instance_id=$INSTANCE_ID" >> $GITHUB_OUTPUT

          # Wait for running
          for i in $(seq 1 30); do
            STATUS=$(vastai show instance $INSTANCE_ID --raw \
              | python3 -c "import sys,json; print(json.load(sys.stdin).get('actual_status','loading'))")
            echo "Status: $STATUS"
            [ "$STATUS" = "running" ] && break
            sleep 10
          done

      - name: Run GPU Tests
        run: |
          INSTANCE_ID=${{ steps.provision.outputs.instance_id }}
          SSH_INFO=$(vastai show instance $INSTANCE_ID --raw \
            | python3 -c "import sys,json; i=json.load(sys.stdin); print(f'{i[\"ssh_host\"]} {i[\"ssh_port\"]}')")
          SSH_HOST=$(echo $SSH_INFO | cut -d' ' -f1)
          SSH_PORT=$(echo $SSH_INFO | cut -d' ' -f2)

          ssh -p $SSH_PORT -o StrictHostKeyChecking=no root@$SSH_HOST \
            "cd /workspace && python -m pytest tests/gpu/ -v --tb=short"

      - name: Cleanup
        if: always()
        run: |
          vastai destroy instance ${{ steps.provision.outputs.instance_id }} || true
```

### Step 2: Cost-Controlled CI

```python
# scripts/ci_gpu_test.py — wrapper with budget controls
import subprocess, json, time, sys, os

MAX_COST = float(os.environ.get("CI_GPU_BUDGET", "1.00"))  # $1 max per run
MAX_DURATION = int(os.environ.get("CI_GPU_TIMEOUT", "1800"))  # 30 min

def ci_gpu_test(test_command):
    # Search for cheapest offer
    offers = json.loads(subprocess.run(
        ["vastai", "search", "offers",
         "num_gpus=1 gpu_ram>=8 reliability>0.90 dph_total<=0.20",
         "--order", "dph_total", "--raw", "--limit", "1"],
        capture_output=True, text=True, check=True).stdout)

    if not offers:
        print("No GPU offers available — skipping GPU tests")
        return 0

    cost_per_hour = offers[0]["dph_total"]
    max_hours = MAX_COST / cost_per_hour
    print(f"GPU: {offers[0]['gpu_name']} at ${cost_per_hour:.3f}/hr "
          f"(budget allows {max_hours:.1f}hrs)")

    # Provision, run, destroy (with timeout)
    # ... (use managed_instance pattern from sdk-patterns)
```

### Step 3: Mock Mode for Non-GPU CI

```python
# conftest.py — skip GPU tests when no API key available
import pytest, os

def pytest_collection_modifyitems(config, items):
    if not os.environ.get("VASTAI_API_KEY"):
        skip_gpu = pytest.mark.skip(reason="VASTAI_API_KEY not set")
        for item in items:
            if "gpu" in item.keywords:
                item.add_marker(skip_gpu)
```

## Output
- GitHub Actions workflow with GPU instance lifecycle
- Cost-controlled CI with budget limits
- Automatic cleanup on success or failure
- Mock mode for non-GPU CI runs

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| No offers in CI | All cheap GPUs rented | Increase `dph_total` limit or retry later |
| Instance timeout in CI | Slow Docker pull | Use pre-cached images or smaller base images |
| SSH fails in CI | GitHub runner IP blocked | Use Vast.ai API for remote execution instead |
| Cleanup skipped | Job cancelled | Use `if: always()` on cleanup step |

## Resources
- [Vast.ai CLI](https://docs.vast.ai/cli/get-started)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps
For deployment patterns, see `vastai-deploy-integration`.

## Examples

**PR validation**: Run GPU tests on every PR with a $0.50 budget cap. Skip GPU tests on draft PRs.

**Nightly benchmarks**: Schedule a nightly workflow that provisions an A100, runs benchmarks, saves results as artifacts, and posts a cost report.
