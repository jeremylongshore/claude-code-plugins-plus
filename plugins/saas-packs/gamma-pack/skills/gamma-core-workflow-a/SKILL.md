---
name: gamma-core-workflow-a
description: |
  Generate presentations, documents, and webpages via Gamma API.
  Use when creating content from text prompts, configuring themes,
  image styles, text modes, and output formats.
  Trigger: "gamma generate", "gamma presentation from text",
  "gamma AI slides", "gamma create deck", "gamma content generation".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, workflow, generation]

---
# Gamma Core Workflow A: Content Generation

## Overview

Generate presentations, documents, webpages, and social posts using Gamma's Generate API (`POST /v1.0/generations`). This skill covers the full parameter set: content, output format, text mode, text amount, themes, image options, sharing, folders, and export format.

## Prerequisites

- Completed `gamma-sdk-patterns` (client wrapper ready)
- Pro account with available credits
- Workspace themes configured (optional)

## API Parameters Reference

| Parameter | Type | Options | Default |
|-----------|------|---------|---------|
| `content` | string | Your text/prompt | Required |
| `outputFormat` | string | `presentation`, `document`, `webpage`, `social_post` | `presentation` |
| `textMode` | string | `generate`, `condense`, `preserve` | `generate` |
| `textAmount` | string | `brief`, `medium`, `detailed`, `extensive` | `medium` |
| `themeId` | string | From `GET /v1.0/themes` | Workspace default |
| `imageOptions.style` | string | Free text (e.g., `"photorealistic"`, `"watercolor illustration"`) | AI default |
| `exportAs` | string | `pdf`, `pptx`, `png` | None (no auto-export) |
| `sharingOptions` | object | `workspaceAccess`, `externalAccess` | Workspace defaults |
| `folderIds` | string[] | From `GET /v1.0/folders` | Root folder |

## Instructions

### Step 1: Basic Presentation Generation

```typescript
import { createGammaClient, pollUntilDone } from "./lib/gamma";

const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });

// Simple generation — just content and format
const { generationId } = await gamma.generate({
  content: "Create a 10-card pitch deck for a sustainable energy startup",
  outputFormat: "presentation",
});

const result = await pollUntilDone(gamma, generationId);
console.log(`View: ${result.gammaUrl}`);
```

### Step 2: Full Parameter Generation

```typescript
// Use all available parameters for precise control
async function generateFullControl() {
  // First, discover workspace themes
  const themes = await gamma.listThemes();
  const corporateTheme = themes.find((t) => t.name.includes("Corporate"));

  // Discover folders
  const folders = await gamma.listFolders();
  const reportsFolder = folders.find((f) => f.name === "Reports");

  const { generationId } = await gamma.generate({
    content: `
      Q1 2026 Business Review
      - Revenue up 23% YoY
      - Customer acquisition cost reduced by 15%
      - Three new product lines launched
      - Team grew from 45 to 62 employees
    `,
    outputFormat: "presentation",
    textMode: "generate",      // AI expands your bullet points
    textAmount: "detailed",     // More text per card
    themeId: corporateTheme?.id,
    exportAs: "pptx",           // Auto-generate PPTX download
    imageOptions: {
      style: "professional corporate photography",
    },
    sharingOptions: {
      workspaceAccess: "comment",   // Team can comment
      externalAccess: "view",       // External viewers read-only
    },
    folderIds: reportsFolder ? [reportsFolder.id] : [],
  });

  const result = await pollUntilDone(gamma, generationId);
  console.log(`View: ${result.gammaUrl}`);
  console.log(`Download PPTX: ${result.exportUrl}`);
  console.log(`Credits used: ${result.creditsUsed}`);
}
```

### Step 3: Text Mode Comparison

```typescript
// Same content, different text modes
const content = "Benefits of remote work: flexibility, reduced commute, global talent access";

// "generate" — AI expands bullets into full paragraphs
await gamma.generate({ content, textMode: "generate", outputFormat: "presentation" });

// "condense" — AI summarizes, keeps it concise
await gamma.generate({ content, textMode: "condense", outputFormat: "presentation" });

// "preserve" — uses your text as-is, no AI rewriting
await gamma.generate({ content, textMode: "preserve", outputFormat: "presentation" });
```

### Step 4: Document and Webpage Generation

```typescript
// Long-form document
const { generationId: docId } = await gamma.generate({
  content: "Comprehensive guide to implementing CI/CD pipelines with GitHub Actions",
  outputFormat: "document",
  textAmount: "extensive",
  exportAs: "pdf",
});

// Webpage
const { generationId: webId } = await gamma.generate({
  content: "Product landing page for an AI-powered code review tool",
  outputFormat: "webpage",
  imageOptions: { style: "modern minimalist tech" },
});

// Social post
const { generationId: socialId } = await gamma.generate({
  content: "Announcing our Series A funding round of $12M",
  outputFormat: "social_post",
  textAmount: "brief",
});
```

### Step 5: Batch Generation with Rate Limiting

```typescript
import pLimit from "p-limit";

const limit = pLimit(3); // Max 3 concurrent generations

const topics = [
  "Machine Learning Fundamentals",
  "Cloud Architecture Best Practices",
  "API Design Patterns",
  "DevOps Culture and Practices",
];

const results = await Promise.allSettled(
  topics.map((topic) =>
    limit(async () => {
      const { generationId } = await gamma.generate({
        content: `Create a training deck: ${topic}`,
        outputFormat: "presentation",
        textAmount: "medium",
        exportAs: "pdf",
      });
      return pollUntilDone(gamma, generationId);
    })
  )
);

results.forEach((r, i) => {
  if (r.status === "fulfilled") {
    console.log(`${topics[i]}: ${r.value.gammaUrl}`);
  } else {
    console.error(`${topics[i]}: FAILED — ${r.reason.message}`);
  }
});
```

### Step 6: curl Reference

```bash
# Generate with all parameters
curl -X POST "https://public-api.gamma.app/v1.0/generations" \
  -H "X-API-KEY: ${GAMMA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "5-card overview of AI in healthcare",
    "outputFormat": "presentation",
    "textMode": "generate",
    "textAmount": "medium",
    "themeId": "theme_abc123",
    "exportAs": "pdf",
    "imageOptions": { "style": "medical illustration" },
    "sharingOptions": {
      "workspaceAccess": "edit",
      "externalAccess": "view"
    }
  }'
```

## Credit Cost Awareness

| Image Model Tier | Credits per Image |
|-------------------|-------------------|
| Standard | 2-15 |
| Advanced | 20-33 |
| Premium | 34-75 |
| Ultra | 30-125 |

A 10-card deck with 5 standard images costs approximately 20-60 credits.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 422 Unprocessable | Invalid parameter combination | Check parameter types and allowed values |
| `status: "failed"` | Content too complex or long | Simplify content or reduce scope |
| 429 Rate Limited | Too many concurrent generations | Use `p-limit` for concurrency control |
| Empty `exportUrl` | No `exportAs` specified | Add `exportAs: "pdf"` to request |

## Resources

- [Generate a Gamma](https://developers.gamma.app/reference/generate-a-gamma)
- [Generate API Parameters Explained](https://developers.gamma.app/guides/generate-api-parameters-explained)
- [Themes and Folders APIs](https://developers.gamma.app/docs/list-themes-and-list-folders-apis-explained)

## Next Steps

Proceed to `gamma-core-workflow-b` for template-based generation and export retrieval.
