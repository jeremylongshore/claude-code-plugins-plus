---
name: gamma-cost-tuning
description: |
  Optimize Gamma usage costs and manage API spending.
  Use when reducing API costs, implementing usage quotas,
  or planning for scale with budget constraints.
  Trigger with phrases like "gamma cost", "gamma billing",
  "gamma budget", "gamma expensive", "gamma pricing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, api, scaling, cost-optimization]

---
# Gamma Cost Tuning

## Overview

Optimize Gamma API usage to minimize credit consumption. Gamma uses a credit-based billing system where costs are driven by image generation model tier and content complexity. API access requires Pro or higher subscription.

## Prerequisites

- Active Gamma Pro/Ultra/Teams/Business subscription
- Understanding of credit system
- Completed `gamma-install-auth` setup

## Gamma Credit System

### Image Model Tiers

| Tier | Credits per Image | Quality Level |
|------|-------------------|---------------|
| Standard | 2-15 | Good for internal/draft presentations |
| Advanced | 20-33 | Higher quality, more detail |
| Premium | 34-75 | Best quality images |
| Ultra | 30-125 | Highest fidelity, photorealistic |

Card text generation also costs credits based on the AI model used.

### Plan Comparison

| Feature | Pro | Ultra | Teams | Business |
|---------|-----|-------|-------|----------|
| Monthly credits | Included | More credits | Team pool | Custom |
| API access | Yes | Yes | Yes | Yes |
| Max cards | Standard | Up to 75 | Standard | Custom |
| Ad-hoc credit purchase | Yes | Yes | Yes | Yes |
| Auto-recharge | Yes | Yes | Yes | Yes |

## Instructions

### Step 1: Track Credit Usage

```typescript
// src/gamma/cost-tracker.ts
interface UsageEntry {
  generationId: string;
  creditsUsed: number;
  outputFormat: string;
  timestamp: Date;
}

class CreditTracker {
  private usage: UsageEntry[] = [];

  record(entry: UsageEntry) {
    this.usage.push(entry);
  }

  getDaily(): { total: number; count: number; avg: number } {
    const today = new Date().toDateString();
    const todayUsage = this.usage.filter(
      (u) => u.timestamp.toDateString() === today
    );
    const total = todayUsage.reduce((sum, u) => sum + u.creditsUsed, 0);
    return {
      total,
      count: todayUsage.length,
      avg: todayUsage.length > 0 ? Math.round(total / todayUsage.length) : 0,
    };
  }

  getMonthly(): { total: number; count: number } {
    const thisMonth = new Date().getMonth();
    const monthUsage = this.usage.filter(
      (u) => u.timestamp.getMonth() === thisMonth
    );
    return {
      total: monthUsage.reduce((sum, u) => sum + u.creditsUsed, 0),
      count: monthUsage.length,
    };
  }
}

// Track after each generation
const tracker = new CreditTracker();

async function generateTracked(gamma: GammaClient, request: GenerateRequest) {
  const { generationId } = await gamma.generate(request);
  const result = await pollUntilDone(gamma, generationId);

  tracker.record({
    generationId,
    creditsUsed: result.creditsUsed ?? 0,
    outputFormat: request.outputFormat ?? "presentation",
    timestamp: new Date(),
  });

  return result;
}
```

### Step 2: Optimize Image Costs

The biggest cost driver is image generation tier. Reduce costs by:

```typescript
// EXPENSIVE: default image settings (may use Advanced/Premium tier)
await gamma.generate({
  content: "Company quarterly review",
  outputFormat: "presentation",
  // No imageOptions = AI chooses model tier
});

// CHEAPER: explicitly use standard tier when quality isn't critical
await gamma.generate({
  content: "Company quarterly review",
  outputFormat: "presentation",
  imageOptions: {
    style: "simple flat illustration", // Simpler styles use fewer credits
  },
});

// CHEAPEST: text-focused, minimal images
await gamma.generate({
  content: "Company quarterly review",
  outputFormat: "document", // Documents typically use fewer images
  textAmount: "detailed",   // Focus on text, not visuals
});
```

### Step 3: Use Templates to Reduce Regeneration

```typescript
// WASTEFUL: regenerating entire presentations for minor content changes
for (const client of clients) {
  await gamma.generate({
    content: `Proposal for ${client.name}: ${fullProposalText}`,
    outputFormat: "presentation",
  });
  // Each generation costs full credits
}

// EFFICIENT: use templates for repeated structures
// Create a one-page template gamma in the app
// Then generate variations with targeted prompts
for (const client of clients) {
  await gamma.generateFromTemplate({
    gammaId: "template_proposal_id",
    prompt: `Customize for ${client.name}. Focus on ${client.industry}.`,
    exportAs: "pdf",
  });
  // Template generations can be more cost-effective
}
```

### Step 4: Budget Alerts

```typescript
// src/gamma/budget.ts
const MONTHLY_BUDGET = 5000; // credits
const ALERT_THRESHOLDS = [0.5, 0.75, 0.9, 1.0]; // 50%, 75%, 90%, 100%

async function checkBudget(tracker: CreditTracker) {
  const { total } = tracker.getMonthly();
  const percentUsed = total / MONTHLY_BUDGET;

  for (const threshold of ALERT_THRESHOLDS) {
    if (percentUsed >= threshold) {
      await sendAlert(
        `Gamma budget ${(threshold * 100)}% used: ${total}/${MONTHLY_BUDGET} credits`
      );
    }
  }

  // Hard stop at 100%
  if (percentUsed >= 1.0) {
    throw new Error(`Monthly Gamma budget exceeded: ${total}/${MONTHLY_BUDGET} credits`);
  }
}
```

### Step 5: Caching to Avoid Regeneration

```typescript
// Cache generation results to avoid paying twice for same content
import NodeCache from "node-cache";

const generationCache = new NodeCache({ stdTTL: 86400 }); // 24 hour TTL

async function generateCached(
  gamma: GammaClient,
  request: GenerateRequest
): Promise<GenerateResult> {
  // Create cache key from request parameters
  const key = JSON.stringify({
    content: request.content,
    outputFormat: request.outputFormat,
    themeId: request.themeId,
    textMode: request.textMode,
  });

  const cached = generationCache.get<GenerateResult>(key);
  if (cached) {
    console.log("Cache hit — skipping generation");
    return cached;
  }

  const result = await generateAndWait(gamma, request);
  generationCache.set(key, result);
  return result;
}
```

## Cost Reduction Summary

| Strategy | Credit Savings | Implementation |
|----------|---------------|----------------|
| Standard image tier | 50-80% on images | Set `imageOptions.style` to simpler styles |
| Templates over ad-hoc | 20-40% | Use `generateFromTemplate` for repeated content |
| Caching results | 100% on duplicates | Cache by content hash |
| Text-focused output | 30-50% | Use `document` format, `textAmount: "detailed"` |
| Budget caps | Prevents overrun | Track credits, alert at thresholds |
| Auto-recharge | Avoids disruption | Enable at gamma.app/settings/billing |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Credits exhausted | Over budget | Purchase ad-hoc credits or enable auto-recharge |
| Unexpected high cost | Premium image tier | Specify `imageOptions.style` explicitly |
| Budget alert missed | Tracker not running | Verify tracking on all generation paths |

## Resources

- [Gamma Pricing](https://gamma.app/pricing)
- [API Access and Pricing](https://developers.gamma.app/docs/get-access)
- [Credit System Explained](https://developers.gamma.app/get-started/access-and-pricing)

## Next Steps

Proceed to `gamma-reference-architecture` for architecture patterns.
