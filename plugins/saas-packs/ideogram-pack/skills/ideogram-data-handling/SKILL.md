---
name: ideogram-data-handling
description: |
  Manage Ideogram generated image assets, metadata tracking, and lifecycle management.
  Use when implementing image persistence, tracking generation history,
  or building asset management for Ideogram outputs.
  Trigger with phrases like "ideogram data", "ideogram images",
  "ideogram asset management", "ideogram metadata", "ideogram image storage".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, data, asset-management]

---
# Ideogram Data Handling

## Overview
Manage generated image assets from Ideogram's API. Critical concern: **Ideogram image URLs expire** (approximately 1 hour). Every generation must be downloaded and persisted immediately. This skill covers metadata tracking, download pipelines, local and cloud storage, lifecycle management, and generation history for reproducibility.

## Prerequisites
- `IDEOGRAM_API_KEY` configured
- Storage solution (local filesystem, S3, or GCS)
- Database for generation metadata (SQLite, Postgres, or JSON files)

## Instructions

### Step 1: Generation Record Schema
```typescript
interface GenerationRecord {
  id: string;                // Unique identifier
  prompt: string;            // Original prompt
  expandedPrompt?: string;   // Magic Prompt expansion (from response)
  negativePrompt?: string;   // Negative prompt used
  model: string;             // V_2, V_2_TURBO, etc.
  styleType: string;         // DESIGN, REALISTIC, etc.
  aspectRatio: string;       // ASPECT_16_9, etc.
  seed: number;              // For reproducibility
  resolution: string;        // e.g., "1024x1024"
  isSafe: boolean;           // is_image_safe from response
  originalUrl: string;       // Temporary Ideogram URL
  storedPath: string;        // Local or S3 path
  createdAt: string;         // ISO timestamp
  sizeBytes?: number;        // Downloaded file size
  tags?: string[];           // User-defined tags
}
```

### Step 2: Generate, Download, and Track
```typescript
import { writeFileSync, mkdirSync, statSync } from "fs";
import { join } from "path";
import { randomUUID } from "crypto";

const STORAGE_DIR = "./generated-images";
const records: GenerationRecord[] = [];

async function generateAndPersist(
  prompt: string,
  options: {
    model?: string;
    style_type?: string;
    aspect_ratio?: string;
    negative_prompt?: string;
    seed?: number;
    tags?: string[];
  } = {}
): Promise<GenerationRecord> {
  // Generate
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
        style_type: options.style_type ?? "AUTO",
        aspect_ratio: options.aspect_ratio ?? "ASPECT_1_1",
        magic_prompt_option: "AUTO",
        negative_prompt: options.negative_prompt,
        seed: options.seed,
      },
    }),
  });

  if (!response.ok) throw new Error(`Generation failed: ${response.status}`);
  const result = await response.json();
  const image = result.data[0];

  // Download IMMEDIATELY (URLs expire ~1 hour)
  const imgResp = await fetch(image.url);
  if (!imgResp.ok) throw new Error(`Download failed: ${imgResp.status}`);
  const buffer = Buffer.from(await imgResp.arrayBuffer());

  mkdirSync(STORAGE_DIR, { recursive: true });
  const filename = `${image.seed}-${Date.now()}.png`;
  const storedPath = join(STORAGE_DIR, filename);
  writeFileSync(storedPath, buffer);

  // Track metadata
  const record: GenerationRecord = {
    id: randomUUID(),
    prompt,
    expandedPrompt: image.prompt !== prompt ? image.prompt : undefined,
    negativePrompt: options.negative_prompt,
    model: options.model ?? "V_2",
    styleType: image.style_type ?? options.style_type ?? "AUTO",
    aspectRatio: options.aspect_ratio ?? "ASPECT_1_1",
    seed: image.seed,
    resolution: image.resolution,
    isSafe: image.is_image_safe,
    originalUrl: image.url,
    storedPath,
    createdAt: new Date().toISOString(),
    sizeBytes: buffer.length,
    tags: options.tags,
  };

  records.push(record);
  saveRecords();
  return record;
}

function saveRecords() {
  writeFileSync(
    join(STORAGE_DIR, "generations.json"),
    JSON.stringify(records, null, 2)
  );
}
```

### Step 3: Cloud Storage (S3)
```typescript
import { S3Client, PutObjectCommand, DeleteObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: process.env.AWS_REGION });

async function persistToS3(imageUrl: string, seed: number): Promise<string> {
  const response = await fetch(imageUrl);
  const buffer = Buffer.from(await response.arrayBuffer());
  const key = `ideogram/${seed}-${Date.now()}.png`;

  await s3.send(new PutObjectCommand({
    Bucket: process.env.S3_BUCKET!,
    Key: key,
    Body: buffer,
    ContentType: "image/png",
    CacheControl: "public, max-age=31536000, immutable",
    Metadata: { seed: String(seed), source: "ideogram" },
  }));

  return `https://${process.env.CDN_DOMAIN}/${key}`;
}
```

### Step 4: Reproduction from Seed
```typescript
// Reproduce an image using the stored seed and prompt
async function reproduceImage(record: GenerationRecord) {
  return generateAndPersist(record.prompt, {
    model: record.model,
    style_type: record.styleType,
    aspect_ratio: record.aspectRatio,
    negative_prompt: record.negativePrompt,
    seed: record.seed, // Same seed = same image
    tags: [...(record.tags ?? []), "reproduced"],
  });
}
```

### Step 5: Lifecycle Management
```typescript
import { unlinkSync, existsSync, readdirSync, statSync } from "fs";

function cleanupOldAssets(retentionDays: number = 30) {
  const cutoffMs = Date.now() - retentionDays * 86400000;
  let deleted = 0;
  let kept = 0;

  for (const record of records) {
    const createdMs = new Date(record.createdAt).getTime();
    if (createdMs < cutoffMs) {
      if (existsSync(record.storedPath)) {
        unlinkSync(record.storedPath);
        deleted++;
      }
    } else {
      kept++;
    }
  }

  // Remove expired records
  const activeRecords = records.filter(
    r => new Date(r.createdAt).getTime() >= cutoffMs
  );
  records.length = 0;
  records.push(...activeRecords);
  saveRecords();

  console.log(`Cleanup: deleted ${deleted}, kept ${kept}`);
}

function storageReport() {
  const totalBytes = records.reduce((sum, r) => sum + (r.sizeBytes ?? 0), 0);
  const byModel = Object.groupBy(records, r => r.model);

  console.log("=== Image Storage Report ===");
  console.log(`Total images: ${records.length}`);
  console.log(`Total size: ${(totalBytes / 1024 / 1024).toFixed(1)} MB`);
  for (const [model, recs] of Object.entries(byModel)) {
    console.log(`  ${model}: ${recs?.length ?? 0} images`);
  }
}
```

### Step 6: Search and Query
```typescript
function findByPrompt(searchTerm: string): GenerationRecord[] {
  return records.filter(r =>
    r.prompt.toLowerCase().includes(searchTerm.toLowerCase())
  );
}

function findBySeed(seed: number): GenerationRecord | undefined {
  return records.find(r => r.seed === seed);
}

function findByTags(tags: string[]): GenerationRecord[] {
  return records.filter(r =>
    tags.every(t => r.tags?.includes(t))
  );
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Expired URL | Downloaded too late | Always download in same function |
| Disk full | Too many stored images | Run `cleanupOldAssets()` regularly |
| Missing metadata | Not tracked at generation | Use `generateAndPersist` wrapper |
| Duplicate prompts | Same prompt run twice | Check by prompt hash before generating |
| Lost seed | Not recorded | Always store seed from response |

## Output
- Generation records with full metadata tracking
- Immediate download preventing URL expiration
- S3 cloud storage with CDN delivery
- Seed-based reproduction for exact image regeneration
- Lifecycle management with configurable retention

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Ideogram Image Expiration](https://developer.ideogram.ai/ideogram-api/api-overview)

## Next Steps
For access control, see `ideogram-enterprise-rbac`.
