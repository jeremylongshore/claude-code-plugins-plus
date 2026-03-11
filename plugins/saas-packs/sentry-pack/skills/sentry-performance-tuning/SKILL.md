---
name: sentry-performance-tuning
description: |
  Optimize Sentry performance monitoring configuration.
  Use when tuning sample rates, reducing overhead,
  or improving performance data quality.
  Trigger with phrases like "sentry performance optimize", "tune sentry tracing",
  "sentry overhead", "improve sentry performance".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Performance Tuning

## Prerequisites

- Performance monitoring enabled
- Transaction volume metrics available
- Critical paths identified
- Performance baseline established

## Instructions

1. Implement dynamic sampling with tracesSampler for endpoint-specific rates
2. Configure environment-based sample rates (higher in dev, lower in prod)
3. Remove unused integrations to reduce SDK overhead
4. Limit breadcrumbs to reduce memory usage
5. Use parameterized transaction names to avoid cardinality explosion
6. Create spans only for meaningful slow operations
7. Configure profile sampling sparingly for performance-critical endpoints
8. Measure SDK initialization time and ongoing overhead
9. Implement high-volume optimization with aggressive filtering
10. Monitor SDK performance metrics and adjust configuration

## Output
- Optimized sample rates configured
- SDK overhead minimized
- Transaction naming standardized
- Resource usage reduced

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Performance](https://docs.sentry.io/product/performance/)
- [Sampling Strategies](https://docs.sentry.io/platforms/javascript/configuration/sampling/)
