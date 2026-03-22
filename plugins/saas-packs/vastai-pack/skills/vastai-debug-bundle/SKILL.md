---
name: vastai-debug-bundle
description: |
  Collect Vast.ai debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Vast.ai problems.
  Trigger with phrases like "vastai debug", "vastai support bundle",
  "collect vastai logs", "vastai diagnostic".
allowed-tools: Read, Bash(vastai:*), Bash(curl:*), Bash(ssh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, debugging]

---
# Vast.ai Debug Bundle

## Current State
!`vastai --version 2>/dev/null || echo 'vastai CLI not installed'`
!`python3 --version 2>/dev/null || echo 'Python not available'`

## Overview
Collect comprehensive diagnostic information for Vast.ai GPU instance issues. Covers account verification, instance inspection, log collection, GPU diagnostics, and network testing.

## Prerequisites
- Vast.ai CLI installed and authenticated
- Access to the problematic instance (if still running)

## Instructions

### Step 1: Account and Auth Diagnostics

```bash
#!/bin/bash
set -euo pipefail
echo "=== Vast.ai Debug Bundle ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo -e "\n--- Account Info ---"
vastai show user --raw | python3 -c "
import sys, json
u = json.load(sys.stdin)
print(f'Username: {u.get(\"username\", \"?\")}')
print(f'Balance: \${u.get(\"balance\", 0):.2f}')
print(f'API Key (first 8): {u.get(\"api_key\", \"?\")[:8]}...')
"
```

### Step 2: Instance Status Collection

```bash
echo -e "\n--- All Instances ---"
vastai show instances --raw | python3 -c "
import sys, json
instances = json.load(sys.stdin)
for i in instances:
    print(f'ID: {i[\"id\"]} | Status: {i.get(\"actual_status\", \"?\")} | '
          f'GPU: {i.get(\"gpu_name\", \"?\")} | '
          f'\$/hr: {i.get(\"dph_total\", 0):.3f} | '
          f'SSH: {i.get(\"ssh_host\", \"?\")}:{i.get(\"ssh_port\", \"?\")}')
"
```

### Step 3: Instance Log Collection

```bash
# Collect logs from a specific instance
INSTANCE_ID="${1:-}"
if [ -n "$INSTANCE_ID" ]; then
    echo -e "\n--- Instance $INSTANCE_ID Logs ---"
    vastai logs "$INSTANCE_ID" --tail 100 2>/dev/null || echo "No logs available"

    echo -e "\n--- Instance $INSTANCE_ID Details ---"
    vastai show instance "$INSTANCE_ID" --raw | python3 -c "
import sys, json
i = json.load(sys.stdin)
for key in ['actual_status', 'status_msg', 'gpu_name', 'gpu_ram',
            'cuda_max_good', 'disk_space', 'ssh_host', 'ssh_port',
            'image_uuid', 'onstart', 'reliability2']:
    print(f'{key}: {i.get(key, \"?\")}')
"
fi
```

### Step 4: Remote GPU Diagnostics (if SSH accessible)

```bash
if [ -n "$SSH_HOST" ] && [ -n "$SSH_PORT" ]; then
    echo -e "\n--- GPU Diagnostics (remote) ---"
    ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "root@$SSH_HOST" << 'REMOTE'
nvidia-smi
echo "---"
nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu --format=csv
echo "---"
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null || echo "PyTorch not available"
echo "---"
df -h /workspace
free -h
REMOTE
fi
```

### Step 5: Network Diagnostics

```bash
echo -e "\n--- API Connectivity ---"
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
  -H "Authorization: Bearer $VASTAI_API_KEY" \
  "https://cloud.vast.ai/api/v0/users/current"
echo ""
```

## Output
- Account info (username, balance, key prefix)
- All instance statuses with GPU details
- Instance logs (last 100 lines)
- Remote GPU diagnostics (nvidia-smi, CUDA, disk, memory)
- API connectivity test

## Error Handling
| Issue | Diagnostic | Solution |
|-------|------------|----------|
| Instance shows `error` | Check `status_msg` in details | Destroy and reprovision on different host |
| SSH unreachable | Instance may still be loading | Wait for `running` status |
| GPU not detected | CUDA driver mismatch | Use image matching host CUDA version |
| Disk full | Check `df -h /workspace` | Increase disk or clean artifacts |

## Resources
- [Vast.ai CLI Reference](https://docs.vast.ai/cli/get-started)
- [vast-cli GitHub](https://github.com/vast-ai/vast-cli)

## Next Steps
For rate limit handling, see `vastai-rate-limits`.

## Examples

**Quick debug**: Run `vastai show instance ID --raw | jq '{actual_status, status_msg, gpu_name, ssh_host, ssh_port}'` for a one-line status summary.

**Support ticket**: Collect the full debug bundle output, include `vastai logs ID`, and attach `nvidia-smi` output from the instance.
