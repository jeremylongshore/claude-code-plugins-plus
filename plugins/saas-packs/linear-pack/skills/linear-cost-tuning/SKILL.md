---
name: linear-cost-tuning
description: |
  Optimize Linear API usage and manage costs effectively.
  Use when reducing API calls, managing rate limits efficiently,
  or optimizing integration costs.
  Trigger with phrases like "linear cost", "reduce linear API calls",
  "linear efficiency", "linear API usage", "optimize linear costs".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Cost Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Linear API usage to maximize efficiency and minimize costs through caching, batching, and smart query patterns.

## Prerequisites
- Working Linear integration
- Monitoring in place
- Understanding of usage patterns

## Cost Factors

| Factor | Impact | Optimization Strategy |
|--------|--------|----------------------|
| Request count | Direct rate limit | Batch operations |
| Query complexity | Complexity limit | Minimal field selection |
| Payload size | Bandwidth/latency | Pagination, filtering |
| Webhook volume | Processing costs | Event filtering |

## Instructions

### Step 1: Audit Current Usage
Track requests, complexity, and bytes transferred. Project monthly usage to identify optimization targets.

### Step 2: Replace Polling with Webhooks
```typescript
// BAD: Polling every minute
setInterval(async () => {
  const issues = await client.issues({ first: 100 });
  await syncIssues(issues.nodes);
}, 60000);

// GOOD: Use webhooks for real-time updates
app.post("/webhooks/linear", async (req, res) => {
  const event = req.body;
  await handleEvent(event);
  res.sendStatus(200);
});
```

### Step 3: Optimize Query Complexity
```typescript
// BAD: ~500 complexity - deeply nested
const expensive = `query { issues(first: 50) { nodes { id title assignee { name } labels { nodes { name } } comments(first: 10) { nodes { body user { name } } } } } }`;

// GOOD: ~100 complexity - flat fields only
const cheap = `query { issues(first: 50) { nodes { id identifier title priority } } }`;
```

### Step 4: Implement Request Coalescing and Caching
Deduplicate in-flight requests and cache responses with appropriate TTLs.

### Step 5: Filter Webhook Events
Skip bot events, trivial updates, and irrelevant teams to reduce processing load.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for full code examples of usage tracking, conditional fetching, coalescing, and lazy loading patterns.

## Output
- Usage audit with projected monthly costs
- Polling replaced with webhooks
- Query complexity reduced
- Request coalescing and caching active

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Rate limit hit | Too many requests | Implement coalescing + caching |
| Stale data | Cache TTL too long | Invalidate on webhook events |
| High complexity | Nested queries | Flatten queries, fetch separately |
| Webhook overload | Unfiltered events | Add event type/team filtering |

## Examples

### Cost Reduction Checklist
- [ ] Replace polling with webhooks
- [ ] Implement request caching (5-min TTL)
- [ ] Use request coalescing for concurrent calls
- [ ] Filter webhook events by team and field
- [ ] Minimize query complexity (<250 per query)
- [ ] Use lazy loading for static data (teams, states)

## Resources
- [Linear Rate Limiting](https://developers.linear.app/docs/graphql/rate-limiting)
- [Query Complexity Guide](https://developers.linear.app/docs/graphql/complexity)
- [Webhook Best Practices](https://developers.linear.app/docs/graphql/webhooks)

## Next Steps
Learn production architecture with `linear-reference-architecture`.
