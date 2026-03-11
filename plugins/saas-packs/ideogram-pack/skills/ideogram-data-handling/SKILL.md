---
name: ideogram-data-handling
description: |
  Implement Ideogram PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Ideogram integrations.
  Trigger with phrases like "ideogram data", "ideogram PII",
  "ideogram GDPR", "ideogram data retention", "ideogram privacy", "ideogram CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram Data Handling

## Overview
Manage generated image assets from Ideogram. Covers prompt metadata tracking, image asset lifecycle management, download and local storage patterns, and generation history for brand consistency auditing.

## Prerequisites
- Ideogram API key
- Image storage (local filesystem, S3, or GCS)
- Understanding of image formats and metadata
- Asset management process defined

## Instructions

### Step 1: Track Generation Metadata
```typescript
interface GenerationRecord {
  id: string;
  prompt: string;
  negativePrompt?: string;
  model: string;
  aspectRatio: string;
  seed?: number;
  imageUrl: string;
  localPath?: string;
  generatedAt: string;
  expiresAt: string; // Ideogram URLs are temporary
}

const generationHistory: GenerationRecord[] = [];

async function generateWithTracking(prompt: string, options: any = {}) {
  const response = await fetch('https://api.ideogram.ai/generate', {
    method: 'POST',
    headers: {
      'Api-Key': process.env.IDEOGRAM_API_KEY!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: options.model || 'V_2',
        aspect_ratio: options.aspectRatio || 'ASPECT_1_1',
        magic_prompt_option: 'AUTO',
      },
    }),
  });

  const result = await response.json();
  const image = result.data?.[0];

  if (image) {
    const record: GenerationRecord = {
      id: `gen_${Date.now()}`,
      prompt,
      model: options.model || 'V_2',
      aspectRatio: options.aspectRatio || 'ASPECT_1_1',
      seed: image.seed,
      imageUrl: image.url,
      generatedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 3600000).toISOString(), // ~1hr  # 3600000 = configured value
    };
    generationHistory.push(record);
    return record;
  }

  throw new Error('No image generated');
}
```

### Step 2: Download and Persist Images
```typescript
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';

async function downloadImage(record: GenerationRecord, outputDir: string) {
  mkdirSync(outputDir, { recursive: true });

  const response = await fetch(record.imageUrl);
  if (!response.ok) throw new Error(`Download failed: ${response.status}`);

  const buffer = Buffer.from(await response.arrayBuffer());
  const filename = `${record.id}.png`;
  const filePath = join(outputDir, filename);

  writeFileSync(filePath, buffer);
  record.localPath = filePath;

  return filePath;
}

// Download immediately since URLs expire
async function generateAndPersist(
  prompt: string,
  outputDir = './generated-images'
) {
  const record = await generateWithTracking(prompt);
  await downloadImage(record, outputDir);
  return record;
}
```

### Step 3: Asset Lifecycle Management
```typescript
import { unlinkSync, existsSync } from 'fs';

function cleanExpiredAssets(
  records: GenerationRecord[],
  retentionDays = 30
) {
  const cutoff = Date.now() - retentionDays * 86400000;  # 86400000 = configured value
  const results = { kept: 0, deleted: 0 };

  for (const record of records) {
    if (new Date(record.generatedAt).getTime() < cutoff) {
      if (record.localPath && existsSync(record.localPath)) {
        unlinkSync(record.localPath);
      }
      results.deleted++;
    } else {
      results.kept++;
    }
  }

  return results;
}
```

### Step 4: Generation History Export
```typescript
function exportGenerationHistory(records: GenerationRecord[]) {
  return records.map(r => ({
    id: r.id,
    prompt: r.prompt,
    model: r.model,
    seed: r.seed,
    generatedAt: r.generatedAt,
    hasLocalCopy: !!r.localPath && existsSync(r.localPath),
  }));
}

function findByPrompt(records: GenerationRecord[], searchTerm: string) {
  return records.filter(r =>
    r.prompt.toLowerCase().includes(searchTerm.toLowerCase())
  );
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Expired image URL | URLs last ~1 hour | Download immediately after generation |
| Disk space full | Too many stored images | Run retention cleanup regularly |
| Missing metadata | Not tracked at generation time | Use `generateWithTracking` wrapper |
| Duplicate prompts | Same prompt run multiple times | Check history before regenerating |

## Examples

### Batch Generate and Store
```typescript
async function batchGenerateAssets(prompts: string[]) {
  const results = [];
  for (const prompt of prompts) {
    const record = await generateAndPersist(prompt);
    results.push(record);
    await new Promise(r => setTimeout(r, 3000)); // Rate limit  # 3000: 3 seconds in ms
  }
  return results;
}
```

## Resources
- [Ideogram API Reference](https://docs.ideogram.ai/api)
- [Ideogram Usage Policies](https://ideogram.ai/terms)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale