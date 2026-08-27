---
name: hex-cost-tuning
description: 'Optimize Hex costs through tier selection, sampling, and usage monitoring.

  Use when analyzing Hex billing, reducing API costs,

  or implementing usage monitoring and budget alerts.

  Trigger with phrases like "hex cost", "hex billing",

  "reduce hex costs", "hex pricing", "hex expensive", "hex budget".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex Cost Tuning

## Overview

Hex pricing combines per-seat licensing with compute-based charges for notebook runs and data connections. Each scheduled or ad-hoc notebook execution consumes compute credits proportional to query complexity and data volume processed. Organizations running dozens of notebooks on hourly schedules — many producing identical results from unchanged data — accumulate unnecessary compute costs. Caching run results, optimizing schedules, and consolidating redundant notebooks are the highest-leverage cost reduction strategies.

## Cost Breakdown

| Component | Cost Driver | Optimization |
|-----------|------------|--------------|
| Seat licenses | Per-user/month (Team: $28/user) | Audit active editors quarterly; move viewers to free tier |
| Notebook runs | Compute per scheduled or manual execution | Cache results for unchanged data; extend run intervals |
| Data connections | Active warehouse/database connections | Consolidate overlapping connections; remove unused ones |
| Scheduled runs | Cron-triggered executions across all projects | Audit schedules — reduce frequency for stable data |
| API calls | Admin and Run API requests | Batch API operations; use cached results endpoint |

## API Call Reduction

```typescript
class HexRunOptimizer {
  private resultCache = new Map<string, { data: any; timestamp: number }>();
  private dataHashes = new Map<string, string>();

  async runIfChanged(projectId: string, runFn: () => Promise<any>): Promise<any> {
    const currentHash = await this.getSourceDataHash(projectId);
    if (this.dataHashes.get(projectId) === currentHash) {
      const cached = this.resultCache.get(projectId);
      if (cached) return cached.data; // Source unchanged — serve cached result
    }
    const result = await runFn();
    this.resultCache.set(projectId, { data: result, timestamp: Date.now() });
    this.dataHashes.set(projectId, currentHash);
    return result;
  }

  private async getSourceDataHash(projectId: string): Promise<string> {
    const res = await fetch(`/api/v1/project/${projectId}/status`);
    return (await res.json()).sourceDataHash;
  }
}
```

## Usage Monitoring

```typescript
class HexCostMonitor {
  private runs = new Map<string, number[]>();
  private weeklyBudget = 500; // max runs per week

  recordRun(projectId: string): void {
    const timestamps = this.runs.get(projectId) || [];
    timestamps.push(Date.now());
    this.runs.set(projectId, timestamps);
  }

  getWeeklyReport(): { totalRuns: number; byProject: Record<string, number> } {
    const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const byProject: Record<string, number> = {};
    let total = 0;
    for (const [id, stamps] of this.runs) {
      const count = stamps.filter(t => t > weekAgo).length;
      byProject[id] = count;
      total += count;
    }
    return { totalRuns: total, byProject };
  }
}
```

## Cost Optimization Checklist

- [ ] Cache notebook results with `updateCacheResult: true`
- [ ] Skip re-runs when source data is unchanged
- [ ] Audit scheduled run frequencies — extend intervals for stable data
- [ ] Move read-only users from Team to free viewer tier
- [ ] Consolidate duplicate notebooks querying the same data
- [ ] Remove unused data connections
- [ ] Set weekly run budget alerts at 80% threshold
- [ ] Identify overrun projects (>20 runs/week) for schedule review

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Compute costs spiking | Hourly schedules on notebooks with daily-changing data | Extend schedule to match data refresh cadence |
| Stale cached results | Source data changed but cache not invalidated | Use source data hash comparison before serving cache |
| API rate limit (429) | Too many concurrent run triggers | Queue runs with concurrency limit of 3 |
| Unused notebooks accruing runs | Abandoned projects still on schedule | Audit and disable schedules for inactive projects |
| Connection pool exhausted | Too many simultaneous data source queries | Consolidate connections; stagger scheduled run times |

## Prerequisites

- An approved budget, baseline run/compute metrics, safe sandbox project, and named owner for each execution path.
- A dry-run plan and rollback revision for schedule, cache, concurrency, and project parameters.

## Instructions

1. Measure aggregate run frequency, duration band, retries, cache behavior, and failure rate before proposing a control.
2. Classify candidates as duplicate, expired, nonessential, or owner-review without inspecting or exporting workspace data.
3. Dry-run the control, compare aggregate cost/run counts and safe project assertions, then canary one project.
4. Promote only with owner approval; roll back for changed output shape, access scope, freshness, or increased failures.
5. Keep a reversible revision and state savings as a range rather than an unsupported guarantee.

## Output

Return a cost-change receipt with baseline/projected runs, control revision, owner approval, canary result, aggregate assertions, estimated savings range, and rollback reference. Exclude SQL, output, and credentials.

## Examples

`project=proj-sandbox-12; baseline_runs=12000; deferred=120; deduped=900; assertions=pass; rollback=cost-r18` is a safe cost decision.

## Resources

- [Hex Pricing](https://hex.tech/pricing/)
- Hex API Documentation

## Next Steps

See `hex-performance-tuning`.
