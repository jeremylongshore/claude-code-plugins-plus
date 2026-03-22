---
name: fondo-performance-tuning
description: |
  Optimize Fondo workflows including faster month-end close, efficient
  data exports, and streamlined CPA communication.
  Trigger: "fondo performance", "fondo faster close", "optimize fondo workflow".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Performance Tuning

## Overview

Speed up Fondo workflows: faster month-end close (target: 15 days), reduced back-and-forth with CPA team, and efficient data export processing.

## Instructions

### Faster Month-End Close

| Bottleneck | Current | Target | How |
|------------|---------|--------|-----|
| Uncategorized transactions | 3-5 days wait | Same day | Set up auto-categorization rules |
| CPA questions | 2-3 day response | 1 day | Batch-answer in single session |
| Missing receipts | 5+ days | 0 days | Use Brex/Ramp auto-receipt capture |
| Bank reconciliation | 2 days | Automated | Ensure Plaid connection is stable |

### Auto-Categorization Rules

```
Dashboard > Settings > Categorization Rules

Examples:
  "AWS" → Cloud Infrastructure (R&D)
  "GitHub" → Software Tools (R&D)
  "Gusto" → Payroll
  "WeWork" → Office/Rent
  "United Airlines" → Travel
  "Uber Eats" → Meals (50% deductible)
```

### Batch CPA Communication

Instead of replying to each question individually:
1. Set aside 30 minutes weekly (e.g., Monday AM)
2. Open Dashboard > Messages > Open Items
3. Answer all outstanding questions in one session
4. This reduces close time by 3-5 days

### Efficient Data Exports

```typescript
// Cache Fondo exports to avoid repeated downloads
const CACHE_DIR = '.cache/fondo';
const CACHE_TTL = 24 * 60 * 60 * 1000;  // 24 hours

async function getCachedExport(reportType: string, dateRange: string) {
  const cacheKey = `${reportType}-${dateRange}.csv`;
  const cachePath = `${CACHE_DIR}/${cacheKey}`;

  if (fs.existsSync(cachePath)) {
    const stat = fs.statSync(cachePath);
    if (Date.now() - stat.mtimeMs < CACHE_TTL) {
      return fs.readFileSync(cachePath, 'utf-8');
    }
  }
  // Download fresh from Dashboard > Reports > Export
  console.log(`Cache miss: download ${reportType} for ${dateRange} from Fondo Dashboard`);
  return null;
}
```

## Resources

- [Fondo Dashboard](https://app.fondo.com)

## Next Steps

For cost optimization, see `fondo-cost-tuning`.
