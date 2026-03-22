---
name: ideogram-performance-tuning
description: |
  Optimize Ideogram API performance with caching, model selection, and parallel generation.
  Use when experiencing slow generation, implementing caching strategies,
  or optimizing throughput for Ideogram integrations.
  Trigger with phrases like "ideogram performance", "optimize ideogram",
  "ideogram latency", "ideogram caching", "ideogram slow", "ideogram speed".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, performance]

---
# Ideogram Performance Tuning

## Overview
Optimize Ideogram image generation for speed, cost, and throughput. Key levers: model and rendering speed selection, prompt-based caching, parallel generation with concurrency limits, and CDN delivery of generated assets.

## Performance Baselines

| Model / Speed | Typical Latency | Relative Cost | Quality |
|---------------|-----------------|---------------|---------|
| V_2_TURBO | 3-6s | ~$0.05/image | Good |
| V_2 | 8-15s | ~$0.08/image | High |
| V3 FLASH | 2-4s | Lowest | Draft |
| V3 TURBO | 4-8s | Low | Good |
| V3 DEFAULT | 8-15s | Standard | High |
| V3 QUALITY | 15-25s | Premium | Highest |

## Instructions

### Step 1: Speed Tiers by Use Case
```typescript
const SPEED_CONFIGS = {
  // Preview / draft mode -- fastest, cheapest
  preview: {
    endpoint: "https://api.ideogram.ai/generate",
    model: "V_2_TURBO",
    note: "3-6s, good enough for iteration",
  },
  // Standard production -- balanced
  standard: {
    endpoint: "https://api.ideogram.ai/generate",
    model: "V_2",
    note: "8-15s, high quality for final assets",
  },
  // V3 with speed control
  v3_fast: {
    endpoint: "https://api.ideogram.ai/v1/ideogram-v3/generate",
    rendering_speed: "TURBO",
    note: "4-8s, V3 quality at faster speed",
  },
  v3_quality: {
    endpoint: "https://api.ideogram.ai/v1/ideogram-v3/generate",
    rendering_speed: "QUALITY",
    note: "15-25s, maximum quality",
  },
} as const;

function getConfig(tier: keyof typeof SPEED_CONFIGS) {
  return SPEED_CONFIGS[tier];
}
```

### Step 2: Prompt-Based Cache Layer
```typescript
import { createHash } from "crypto";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const CACHE_DIR = "./ideogram-cache";

function cacheKey(prompt: string, style: string, aspect: string): string {
  return createHash("sha256")
    .update(`${prompt.toLowerCase().trim()}:${style}:${aspect}`)
    .digest("hex")
    .slice(0, 16);
}

async function cachedGenerate(
  prompt: string,
  options: { style_type?: string; aspect_ratio?: string; model?: string } = {}
) {
  const style = options.style_type ?? "AUTO";
  const aspect = options.aspect_ratio ?? "ASPECT_1_1";
  const key = cacheKey(prompt, style, aspect);
  const metaPath = join(CACHE_DIR, `${key}.json`);
  const imgPath = join(CACHE_DIR, `${key}.png`);

  // Return cached if exists
  if (existsSync(metaPath) && existsSync(imgPath)) {
    console.log(`Cache hit: ${key}`);
    return JSON.parse(readFileSync(metaPath, "utf-8"));
  }

  // Generate and cache
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: options.model ?? "V_2",
        style_type: style,
        aspect_ratio: aspect,
        magic_prompt_option: "AUTO",
      },
    }),
  });

  if (!response.ok) throw new Error(`Generate failed: ${response.status}`);
  const result = await response.json();
  const image = result.data[0];

  // Download and cache
  const imgResp = await fetch(image.url);
  const buffer = Buffer.from(await imgResp.arrayBuffer());

  mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(imgPath, buffer);
  writeFileSync(metaPath, JSON.stringify({
    ...image,
    localPath: imgPath,
    cachedAt: new Date().toISOString(),
  }));

  return { ...image, localPath: imgPath };
}
```

### Step 3: Parallel Generation with Concurrency Control
```typescript
import PQueue from "p-queue";

// 8 concurrent (under Ideogram's 10 in-flight limit)
const queue = new PQueue({ concurrency: 8 });

async function parallelGenerate(
  prompts: string[],
  options: { style_type?: string; model?: string } = {}
) {
  const start = Date.now();

  const results = await Promise.all(
    prompts.map(prompt =>
      queue.add(() => cachedGenerate(prompt, options))
    )
  );

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  console.log(`Generated ${results.length} images in ${elapsed}s`);
  console.log(`Throughput: ${(results.length / (elapsed as any)).toFixed(2)} img/s`);

  return results;
}

// Generate 20 images -- queue manages concurrency automatically
const prompts = Array.from({ length: 20 }, (_, i) => `Product design variant ${i + 1}`);
await parallelGenerate(prompts, { style_type: "DESIGN", model: "V_2_TURBO" });
```

### Step 4: CDN Upload for Fast Delivery
```typescript
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

async function generateWithCDN(prompt: string, options: any = {}) {
  const result = await cachedGenerate(prompt, options);

  // Upload to S3 for CDN delivery
  const key = `ideogram/${result.seed}.png`;
  const buffer = readFileSync(result.localPath);

  await s3.send(new PutObjectCommand({
    Bucket: process.env.S3_BUCKET!,
    Key: key,
    Body: buffer,
    ContentType: "image/png",
    CacheControl: "public, max-age=31536000, immutable",
  }));

  return {
    cdnUrl: `https://${process.env.CDN_DOMAIN}/${key}`,
    seed: result.seed,
    resolution: result.resolution,
  };
}
```

## Performance Tips
1. **Use TURBO for drafts** -- V_2_TURBO is 2-3x faster than V_2 at lower cost
2. **Cache by prompt hash** -- identical prompts produce cacheable results
3. **Batch with num_images** -- 4 images in 1 call is faster than 4 separate calls
4. **Download immediately** -- URLs expire; download in the same function
5. **Set CDN headers** -- images are immutable once generated; cache forever
6. **Use V3 FLASH for previews** -- fastest option for UI thumbnails

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limit 429 | Concurrency too high | Reduce queue concurrency to 5-8 |
| Slow generation | QUALITY speed or complex prompt | Use TURBO for drafts, simplify prompts |
| Expired URL | Delayed download | Download immediately in same function |
| Cache stale | Prompt changed slightly | Normalize prompts before hashing |

## Output
- Speed-tiered configuration for different use cases
- Prompt-based cache layer preventing duplicate generations
- Parallel generation with concurrency control
- CDN integration for fast image delivery

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For cost optimization, see `ideogram-cost-tuning`.
