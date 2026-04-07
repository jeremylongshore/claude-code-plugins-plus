---
name: linktree-core-workflow-b
description: |
  Execute Linktree secondary workflow: Analytics & Insights.
  Trigger: "linktree analytics & insights", "secondary linktree workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree — Analytics & Reporting

## Overview

Pull click tracking data, measure conversion rates, and extract audience insights from
your Linktree profile. Use this workflow when you need to understand which links drive
traffic, where your audience comes from, and how engagement trends over time. This is
the secondary workflow — for link creation and profile management, see
`linktree-core-workflow-a`.

## Instructions

### Step 1: Fetch Overall Profile Analytics

```typescript
const analytics = await client.analytics.get({
  profile_id: profile.id,
  period: 'last_30_days',
  granularity: 'daily',
});
console.log(`Total views: ${analytics.views}`);
console.log(`Total clicks: ${analytics.clicks}`);
console.log(`CTR: ${(analytics.clicks / analytics.views * 100).toFixed(1)}%`);
analytics.daily.forEach(d =>
  console.log(`  ${d.date}: ${d.views} views, ${d.clicks} clicks`)
);
```

### Step 2: Rank Per-Link Performance

```typescript
const linkStats = await client.analytics.byLink({
  profile_id: profile.id,
  period: 'last_7_days',
  sort: 'clicks_desc',
});
linkStats.forEach((s, i) =>
  console.log(`#${i + 1} ${s.title}: ${s.clicks} clicks (${s.unique_visitors} unique, CTR ${s.ctr}%)`)
);
```

### Step 3: Pull Audience Demographics

```typescript
const audience = await client.analytics.audience({
  profile_id: profile.id,
  period: 'last_30_days',
});
console.log('Top locations:', audience.locations.slice(0, 5).map(l => `${l.country}: ${l.pct}%`));
console.log('Top referrers:', audience.referrers.slice(0, 5).map(r => `${r.source}: ${r.visits}`));
console.log('Devices:', `Mobile ${audience.devices.mobile}% / Desktop ${audience.devices.desktop}%`);
```

### Step 4: Generate a Conversion Report

```typescript
const report = await client.analytics.report({
  profile_id: profile.id,
  period: 'last_30_days',
  metrics: ['views', 'clicks', 'ctr', 'unique_visitors', 'top_referrers'],
  format: 'json',
});
console.log(`Report period: ${report.start_date} to ${report.end_date}`);
console.log(`Highest CTR link: ${report.top_link.title} (${report.top_link.ctr}%)`);
console.log(`Total unique visitors: ${report.unique_visitors}`);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Expired or invalid bearer token | Re-authenticate via OAuth flow |
| `403 Analytics unavailable` | Free-tier profile without analytics | Upgrade to Pro plan for analytics access |
| `404 Profile not found` | Wrong profile_id | Verify with `client.profiles.list()` |
| `422 Invalid period` | Unsupported date range format | Use `last_7_days`, `last_30_days`, or ISO dates |
| Empty daily array | Profile has zero traffic in range | Widen the date range or verify profile is published |

## Output

A successful workflow produces daily view/click time series, a ranked list of link
performance with CTR, audience demographics broken down by location, referrer, and
device type, and a summary conversion report identifying top-performing links.

## Resources

- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)

## Next Steps

See `linktree-sdk-patterns` for OAuth setup and rate-limit handling.
