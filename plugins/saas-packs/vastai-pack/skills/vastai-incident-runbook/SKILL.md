---
name: vastai-incident-runbook
description: |
  Execute Vast.ai incident response for GPU instance failures and outages.
  Use when responding to instance failures, investigating training crashes,
  or handling spot preemption emergencies.
  Trigger with phrases like "vastai incident", "vastai outage",
  "vastai down", "vastai emergency", "vastai instance failed".
allowed-tools: Read, Grep, Bash(vastai:*), Bash(curl:*), Bash(ssh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, incident-response]

---
# Vast.ai Incident Runbook

## Overview
Rapid incident response procedures for Vast.ai GPU instance failures. Covers triage, mitigation, recovery, and postmortem for common incident types: spot preemption, instance crashes, GPU failures, and billing issues.

## Prerequisites
- Vast.ai CLI access
- SSH access to instances (if still running)
- Checkpoint storage accessible (S3/GCS)

## Instructions

### Triage: Assess Impact (< 2 minutes)

```bash
#!/bin/bash
set -euo pipefail
echo "=== INCIDENT TRIAGE ==="
echo "Time: $(date -u)"

# 1. Check all instances
echo -e "\n--- Instance Status ---"
vastai show instances --raw | python3 -c "
import sys, json
for inst in json.load(sys.stdin):
    status = inst.get('actual_status', '?')
    flag = 'ALERT' if status in ('error', 'exited', 'offline') else 'OK'
    print(f'  [{flag}] ID:{inst[\"id\"]} Status:{status} '
          f'GPU:{inst.get(\"gpu_name\",\"?\")} \${inst.get(\"dph_total\",0):.3f}/hr')
"

# 2. Check if affected instance has recent logs
echo -e "\n--- Recent Logs (last 20 lines) ---"
vastai logs ${INSTANCE_ID:-0} --tail 20 2>/dev/null || echo "No logs available"

# 3. Check account balance
echo -e "\n--- Account ---"
vastai show user --raw | python3 -c "import sys,json; u=json.load(sys.stdin); print(f'Balance: \${u.get(\"balance\",0):.2f}')"
```

### Incident Type 1: Spot Preemption

**Symptoms**: Instance status changes from `running` to `exited` or `offline` without user action.

```bash
# 1. Verify preemption (not user error)
vastai show instance $ID --raw | python3 -c "
import sys, json; i=json.load(sys.stdin)
print(f'Status: {i.get(\"actual_status\")}')
print(f'Status msg: {i.get(\"status_msg\", \"none\")}')
"

# 2. Check if checkpoint was saved
# (depends on your checkpoint storage — S3, GCS, etc.)
aws s3 ls s3://bucket/checkpoints/ --recursive | tail -5

# 3. Provision replacement instance
vastai search offers "gpu_name=${GPU_NAME} reliability>0.98 rentable=true" \
  --order dph_total --limit 3

# 4. Create replacement and resume from checkpoint
vastai create instance $NEW_OFFER_ID --image $IMAGE --disk 50
```

### Incident Type 2: Training Job Crash

**Symptoms**: Instance running but training process exited with error.

```bash
# 1. SSH in and check logs
ssh -p $PORT root@$HOST "tail -100 /workspace/train.log 2>/dev/null || echo 'No log file'"

# 2. Common causes
ssh -p $PORT root@$HOST << 'CHECK'
# GPU memory issue?
nvidia-smi | grep -i "out of memory" && echo "OOM detected"
# Disk full?
df -h /workspace | tail -1
# Process still running?
ps aux | grep python | grep -v grep
CHECK

# 3. Restart training from checkpoint
ssh -p $PORT root@$HOST "cd /workspace && python train.py --resume-from latest"
```

### Incident Type 3: GPU Hardware Failure

**Symptoms**: `nvidia-smi` fails, CUDA errors, or ECC memory errors.

```bash
# 1. Check GPU health
ssh -p $PORT root@$HOST "nvidia-smi" || echo "GPU not responding"

# 2. This is a host-level failure — you cannot fix it
# Destroy the instance and provision on a different host
vastai destroy instance $ID

# 3. Report the host to Vast.ai support
echo "Report host ID to Vast.ai support for investigation"
```

### Incident Type 4: Billing Emergency

```bash
# Stop all billing immediately
echo "EMERGENCY: Destroying all instances"
vastai show instances --raw | python3 -c "
import sys, json, subprocess
for inst in json.load(sys.stdin):
    if inst.get('actual_status') in ('running', 'loading'):
        subprocess.run(['vastai', 'destroy', 'instance', str(inst['id'])])
        print(f'Destroyed instance {inst[\"id\"]}')
"
```

### Postmortem Template

```markdown
## Incident Report
- **Date**: YYYY-MM-DD
- **Duration**: X hours
- **Impact**: N instances affected, $X cost
- **Root cause**: [spot preemption / OOM / disk full / GPU failure]
- **Resolution**: [replaced instance / increased VRAM / expanded disk]
- **Prevention**: [higher reliability filter / checkpoints / auto-recovery]
```

## Output
- Triage script with instant status assessment
- Recovery procedures for 4 incident types
- Emergency billing stop command
- Postmortem template

## Error Handling
| Incident | MTTR Target | Recovery |
|----------|-------------|----------|
| Spot preemption | < 10 min | Auto-provision replacement, resume from checkpoint |
| Training crash | < 5 min | SSH in, diagnose, restart from checkpoint |
| GPU failure | < 15 min | Destroy instance, provision on different host |
| Billing emergency | < 1 min | Destroy all instances immediately |

## Resources
- [Vast.ai Status](https://status.vast.ai)
- [Vast.ai CLI](https://docs.vast.ai/cli/get-started)

## Next Steps
For data handling and security, see `vastai-data-handling`.

## Examples

**Auto-recovery script**: Run the event poller from `vastai-webhooks-events` with an auto-recovery handler that provisions a replacement within 5 minutes of preemption.

**Kill switch**: Keep `vastai show instances && vastai destroy instance ALL` aliased for emergency billing stops.
