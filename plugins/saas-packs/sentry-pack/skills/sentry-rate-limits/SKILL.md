---
name: sentry-rate-limits
description: |
  Manage Sentry rate limits and quota optimization.
  Use when hitting rate limits, optimizing event volume,
  or managing Sentry costs.
  Trigger with phrases like "sentry rate limit", "sentry quota",
  "reduce sentry events", "sentry 429".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Rate Limits

## Prerequisites

- Understanding of current event volume
- Sentry billing plan known
- High-volume endpoints identified
- Noisy error patterns documented

## Instructions

1. Check current usage via Sentry API or dashboard stats
2. Implement error sampling with sampleRate for non-critical errors
3. Configure dynamic transaction sampling with tracesSampler
4. Add ignoreErrors patterns for common noisy errors
5. Enable deduplication integration to reduce duplicates
6. Apply client-side filtering in beforeSend hook
7. Set project rate limits via API or dashboard
8. Enable inbound filters for legacy browsers and extensions
9. Monitor event volume and set up quota alerts
10. Adjust sample rates based on billing period usage

## Output
- Optimized sample rates configured
- Rate limiting rules applied
- Event filtering implemented
- Quota usage monitoring setup

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Quota Management](https://docs.sentry.io/product/accounts/quotas/)
- [Sampling Strategies](https://docs.sentry.io/platforms/javascript/configuration/sampling/)

## Overview

Manage Sentry rate limits and quota optimization.