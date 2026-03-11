---
name: gamma-cost-tuning
description: |
  Optimize Gamma usage costs and manage API spending.
  Use when reducing API costs, implementing usage quotas,
  or planning for scale with budget constraints.
  Trigger with phrases like "gamma cost", "gamma billing",
  "gamma budget", "gamma expensive", "gamma pricing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Gamma Cost Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Gamma API usage to minimize costs through usage monitoring, quotas, caching, and smart AI generation patterns.

## Prerequisites
- Active Gamma subscription
- Access to usage dashboard
- Understanding of pricing tiers

## Instructions

### Step 1: Implement Usage Monitoring
Track daily usage by operation type (presentations, generations, exports, API calls). Alert at 80% of plan limits.

### Step 2: Configure Per-User Quotas
Set quotas per user with auto-reset. Check quotas before API calls and decrement on success.

### Step 3: Optimize AI Generation
Use templates with targeted AI generation only for slides that need it, rather than full AI generation for every slide.

### Step 4: Add Response Caching
Use Redis with 1-hour TTL to eliminate redundant API calls for repeated data.

### Step 5: Batch Operations
Replace individual API calls with batch operations. Queue non-urgent work for off-peak processing.

### Step 6: Set Budget Alerts
Configure threshold alerts at 50%, 75%, 90%, and 100% of monthly budget. Auto-disable non-critical features at budget cap.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Usage monitoring with alerts
- Per-user quota system
- Optimized AI generation patterns
- Caching layer for API calls
- Budget management with auto-cutoff

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Quota exceeded | Heavy usage | Increase quota or throttle |
| Budget overrun | No alerts set | Configure threshold alerts |
| Cache stale data | Long TTL | Reduce TTL or add invalidation |

## Examples

### Gamma Pricing Reference
| Resource | Free | Pro | Team | Enterprise |
|----------|------|-----|------|------------|
| Presentations/mo | 10 | 100 | 500 | Custom |
| AI generations | 5 | 50 | 200 | Unlimited |
| Exports/mo | 10 | 100 | 500 | Unlimited |

### Cost Reduction Strategies
| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Caching | 30-50% | Redis/in-memory cache |
| Batching | 20-40% | Batch API calls |
| Templates | 40-60% | Reduce AI usage |
| Off-peak | 10-20% | Queue for low-cost periods |

## Resources
- [Gamma Pricing](https://gamma.app/pricing)
- [Gamma Usage Dashboard](https://gamma.app/dashboard/usage)
