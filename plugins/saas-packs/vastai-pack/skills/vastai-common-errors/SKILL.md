---
name: vastai-common-errors
description: |
  Diagnose and fix Vast.ai common errors and exceptions.
  Use when encountering Vast.ai errors, debugging failed instances,
  or troubleshooting GPU rental issues.
  Trigger with phrases like "vastai error", "fix vastai",
  "vastai not working", "debug vastai", "vastai instance failed".
allowed-tools: Read, Grep, Bash(vastai:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, debugging]

---
# Vast.ai Common Errors

## Overview
Quick reference for the most common Vast.ai errors across CLI, REST API, and instance operations. Vast.ai uses HTTP status codes for API errors and instance status strings for machine-level issues.

## Prerequisites
- Vast.ai CLI installed (`pip install vastai`)
- API key configured

## Instructions

### API Errors

| HTTP Code | Error | Cause | Fix |
|-----------|-------|-------|-----|
| 401 | Unauthorized | Invalid or missing API key | Verify with `vastai show user`; regenerate at cloud.vast.ai |
| 403 | Forbidden | Insufficient balance or permissions | Add credits; check account restrictions |
| 404 | Not Found | Instance or offer ID does not exist | Re-search offers; instance may have been destroyed |
| 409 | Conflict | Offer already rented by someone else | Search again and pick another offer |
| 429 | Rate Limited | Too many API requests | Wait 60s and retry with backoff |
| 500 | Server Error | Vast.ai platform issue | Check status.vast.ai; retry after 5 minutes |

### Instance Status Errors

| Status | Meaning | Action |
|--------|---------|--------|
| `loading` | Docker image downloading | Wait; large images can take 5-10 min |
| `running` | Instance ready | Connect via SSH |
| `exited` | Container stopped | Check logs: `vastai logs INSTANCE_ID` |
| `error` | Provisioning failed | Destroy and try a different offer |
| `offline` | Host machine went down | Destroy; provision on a different host |

### Common CLI Errors

```bash
# Error: "No offers found"
# Cause: Filters too restrictive
# Fix: Relax filters
vastai search offers 'num_gpus=1 rentable=true' --limit 5  # broader search

# Error: "Insufficient funds"
# Fix: Check balance and add credits
vastai show user --raw | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Balance: \${d[\"balance\"]:.2f}')"

# Error: "Instance creation failed"
# Fix: Try a different offer or smaller disk
vastai create instance OFFER_ID --image ubuntu --disk 10
```

### Docker Image Errors

```bash
# Error: Instance stuck in "loading" for >10 minutes
# Cause: Very large Docker image or slow host internet
# Fix: Use smaller base images or pre-cached templates
# Good: pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime (4GB)
# Bad:  custom-image-with-everything:latest (30GB)

# Error: "Container exited immediately"
# Cause: Bad entrypoint or missing dependencies
# Fix: Check logs
vastai logs INSTANCE_ID --tail 50
```

### SSH Connection Errors

```bash
# Error: "Connection refused" after instance shows "running"
# Cause: SSH server not yet started inside container
# Fix: Wait 30-60 seconds after status changes to running

# Error: "Permission denied (publickey)"
# Cause: SSH key not uploaded to Vast.ai
# Fix: Upload at cloud.vast.ai > Account > SSH Keys

# Error: "Host key verification failed"
# Fix: Use -o StrictHostKeyChecking=no for ephemeral instances
ssh -p PORT -o StrictHostKeyChecking=no root@HOST
```

### GPU/CUDA Errors

```bash
# Error: "CUDA not available" inside container
# Cause: Docker image missing CUDA or driver mismatch
# Fix: Use NVIDIA-provided images with matching CUDA version
# Check host CUDA: vastai show instance ID --raw | jq '.cuda_max_good'

# Error: "CUDA out of memory"
# Cause: Model too large for GPU VRAM
# Fix: Search for more VRAM or reduce batch size
vastai search offers 'gpu_ram>=48 num_gpus=1' --order dph_total
```

## Output
- Identified error with matching resolution
- Corrected configuration or command
- Verification that the fix resolves the issue

## Error Handling
| Category | Diagnostic Command |
|----------|--------------------|
| Auth issues | `vastai show user` |
| Instance status | `vastai show instances` |
| Instance logs | `vastai logs INSTANCE_ID` |
| Offer availability | `vastai search offers 'rentable=true' --limit 5` |
| Balance check | `vastai show user --raw \| jq '.balance'` |

## Resources
- [Vast.ai Documentation](https://docs.vast.ai)
- [Vast.ai Status Page](https://status.vast.ai)
- [CLI Reference](https://docs.vast.ai/cli/get-started)

## Next Steps
For comprehensive debugging, see `vastai-debug-bundle`.

## Examples

**Instance won't start**: Run `vastai show instance ID --raw | jq '{actual_status, status_msg}'` to get the status message. If `error`, destroy and reprovision on a different host.

**Billing surprise**: Run `vastai show instances` to check for forgotten running instances. Destroy any you're not using to stop charges.
