---
name: hootsuite-cost-tuning
description: 'Optimize Hootsuite costs through tier selection, sampling, and usage
  monitoring.

  Use when analyzing Hootsuite billing, reducing API costs,

  or implementing usage monitoring and budget alerts.

  Trigger with phrases like "hootsuite cost", "hootsuite billing",

  "reduce hootsuite costs", "hootsuite pricing", "hootsuite expensive", "hootsuite
  budget".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hootsuite
- social-media
compatibility: Designed for Claude Code
---
# Hootsuite Cost Tuning

## Hootsuite Plans

| Plan | Price | Profiles | Users | API Access |
|------|-------|----------|-------|------------|
| Professional | $99/mo | 10 | 1 | REST API |
| Team | $249/mo | 20 | 3 | REST API |
| Business | $739/mo | 35 | 5+ | Full API + webhooks |
| Enterprise | Custom | 50+ | Unlimited | Full API + SCIM |

## Cost Optimization

### Step 1: Minimize API Calls

```typescript
// Cache profile lists (don't refetch every request)
// Batch schedule posts (one session, many messages)
// Use bulk endpoints where available
```

### Step 2: Right-Size Your Plan

```typescript
// Audit actual profile usage
async function auditUsage() {
  const profiles = await getCachedProfiles();
  console.log(`Active profiles: ${profiles.length}`);
  console.log(`Networks: ${[...new Set(profiles.map(p => p.type))].join(', ')}`);
  // If using < 10 profiles, Professional plan may suffice
}
```

### Step 3: Track API Usage

```typescript
let apiCallCount = 0;
const originalFetch = fetch;
globalThis.fetch = async (...args) => {
  if (String(args[0]).includes('hootsuite.com')) apiCallCount++;
  return originalFetch(...args);
};
// Log periodically
setInterval(() => { console.log(`Hootsuite API calls: ${apiCallCount}`); apiCallCount = 0; }, 3600000);
```

## Overview

Tune social operations using aggregate volume and quota data. A cost saving is invalid if it widens account access, removes approval, changes audience targeting, or causes duplicate/public posts.

## Prerequisites

- An approved budget, account inventory, baseline API/quota metrics, and named owner for each social profile.
- A sandbox/draft-only rehearsal, rollback revision for schedule/cache/concurrency, and an approval path for any audience change.

## Instructions

1. Measure aggregate publish, schedule, retry, and quota counts before proposing a control; never export unpublished copy merely to assess cost.
2. Classify candidates as duplicate, expired, nonessential, or owner-review, retaining draft and approval state.
3. Dry-run the change against draft-only content, compare aggregate counts and approval/audience assertions, then canary one non-production profile.
4. Promote only with owner approval; roll back for duplicate posting, target drift, approval bypass, or increased failures.
5. State savings as a range and preserve a reversible schedule/configuration revision.

## Output

Return a cost-change receipt with baseline/projected counts, control revision, owner approval, draft/canary result, approval/audience assertions, savings range, and rollback reference. Exclude copy, tokens, and account identities.

## Error Handling

Stop for unknown profile, destination, audience, approval state, or an attempt to apply a cost control directly to public content. Revert to the prior schedule/configuration rather than bypass review.

## Examples

`profile=sandbox-brand; baseline=12000; deferred=120; deduped=900; approval=pass; audience=unchanged; rollback=cost-r18` is a safe cost decision.

## Resources

- [Hootsuite Pricing](https://www.hootsuite.com/plans)

## Next Steps

For architecture, see `hootsuite-reference-architecture`.
