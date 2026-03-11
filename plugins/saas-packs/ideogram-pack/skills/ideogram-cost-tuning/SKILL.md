---
name: ideogram-cost-tuning
description: |
  Optimize Ideogram costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Ideogram billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "ideogram cost", "ideogram billing",
  "reduce ideogram costs", "ideogram pricing", "ideogram expensive", "ideogram budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Ideogram Cost Tuning

## Overview
Reduce Ideogram AI image generation costs by optimizing credit usage per generation, choosing appropriate model quality, and implementing generation caching. Ideogram uses credit-based pricing where each generation costs credits based on model version (V_2 vs V_2_TURBO) and quality settings. The key cost levers are: using V_2_TURBO for drafts and iteration (faster, fewer credits), reserving V_2 for final outputs, and caching generated images for repeated similar prompts.

## Prerequisites
- Ideogram API account with credit balance visibility
- Understanding of model differences (V_2 vs V_2_TURBO)
- Image storage for caching generated outputs

## Instructions

### Step 1: Use the Right Model for the Right Phase
```yaml
# Model selection by workflow phase
draft_iteration:
  model: V_2_TURBO
  quality: standard
  use_for: "Exploring concepts, testing prompts, quick previews"
  cost: "~1 credit per generation"

final_production:
  model: V_2
  quality: high
  use_for: "Final marketing assets, client deliverables"
  cost: "~2-3 credits per generation"

# Workflow: Generate 5 drafts with TURBO (5 credits) -> pick best -> regenerate with V_2 (3 credits)
# Total: 8 credits instead of 15 credits (5 x V_2)
```

### Step 2: Optimize Resolution Settings
```typescript
// Only use high resolution when needed
const RESOLUTION_CONFIGS: Record<string, { resolution: string; credits: number }> = {
  'social-thumbnail':  { resolution: 'RESOLUTION_512_512',   credits: 1 },
  'blog-header':       { resolution: 'RESOLUTION_1024_576',  credits: 1 },
  'marketing-banner':  { resolution: 'RESOLUTION_1024_1024', credits: 2 },
  'print-quality':     { resolution: 'RESOLUTION_1024_1024', credits: 3 }, // V_2 + high quality
};

function getResolution(useCase: string) {
  return RESOLUTION_CONFIGS[useCase] || RESOLUTION_CONFIGS['social-thumbnail'];
}
```

### Step 3: Cache Generated Images
```typescript
import { createHash } from 'crypto';

// Cache images by prompt hash to avoid regenerating identical content
const imageCache = new Map<string, { url: string; timestamp: number }>();

async function cachedGeneration(prompt: string, options: any) {
  const key = createHash('md5').update(`${prompt}:${JSON.stringify(options)}`).digest('hex');
  const cached = imageCache.get(key);
  if (cached && Date.now() - cached.timestamp < 7 * 24 * 3600 * 1000) {
    return cached.url; // Reuse for 7 days
  }
  const result = await ideogram.generate({ image_request: { prompt, ...options } });
  imageCache.set(key, { url: result.data[0].url, timestamp: Date.now() });
  return result.data[0].url;
}
```

### Step 4: Batch Similar Generations
```typescript
// Generate variations in a single API call instead of multiple calls
async function generateVariations(prompt: string, count: number = 4) {
  // Single API call generates up to 4 images
  const result = await ideogram.generate({
    image_request: {
      prompt,
      model: 'V_2_TURBO',
      magic_prompt_option: 'AUTO',
      num_images: count, // 1 API call for 4 images vs 4 separate calls
    },
  });
  return result.data;
}
```

### Step 5: Monitor Credit Burn Rate
```bash
# Track credit consumption and forecast depletion
curl -s https://api.ideogram.ai/v1/usage \
  -H "Api-Key: $IDEOGRAM_API_KEY" | \
  jq '{
    credits_remaining: .credits_remaining,
    used_today: .credits_used_today,
    used_month: .credits_used_month,
    daily_avg: (.credits_used_month / 30),
    days_until_empty: (.credits_remaining / ((.credits_used_month / 30) + 0.01))
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credits exhausted mid-project | No budget tracking | Set daily credit alerts at 80% of daily budget |
| Regenerating same images | No caching implemented | Cache by prompt hash, reuse for 7 days |
| High cost per final image | Using V_2 for all iterations | Draft with V_2_TURBO, finalize with V_2 |
| Unexpected credit drain | High-res generations for small uses | Match resolution to actual display size needed |

## Examples
```bash
# Cost comparison: draft vs production workflow
echo "5 iterations all on V_2: ~15 credits"
echo "4 drafts on V_2_TURBO + 1 final V_2: ~7 credits"
echo "Savings: 53%"
```
