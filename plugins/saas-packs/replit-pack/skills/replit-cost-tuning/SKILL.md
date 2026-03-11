---
name: replit-cost-tuning
description: |
  Optimize Replit costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Replit billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "replit cost", "replit billing",
  "reduce replit costs", "replit pricing", "replit expensive", "replit budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Replit Cost Tuning

## Overview
Optimize Replit costs by right-sizing deployment tiers, managing compute resources, and controlling AI feature (Ghostwriter) consumption. Replit pricing combines per-seat subscription (Teams: ~$25/seat/month) with deployment compute costs (billed by CPU/memory/egress). The biggest cost levers are: using Reserved VMs for predictable workloads instead of on-demand (40% savings), configuring auto-sleep for development Repls, and right-sizing deployment resources to actual usage.

## Prerequisites
- Replit Teams account with billing access
- Deployment usage metrics from Replit dashboard
- Understanding of compute resource needs per application

## Instructions

### Step 1: Audit Compute Costs by Repl
```bash
# Check resource consumption across team Repls
curl "https://replit.com/api/v1/teams/TEAM_ID/usage?period=last_30d" \
  -H "Authorization: Bearer $REPLIT_API_KEY" | \
  jq '.usage | sort_by(-.cost_usd) | .[0:10] | .[] | {repl_name, cpu_hours, memory_gb_hours, egress_gb, cost_usd}'
```

### Step 2: Right-Size Deployment Resources
```yaml
# Match resources to actual workload needs
undersized:  # Causes crashes, bad UX
  cpu: 0.25 vCPU
  memory: 512 MB
  cost: "$5/month"

right_sized:  # Handles normal traffic
  cpu: 0.5 vCPU
  memory: 1 GB
  cost: "$10/month"

oversized:  # Wasting money
  cpu: 2 vCPU
  memory: 4 GB
  cost: "$40/month"

# Check actual usage: if peak CPU <30% and peak memory <50%, downsize
```

### Step 3: Use Reserved VMs for Production
```yaml
# Reserved VMs vs on-demand pricing
on_demand:
  price: "Pay per CPU-second and memory-second"
  best_for: "Development, testing, low-traffic apps"
  tip: "Enable auto-sleep (stops billing when no traffic)"

reserved:
  price: "Fixed monthly rate, ~40% cheaper than on-demand at full utilization"
  best_for: "Production apps with consistent traffic"
  tip: "Choose reserved when app runs >16 hours/day"
```

### Step 4: Configure Auto-Sleep for Dev Environments
In Repl Settings > Deployment:
- Enable "Sleep after inactivity" for development Repls (default: 5 minutes)
- Set auto-sleep timeout to 2 minutes for rarely-used tools
- Keep always-on only for production deployments that need instant response

### Step 5: Optimize Seat Costs
```yaml
# Seat audit
audit:
  total_seats: 15
  active_daily: 8
  active_weekly: 11
  inactive_30d: 4

# Strategy:
# - Remove 4 inactive members: saves $100/month (at $25/seat)
# - Consider Teams Lite for members who only need read access
# - Share Repls between team members instead of duplicating
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High compute bill | Repls running 24/7 with low traffic | Enable auto-sleep for non-production |
| Cold start complaints | Auto-sleep waking too slowly | Use Reserved VM for customer-facing apps |
| Egress costs high | Serving large files from Repl | Move static assets to CDN (Cloudflare, Vercel) |
| Seat costs growing | Team expanding without audit | Quarterly seat utilization review |

## Examples
```bash
# Quick cost check: which Repls cost the most?
curl -s "https://replit.com/api/v1/teams/TEAM_ID/usage?period=last_30d" \
  -H "Authorization: Bearer $REPLIT_API_KEY" | \
  jq '{
    total_cost: ([.usage[].cost_usd] | add),
    top_3: [.usage | sort_by(-.cost_usd) | .[0:3] | .[] | {repl: .repl_name, cost: .cost_usd}]
  }'
```
