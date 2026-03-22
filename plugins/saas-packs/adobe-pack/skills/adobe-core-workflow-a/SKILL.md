---
name: adobe-core-workflow-a
description: |
  Execute Adobe Firefly Services workflow: AI image generation, generative fill,
  and expand image using the Firefly v3 API.
  Use when generating images from prompts, filling or expanding images with AI,
  or building creative automation pipelines.
  Trigger with phrases like "adobe firefly", "generate image adobe",
  "firefly text to image", "adobe AI image", "generative fill".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Core Workflow A — Firefly Services

## Overview

Primary creative workflow using Adobe Firefly v3 APIs: text-to-image generation, generative fill (inpainting), and image expansion (outpainting). These are the most common Firefly Services operations for marketing asset automation.

## Prerequisites

- Completed `adobe-install-auth` with Firefly API scopes (`firefly_api,ff_apis`)
- `@adobe/firefly-apis` installed, or direct REST access
- Pre-signed cloud storage URLs for input/output images (S3, Azure Blob, or Dropbox)

## Instructions

### Step 1: Text-to-Image Generation (Synchronous)

```typescript
// src/workflows/firefly-generate.ts
import { getAccessToken } from '../adobe/client';

interface FireflyGenerateOptions {
  prompt: string;
  negativePrompt?: string;
  width?: number;    // 1024, 1472, 1792, 2048
  height?: number;
  n?: number;        // 1-4 images
  contentClass?: 'art' | 'photo';
  style?: {
    presets?: string[];  // e.g., ['digital_art', 'cinematic']
    strength?: number;   // 0-100
  };
}

interface FireflyOutput {
  outputs: Array<{
    image: { url: string };
    seed: number;
  }>;
}

export async function generateImage(opts: FireflyGenerateOptions): Promise<FireflyOutput> {
  const token = await getAccessToken();

  const body: Record<string, any> = {
    prompt: opts.prompt,
    n: opts.n || 1,
    size: { width: opts.width || 1024, height: opts.height || 1024 },
    contentClass: opts.contentClass || 'photo',
  };

  if (opts.negativePrompt) body.negativePrompt = opts.negativePrompt;
  if (opts.style?.presets) {
    body.styles = { presets: opts.style.presets };
  }

  const response = await fetch('https://firefly-api.adobe.io/v3/images/generate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Firefly generate failed (${response.status}): ${err}`);
  }

  return response.json();
}
```

### Step 2: Async Generation (for High Volume)

```typescript
// For production pipelines, use async endpoint to avoid HTTP timeouts
export async function generateImageAsync(opts: FireflyGenerateOptions) {
  const token = await getAccessToken();

  const response = await fetch('https://firefly-api.adobe.io/v3/images/generate-async', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: opts.prompt,
      n: opts.n || 1,
      size: { width: opts.width || 1024, height: opts.height || 1024 },
    }),
  });

  const { jobId, statusUrl, cancelUrl } = await response.json();
  console.log(`Firefly async job: ${jobId}`);

  // Poll for completion
  let result: any;
  while (true) {
    await new Promise(r => setTimeout(r, 2000));
    const poll = await fetch(statusUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
      },
    });
    result = await poll.json();
    if (result.status === 'succeeded' || result.status === 'failed') break;
  }

  if (result.status === 'failed') throw new Error(`Async generation failed: ${result.error}`);
  return result;
}
```

### Step 3: Generative Fill (Inpainting)

```typescript
// Fill a masked region of an image with AI-generated content
export async function generativeFill(
  imageUrl: string,
  maskUrl: string,
  prompt: string
): Promise<FireflyOutput> {
  const token = await getAccessToken();

  const response = await fetch('https://firefly-api.adobe.io/v3/images/fill', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image: { source: { url: imageUrl } },
      mask: { source: { url: maskUrl } },
      prompt,
      n: 1,
    }),
  });

  if (!response.ok) throw new Error(`Fill failed: ${response.status}`);
  return response.json();
}
```

### Step 4: Image Expansion (Outpainting)

```typescript
// Expand an image to a larger canvas size with AI-generated surroundings
export async function expandImage(
  imageUrl: string,
  targetWidth: number,
  targetHeight: number,
  prompt?: string
): Promise<FireflyOutput> {
  const token = await getAccessToken();

  const response = await fetch('https://firefly-api.adobe.io/v3/images/expand', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image: { source: { url: imageUrl } },
      size: { width: targetWidth, height: targetHeight },
      ...(prompt && { prompt }),
      n: 1,
    }),
  });

  if (!response.ok) throw new Error(`Expand failed: ${response.status}`);
  return response.json();
}
```

## Output

- AI-generated images from text prompts (sync or async)
- Inpainted regions via generative fill with mask
- Expanded/outpainted images to larger canvas sizes
- Temporary URLs for generated images (download within 24h)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `400` prompt rejected | Content policy violation | Remove trademarks, real people, or explicit content from prompt |
| `403 Forbidden` | Missing `firefly_api` scope | Add Firefly API to Developer Console project |
| `413 Payload Too Large` | Image too large for fill/expand | Resize input to max 4096x4096 |
| `429 Too Many Requests` | Rate limited | Use async endpoint; honor `Retry-After` header |
| `500 Internal Server Error` | Transient Firefly error | Retry with backoff; check status.adobe.com |

## Resources

- [Firefly API Reference](https://developer.adobe.com/firefly-services/docs/firefly-api/api/)
- [Firefly Generate Image Tutorial](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/how-tos/firefly-generate-image-api-tutorial)
- [Using Async APIs](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/how-tos/using-async-apis)

## Next Steps

For PDF document workflows, see `adobe-core-workflow-b`.
