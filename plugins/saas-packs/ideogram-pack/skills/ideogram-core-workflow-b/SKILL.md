---
name: ideogram-core-workflow-b
description: |
  Execute Ideogram secondary workflows: edit (Magic Fill), remix, upscale, describe, and reframe.
  Use when modifying existing images, applying style transfer, upscaling,
  or building image-to-image pipelines.
  Trigger with phrases like "ideogram edit image", "ideogram remix",
  "ideogram upscale", "ideogram inpaint", "ideogram magic fill", "ideogram reframe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, workflow, editing, remix, upscale]

---
# Ideogram Core Workflow B -- Edit, Remix, Upscale, Describe, Reframe

## Overview
Secondary workflows for Ideogram beyond text-to-image generation. Covers five endpoints: **Edit** (Magic Fill inpainting), **Remix** (style transfer with image weight), **Upscale** (enhance resolution), **Describe** (image-to-text), and **Reframe** (extend canvas to new aspect ratio). All image-input endpoints use multipart form data.

## Prerequisites
- Completed `ideogram-install-auth` setup
- Source images in JPEG, PNG, or WebP format (max 10MB each)
- For editing: a black-and-white mask image matching source dimensions

## Instructions

### Step 1: Edit (Magic Fill / Inpainting)
Replace specific regions of an image using a mask. Black regions in the mask indicate areas to regenerate.

```typescript
import { readFileSync, writeFileSync, mkdirSync } from "fs";

async function editImage(imagePath: string, maskPath: string, prompt: string, options: {
  style_type?: string;
  rendering_speed?: string;
  magic_prompt?: string;
} = {}) {
  const form = new FormData();
  form.append("image", new Blob([readFileSync(imagePath)]), "image.png");
  form.append("mask", new Blob([readFileSync(maskPath)]), "mask.png");
  form.append("prompt", prompt);
  form.append("style_type", options.style_type ?? "GENERAL");
  form.append("rendering_speed", options.rendering_speed ?? "DEFAULT");
  form.append("magic_prompt", options.magic_prompt ?? "AUTO");

  const response = await fetch("https://api.ideogram.ai/v1/ideogram-v3/edit", {
    method: "POST",
    headers: { "Api-Key": process.env.IDEOGRAM_API_KEY! },
    body: form,
  });

  if (!response.ok) throw new Error(`Edit failed: ${response.status} ${await response.text()}`);
  const result = await response.json();

  // Download immediately
  const imgResp = await fetch(result.data[0].url);
  const buffer = Buffer.from(await imgResp.arrayBuffer());
  mkdirSync("./output", { recursive: true });
  writeFileSync(`./output/edited-${result.data[0].seed}.png`, buffer);
  return result;
}

// Example: Replace background
await editImage("product.png", "background-mask.png",
  "Clean white studio background with soft shadows");

// Example: Add text to existing image
await editImage("poster.png", "text-area-mask.png",
  'Bold red text saying "SALE 50% OFF"', { style_type: "DESIGN" });
```

### Step 2: Remix (Style Transfer / Variation)
Generate a new image influenced by a source image. The `image_weight` parameter (1-100) controls how closely the output matches the original.

```typescript
async function remixImage(imagePath: string, prompt: string, options: {
  image_weight?: number;
  aspect_ratio?: string;
  style_type?: string;
  rendering_speed?: string;
} = {}) {
  const form = new FormData();
  form.append("image", new Blob([readFileSync(imagePath)]), "image.png");
  form.append("prompt", prompt);
  form.append("image_weight", String(options.image_weight ?? 50));
  form.append("aspect_ratio", options.aspect_ratio ?? "1x1");
  form.append("style_type", options.style_type ?? "GENERAL");
  form.append("rendering_speed", options.rendering_speed ?? "DEFAULT");

  const response = await fetch("https://api.ideogram.ai/v1/ideogram-v3/remix", {
    method: "POST",
    headers: { "Api-Key": process.env.IDEOGRAM_API_KEY! },
    body: form,
  });

  if (!response.ok) throw new Error(`Remix failed: ${response.status}`);
  return response.json();
}

// Low weight = more creative freedom, high weight = closer to original
await remixImage("photo.jpg", "Same scene but in watercolor painting style", { image_weight: 30 });
await remixImage("logo.png", "Same logo but with neon glow effect", { image_weight: 80 });
```

### Step 3: Upscale (Enhance Resolution)
```typescript
async function upscaleImage(imagePath: string, options: {
  prompt?: string;
  resemblance?: number;
  detail?: number;
} = {}) {
  const form = new FormData();
  form.append("image_file", new Blob([readFileSync(imagePath)]), "image.png");
  form.append("image_request", JSON.stringify({
    prompt: options.prompt,
    resemblance: options.resemblance ?? 50,   // 0-100: fidelity to original
    detail: options.detail ?? 50,              // 0-100: level of detail enhancement
    magic_prompt_option: "AUTO",
  }));

  const response = await fetch("https://api.ideogram.ai/upscale", {
    method: "POST",
    headers: { "Api-Key": process.env.IDEOGRAM_API_KEY! },
    body: form,
  });

  if (!response.ok) throw new Error(`Upscale failed: ${response.status}`);
  const result = await response.json();
  console.log(`Upscaled: ${result.data[0].resolution} -> ${result.data[0].upscaled_resolution}`);
  return result;
}
```

### Step 4: Describe (Image to Text)
```typescript
async function describeImage(imagePath: string, modelVersion: "V_2" | "V_3" = "V_3") {
  const form = new FormData();
  form.append("image_file", new Blob([readFileSync(imagePath)]), "image.png");
  form.append("describe_model_version", modelVersion);

  const response = await fetch("https://api.ideogram.ai/describe", {
    method: "POST",
    headers: { "Api-Key": process.env.IDEOGRAM_API_KEY! },
    body: form,
  });

  if (!response.ok) throw new Error(`Describe failed: ${response.status}`);
  const result = await response.json();
  return result.descriptions.map((d: any) => d.text);
}

// Use describe to reverse-engineer prompts for existing images
const descriptions = await describeImage("reference-image.jpg");
console.log("Suggested prompts:", descriptions);
```

### Step 5: Reframe (Extend Canvas)
Expand an image to a new resolution while maintaining style consistency.

```typescript
async function reframeImage(imagePath: string, resolution: string, options: {
  rendering_speed?: string;
  style_preset?: string;
} = {}) {
  const form = new FormData();
  form.append("image", new Blob([readFileSync(imagePath)]), "image.png");
  form.append("resolution", resolution);  // e.g., "1024x576" for 16:9
  form.append("rendering_speed", options.rendering_speed ?? "DEFAULT");
  if (options.style_preset) form.append("style_preset", options.style_preset);

  const response = await fetch("https://api.ideogram.ai/v1/ideogram-v3/reframe", {
    method: "POST",
    headers: { "Api-Key": process.env.IDEOGRAM_API_KEY! },
    body: form,
  });

  if (!response.ok) throw new Error(`Reframe failed: ${response.status}`);
  return response.json();
}

// Reframe a square image to widescreen
await reframeImage("square-photo.png", "1344x768");
```

## Endpoint Quick Reference

| Endpoint | URL | Input | Key Parameters |
|----------|-----|-------|----------------|
| Edit V3 | `/v1/ideogram-v3/edit` | image + mask + prompt | `style_type`, `rendering_speed` |
| Remix V3 | `/v1/ideogram-v3/remix` | image + prompt | `image_weight` (1-100) |
| Upscale | `/upscale` | image + `image_request` JSON | `resemblance`, `detail` (0-100) |
| Describe | `/describe` | image | `describe_model_version` (V_2/V_3) |
| Reframe V3 | `/v1/ideogram-v3/reframe` | image + resolution | `rendering_speed`, `style_preset` |

## Error Handling
| Error | HTTP Status | Cause | Solution |
|-------|-------------|-------|----------|
| Mask size mismatch | 400 | Mask dimensions differ from image | Ensure mask matches source image size exactly |
| File too large | 400 | Image exceeds 10MB | Compress or resize before uploading |
| Safety rejected | 422 | Image or prompt flagged | Modify content, avoid restricted subjects |
| Format unsupported | 400 | Not JPEG/PNG/WebP | Convert image to a supported format |
| Rate limited | 429 | Too many requests | Queue with delays between calls |

## Output
- Edited, remixed, upscaled, or reframed images downloaded locally
- Descriptions array for image-to-text analysis
- Metadata including seed, resolution, and safety status

## Resources
- [Edit V3 API](https://developer.ideogram.ai/api-reference/api-reference/edit-v3)
- [Remix V3 API](https://developer.ideogram.ai/api-reference/api-reference/remix-v3)
- [Upscale API](https://developer.ideogram.ai/api-reference/api-reference/upscale)
- [Describe API](https://developer.ideogram.ai/api-reference/api-reference/describe)
- [Reframe V3 API](https://developer.ideogram.ai/api-reference/api-reference/reframe-v3)

## Next Steps
For common errors, see `ideogram-common-errors`.
