---
name: ideogram-hello-world
description: |
  Create a minimal working Ideogram image generation example.
  Use when starting a new Ideogram integration, testing your setup,
  or learning basic Ideogram API patterns.
  Trigger with phrases like "ideogram hello world", "ideogram example",
  "ideogram quick start", "simple ideogram code", "first ideogram image".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, getting-started, image-generation]

---
# Ideogram Hello World

## Overview
Generate your first AI image with Ideogram. Demonstrates the legacy `/generate` endpoint (JSON body) and the V3 `/v1/ideogram-v3/generate` endpoint (multipart form). Both return temporary image URLs that must be downloaded promptly.

## Prerequisites
- Completed `ideogram-install-auth` setup
- `IDEOGRAM_API_KEY` environment variable set
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Quick Test with curl
```bash
set -euo pipefail
# Legacy endpoint (V_2 model, JSON body)
curl -s -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_request": {
      "prompt": "A cheerful golden retriever wearing sunglasses on a beach, with text saying \"Hello Ideogram!\"",
      "model": "V_2",
      "style_type": "REALISTIC",
      "aspect_ratio": "ASPECT_16_9",
      "magic_prompt_option": "AUTO"
    }
  }' | jq '.data[0] | {url, seed, resolution, is_image_safe}'
```

### Step 2: TypeScript -- Generate and Download
```typescript
// hello-ideogram.ts
import { writeFileSync } from "fs";

async function helloIdeogram() {
  // Generate an image with embedded text (Ideogram's specialty)
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt: 'Modern poster design with bold text "HELLO WORLD" in neon gradient, dark background, clean typography',
        model: "V_2",
        style_type: "DESIGN",
        aspect_ratio: "ASPECT_1_1",
        magic_prompt_option: "AUTO",
        num_images: 1,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Generation failed: ${response.status} ${await response.text()}`);
  }

  const result = await response.json();
  const image = result.data[0];

  console.log("Generated image:");
  console.log("  URL:", image.url);
  console.log("  Seed:", image.seed);
  console.log("  Resolution:", image.resolution);
  console.log("  Style:", image.style_type);
  console.log("  Safe:", image.is_image_safe);

  // Download immediately -- URLs expire after ~1 hour
  const imgResponse = await fetch(image.url);
  const buffer = Buffer.from(await imgResponse.arrayBuffer());
  writeFileSync("hello-ideogram.png", buffer);
  console.log("Saved to hello-ideogram.png");
}

helloIdeogram().catch(console.error);
```

### Step 3: Python -- Generate and Download
```python
# hello_ideogram.py
import os, requests

response = requests.post(
    "https://api.ideogram.ai/generate",
    headers={
        "Api-Key": os.environ["IDEOGRAM_API_KEY"],
        "Content-Type": "application/json",
    },
    json={
        "image_request": {
            "prompt": 'Modern poster design with bold text "HELLO WORLD" in neon gradient, dark background',
            "model": "V_2",
            "style_type": "DESIGN",
            "aspect_ratio": "ASPECT_1_1",
            "magic_prompt_option": "AUTO",
        }
    },
)
response.raise_for_status()

image = response.json()["data"][0]
print(f"URL: {image['url']}")
print(f"Seed: {image['seed']}")

# Download the image (URLs expire)
img_data = requests.get(image["url"]).content
with open("hello-ideogram.png", "wb") as f:
    f.write(img_data)
print("Saved to hello-ideogram.png")
```

## Key Parameters Quick Reference

| Parameter | Values | Default |
|-----------|--------|---------|
| `model` | `V_1`, `V_1_TURBO`, `V_2`, `V_2_TURBO`, `V_2A`, `V_2A_TURBO` | `V_2` |
| `style_type` | `AUTO`, `GENERAL`, `REALISTIC`, `DESIGN`, `RENDER_3D`, `ANIME` | `AUTO` |
| `aspect_ratio` | `ASPECT_1_1`, `ASPECT_16_9`, `ASPECT_9_16`, `ASPECT_3_2`, `ASPECT_2_3`, `ASPECT_4_3`, `ASPECT_3_4`, `ASPECT_10_16`, `ASPECT_16_10`, `ASPECT_1_3`, `ASPECT_3_1` | `ASPECT_1_1` |
| `magic_prompt_option` | `AUTO`, `ON`, `OFF` | `AUTO` |
| `num_images` | 1-4 | 1 |

## Response Shape
```json
{
  "created": "2025-01-15T10:30:00Z",
  "data": [
    {
      "url": "https://ideogram.ai/assets/image/...",
      "prompt": "expanded prompt if magic_prompt was ON",
      "resolution": "1024x1024",
      "is_image_safe": true,
      "seed": 12345,
      "style_type": "DESIGN"
    }
  ]
}
```

## Error Handling
| Error | HTTP Status | Cause | Solution |
|-------|-------------|-------|----------|
| Auth error | 401 | Missing or invalid `Api-Key` header | Check `IDEOGRAM_API_KEY` env var |
| Safety rejected | 422 | Prompt failed content filter | Remove flagged terms, rephrase |
| Rate limited | 429 | Too many in-flight requests | Wait and retry with backoff |
| Bad request | 400 | Invalid parameter values | Check enum values match exactly |

## Output
- Generated image file downloaded locally
- Console output with URL, seed, resolution, and safety status
- Seed value for reproducible regeneration

## Resources
- [Legacy Generate Endpoint](https://developer.ideogram.ai/api-reference/api-reference/generate)
- [V3 Generate Endpoint](https://developer.ideogram.ai/api-reference/api-reference/generate-v3)
- [Ideogram Prompt Tips](https://docs.ideogram.ai/using-ideogram/generation-settings/style)

## Next Steps
Proceed to `ideogram-local-dev-loop` for development workflow setup.
