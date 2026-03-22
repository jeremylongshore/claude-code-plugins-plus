---
name: anima-cost-tuning
description: |
  Optimize Anima API costs through caching, incremental generation, and tier selection.
  Use when managing Anima API usage, reducing unnecessary code generations,
  or right-sizing your Anima plan for team size.
  Trigger: "anima cost", "anima pricing", "anima budget", "anima API usage".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, cost-optimization]
compatible-with: claude-code
---

# Anima Cost Tuning

## Pricing Context

Anima uses partner-based pricing (not self-service). API access is currently granted to partners with custom agreements. Costs are typically per-generation or per-seat.

## Cost Optimization Strategies

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| Generation cache | 60-80% | Cache results; only regenerate on design change |
| Incremental generation | 40-60% | Detect changed components; skip unchanged |
| Batch scheduling | 20-30% | Generate during off-peak; avoid real-time |
| Output reuse | 30-50% | Generate once, customize programmatically |

## Instructions

### Step 1: Usage Tracker

```typescript
// src/cost/usage-tracker.ts
interface GenerationRecord {
  timestamp: string;
  fileKey: string;
  nodeId: string;
  cached: boolean;
  durationMs: number;
}

class AnimaUsageTracker {
  private records: GenerationRecord[] = [];

  record(entry: GenerationRecord): void { this.records.push(entry); }

  getReport(): { total: number; cached: number; savings: string } {
    const total = this.records.length;
    const cached = this.records.filter(r => r.cached).length;
    return {
      total,
      cached,
      savings: total > 0 ? `${((cached / total) * 100).toFixed(0)}% saved by caching` : 'No data',
    };
  }
}
```

### Step 2: Smart Generation Policy

```typescript
// Only generate when:
// 1. Figma file version changed (check via Figma API)
// 2. Cache is expired (>1 hour for active dev, >24h for CI)
// 3. Settings changed (new framework/styling)
// 4. Force flag passed (manual override)

async function shouldGenerate(
  fileKey: string,
  nodeId: string,
  cache: any,
): Promise<boolean> {
  // Check cache first
  const cached = cache.get(fileKey, nodeId);
  if (cached && Date.now() - new Date(cached.generatedAt).getTime() < 3600000) {
    console.log('Using cached generation (< 1 hour old)');
    return false;
  }
  return true;
}
```

## Output

- Usage tracking with cache hit rate reporting
- Smart generation policy reducing unnecessary API calls
- Cost savings through caching and incremental updates

## Resources

- [Anima Pricing](https://www.animaapp.com)
- [Anima API](https://docs.animaapp.com/docs/anima-api)

## Next Steps

For architecture design, see `anima-reference-architecture`.
