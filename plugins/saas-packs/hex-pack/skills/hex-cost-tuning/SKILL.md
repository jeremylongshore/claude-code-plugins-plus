---
name: hex-cost-tuning
description: |
  Optimize Hex costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Hex billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "hex cost", "hex billing",
  "reduce hex costs", "hex pricing", "hex expensive", "hex budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Cost Tuning

## Hex Plans

| Plan | Price | API Access | Scheduled Runs | Cron |
|------|-------|------------|----------------|------|
| Free | $0 | No | No | No |
| Team | $28/user/mo | Admin API + Run | Yes | Yes |
| Enterprise | Custom | Full API | Yes | Yes |

## Cost Optimization

### Reduce Unnecessary Runs

```typescript
// Track run frequency per project
const runTracker = new Map<string, number>();
function trackRun(projectId: string) {
  runTracker.set(projectId, (runTracker.get(projectId) || 0) + 1);
}
// Report weekly
setInterval(() => {
  for (const [id, count] of runTracker) console.log(`Project ${id}: ${count} runs`);
  runTracker.clear();
}, 604800000);
```

### Cache Results Instead of Re-Running

Use `updateCacheResult: true` and read cached results instead of triggering new runs for unchanged data.

## Resources

- [Hex Pricing](https://hex.tech/pricing/)
