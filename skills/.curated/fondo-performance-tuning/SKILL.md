---
name: fondo-performance-tuning
description: 'Optimize Fondo workflows including faster month-end close, efficient

  data exports, and streamlined CPA communication.

  Trigger: "fondo performance", "fondo faster close", "optimize fondo workflow".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Performance Tuning

## Overview

Speed up Fondo workflows: faster month-end close (target: 15 days), reduced back-and-forth with CPA team, and efficient data export processing.

## Prerequisites

- A named finance owner, approved close calendar, data-access policy, and aggregate baseline for close time and exception volume.
- Synthetic/sample data for workflow tests; real financial records remain in the approved accounting environment.

## Output

Produce an operational receipt with period, aggregate bottleneck metrics, approved workflow change, owner, verification date, and unresolved exceptions. Do not include account numbers, transactions, tax documents, or credentials.

## Error Handling

- Pause automation when an import, categorization, or reconciliation result is incomplete or unexpected; route it to the finance owner.
- Do not replace professional review with an automated classification or calculator result.
- Redact all financial data in performance diagnostics and roll back changes that harm accuracy or auditability.

## Examples

Use a fictional month of aggregate expenses to test a categorization workflow. Compare only close duration and exception count, then have the authorized finance reviewer approve the result before changing a live process.

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

- Fondo Dashboard

## Next Steps

For cost optimization, see `fondo-cost-tuning`.
