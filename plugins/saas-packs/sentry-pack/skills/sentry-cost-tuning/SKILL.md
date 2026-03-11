---
name: sentry-cost-tuning
description: |
  Optimize Sentry costs and event volume.
  Use when managing Sentry billing, reducing event volume,
  or optimizing quota usage.
  Trigger with phrases like "reduce sentry costs", "sentry billing",
  "sentry quota", "optimize sentry spend".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Cost Tuning

## Prerequisites

- Current Sentry billing plan known
- Event volume metrics available
- High-volume error sources identified
- Cost reduction target defined

## Instructions

1. Review current usage and cost breakdown by event type
2. Implement error sampling to reduce volume (e.g., 50% sampleRate)
3. Configure aggressive transaction sampling (1% or lower for high-volume)
4. Add ignoreErrors and denyUrls patterns for common noise
5. Enable server-side inbound filters in project settings
6. Set project rate limits to cap maximum events
7. Reduce event size with maxValueLength and maxBreadcrumbs limits
8. Disable unused features (replays, profiling) if not needed
9. Configure tiered environment settings (disable in dev, reduce in staging)
10. Set up spend alerts and monitor cost projections monthly

## Output
- Optimized sample rates
- Event filtering rules
- Cost projection updated
- Spend alerts configured

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Pricing](https://sentry.io/pricing/)
- [Quota Management](https://docs.sentry.io/product/accounts/quotas/)
