---
name: ideogram-webhooks-events
description: |
  Implement Ideogram webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Ideogram event notifications securely.
  Trigger with phrases like "ideogram webhook", "ideogram events",
  "ideogram webhook signature", "handle ideogram events", "ideogram notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Ideogram Events & Async Patterns

## Overview
Build event-driven workflows around Ideogram's AI image generation API. Ideogram's `api.ideogram.ai` endpoints handle text-to-image and image editing requests. Since generation can take several seconds, this skill covers async patterns for handling generation callbacks, building image processing pipelines, and monitoring generation jobs.

## Prerequisites
- Ideogram API key stored in `IDEOGRAM_API_KEY` environment variable
- Storage solution for generated images (S3, GCS, Cloudflare R2)
- Queue system for batch image generation
- Understanding of Ideogram models (V_2, V_2_TURBO)

## Event Patterns

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| Generation callback | Image generation completes | Asset pipeline processing |
| Batch generation | Multiple prompts queued | Marketing asset creation |
| Image ready notification | Post-processing done | CDN upload and cache warming |
| Generation failure alert | API error or content filter | Retry or manual review |

## Instructions

### Step 1: Async Image Generation with Callbacks
```typescript
import { Queue, Worker } from "bullmq";

interface GenerationJob {
  prompt: string;
  style: "REALISTIC" | "DESIGN" | "RENDER_3D" | "ANIME";
  aspectRatio: "ASPECT_1_1" | "ASPECT_16_9" | "ASPECT_9_16";
  callbackUrl?: string;
  model: "V_2" | "V_2_TURBO";
}

const imageQueue = new Queue("ideogram-generation");

async function queueGeneration(job: GenerationJob) {
  return imageQueue.add("generate", job, {
    attempts: 3,
    backoff: { type: "exponential", delay: 2000 },
  });
}

const worker = new Worker("ideogram-generation", async (job) => {
  const { prompt, style, aspectRatio, model, callbackUrl } = job.data;

  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model,
        style_type: style,
        aspect_ratio: aspectRatio,
        magic_prompt_option: "AUTO",
      },
    }),
  });

  const result = await response.json();
  const images = result.data;

  // Upload generated images to storage
  const uploadedUrls = [];
  for (const image of images) {
    const url = await uploadToStorage(image.url, `generated/${job.id}`);
    uploadedUrls.push(url);
  }

  // Fire callback
  if (callbackUrl) {
    await fetch(callbackUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "ideogram.generation.completed",
        jobId: job.id,
        prompt,
        images: uploadedUrls,
        resolution: images[0]?.resolution,
      }),
    });
  }

  return { images: uploadedUrls };
});
```

### Step 2: Handle Generation Events
```typescript
app.post("/webhooks/ideogram-callback", async (req, res) => {
  const { event, jobId, images, prompt } = req.body;
  res.status(200).json({ received: true });

  switch (event) {
    case "ideogram.generation.completed":
      console.log(`Generated ${images.length} images for: "${prompt}"`);
      await processGeneratedImages(jobId, images);
      break;
    case "ideogram.generation.failed":
      console.error(`Generation failed for job ${jobId}`);
      await handleGenerationFailure(jobId, req.body.error);
      break;
  }
});
```

### Step 3: Batch Marketing Asset Generation
```typescript
async function generateMarketingAssets(campaign: string, prompts: string[]) {
  const jobs = prompts.map(prompt =>
    queueGeneration({
      prompt,
      style: "DESIGN",
      aspectRatio: "ASPECT_16_9",
      model: "V_2",
      callbackUrl: `https://api.myapp.com/webhooks/ideogram-callback`,
    })
  );

  const results = await Promise.all(jobs);
  return results.map(j => j.id);
}
```

### Step 4: Image Post-Processing Pipeline
```typescript
async function processGeneratedImages(jobId: string, imageUrls: string[]) {
  for (const url of imageUrls) {
    // Resize for different platforms
    await imageProcessor.resize(url, { width: 1200, height: 630, format: "og-image" });
    await imageProcessor.resize(url, { width: 1080, height: 1080, format: "instagram" });
    await imageProcessor.resize(url, { width: 1500, height: 500, format: "twitter-header" });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Content filtered | Prompt violates policy | Revise prompt, check content guidelines |
| Rate limited | Too many requests | Queue jobs with concurrency limits |
| Low quality output | Vague prompt | Add style details and negative prompts |
| Timeout | Large batch | Process sequentially with delays |

## Examples

### Quick Single Generation
```bash
curl -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request": {"prompt": "Modern logo for tech startup", "model": "V_2", "style_type": "DESIGN"}}'
```

## Resources
- [Ideogram API Documentation](https://developer.ideogram.ai/api-reference)
- [Ideogram Style Guide](https://developer.ideogram.ai/styles)

## Next Steps
For deployment setup, see `ideogram-deploy-integration`.
