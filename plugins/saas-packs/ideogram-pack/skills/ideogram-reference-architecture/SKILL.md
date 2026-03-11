---
name: ideogram-reference-architecture
description: |
  Implement Ideogram reference architecture with best-practice project layout.
  Use when designing new Ideogram integrations, reviewing project structure,
  or establishing architecture standards for Ideogram applications.
  Trigger with phrases like "ideogram architecture", "ideogram best practices",
  "ideogram project structure", "how to organize ideogram", "ideogram layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram Reference Architecture

## Overview
Production architecture for AI image generation with Ideogram. Covers generation pipelines, asset management, brand consistency workflows, prompt templating, and CDN delivery for generated images.

## Prerequisites
- Ideogram API key
- Image storage (S3, GCS, or filesystem)
- CDN for image delivery (optional)
- Understanding of Ideogram models and parameters

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Prompt Engineering Layer                  │
│  Templates │ Brand Guidelines │ Style Presets         │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│              Ideogram Generation API                  │
│  ┌───────────┐  ┌───────────┐  ┌─────────────────┐   │
│  │ Generate  │  │ Edit      │  │ Remix           │   │
│  │ (text→img)│  │ (inpaint) │  │ (style transfer)│   │
│  └─────┬─────┘  └─────┬─────┘  └───────┬─────────┘   │
│        └───────────────┴────────────────┘             │
│                        │                              │
│                        ▼                              │
│  ┌──────────────────────────────────────────────┐     │
│  │         Post-Processing                       │     │
│  │  Resize │ Optimize │ Watermark │ Metadata    │     │
│  └──────────────────────┬───────────────────────┘     │
└─────────────────────────┼───────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│              Asset Storage & Delivery                 │
│  S3/GCS │ CDN │ DAM System │ CMS Integration        │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Prompt Template System
```typescript
interface PromptTemplate {
  name: string;
  base: string;
  style: string;
  negativePrompt?: string;
  aspectRatio: string;
  model: 'V_2' | 'V_2_TURBO';
}

const BRAND_TEMPLATES: Record<string, PromptTemplate> = {
  socialPost: {
    name: 'Social Media Post',
    base: '{subject}, modern clean design, vibrant colors',
    style: 'professional photography, high quality',
    negativePrompt: 'text, watermark, blurry, low quality',
    aspectRatio: 'ASPECT_1_1',
    model: 'V_2',
  },
  blogHero: {
    name: 'Blog Hero Image',
    base: '{subject}, editorial style, wide composition',
    style: 'professional, minimalist, tech aesthetic',
    aspectRatio: 'ASPECT_16_9',
    model: 'V_2',
  },
  appIcon: {
    name: 'App Icon',
    base: '{subject}, flat design, rounded corners, gradient',
    style: 'minimal, modern, app store ready',
    aspectRatio: 'ASPECT_1_1',
    model: 'V_2_TURBO',
  },
};

function buildPrompt(template: PromptTemplate, subject: string): string {
  return template.base.replace('{subject}', subject) + ', ' + template.style;
}
```

### Step 2: Generation Service
```typescript
const IDEOGRAM_API = 'https://api.ideogram.ai/generate';

async function generateFromTemplate(
  templateKey: string,
  subject: string
) {
  const template = BRAND_TEMPLATES[templateKey];
  if (!template) throw new Error(`Unknown template: ${templateKey}`);

  const response = await fetch(IDEOGRAM_API, {
    method: 'POST',
    headers: {
      'Api-Key': process.env.IDEOGRAM_API_KEY!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_request: {
        prompt: buildPrompt(template, subject),
        negative_prompt: template.negativePrompt,
        aspect_ratio: template.aspectRatio,
        model: template.model,
        magic_prompt_option: 'AUTO',
      },
    }),
  });

  return response.json();
}
```

### Step 3: Asset Management Pipeline
```typescript
import { createWriteStream, mkdirSync } from 'fs';
import { join } from 'path';

async function generateAndStore(
  templateKey: string,
  subject: string,
  outputDir: string
) {
  mkdirSync(outputDir, { recursive: true });

  const result = await generateFromTemplate(templateKey, subject);
  const imageUrl = result.data?.[0]?.url;
  if (!imageUrl) throw new Error('No image generated');

  const filename = `${templateKey}_${Date.now()}.png`;
  const outputPath = join(outputDir, filename);

  const response = await fetch(imageUrl);
  const buffer = Buffer.from(await response.arrayBuffer());
  const { writeFileSync } = await import('fs');
  writeFileSync(outputPath, buffer);

  return {
    path: outputPath,
    url: imageUrl,
    prompt: buildPrompt(BRAND_TEMPLATES[templateKey], subject),
    seed: result.data[0].seed,
  };
}
```

### Step 4: Batch Generation with Style Consistency
```typescript
async function generateBrandAssets(brandSubjects: string[]) {
  const assets = [];

  for (const subject of brandSubjects) {
    for (const templateKey of Object.keys(BRAND_TEMPLATES)) {
      const asset = await generateAndStore(templateKey, subject, './assets');
      assets.push(asset);
      // Rate limit: wait between generations
      await new Promise(r => setTimeout(r, 3000));  # 3000: 3 seconds in ms
    }
  }

  return assets;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Content filtered | NSFW prompt detected | Review and sanitize prompt text |
| Generation timeout | Complex prompt | Simplify prompt, use V_2_TURBO |
| URL expired | Images are temporary (~1hr) | Download immediately after generation |
| Inconsistent style | No template system | Use consistent prompt templates |

## Examples

### Quick Brand Asset Generation
```typescript
const assets = await generateBrandAssets([
  'cloud computing platform',
  'data analytics dashboard',
  'team collaboration tool',
]);
console.log(`Generated ${assets.length} brand assets`);
```

## Resources
- [Ideogram API Reference](https://docs.ideogram.ai/api)
- [Ideogram Prompt Guide](https://docs.ideogram.ai/prompting)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale