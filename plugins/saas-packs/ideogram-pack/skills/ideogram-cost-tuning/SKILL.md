---
name: ideogram-cost-tuning
description: |
  Optimize Ideogram costs through model selection, caching, and usage monitoring.
  Use when analyzing Ideogram billing, reducing API costs,
  or implementing budget alerts and usage tracking.
  Trigger with phrases like "ideogram cost", "ideogram billing",
  "reduce ideogram costs", "ideogram pricing", "ideogram budget", "ideogram credits".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, cost-optimization]

---
# Ideogram Cost Tuning

## Overview
Minimize Ideogram API spending by selecting the right model per task, caching identical prompts, batching images per call, and tracking credit burn rate. Ideogram bills per image generated at a flat rate that varies by model and rendering speed.

## Pricing Reference

| Model / Speed | Approx. Cost per Image | Best For |
|---------------|------------------------|----------|
| V_2_TURBO | ~$0.05 | Drafts, iteration, testing |
| V_2 | ~$0.08 | Final production assets |
| V3 FLASH | ~$0.03-0.04 | Quick previews |
| V3 TURBO | ~$0.05 | Good quality at speed |
| V3 DEFAULT | ~$0.06-0.08 | Standard production |
| V3 QUALITY | ~$0.09+ | Premium deliverables |
| + Character ref | +$0.02-0.04 | Consistent character faces |

*Prices approximate; check [ideogram.ai/features/api-pricing](https://ideogram.ai/features/api-pricing) for current rates.*

## Instructions

### Step 1: Two-Phase Generation Workflow
```typescript
// Draft with TURBO (cheap), finalize with V_2 (quality)
async function costEfficientGeneration(prompt: string, iterations = 5) {
  // Phase 1: Generate drafts cheaply
  const drafts = [];
  for (let i = 0; i < iterations; i++) {
    const result = await generateImage(prompt, { model: "V_2_TURBO" });
    drafts.push(result);
  }
  // Cost: 5 x $0.05 = $0.25

  // Phase 2: Pick best seed, regenerate at full quality
  const bestSeed = await selectBestDraft(drafts); // manual or automated
  const final = await generateImage(prompt, { model: "V_2", seed: bestSeed });
  // Cost: 1 x $0.08 = $0.08

  // Total: $0.33 instead of $0.40 (5 x V_2)
  return final;
}
```

### Step 2: Batch Images Per Call
```typescript
// Single API call for up to 4 images costs the same as 4 separate calls
// BUT saves latency (one round-trip instead of four)
async function generateVariations(prompt: string) {
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: "V_2_TURBO",
        num_images: 4, // 4 images in one call
        magic_prompt_option: "AUTO",
      },
    }),
  });

  const result = await response.json();
  return result.data; // 4 image objects
}
```

### Step 3: Cache Identical Prompts
```typescript
import { createHash } from "crypto";

const cache = new Map<string, { url: string; seed: number; cachedAt: number }>();
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function promptKey(prompt: string, style: string, model: string): string {
  return createHash("md5").update(`${prompt}:${style}:${model}`).digest("hex");
}

async function cachedGeneration(prompt: string, style = "AUTO", model = "V_2") {
  const key = promptKey(prompt, style, model);
  const cached = cache.get(key);

  if (cached && Date.now() - cached.cachedAt < CACHE_TTL_MS) {
    console.log("Cache hit -- saved one generation credit");
    return cached;
  }

  const result = await generateImage(prompt, { style_type: style, model });
  // Download and store locally before caching (URLs expire)
  const localPath = await downloadImage(result.data[0].url);
  cache.set(key, {
    url: localPath,
    seed: result.data[0].seed,
    cachedAt: Date.now(),
  });

  return cache.get(key);
}
```

### Step 4: Budget Tracking
```typescript
interface CostTracker {
  totalImages: number;
  totalCostUSD: number;
  byModel: Record<string, { count: number; cost: number }>;
  dailyBudgetUSD: number;
}

const tracker: CostTracker = {
  totalImages: 0,
  totalCostUSD: 0,
  byModel: {},
  dailyBudgetUSD: 10, // $10/day cap
};

const MODEL_COSTS: Record<string, number> = {
  V_2_TURBO: 0.05,
  V_2: 0.08,
  V_2A: 0.04,
  V_2A_TURBO: 0.025,
};

function trackGeneration(model: string, numImages: number) {
  const costPerImage = MODEL_COSTS[model] ?? 0.08;
  const cost = costPerImage * numImages;

  tracker.totalImages += numImages;
  tracker.totalCostUSD += cost;

  if (!tracker.byModel[model]) tracker.byModel[model] = { count: 0, cost: 0 };
  tracker.byModel[model].count += numImages;
  tracker.byModel[model].cost += cost;

  // Budget alert
  if (tracker.totalCostUSD > tracker.dailyBudgetUSD * 0.8) {
    console.warn(`Budget warning: $${tracker.totalCostUSD.toFixed(2)} of $${tracker.dailyBudgetUSD}/day`);
  }
  if (tracker.totalCostUSD > tracker.dailyBudgetUSD) {
    throw new Error(`Daily budget exceeded: $${tracker.totalCostUSD.toFixed(2)}`);
  }
}

function costReport() {
  console.log("=== Ideogram Cost Report ===");
  console.log(`Total images: ${tracker.totalImages}`);
  console.log(`Total cost: $${tracker.totalCostUSD.toFixed(2)}`);
  for (const [model, data] of Object.entries(tracker.byModel)) {
    console.log(`  ${model}: ${data.count} images, $${data.cost.toFixed(2)}`);
  }
}
```

### Step 5: Billing Auto Top-Up Configuration
```
Ideogram Dashboard > Settings > API Beta > Billing:

Recommended settings:
  Top-up Balance: $20.00 (default)
  Minimum Threshold: $10.00 (default)

Conservative (small projects):
  Top-up Balance: $10.00
  Minimum Threshold: $5.00

Enterprise:
  Contact partnership@ideogram.ai for volume pricing
  1M+ images/month for custom rates
```

## Cost Optimization Checklist
- [ ] Use V_2_TURBO for iteration, V_2 for final assets only
- [ ] Cache identical prompts (7-day TTL)
- [ ] Batch with `num_images: 4` where possible
- [ ] Track daily spend with budget alerts
- [ ] Use V3 FLASH for UI previews and thumbnails
- [ ] Download images immediately (regeneration = double cost)
- [ ] Set conservative auto top-up limits

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 402 credits exhausted | Balance depleted | Top up in dashboard, check auto top-up |
| Regenerating same images | No cache | Cache by prompt hash |
| High daily cost | Using V_2 for everything | Draft with TURBO, finalize with V_2 |
| Unexpected charges | High-res for thumbnails | Match model to use case |

## Output
- Two-phase generation workflow (draft then finalize)
- Prompt-based cache preventing duplicate charges
- Budget tracker with daily spending alerts
- Cost report by model version

## Resources
- [Ideogram API Pricing](https://ideogram.ai/features/api-pricing)
- [API Billing Setup](https://developer.ideogram.ai/ideogram-api/api-setup)

## Next Steps
For architecture patterns, see `ideogram-reference-architecture`.
