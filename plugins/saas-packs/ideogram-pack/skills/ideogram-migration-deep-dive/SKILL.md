---
name: ideogram-migration-deep-dive
description: |
  Migrate from other image generation APIs to Ideogram, or re-architect existing Ideogram integrations.
  Use when switching from DALL-E/Midjourney/Stable Diffusion to Ideogram,
  or performing major integration overhauls.
  Trigger with phrases like "migrate to ideogram", "switch to ideogram",
  "replace dall-e with ideogram", "ideogram replatform", "ideogram migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, migration]

---
# Ideogram Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -10`

## Overview
Comprehensive migration guide for moving to Ideogram from DALL-E, Midjourney, Stable Diffusion, or another image generation provider. Uses the strangler fig pattern for gradual migration. Key Ideogram advantages: superior text rendering in images, REST API with no SDK dependency, and flexible style/aspect ratio control.

## Migration Types

| From | Complexity | Key Changes | Timeline |
|------|-----------|-------------|----------|
| DALL-E (OpenAI) | Low | Auth header, response format, aspect ratios | 1-2 days |
| Midjourney (Discord bot) | Medium | Move from Discord to REST API | 1-2 weeks |
| Stable Diffusion (local) | Medium | Cloud API vs local inference | 1-2 weeks |
| Custom pipeline | High | Full integration overhaul | 2-4 weeks |

## Instructions

### Step 1: Audit Current Integration
```bash
set -euo pipefail
# Find all image generation API calls
grep -rn "openai\|dall-e\|dalle\|midjourney\|stability\|stablediffusion" \
  --include="*.ts" --include="*.js" --include="*.py" . | head -30

# Count integration points
echo "Integration points:"
grep -rl "images/generations\|api.openai.com\|api.stability.ai" \
  --include="*.ts" --include="*.js" . | wc -l
```

### Step 2: API Mapping -- DALL-E to Ideogram
```typescript
// === DALL-E (Before) ===
const dallEResponse = await fetch("https://api.openai.com/v1/images/generations", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${OPENAI_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "dall-e-3",
    prompt: "A sunset over mountains",
    n: 1,
    size: "1024x1024",
    quality: "standard",
    style: "natural",
  }),
});
const dallEResult = await dallEResponse.json();
const imageUrl = dallEResult.data[0].url;

// === Ideogram (After) ===
const ideogramResponse = await fetch("https://api.ideogram.ai/generate", {
  method: "POST",
  headers: {
    "Api-Key": process.env.IDEOGRAM_API_KEY!,  // Note: Api-Key, not Authorization
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    image_request: {                             // Note: wrapped in image_request
      prompt: "A sunset over mountains",
      model: "V_2",
      aspect_ratio: "ASPECT_1_1",               // Note: enum, not "1024x1024"
      style_type: "REALISTIC",                   // Note: different style system
      magic_prompt_option: "AUTO",
    },
  }),
});
const ideogramResult = await ideogramResponse.json();
const imageUrl = ideogramResult.data[0].url;    // DOWNLOAD IMMEDIATELY - expires!
```

### Step 3: Parameter Mapping Table

| Concept | DALL-E | Ideogram (Legacy) | Ideogram (V3) |
|---------|--------|-------------------|---------------|
| Auth | `Authorization: Bearer` | `Api-Key: key` | `Api-Key: key` |
| Body wrapper | None | `image_request` | FormData |
| Size | `"1024x1024"` | `"ASPECT_1_1"` | `"1x1"` |
| Widescreen | `"1792x1024"` | `"ASPECT_16_9"` | `"16x9"` |
| Portrait | `"1024x1792"` | `"ASPECT_9_16"` | `"9x16"` |
| Quality | `"standard"/"hd"` | Model choice (V_2/V_2_TURBO) | `rendering_speed` |
| Style | `"natural"/"vivid"` | `style_type` enum | `style_type` + `style_preset` |
| Prompt enhance | N/A | `magic_prompt_option` | `magic_prompt` |
| Count | `n: 1-4` | `num_images: 1-4` | `num_images: 1-4` |
| Negative prompt | N/A | `negative_prompt` | `negative_prompt` |
| Reproducibility | N/A | `seed` | `seed` |
| URL lifetime | ~1 hour | ~1 hour | ~1 hour |

### Step 4: Adapter Pattern for Gradual Migration
```typescript
interface ImageGenerationRequest {
  prompt: string;
  aspectRatio: "square" | "landscape" | "portrait";
  quality: "draft" | "standard" | "premium";
  style: "natural" | "artistic" | "design";
  count: number;
}

interface ImageGenerationResult {
  images: Array<{ url: string; seed?: number }>;
  provider: "dall-e" | "ideogram";
}

// Adapter interface
interface ImageProvider {
  generate(req: ImageGenerationRequest): Promise<ImageGenerationResult>;
}

// Ideogram implementation
class IdeogramProvider implements ImageProvider {
  private aspectMap = { square: "ASPECT_1_1", landscape: "ASPECT_16_9", portrait: "ASPECT_9_16" };
  private modelMap = { draft: "V_2_TURBO", standard: "V_2", premium: "V_2" };
  private styleMap = { natural: "REALISTIC", artistic: "GENERAL", design: "DESIGN" };

  async generate(req: ImageGenerationRequest): Promise<ImageGenerationResult> {
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: {
        "Api-Key": process.env.IDEOGRAM_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_request: {
          prompt: req.prompt,
          model: this.modelMap[req.quality],
          aspect_ratio: this.aspectMap[req.aspectRatio],
          style_type: this.styleMap[req.style],
          num_images: req.count,
          magic_prompt_option: "AUTO",
        },
      }),
    });

    if (!response.ok) throw new Error(`Ideogram: ${response.status}`);
    const result = await response.json();

    return {
      images: result.data.map((d: any) => ({ url: d.url, seed: d.seed })),
      provider: "ideogram",
    };
  }
}
```

### Step 5: Feature-Flagged Traffic Split
```typescript
function getImageProvider(userId?: string): ImageProvider {
  const percentage = parseInt(process.env.IDEOGRAM_MIGRATION_PCT ?? "0");

  if (percentage >= 100) return new IdeogramProvider();
  if (percentage <= 0) return new DallEProvider();

  // Deterministic split by user ID
  if (userId) {
    const hash = Array.from(userId).reduce((h, c) => h * 31 + c.charCodeAt(0), 0);
    if (Math.abs(hash) % 100 < percentage) return new IdeogramProvider();
  }

  return new DallEProvider();
}

// Migration rollout:
// Week 1: IDEOGRAM_MIGRATION_PCT=10  (internal testing)
// Week 2: IDEOGRAM_MIGRATION_PCT=25  (canary)
// Week 3: IDEOGRAM_MIGRATION_PCT=50  (half traffic)
// Week 4: IDEOGRAM_MIGRATION_PCT=100 (complete)
```

### Step 6: Migration Validation
```typescript
async function validateMigration(testPrompts: string[]) {
  const results = { passed: 0, failed: 0, errors: [] as string[] };

  for (const prompt of testPrompts) {
    try {
      const provider = new IdeogramProvider();
      const result = await provider.generate({
        prompt,
        aspectRatio: "square",
        quality: "draft",
        style: "natural",
        count: 1,
      });

      if (result.images.length > 0 && result.images[0].url) {
        results.passed++;
      } else {
        results.failed++;
        results.errors.push(`No image returned for: ${prompt.slice(0, 40)}`);
      }
    } catch (err: any) {
      results.failed++;
      results.errors.push(`${prompt.slice(0, 40)}: ${err.message}`);
    }

    await new Promise(r => setTimeout(r, 3000)); // Rate limit
  }

  console.log(`Migration validation: ${results.passed} passed, ${results.failed} failed`);
  if (results.errors.length) console.log("Errors:", results.errors);
}
```

## Ideogram Advantages Post-Migration
- **Text rendering**: Ideogram generates legible text inside images (DALL-E struggles with this)
- **Seed reproducibility**: Same seed + prompt = same image
- **No SDK dependency**: Plain REST API, no `openai` package needed
- **Style presets**: 50+ artistic presets in V3
- **Negative prompts**: Explicit control over what to exclude
- **Character consistency**: V3 character reference images

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Auth format wrong | Using `Authorization: Bearer` | Switch to `Api-Key` header |
| Body format wrong | No `image_request` wrapper | Wrap params in `image_request` |
| Size format wrong | Using pixel dimensions | Use enum (`ASPECT_16_9`) |
| URL expired | Not downloading immediately | Download in same function |

## Output
- Parameter mapping from DALL-E/Midjourney to Ideogram
- Adapter pattern supporting multiple providers
- Feature-flagged gradual migration
- Validation script for migration testing

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Ideogram 3.0 Features](https://ideogram.ai/features/3.0)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Next Steps
For advanced troubleshooting, see `ideogram-debug-bundle`.
