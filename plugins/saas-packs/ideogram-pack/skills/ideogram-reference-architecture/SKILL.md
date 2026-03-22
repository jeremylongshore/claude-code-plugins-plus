---
name: ideogram-reference-architecture
description: |
  Implement Ideogram reference architecture with prompt templates, asset pipelines, and CDN delivery.
  Use when designing new Ideogram integrations, building brand asset systems,
  or establishing architecture for image generation at scale.
  Trigger with phrases like "ideogram architecture", "ideogram project structure",
  "ideogram brand assets", "ideogram pipeline design", "ideogram at scale".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, architecture, reference]

---
# Ideogram Reference Architecture

## Overview
Production architecture for AI image generation with Ideogram at scale. Covers prompt templating for brand consistency, generation pipelines using all six API endpoints, asset storage and CDN delivery, and metadata tracking for reproducibility.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Prompt Engineering Layer                                │
│  Templates │ Brand Guidelines │ Negative Prompts         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Ideogram API (api.ideogram.ai)                          │
│  ┌──────────┐ ┌────────┐ ┌───────┐ ┌────────┐          │
│  │ Generate │ │ Edit   │ │ Remix │ │Describe│          │
│  │(text→img)│ │(inpaint)│ │(vary) │ │(img→txt)│         │
│  └────┬─────┘ └───┬────┘ └──┬────┘ └───┬────┘          │
│       │           │         │          │                │
│  ┌────┴───────────┴─────────┴──────────┘                │
│  │  ┌──────────┐  ┌─────────┐                           │
│  │  │ Upscale  │  │ Reframe │                           │
│  │  └────┬─────┘  └────┬────┘                           │
│  └───────┴──────────────┘                               │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Post-Processing & Storage                               │
│  Download │ Resize │ WebP Convert │ S3/GCS │ CDN        │
└─────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Prompt Template System
```typescript
interface PromptTemplate {
  name: string;
  base: string;
  style: string;
  negativePrompt: string;
  aspectRatio: string;
  model: string;
  renderingSpeed?: string;
}

const BRAND_TEMPLATES: Record<string, PromptTemplate> = {
  socialPost: {
    name: "Social Media Post",
    base: "{subject}, modern clean design, vibrant colors, professional",
    style: "DESIGN",
    negativePrompt: "blurry text, misspelled, watermark, low quality",
    aspectRatio: "ASPECT_1_1",
    model: "V_2",
  },
  blogHero: {
    name: "Blog Hero Image",
    base: "{subject}, editorial photography, wide composition, cinematic lighting",
    style: "REALISTIC",
    negativePrompt: "text overlay, watermark, blurry, oversaturated",
    aspectRatio: "ASPECT_16_9",
    model: "V_2",
  },
  storyVertical: {
    name: "Story / Reel",
    base: "{subject}, vertical composition, eye-catching, bold colors",
    style: "DESIGN",
    negativePrompt: "horizontal layout, small text, blurry",
    aspectRatio: "ASPECT_9_16",
    model: "V_2_TURBO",
  },
  ogImage: {
    name: "Open Graph Image",
    base: '{subject}, with text "{title}" in bold clean font, tech aesthetic',
    style: "DESIGN",
    negativePrompt: "blurry text, misspelled words, cluttered",
    aspectRatio: "ASPECT_16_9",
    model: "V_2",
  },
};

function buildPrompt(templateKey: string, vars: Record<string, string>): string {
  const template = BRAND_TEMPLATES[templateKey];
  if (!template) throw new Error(`Unknown template: ${templateKey}`);
  let prompt = template.base;
  for (const [key, value] of Object.entries(vars)) {
    prompt = prompt.replace(`{${key}}`, value);
  }
  return prompt;
}
```

### Step 2: Generation Service
```typescript
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const API_KEY = process.env.IDEOGRAM_API_KEY!;

async function generateFromTemplate(
  templateKey: string,
  vars: Record<string, string>,
  outputDir = "./assets"
) {
  const template = BRAND_TEMPLATES[templateKey];
  const prompt = buildPrompt(templateKey, vars);

  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: { "Api-Key": API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: template.model,
        style_type: template.style,
        aspect_ratio: template.aspectRatio,
        negative_prompt: template.negativePrompt,
        magic_prompt_option: "AUTO",
      },
    }),
  });

  if (!response.ok) throw new Error(`Generate failed: ${response.status}`);
  const result = await response.json();
  const image = result.data[0];

  // Download immediately (URLs expire ~1hr)
  const imgResp = await fetch(image.url);
  const buffer = Buffer.from(await imgResp.arrayBuffer());
  mkdirSync(outputDir, { recursive: true });
  const filename = `${templateKey}-${image.seed}.png`;
  writeFileSync(join(outputDir, filename), buffer);

  return {
    localPath: join(outputDir, filename),
    seed: image.seed,
    prompt,
    resolution: image.resolution,
    template: templateKey,
  };
}
```

### Step 3: Multi-Format Asset Pipeline
```typescript
import sharp from "sharp";

async function generateBrandAssetSet(subject: string, title: string) {
  const results = [];

  for (const [key, template] of Object.entries(BRAND_TEMPLATES)) {
    const asset = await generateFromTemplate(key, { subject, title });
    results.push(asset);

    // Generate WebP variant for web
    await sharp(asset.localPath)
      .webp({ quality: 85 })
      .toFile(asset.localPath.replace(".png", ".webp"));

    // Rate limit courtesy
    await new Promise(r => setTimeout(r, 3000));
  }

  // Generate manifest for asset tracking
  const manifest = results.map(r => ({
    template: r.template,
    seed: r.seed,
    prompt: r.prompt,
    files: {
      png: r.localPath,
      webp: r.localPath.replace(".png", ".webp"),
    },
  }));

  writeFileSync("./assets/manifest.json", JSON.stringify(manifest, null, 2));
  console.log(`Generated ${results.length} brand assets with manifest`);
  return results;
}
```

### Step 4: Describe-then-Remix Pipeline
```typescript
// Use Describe to analyze a reference image, then Remix to create variations
async function referenceBasedGeneration(referenceImagePath: string, modifications: string) {
  // Step 1: Describe the reference image
  const form1 = new FormData();
  form1.append("image_file", new Blob([readFileSync(referenceImagePath)]));
  form1.append("describe_model_version", "V_3");

  const descResp = await fetch("https://api.ideogram.ai/describe", {
    method: "POST",
    headers: { "Api-Key": API_KEY },
    body: form1,
  });
  const descriptions = await descResp.json();
  const basePrompt = descriptions.descriptions[0].text;

  // Step 2: Remix with modifications
  const form2 = new FormData();
  form2.append("image", new Blob([readFileSync(referenceImagePath)]));
  form2.append("prompt", `${basePrompt}, ${modifications}`);
  form2.append("image_weight", "40");
  form2.append("rendering_speed", "DEFAULT");

  const remixResp = await fetch("https://api.ideogram.ai/v1/ideogram-v3/remix", {
    method: "POST",
    headers: { "Api-Key": API_KEY },
    body: form2,
  });

  return remixResp.json();
}
```

## Project Structure
```
project/
├── src/
│   ├── ideogram/
│   │   ├── client.ts          # API wrapper
│   │   ├── templates.ts       # Prompt templates
│   │   ├── pipeline.ts        # Generation pipeline
│   │   └── types.ts           # TypeScript types
│   ├── storage/
│   │   └── s3.ts              # Image upload to S3/GCS
│   └── api/
│       └── generate.ts        # API route handler
├── assets/                    # Generated image output
│   └── manifest.json          # Asset tracking
├── tests/
│   ├── templates.test.ts      # Prompt template tests
│   └── pipeline.test.ts       # Pipeline tests (mocked)
└── config/
    ├── ideogram.ts            # API configuration
    └── templates.json         # Prompt templates (optional)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Inconsistent style | No template system | Use branded prompt templates |
| URL expired | Late download | Download in same function call |
| Text misspelled | Prompt too vague | Use `DESIGN` style, quote exact text |
| Wrong aspect ratio | Template mismatch | Map templates to target platforms |

## Output
- Prompt template system for brand consistency
- Generation service with auto-download
- Multi-format asset pipeline (PNG + WebP)
- Describe-then-remix pipeline for reference-based generation
- Asset manifest for tracking and reproducibility

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Style Guide](https://docs.ideogram.ai/using-ideogram/generation-settings/style)
- [Aspect Ratios](https://docs.ideogram.ai/using-ideogram/generation-settings/aspect-ratio-and-dimensions)

## Next Steps
For multi-environment setup, see `ideogram-multi-env-setup`.
