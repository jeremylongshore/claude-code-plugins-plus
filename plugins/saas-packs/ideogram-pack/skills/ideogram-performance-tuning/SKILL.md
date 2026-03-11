---
name: ideogram-performance-tuning
description: |
  Optimize Ideogram API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Ideogram integrations.
  Trigger with phrases like "ideogram performance", "optimize ideogram",
  "ideogram latency", "ideogram caching", "ideogram slow", "ideogram batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Ideogram Performance Tuning

## Overview
Optimize Ideogram image generation pipelines for throughput, cost, and latency. Focus on prompt reuse, resolution selection, parallel generation, and CDN caching for generated assets.

## Prerequisites
- Ideogram API key
- Image storage (S3, GCS, or local filesystem)
- Understanding of Ideogram generation parameters
- CDN or caching layer for generated images

## Instructions

### Step 1: Optimize Generation Parameters
```typescript
const IDEOGRAM_API = 'https://api.ideogram.ai/generate';

// Quality tiers for different use cases
const QUALITY_PRESETS = {
  draft: { resolution: '512x512', model: 'V_2', steps: 20 },
  standard: { resolution: '1024x1024', model: 'V_2', steps: 30 },
  premium: { resolution: '1024x1024', model: 'V_2_TURBO', steps: 50 },
};

async function generateImage(
  prompt: string,
  preset: keyof typeof QUALITY_PRESETS = 'standard'
) {
  const config = QUALITY_PRESETS[preset];
  const response = await fetch(IDEOGRAM_API, {
    method: 'POST',
    headers: {
      'Api-Key': process.env.IDEOGRAM_API_KEY!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        aspect_ratio: 'ASPECT_1_1',
        model: config.model,
        magic_prompt_option: 'AUTO',
      },
    }),
  });
  return response.json();
}
```

### Step 2: Prompt-Based Cache Layer
```typescript
import { createHash } from 'crypto';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const CACHE_DIR = './image-cache';

function promptHash(prompt: string, preset: string): string {
  return createHash('sha256')
    .update(`${preset}:${prompt.toLowerCase().trim()}`)
    .digest('hex')
    .slice(0, 16);
}

async function cachedGenerate(prompt: string, preset = 'standard') {
  const hash = promptHash(prompt, preset);
  const cachePath = join(CACHE_DIR, `${hash}.json`);

  if (existsSync(cachePath)) {
    return JSON.parse(readFileSync(cachePath, 'utf-8'));
  }

  const result = await generateImage(prompt, preset as any);

  mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(cachePath, JSON.stringify(result));
  return result;
}
```

### Step 3: Batch Generation with Concurrency Control
```typescript
async function batchGenerate(
  prompts: string[],
  concurrency = 2 // Ideogram rate limits are strict
) {
  const results: any[] = [];

  for (let i = 0; i < prompts.length; i += concurrency) {
    const batch = prompts.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(p => cachedGenerate(p))
    );
    results.push(...batchResults);

    // Rate limit: ~10 requests/minute on standard plans
    if (i + concurrency < prompts.length) {
      await new Promise(r => setTimeout(r, 6000));
    }
  }
  return results;
}
```

### Step 4: Image Asset Pipeline
```typescript
import { pipeline } from 'stream/promises';
import { createWriteStream } from 'fs';

async function downloadAndStore(imageUrl: string, outputPath: string) {
  const response = await fetch(imageUrl);
  if (!response.ok) throw new Error(`Download failed: ${response.status}`);

  const fileStream = createWriteStream(outputPath);
  await pipeline(response.body as any, fileStream);
  return outputPath;
}

async function generateAndStore(prompt: string, outputDir: string) {
  const result = await cachedGenerate(prompt);
  const imageUrl = result.data?.[0]?.url;
  if (!imageUrl) throw new Error('No image URL in response');

  const hash = promptHash(prompt, 'standard');
  const outputPath = join(outputDir, `${hash}.png`);
  return downloadAndStore(imageUrl, outputPath);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limit 429 | Too many concurrent requests | Limit concurrency to 2, add 6s delays |
| Generation timeout | Complex prompt or high resolution | Use draft preset, simplify prompt |
| NSFW rejection | Content filter triggered | Review prompt for flagged terms |
| Expired URL | Image URLs are temporary | Download immediately, cache locally |

## Examples

### Brand Asset Batch Generation
```typescript
const brandPrompts = [
  'Minimalist logo for tech startup, blue gradient, clean lines',
  'Social media banner, abstract geometric pattern, brand colors',
  'App icon, rounded square, modern flat design',
];

const assets = await batchGenerate(brandPrompts);
console.log(`Generated ${assets.length} brand assets`);
```

## Resources
- [Ideogram API Reference](https://docs.ideogram.ai/api)
- [Ideogram Model Guide](https://docs.ideogram.ai/models)
