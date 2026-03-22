---
name: gamma-migration-deep-dive
description: |
  Deep dive into migrating to Gamma from other presentation platforms.
  Use when migrating from PowerPoint, Google Slides, Canva,
  or other presentation tools to Gamma.
  Trigger with phrases like "gamma migration", "migrate to gamma",
  "gamma import", "gamma from powerpoint", "gamma from google slides".
allowed-tools: Read, Write, Edit, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, migration]

---
# Gamma Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -10`

## Overview

Migrate presentation workflows from PowerPoint, Google Slides, Canva, or other platforms to Gamma's AI-powered generation. Gamma takes a fundamentally different approach -- instead of manually placing slides, you provide content and Gamma generates the presentation. Migration is about converting your content pipeline, not your slide files.

## Prerequisites

- Gamma API access (Pro+ plan)
- Source presentations accessible for content extraction
- Node.js 18+ for migration scripts
- Completed `gamma-install-auth` setup

## Migration Approaches

| Approach | When to Use | Effort |
|----------|-------------|--------|
| Content extraction + regeneration | Lots of text-heavy presentations | Medium |
| Import via Gamma UI | One-off migration of key decks | Low |
| Template recreation | Repeatable presentation formats | Medium |
| Parallel operation | Gradual transition over time | Low |

**Key insight:** You don't "import" slides into Gamma. You extract content from old presentations and regenerate them using Gamma's AI. This often produces better results than the originals.

## Instructions

### Step 1: Inventory Source Presentations

```typescript
// scripts/inventory-presentations.ts
import { readdir, stat } from "node:fs/promises";
import { join, extname } from "node:path";

interface PresentationInfo {
  path: string;
  format: string;
  sizeMB: number;
  lastModified: Date;
}

async function inventoryPresentations(dir: string): Promise<PresentationInfo[]> {
  const entries = await readdir(dir, { recursive: true });
  const presentations: PresentationInfo[] = [];

  for (const entry of entries) {
    const ext = extname(entry).toLowerCase();
    if ([".pptx", ".ppt", ".key", ".pdf", ".md"].includes(ext)) {
      const fullPath = join(dir, entry);
      const info = await stat(fullPath);
      presentations.push({
        path: fullPath,
        format: ext,
        sizeMB: info.size / (1024 * 1024),
        lastModified: info.mtime,
      });
    }
  }

  console.log(`Found ${presentations.length} presentations:`);
  const byFormat = presentations.reduce((acc, p) => {
    acc[p.format] = (acc[p.format] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  console.log("By format:", byFormat);

  return presentations;
}
```

### Step 2: Extract Content from PowerPoint

```typescript
// scripts/extract-pptx.ts
// Use 'pptx-parser' or 'officegen' to extract text content

import JSZip from "jszip";
import { readFile } from "node:fs/promises";
import { DOMParser } from "xmldom";

async function extractPptxContent(pptxPath: string): Promise<string[]> {
  const buffer = await readFile(pptxPath);
  const zip = await JSZip.loadAsync(buffer);

  const slides: string[] = [];
  const slideFiles = Object.keys(zip.files)
    .filter((f) => f.match(/ppt\/slides\/slide\d+\.xml$/))
    .sort();

  for (const slideFile of slideFiles) {
    const xml = await zip.file(slideFile)!.async("string");
    const doc = new DOMParser().parseFromString(xml);
    // Extract all text elements
    const textNodes = doc.getElementsByTagName("a:t");
    const texts: string[] = [];
    for (let i = 0; i < textNodes.length; i++) {
      const text = textNodes[i].textContent?.trim();
      if (text) texts.push(text);
    }
    slides.push(texts.join("\n"));
  }

  return slides;
}

// Convert extracted content to Gamma prompt
function slidesToGammaPrompt(slides: string[], title: string): string {
  let prompt = `${title}\n\n`;
  slides.forEach((content, i) => {
    prompt += `Slide ${i + 1}:\n${content}\n\n`;
  });
  return prompt;
}
```

### Step 3: Batch Migration Script

```typescript
// scripts/migrate-to-gamma.ts
import { createGammaClient } from "../src/client";
import { pollUntilDone } from "../src/poll";
import pLimit from "p-limit";

const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });
const limit = pLimit(2); // Max 2 concurrent generations

interface MigrationItem {
  title: string;
  content: string;
  sourceFile: string;
}

async function migrateBatch(items: MigrationItem[]) {
  const results = await Promise.allSettled(
    items.map((item) =>
      limit(async () => {
        console.log(`Migrating: ${item.title}`);
        const { generationId } = await gamma.generate({
          content: item.content,
          outputFormat: "presentation",
          textMode: "condense", // AI condenses extracted text
          exportAs: "pptx",    // Get PPTX for comparison
        });

        const result = await pollUntilDone(gamma, generationId);
        return {
          title: item.title,
          sourceFile: item.sourceFile,
          gammaUrl: result.gammaUrl,
          exportUrl: result.exportUrl,
          creditsUsed: result.creditsUsed,
        };
      })
    )
  );

  // Report
  const succeeded = results.filter((r) => r.status === "fulfilled");
  const failed = results.filter((r) => r.status === "rejected");
  console.log(`\nMigration complete: ${succeeded.length} succeeded, ${failed.length} failed`);

  for (const r of results) {
    if (r.status === "fulfilled") {
      console.log(`  OK: ${r.value.title} → ${r.value.gammaUrl}`);
    } else {
      console.log(`  FAIL: ${r.reason}`);
    }
  }
}
```

### Step 4: Template Recreation

For recurring presentation types (weekly reports, proposals, etc.), create Gamma templates:

```text
Migration steps for templates:
1. Identify repeating presentation formats in your org
2. Create a one-page template gamma in the Gamma app:
   - gamma.app → Create → design a single representative page
3. Note the template gamma ID from the URL
4. Use POST /v1.0/generations/from-template with the gammaId
5. Update your automation scripts to use generateFromTemplate()
```

```typescript
// After template creation in Gamma UI
const MIGRATED_TEMPLATES: Record<string, string> = {
  "weekly-report": "gamma_template_weekly_abc123",
  "sales-proposal": "gamma_template_proposal_def456",
  "team-update": "gamma_template_update_ghi789",
};

async function generateFromMigratedTemplate(
  templateKey: string,
  content: string
) {
  const gammaId = MIGRATED_TEMPLATES[templateKey];
  if (!gammaId) throw new Error(`Unknown template: ${templateKey}`);

  const { generationId } = await gamma.generateFromTemplate({
    gammaId,
    prompt: content,
    exportAs: "pdf",
  });

  return pollUntilDone(gamma, generationId);
}
```

### Step 5: Validation Checklist

After migrating each presentation:

```text
- [ ] Content accuracy: AI-generated text matches source intent
- [ ] Slide count: reasonable for the content volume
- [ ] Theme/branding: workspace theme applied correctly
- [ ] Export quality: PDF/PPTX downloads successfully
- [ ] Links preserved: any URLs from original are in the content
- [ ] Stakeholder review: key presentations reviewed by owners
```

## Supported Migration Paths

| Source | Method | Fidelity | Notes |
|--------|--------|----------|-------|
| PowerPoint (.pptx) | Extract text → regenerate | Content-high, design-new | AI redesigns slides |
| Google Slides | Export as .pptx → extract | Content-high, design-new | Export first |
| Canva | Export as .pdf → extract text | Medium | Limited text extraction |
| Keynote (.key) | Export as .pptx → extract | Content-high, design-new | Export first |
| Markdown (.md) | Direct use as content | High | Best migration path |
| Notion pages | Export as .md → use directly | High | Clean text extraction |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Content too long | Exceeds 100K token limit | Split into multiple presentations |
| Credit budget exceeded | Too many migrations at once | Batch over multiple days |
| Poor output quality | Content too unstructured | Add structure (headings, bullets) to extracted content |
| Missing images | Images in source not extracted | Gamma generates new images; reference image concepts in text |

## Resources

- [Gamma Import Guide](https://gamma.app/docs/import)
- [Generate API Parameters](https://developers.gamma.app/guides/generate-api-parameters-explained)
- [Text Mode Options](https://developers.gamma.app/docs/understand-the-api-options)

## Next Steps

Review `gamma-core-workflow-a` for ongoing content generation after migration.
