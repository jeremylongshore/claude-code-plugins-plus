---
name: supabase-cost-tuning
description: |
  Optimize Supabase costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Supabase billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "supabase cost", "supabase billing",
  "reduce supabase costs", "supabase pricing", "supabase expensive", "supabase budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Cost Tuning

## Prerequisites
- Access to Supabase billing dashboard
- Understanding of current usage patterns
- Database for usage tracking (optional)
- Alerting system configured (optional)

## Instructions

### Step 1: Analyze Current Usage
Review Supabase dashboard for usage patterns and costs.

### Step 2: Select Optimal Tier
Use the cost estimation function to find the right tier.

### Step 3: Implement Monitoring
Add usage tracking to catch budget overruns early.

### Step 4: Apply Optimizations
Enable batching, caching, and sampling where appropriate.

## Output
- Optimized tier selection
- Usage monitoring implemented
- Budget alerts configured
- Cost reduction strategies applied

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase Pricing](https://supabase.com/pricing)
- [Supabase Billing Dashboard](https://dashboard.supabase.com/billing)
