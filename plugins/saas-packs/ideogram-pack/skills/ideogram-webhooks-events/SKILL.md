---
name: ideogram-webhooks-events
description: |
  Build event-driven workflows around Ideogram's synchronous API.
  Use when implementing async generation queues, batch processing,
  callback patterns, or image processing pipelines.
  Trigger with phrases like "ideogram webhook", "ideogram events",
  "ideogram async", "ideogram queue", "ideogram batch pipeline".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, webhooks, async, queue]

---
# Ideogram Events & Async Patterns

## Overview
Ideogram's API is synchronous -- each call blocks until the image is generated (5-15 seconds). For production applications, wrap it in async patterns: job queues for batch generation, callbacks for downstream processing, and pipelines for image post-processing. This skill covers BullMQ queue patterns, callback handlers, and asset processing pipelines.

## Prerequisites
- `IDEOGRAM_API_KEY` configured
- Redis for BullMQ job queue
- Storage for generated images (S3, GCS, or R2)
- Understanding of Ideogram models and style types

## Instructions

### Step 1: Job Queue for Async Generation
```typescript
import { Queue, Worker } from "bullmq";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

interface GenerationJob {
  prompt: string;
  style: string;
  aspectRatio: string;
  model: string;
  callbackUrl?: string;
  metadata?: Record<string, string>;
}

const connection = { host: "localhost", port: 6379 };
const imageQueue = new Queue("ideogram-generation", { connection });

// Enqueue a generation job
async function submitGeneration(job: GenerationJob) {
  return imageQueue.add("generate", job, {
    attempts: 3,
    backoff: { type: "exponential", delay: 2000 },
    removeOnComplete: 100,
    removeOnFail: 50,
  });
}

// Worker processes jobs with concurrency limit
const worker = new Worker("ideogram-generation", async (job) => {
  const { prompt, style, aspectRatio, model, callbackUrl, metadata } = job.data;

  // Call Ideogram API (synchronous, blocks 5-15s)
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: model || "V_2",
        style_type: style || "AUTO",
        aspect_ratio: aspectRatio || "ASPECT_1_1",
        magic_prompt_option: "AUTO",
      },
    }),
  });

  if (response.status === 429) {
    throw new Error("Rate limited"); // BullMQ will retry with backoff
  }
  if (!response.ok) {
    throw new Error(`Ideogram API error: ${response.status}`);
  }

  const result = await response.json();
  const image = result.data[0];

  // Download immediately (URLs expire)
  const imgResp = await fetch(image.url);
  const buffer = Buffer.from(await imgResp.arrayBuffer());
  const outputDir = "./generated";
  mkdirSync(outputDir, { recursive: true });
  const filePath = join(outputDir, `${image.seed}.png`);
  writeFileSync(filePath, buffer);

  // Fire callback if provided
  if (callbackUrl) {
    await fetch(callbackUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "generation.completed",
        jobId: job.id,
        prompt,
        seed: image.seed,
        resolution: image.resolution,
        filePath,
        metadata,
      }),
    });
  }

  return { seed: image.seed, filePath, resolution: image.resolution };
}, {
  connection,
  concurrency: 5, // Stay under 10 in-flight limit
});

worker.on("failed", (job, err) => {
  console.error(`Job ${job?.id} failed:`, err.message);
});
```

### Step 2: Callback Handler
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/callbacks/ideogram", async (req, res) => {
  const { event, jobId, seed, filePath, metadata } = req.body;
  res.status(200).json({ received: true });

  switch (event) {
    case "generation.completed":
      console.log(`Image generated: seed=${seed}, path=${filePath}`);
      await processImage(filePath, metadata);
      break;
    case "generation.failed":
      console.error(`Generation failed: job=${jobId}`);
      await notifyFailure(jobId, req.body.error);
      break;
  }
});
```

### Step 3: Batch Marketing Asset Generation
```typescript
async function generateMarketingCampaign(
  campaignName: string,
  products: string[],
  formats: Array<{ name: string; aspect: string; style: string }>
) {
  const jobs = [];

  for (const product of products) {
    for (const format of formats) {
      const job = await submitGeneration({
        prompt: `${product}, professional ${format.name} design, high quality`,
        style: format.style,
        aspectRatio: format.aspect,
        model: "V_2",
        callbackUrl: "https://api.myapp.com/callbacks/ideogram",
        metadata: { campaign: campaignName, product, format: format.name },
      });
      jobs.push(job);
    }
  }

  console.log(`Submitted ${jobs.length} generation jobs for campaign: ${campaignName}`);
  return jobs.map(j => j.id);
}

// Example: Generate all assets for a product launch
await generateMarketingCampaign("Q1 Launch", [
  "Cloud analytics dashboard",
  "Mobile payment app",
], [
  { name: "social-square", aspect: "ASPECT_1_1", style: "DESIGN" },
  { name: "story-vertical", aspect: "ASPECT_9_16", style: "DESIGN" },
  { name: "blog-hero", aspect: "ASPECT_16_9", style: "REALISTIC" },
]);
```

### Step 4: Image Post-Processing Pipeline
```typescript
import sharp from "sharp";

async function processImage(filePath: string, metadata?: Record<string, string>) {
  const variants = [
    { suffix: "-og", width: 1200, height: 630 },       // Open Graph
    { suffix: "-thumb", width: 400, height: 400 },      // Thumbnail
    { suffix: "-social", width: 1080, height: 1080 },   // Instagram
  ];

  for (const variant of variants) {
    const outputPath = filePath.replace(".png", `${variant.suffix}.webp`);
    await sharp(filePath)
      .resize(variant.width, variant.height, { fit: "cover" })
      .webp({ quality: 85 })
      .toFile(outputPath);
    console.log(`Created variant: ${outputPath}`);
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many concurrent jobs | Set worker concurrency to 5 |
| Content filtered | Prompt violates policy | Log and skip, notify reviewer |
| Expired URL | Worker too slow | Download in same worker step |
| Queue stalled | Redis connection lost | Configure BullMQ connection retry |
| Callback fails | Downstream service down | Fire-and-forget with retry queue |

## Output
- BullMQ job queue for async generation
- Callback handler for downstream processing
- Batch generation for marketing campaigns
- Post-processing pipeline with sharp

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [BullMQ Documentation](https://docs.bullmq.io/)
- [sharp Image Processing](https://sharp.pixelplumbing.com/)

## Next Steps
For performance optimization, see `ideogram-performance-tuning`.
