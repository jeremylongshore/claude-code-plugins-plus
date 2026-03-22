---
name: ideogram-upgrade-migration
description: |
  Migrate between Ideogram API versions (V_1 to V_2 to V3) with breaking change detection.
  Use when upgrading from legacy to V3 endpoints, updating model versions,
  or handling deprecated API parameters.
  Trigger with phrases like "upgrade ideogram", "ideogram migration",
  "ideogram v2 to v3", "ideogram breaking changes", "migrate ideogram API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, migration]

---
# Ideogram Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -10`

## Overview
Guide for migrating between Ideogram API versions. The primary migration path is from the legacy `/generate` endpoint (JSON body, V_1/V_2 models) to the V3 endpoints (multipart form data, new parameters). This covers breaking changes in request format, model names, aspect ratio syntax, style types, and new capabilities.

## Breaking Changes: Legacy to V3

| Aspect | Legacy (`/generate`) | V3 (`/v1/ideogram-v3/generate`) |
|--------|---------------------|--------------------------------|
| Content-Type | `application/json` | `multipart/form-data` |
| Body format | `{ "image_request": { ... } }` | FormData fields |
| Models | `V_1`, `V_1_TURBO`, `V_2`, `V_2_TURBO`, `V_2A` | Implicit V3 (no model field) |
| Aspect ratio | `ASPECT_16_9` | `16x9` |
| Style types | `AUTO`, `GENERAL`, `REALISTIC`, `DESIGN`, `RENDER_3D`, `ANIME` | `AUTO`, `GENERAL`, `REALISTIC`, `DESIGN`, `FICTION` |
| Magic prompt | `magic_prompt_option` | `magic_prompt` |
| New in V3 | -- | `rendering_speed`, `style_preset`, `style_codes`, `character_reference_images` |
| Color palette | Preset name or hex array | Same, with weight support |

## Instructions

### Step 1: Audit Current API Usage
```bash
set -euo pipefail
# Find all Ideogram API calls in your codebase
grep -rn "api.ideogram.ai" --include="*.ts" --include="*.js" --include="*.py" .
grep -rn "ASPECT_" --include="*.ts" --include="*.js" .
grep -rn "image_request" --include="*.ts" --include="*.js" .
grep -rn "magic_prompt_option" --include="*.ts" --include="*.js" .
```

### Step 2: Create Adapter for Both Versions
```typescript
// src/ideogram/adapter.ts
interface GenerateOptions {
  prompt: string;
  style?: string;
  aspectRatio?: string;
  negativePrompt?: string;
  seed?: number;
  renderingSpeed?: string; // V3 only
  stylePreset?: string;    // V3 only
}

const API_KEY = process.env.IDEOGRAM_API_KEY!;
const USE_V3 = process.env.IDEOGRAM_API_VERSION === "v3";

async function generateImage(options: GenerateOptions) {
  return USE_V3 ? generateV3(options) : generateLegacy(options);
}

// Legacy endpoint -- JSON body
async function generateLegacy(options: GenerateOptions) {
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: { "Api-Key": API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({
      image_request: {
        prompt: options.prompt,
        model: "V_2",
        style_type: options.style ?? "AUTO",
        aspect_ratio: options.aspectRatio ?? "ASPECT_1_1",
        magic_prompt_option: "AUTO",
        negative_prompt: options.negativePrompt,
        seed: options.seed,
      },
    }),
  });
  if (!response.ok) throw new Error(`Legacy generate: ${response.status}`);
  return response.json();
}

// V3 endpoint -- multipart form data
async function generateV3(options: GenerateOptions) {
  const form = new FormData();
  form.append("prompt", options.prompt);
  form.append("style_type", mapStyleToV3(options.style ?? "AUTO"));
  form.append("aspect_ratio", mapAspectRatioToV3(options.aspectRatio ?? "ASPECT_1_1"));
  form.append("magic_prompt", "AUTO");
  form.append("rendering_speed", options.renderingSpeed ?? "DEFAULT");
  if (options.negativePrompt) form.append("negative_prompt", options.negativePrompt);
  if (options.seed) form.append("seed", String(options.seed));
  if (options.stylePreset) form.append("style_preset", options.stylePreset);

  const response = await fetch("https://api.ideogram.ai/v1/ideogram-v3/generate", {
    method: "POST",
    headers: { "Api-Key": API_KEY },
    body: form,
  });
  if (!response.ok) throw new Error(`V3 generate: ${response.status}`);
  return response.json();
}
```

### Step 3: Map Legacy Enums to V3
```typescript
function mapAspectRatioToV3(legacy: string): string {
  const map: Record<string, string> = {
    "ASPECT_1_1": "1x1",    "ASPECT_16_9": "16x9",  "ASPECT_9_16": "9x16",
    "ASPECT_3_2": "3x2",    "ASPECT_2_3": "2x3",    "ASPECT_4_3": "4x3",
    "ASPECT_3_4": "3x4",    "ASPECT_10_16": "10x16", "ASPECT_16_10": "16x10",
    "ASPECT_1_3": "1x3",    "ASPECT_3_1": "3x1",
  };
  return map[legacy] ?? legacy; // Pass through if already V3 format
}

function mapStyleToV3(legacy: string): string {
  const map: Record<string, string> = {
    "AUTO": "AUTO",
    "GENERAL": "GENERAL",
    "REALISTIC": "REALISTIC",
    "DESIGN": "DESIGN",
    "RENDER_3D": "GENERAL",  // No V3 equivalent -- use GENERAL
    "ANIME": "FICTION",      // V3 renamed to FICTION
  };
  return map[legacy] ?? "GENERAL";
}
```

### Step 4: Feature Flag Rollout
```typescript
// Gradual migration with feature flag
function shouldUseV3(userId?: string): boolean {
  // Phase 1: Internal testing
  if (process.env.IDEOGRAM_FORCE_V3 === "true") return true;

  // Phase 2: Percentage rollout
  if (userId) {
    const hash = Array.from(userId).reduce((h, c) => h * 31 + c.charCodeAt(0), 0);
    const percentage = parseInt(process.env.IDEOGRAM_V3_PERCENTAGE ?? "0");
    return (Math.abs(hash) % 100) < percentage;
  }

  return false;
}
```

### Step 5: Validate Migration
```typescript
// Run both endpoints and compare results
async function validateMigration(prompt: string) {
  const [legacy, v3] = await Promise.all([
    generateLegacy({ prompt, style: "REALISTIC", aspectRatio: "ASPECT_16_9" }),
    generateV3({ prompt, style: "REALISTIC", aspectRatio: "ASPECT_16_9" }),
  ]);

  console.log("Legacy:", { resolution: legacy.data[0].resolution, seed: legacy.data[0].seed });
  console.log("V3:", { resolution: v3.data[0].resolution, seed: v3.data[0].seed });
  console.log("Both returned images:", legacy.data.length > 0 && v3.data.length > 0);
}
```

## V3 Exclusive Features
After migration, you gain access to:
- **Rendering speed**: `FLASH`, `TURBO`, `DEFAULT`, `QUALITY`
- **50+ style presets**: `OIL_PAINTING`, `WATERCOLOR`, `POP_ART`, `JAPANDI_FUSION`, etc.
- **Style codes**: 8-char hex codes for precise style matching
- **Character reference images**: Consistent character faces across generations
- **Style reference images**: Upload style examples
- **Color palettes with weights**: Fine-grained color control

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `RENDER_3D` fails in V3 | Removed from V3 style types | Map to `GENERAL` |
| `ANIME` fails in V3 | Renamed to `FICTION` | Update enum mapping |
| JSON body rejected by V3 | V3 requires multipart form | Switch to FormData |
| `magic_prompt_option` ignored | V3 uses `magic_prompt` | Update field name |
| `model` field in V3 | V3 has no model field | Remove from V3 requests |

## Output
- Adapter supporting both legacy and V3 endpoints
- Enum mapping functions for breaking changes
- Feature flag for gradual rollout
- Validation script comparing both endpoints

## Resources
- [Legacy Generate API](https://developer.ideogram.ai/api-reference/api-reference/generate)
- [V3 Generate API](https://developer.ideogram.ai/api-reference/api-reference/generate-v3)
- [Ideogram 3.0 Features](https://ideogram.ai/features/3.0)

## Next Steps
For CI integration during upgrades, see `ideogram-ci-integration`.
