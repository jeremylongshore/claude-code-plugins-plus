---
name: ideogram-core-workflow-a
description: |
  Execute Ideogram primary workflow: text-to-image generation with text rendering.
  Use when generating images from text prompts, creating designs with embedded text,
  or building the main image generation pipeline.
  Trigger with phrases like "ideogram generate image", "ideogram text to image",
  "create image with ideogram", "ideogram primary workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, workflow, image-generation, text-rendering]

---
# Ideogram Core Workflow A -- Text-to-Image Generation

## Overview
Primary workflow for Ideogram: generating images from text prompts. Ideogram excels at rendering legible text inside images -- a capability where most image models fail. Use this for social media graphics, marketing banners, product mockups, posters, logos, and any visual that combines illustration with typography.

## Prerequisites
- Completed `ideogram-install-auth` setup
- `IDEOGRAM_API_KEY` environment variable set
- Understanding of style types and aspect ratios

## Instructions

### Step 1: Choose Parameters for Your Use Case

| Use Case | Style Type | Aspect Ratio | Model | Notes |
|----------|-----------|--------------|-------|-------|
| Social media post | `DESIGN` | `ASPECT_1_1` | `V_2` | Best text rendering |
| Blog hero image | `REALISTIC` | `ASPECT_16_9` | `V_2` | Photorealistic |
| Story / Reel | `GENERAL` | `ASPECT_9_16` | `V_2_TURBO` | Fast, vertical |
| Logo / Icon | `DESIGN` | `ASPECT_1_1` | `V_2` | Clean typography |
| Product mockup | `REALISTIC` | `ASPECT_4_3` | `V_2` | Studio quality |
| Anime illustration | `ANIME` | `ASPECT_3_4` | `V_2` | Japanese art style |
| 3D render | `RENDER_3D` | `ASPECT_16_9` | `V_2` | 3D scene |
| Wide banner | `DESIGN` | `ASPECT_3_1` | `V_2` | Website header |

### Step 2: Generate Image (Legacy Endpoint)
```typescript
import { writeFileSync, mkdirSync } from "fs";

async function generateImage(prompt: string, options: {
  model?: string;
  style_type?: string;
  aspect_ratio?: string;
  negative_prompt?: string;
  seed?: number;
} = {}) {
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
        style_type: options.style_type ?? "DESIGN",
        aspect_ratio: options.aspect_ratio ?? "ASPECT_1_1",
        magic_prompt_option: "AUTO",
        negative_prompt: options.negative_prompt,
        seed: options.seed,
        num_images: 1,
      },
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Generation failed (${response.status}): ${err}`);
  }

  const result = await response.json();
  const image = result.data[0];

  // Download immediately -- URLs expire after ~1 hour
  const imgResp = await fetch(image.url);
  const buffer = Buffer.from(await imgResp.arrayBuffer());
  mkdirSync("./output", { recursive: true });
  const filename = `ideogram-${image.seed}.png`;
  writeFileSync(`./output/${filename}`, buffer);

  return { ...image, localPath: `./output/${filename}` };
}
```

### Step 3: Generate with V3 Endpoint (Multipart)
```typescript
async function generateV3(prompt: string, options: {
  aspect_ratio?: string;
  style_type?: string;
  rendering_speed?: string;
  negative_prompt?: string;
  magic_prompt?: string;
  style_preset?: string;
} = {}) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("aspect_ratio", options.aspect_ratio ?? "1x1");
  form.append("style_type", options.style_type ?? "DESIGN");
  form.append("rendering_speed", options.rendering_speed ?? "DEFAULT");
  form.append("magic_prompt", options.magic_prompt ?? "AUTO");
  if (options.negative_prompt) form.append("negative_prompt", options.negative_prompt);
  if (options.style_preset) form.append("style_preset", options.style_preset);

  const response = await fetch("https://api.ideogram.ai/v1/ideogram-v3/generate", {
    method: "POST",
    headers: { "Api-Key": process.env.IDEOGRAM_API_KEY! },
    body: form,
  });

  if (!response.ok) throw new Error(`V3 generation failed: ${response.status}`);
  return response.json();
}
```

### Step 4: Text-in-Image Best Practices
```typescript
// Ideogram renders quoted text literally inside the image
const textPrompts = [
  // Enclose desired text in quotes within the prompt
  'A coffee shop chalkboard menu with text "DAILY SPECIALS" and "Latte $4.50"',
  'A retro neon sign glowing with the words "OPEN 24 HOURS"',
  'Professional business card design with "Jane Smith" and "CEO" text',
  'Birthday card with elegant gold script "Happy Birthday!"',
];

// Use DESIGN style for best text accuracy
for (const prompt of textPrompts) {
  const result = await generateImage(prompt, {
    style_type: "DESIGN",
    negative_prompt: "blurry text, misspelled, distorted letters",
  });
  console.log(`Generated: ${result.localPath} (seed: ${result.seed})`);
}
```

### Step 5: Batch Generation with Seed Consistency
```typescript
// Use the same seed to reproduce or create consistent variations
async function generateVariations(basePrompt: string, seed: number) {
  const variations = [
    { suffix: ", minimalist style", style: "DESIGN" },
    { suffix: ", photorealistic", style: "REALISTIC" },
    { suffix: ", anime style", style: "ANIME" },
  ];

  const results = [];
  for (const v of variations) {
    const result = await generateImage(`${basePrompt}${v.suffix}`, {
      style_type: v.style,
      seed,
    });
    results.push(result);
    await new Promise(r => setTimeout(r, 3000)); // Rate limit courtesy
  }
  return results;
}
```

## V3 Style Presets (50+)
`80S_ILLUSTRATION`, `90S_NOSTALGIA`, `ART_DECO`, `ART_POSTER`, `BAUHAUS`, `BLUEPRINT`, `BRIGHT_ART`, `CHILDRENS_BOOK`, `COLLAGE`, `CUBISM`, `DOUBLE_EXPOSURE`, `DRAMATIC_CINEMA`, `EDITORIAL`, `FLAT_ART`, `FLAT_VECTOR`, `GOLDEN_HOUR`, `GRAFFITI_I`, `HALFTONE_PRINT`, `JAPANDI_FUSION`, `LONG_EXPOSURE`, `MAGAZINE_EDITORIAL`, `MIXED_MEDIA`, `MONOCHROME`, `OIL_PAINTING`, `POP_ART`, `RETRO_ETCHING`, `SURREAL_COLLAGE`, `TRAVEL_POSTER`, `VINTAGE_POSTER`, `WATERCOLOR`, and more.

## V3 Rendering Speeds
| Speed | Quality | Cost | Use Case |
|-------|---------|------|----------|
| `FLASH` | Lowest | Cheapest | Quick previews |
| `TURBO` | Good | Low | Drafts, iteration |
| `DEFAULT` | High | Standard | Production assets |
| `QUALITY` | Highest | Premium | Final deliverables |

## Error Handling
| Error | HTTP Status | Cause | Solution |
|-------|-------------|-------|----------|
| Content filtered | 422 | Prompt failed safety check | Remove brand names, trademarks, or flagged terms |
| Bad aspect ratio | 400 | Invalid enum value | Use exact enum values (e.g., `ASPECT_16_9` not `16:9`) |
| Rate limited | 429 | 10+ in-flight requests | Queue with 3s delays between calls |
| Expired URL | -- | Downloaded too late | Fetch image within minutes of generation |

## Output
- Generated image files downloaded to `./output/`
- Metadata: URL, seed, resolution, style type, safety status
- Seed values logged for reproducibility

## Resources
- [Legacy Generate API](https://developer.ideogram.ai/api-reference/api-reference/generate)
- [V3 Generate API](https://developer.ideogram.ai/api-reference/api-reference/generate-v3)
- [Style Guide](https://docs.ideogram.ai/using-ideogram/generation-settings/style)
- [Aspect Ratios](https://docs.ideogram.ai/using-ideogram/generation-settings/aspect-ratio-and-dimensions)

## Next Steps
For editing and remixing, see `ideogram-core-workflow-b`.
