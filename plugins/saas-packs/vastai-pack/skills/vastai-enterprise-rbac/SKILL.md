---
name: vastai-enterprise-rbac
description: |
  Configure Vast.ai enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Vast.ai.
  Trigger with phrases like "vastai SSO", "vastai RBAC",
  "vastai enterprise", "vastai roles", "vastai permissions", "vastai SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vast.ai Enterprise RBAC

## Overview
Control access to Vast.ai GPU cloud instances and spending through team billing and API key management. Vast.ai uses a marketplace model with per-GPU-hour pricing that varies by GPU type (RTX 4090 ~$0.20/hr, A100 ~$1.50/hr, H100 ~$3.00/hr).

## Prerequisites
- Vast.ai account with team billing enabled
- API key from cloud.vast.ai
- Understanding of GPU pricing tiers on the Vast.ai marketplace

## Instructions

### Step 1: Create Scoped API Keys per Team
```bash
# Key for the ML training team (high-end GPUs, high budget)
vastai set api-key --name "ml-training-team" \
  --spending-limit 5000 \  # 5000: 5 seconds in ms
  --allowed-gpu-types "A100,H100" \
  --max-instances 10

# Key for the inference team (cost-efficient GPUs)
vastai set api-key --name "inference-prod" \
  --spending-limit 1000 \  # 1000: 1 second in ms
  --allowed-gpu-types "RTX_4090,RTX_3090,A6000" \
  --max-instances 20
```

### Step 2: Implement GPU Provisioning Policies
```typescript
// vastai-policy.ts - Enforce rules before provisioning
interface ProvisionPolicy {
  allowedGpuTypes: string[];
  maxPricePerHour: number;
  maxInstances: number;
  requireSpotInstance: boolean;
}

const TEAM_POLICIES: Record<string, ProvisionPolicy> = {
  training:  { allowedGpuTypes: ['A100', 'H100'], maxPricePerHour: 4.00, maxInstances: 10, requireSpotInstance: false },
  inference: { allowedGpuTypes: ['RTX_4090', 'RTX_3090'], maxPricePerHour: 0.50, maxInstances: 20, requireSpotInstance: true },
  research:  { allowedGpuTypes: ['RTX_4090'], maxPricePerHour: 0.30, maxInstances: 3, requireSpotInstance: true },
};
```

### Step 3: Set Spending Alerts
```bash
# Configure spending alerts via the Vast.ai CLI
vastai set spending-alert --threshold 1000 --email "ops@company.com"  # 1000: 1 second in ms
vastai set spending-alert --threshold 4000 --email "ops@company.com,finance@company.com"  # 4000: dev server port
vastai set auto-stop --daily-limit 500  # Auto-destroy instances if daily spend exceeds $500
```

### Step 4: Monitor Active Instances and Costs
```bash
# List all running instances with cost data
vastai show instances --raw | jq '.[] | {
  id, gpu_name, num_gpus,
  cost_per_hr: .dph_total,
  hours_running: ((.end_date // now) - .start_date) / 3600,  # 3600: timeout: 1 hour
  total_cost: .total_dph
}'

# Get team spending summary
vastai show invoices --last 30 | jq '.total_cost'
```

### Step 5: Auto-Terminate Idle Instances
```bash
# Cron job: destroy instances idle for more than 2 hours
vastai show instances --raw | \
  jq -r '.[] | select(.gpu_utilization < 5 and .duration > 7200) | .id' | \  # 7200: timeout: 2 hours
  xargs -I{} vastai destroy instance {}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `insufficient_funds` | Account balance depleted | Add credits or enable auto-recharge |
| Instance won't start | GPU type unavailable in region | Try different region or GPU type |
| Spending limit hit | Daily cap reached | Increase limit or wait for next day |
| SSH connection refused | Instance still initializing | Wait 2-3 minutes after creation |

## Examples

**Basic usage**: Apply vastai enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize vastai enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Vastai Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack