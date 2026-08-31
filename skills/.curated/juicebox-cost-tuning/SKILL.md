---
name: juicebox-cost-tuning
description: 'Optimize Juicebox costs.

  Trigger: "juicebox cost", "juicebox billing", "juicebox budget".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.16.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Cost Tuning

## Cost Factors

| Feature | Cost Driver |
|---------|-------------|
| Search | Per query |
| Enrichment | Per profile |
| Contact data | Per lookup |
| Outreach | Per message |

## Reduction Strategies

1. Cache search results (avoid duplicate queries)
2. Use filters (fewer wasted enrichments)
3. Only enrich top-scored candidates
4. Only get contacts for final candidates

## Quota Monitoring

```typescript
const quota = await client.account.getQuota();
console.log(`Searches: ${quota.searches.used}/${quota.searches.limit}`);
if (quota.searches.used > quota.searches.limit * 0.8) console.warn('80% quota used');
```

## Overview

Use cost controls as a safety boundary: validate them first in a sandbox, reduce unnecessary processing, and never treat cost optimization as permission to expand data or outreach scope.

## Prerequisites

- An approved budget, synthetic sandbox fixture, source/destination allowlists, suppression controls, current quota baseline, and a rollback owner.

## Instructions

1. Measure cache and batching changes with synthetic inputs and aggregate counters only; reject unapproved sources, destinations, or contact exports.
2. Compare each canary to the approved quota baseline, verify suppression and `contacts_exported=0`, and stop on material scope or policy drift.
3. Promote cost settings only after owner approval; restore the prior configuration and cancel queued work on failure.
4. Retain a redacted summary and delete test artifacts at the end of the approved window.

## Output

Record a cost-control receipt with environment, baseline and aggregate usage, cache/batch setting, suppression/no-export results, owner approval, rollback action, and retention/deletion proof. Exclude query text, contacts, and credentials.

## Error Handling

| Condition | Response |
|---|---|
| Budget or quota anomaly | Pause the canary, cancel queued work, and restore the approved configuration. |
| Source, destination, or suppression drift | Reject the run and investigate with redacted aggregate telemetry only. |

## Examples

`env=staging; fixture=synthetic; cache=enabled; usage_delta=-18%; suppression=pass; contacts_exported=0; rollback=available` supports an approval decision.

## Resources

- [Pricing](https://juicebox.ai/pricing)

## Next Steps

See `juicebox-reference-architecture`.
