---
name: flyio-cost-tuning
description: |
  Optimize Fly.io costs with auto-stop/suspend, right-sizing VMs,
  volume management, and monitoring spend across apps and regions.
  Trigger: "fly.io costs", "fly.io pricing", "fly.io billing", "reduce fly.io spend".
allowed-tools: Read, Write, Edit, Bash(fly:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Cost Tuning

## Overview

Fly.io charges per-second for running machines plus storage. Key levers: auto-stop idle machines, suspend instead of stop, right-size VMs, and clean up unused volumes.

## Pricing Quick Reference

| Resource | Free Tier | Cost |
|----------|-----------|------|
| shared-cpu-1x (256mb) | 3 VMs free | ~$1.94/month each |
| shared-cpu-1x (512mb) | included | ~$3.88/month |
| shared-cpu-2x (1gb) | - | ~$11.62/month |
| Volumes | 3GB free | $0.15/GB/month |
| Bandwidth | 100GB free | $0.02/GB after |
| IPv4 | 1 free per org | $2/month each |

## Instructions

### Strategy 1: Auto-Stop Idle Machines

```toml
# fly.toml — stop machines when no traffic
[http_service]
  auto_stop_machines = "stop"     # Full stop (cheapest, ~5s cold start)
  auto_start_machines = true
  min_machines_running = 0        # Allow all machines to stop
  # Use min_machines_running = 1 only for production apps
```

### Strategy 2: Suspend for Faster Resume

```toml
# Suspend keeps memory state — resumes in ~100ms but costs ~$0.50/month
[http_service]
  auto_stop_machines = "suspend"
```

### Strategy 3: Audit and Clean Up

```bash
# List all apps and their machine counts
fly apps list

# Find idle/stopped machines
fly machine list -a my-app --json | jq '.[] | select(.state != "started") | {id, state, region}'

# Destroy unused apps
fly apps destroy old-app --yes

# List and delete orphaned volumes
fly volumes list -a my-app
fly volumes destroy vol_xxx
```

### Strategy 4: Right-Size VMs

```bash
# Check memory usage to see if oversized
fly ssh console -a my-app -C "cat /proc/meminfo | head -3"

# Downgrade if using <50% of allocated memory
fly scale vm shared-cpu-1x --memory 256 -a my-app
```

### Cost Monitoring

```bash
# Check current month's usage
fly billing  # Shows org-level billing

# Estimate per-app cost
fly scale show -a my-app  # See VM count and size
```

## Resources

- [Fly.io Pricing](https://fly.io/docs/about/pricing/)
- [Auto Stop/Start](https://fly.io/docs/launch/autostop-autostart/)

## Next Steps

For architecture design, see `flyio-reference-architecture`.
