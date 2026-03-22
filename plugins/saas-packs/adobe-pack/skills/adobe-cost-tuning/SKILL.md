---
name: adobe-cost-tuning
description: |
  Optimize Adobe API costs across Firefly Services (generative credits),
  PDF Services (document transactions), and Photoshop/Lightroom APIs.
  Use when analyzing Adobe billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "adobe cost", "adobe billing", "adobe credits",
  "reduce adobe costs", "adobe pricing", "adobe budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Cost Tuning

## Overview

Optimize costs across Adobe's consumption-based APIs. Each API family has different pricing models: Firefly uses generative credits, PDF Services uses document transactions, and Photoshop/Lightroom use API call credits.

## Prerequisites

- Access to Adobe Admin Console billing (https://adminconsole.adobe.com)
- Understanding of current API usage patterns
- Monitoring infrastructure for usage tracking

## Instructions

### Step 1: Understand Adobe API Pricing Models

| API | Free Tier | Paid Unit | Key Limit |
|-----|-----------|-----------|-----------|
| **PDF Services** | 500 tx/month | Document Transaction | Per-page for extract, per-file for create |
| **Firefly API** | Trial credits | Generative Credit | 1 credit per image generated |
| **Photoshop API** | Trial credits | API Credit | 1 credit per operation (cutout, actions, etc.) |
| **Lightroom API** | Trial credits | API Credit | 1 credit per auto-edit |
| **I/O Events** | Included | Free with entitlement | 3,000 events/5sec rate limit |
| **Document Generation** | Part of PDF Services | Document Transaction | Per-document generated |

### Step 2: Track Usage per API

```typescript
// src/adobe/usage-tracker.ts
interface ApiUsageEntry {
  api: 'firefly' | 'pdf-services' | 'photoshop' | 'lightroom';
  operation: string;
  timestamp: Date;
  durationMs: number;
  creditsUsed: number;
}

class AdobeUsageTracker {
  private entries: ApiUsageEntry[] = [];

  record(entry: Omit<ApiUsageEntry, 'timestamp'>): void {
    this.entries.push({ ...entry, timestamp: new Date() });
  }

  getMonthlySummary(): Record<string, { calls: number; credits: number }> {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const monthly = this.entries.filter(e => e.timestamp >= monthStart);

    return monthly.reduce((acc, entry) => {
      const key = entry.api;
      if (!acc[key]) acc[key] = { calls: 0, credits: 0 };
      acc[key].calls++;
      acc[key].credits += entry.creditsUsed;
      return acc;
    }, {} as Record<string, { calls: number; credits: number }>);
  }

  checkBudget(api: string, monthlyLimit: number): { remaining: number; warning: boolean } {
    const summary = this.getMonthlySummary();
    const used = summary[api]?.credits || 0;
    const remaining = monthlyLimit - used;
    return { remaining, warning: remaining < monthlyLimit * 0.2 };
  }
}
```

### Step 3: Cost Reduction Strategies

**Strategy 1: Cache Firefly outputs by prompt hash**
```typescript
import crypto from 'crypto';

function promptHash(prompt: string, size: { width: number; height: number }): string {
  return crypto.createHash('sha256')
    .update(`${prompt}:${size.width}x${size.height}`)
    .digest('hex')
    .slice(0, 16);
}

// Before generating, check if identical prompt was already run
const hash = promptHash(prompt, { width: 1024, height: 1024 });
const cached = await cache.get(`firefly:${hash}`);
if (cached) return cached; // Saves 1 generative credit
```

**Strategy 2: Minimize PDF Services transactions**
```typescript
// EXPENSIVE: Extract + Create + Merge = 3 transactions
await extractPdf(input);
await createPdf(html);
await mergePdfs([pdf1, pdf2]);

// CHEAPER: Combine operations where possible
// Use Document Generation API (1 transaction) instead of
// creating PDF then merging
await generateDocument(template, data); // 1 transaction
```

**Strategy 3: Right-size Firefly image dimensions**
```typescript
// Same credit cost but different use cases:
// - Thumbnails: 512x512 (same 1 credit, faster generation)
// - Social media: 1024x1024
// - Print: 2048x2048 (same 1 credit, slower generation)
// Generate at the size you actually need — don't upscale unnecessarily
```

**Strategy 4: Use Photoshop batch actions**
```typescript
// EXPENSIVE: 5 separate API calls = 5 credits
await removeBackground(image1);
await removeBackground(image2);
// ...

// CHEAPER: Photoshop Actions can chain operations
// Record an action that does: remove bg + resize + add watermark
// Run it once per image = 1 credit for all 3 operations
await runPhotoshopAction(image, actionFile);
```

### Step 4: Budget Alert System

```typescript
// Check PDF Services free tier monthly limit
const pdfTracker = new AdobeUsageTracker();

// Wrap PDF Services calls with tracking
async function trackedPdfExtract(pdfPath: string) {
  const budget = pdfTracker.checkBudget('pdf-services', 500); // Free tier

  if (budget.remaining <= 0) {
    throw new Error('PDF Services monthly quota exhausted. Upgrade or wait for reset.');
  }

  if (budget.warning) {
    console.warn(`PDF Services: only ${budget.remaining} transactions remaining this month`);
    // Send alert to Slack/email
  }

  const result = await extractPdfContent(pdfPath);
  pdfTracker.record({
    api: 'pdf-services',
    operation: 'extract',
    durationMs: 0,
    creditsUsed: 1,
  });

  return result;
}
```

### Step 5: Cost Dashboard Query

```sql
-- If tracking usage in your database
SELECT
  api,
  operation,
  DATE_TRUNC('day', timestamp) as date,
  COUNT(*) as calls,
  SUM(credits_used) as credits,
  AVG(duration_ms) as avg_latency_ms
FROM adobe_api_usage
WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1, 2, 3
ORDER BY credits DESC;
```

## Output

- Per-API usage tracking with credit consumption
- Budget alerts at 80% threshold
- Caching to prevent duplicate Firefly credit charges
- Operation batching for Photoshop workflows
- Monthly cost dashboard query

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected charges | Untracked batch jobs | Wrap all calls with usage tracker |
| Free tier exceeded | No budget alerts | Implement 80% warning threshold |
| High Firefly costs | Duplicate prompts | Cache by prompt hash |
| PDF overage | Unnecessary re-extractions | Cache extraction results |

## Resources

- [Adobe PDF Services Pricing](https://developer.adobe.com/document-services/pricing/main/)
- [Firefly Services Documentation](https://developer.adobe.com/firefly-services/docs/guides/)
- [Adobe Admin Console](https://adminconsole.adobe.com)

## Next Steps

For architecture patterns, see `adobe-reference-architecture`.
