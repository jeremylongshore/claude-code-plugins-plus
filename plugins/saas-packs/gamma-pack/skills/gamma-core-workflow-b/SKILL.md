---
name: gamma-core-workflow-b
description: |
  Generate from templates, retrieve exports, and manage sharing via Gamma API.
  Use when creating content from template gammas, downloading PDF/PPTX/PNG exports,
  or configuring sharing and folder organization.
  Trigger: "gamma template", "gamma export", "gamma download PDF",
  "gamma PPTX", "gamma sharing", "gamma from template".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, workflow, export, templates]

---
# Gamma Core Workflow B: Templates & Export

## Overview

Use Gamma's template-based generation (`POST /v1.0/generations/from-template`) and export retrieval (`GET /v1.0/generations/{id}/files`) endpoints. Template generation lets you replicate a single-page gamma template across multiple variations. Export retrieval gives you downloadable PDF, PPTX, and PNG files.

## Prerequisites

- Completed `gamma-core-workflow-a`
- A template gamma with exactly one page (created in the Gamma app)
- Understanding of the generate-poll-retrieve pattern

## Key Concepts

- **Template gamma**: A regular gamma with exactly one page, used as a repeatable template
- **gammaId**: Found in the gamma URL or copied from the app
- **Export URLs**: Temporary download links returned after generation — download promptly as they expire

## Instructions

### Step 1: Create from Template

```typescript
import { createGammaClient, pollUntilDone } from "./lib/gamma";

const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });

// POST /v1.0/generations/from-template
// The template gamma MUST have exactly one page
async function generateFromTemplate(
  templateGammaId: string,
  prompt: string,
  options: {
    themeId?: string;
    exportAs?: "pdf" | "pptx" | "png";
    imageStyle?: string;
  } = {}
) {
  const { generationId } = await gamma.generateFromTemplate({
    gammaId: templateGammaId,
    prompt,
    themeId: options.themeId,
    exportAs: options.exportAs,
    imageOptions: options.imageStyle
      ? { style: options.imageStyle }
      : undefined,
  });

  return pollUntilDone(gamma, generationId);
}

// Usage: generate a sales proposal from a template
const result = await generateFromTemplate(
  "gamma_template_abc123",   // Your one-page template ID
  "Create a sales proposal for Acme Corp. Highlight our cloud migration services, 99.9% uptime SLA, and 24/7 support.",
  { exportAs: "pdf", imageStyle: "corporate professional" }
);

console.log(`View: ${result.gammaUrl}`);
console.log(`Download: ${result.exportUrl}`);
```

### Step 2: Batch Template Generation

```typescript
// Generate multiple variations from the same template
const clients = [
  { name: "Acme Corp", focus: "cloud migration" },
  { name: "TechStart Inc", focus: "AI implementation" },
  { name: "GlobalBank", focus: "security compliance" },
];

import pLimit from "p-limit";
const limit = pLimit(2); // Respect rate limits

const proposals = await Promise.allSettled(
  clients.map((client) =>
    limit(() =>
      generateFromTemplate(
        "gamma_template_abc123",
        `Proposal for ${client.name} focusing on ${client.focus}. Include pricing tier for enterprise. Reference their industry.`,
        { exportAs: "pptx" }
      )
    )
  )
);

proposals.forEach((r, i) => {
  const status = r.status === "fulfilled" ? r.value.gammaUrl : `FAILED: ${r.reason}`;
  console.log(`${clients[i].name}: ${status}`);
});
```

### Step 3: Export Format Selection

```typescript
// Export is specified at generation time via `exportAs`
// You cannot export an already-generated gamma via the API
// Instead, generate with the desired export format

// PDF export — best for sharing externally
const pdfResult = await gamma.generate({
  content: "Annual report for 2025",
  outputFormat: "document",
  exportAs: "pdf",
});

// PPTX export — for editing in PowerPoint/Google Slides
// Note: PPTX exports may have layout shifts and font differences
const pptxResult = await gamma.generate({
  content: "Team kickoff presentation",
  outputFormat: "presentation",
  exportAs: "pptx",
});

// PNG export — for thumbnails or social sharing
const pngResult = await gamma.generate({
  content: "Product announcement graphic",
  outputFormat: "social_post",
  exportAs: "png",
});
```

### Step 4: Retrieve Export Files

```typescript
// After generation completes, exportUrl is in the poll response
// Download files promptly — URLs expire after a period

import { writeFile } from "node:fs/promises";

async function downloadExport(generationId: string, outputPath: string) {
  // Poll until complete
  const result = await pollUntilDone(gamma, generationId);

  if (!result.exportUrl) {
    throw new Error("No export URL — did you specify exportAs?");
  }

  // Download the file
  const response = await fetch(result.exportUrl);
  if (!response.ok) throw new Error(`Download failed: ${response.status}`);

  const buffer = Buffer.from(await response.arrayBuffer());
  await writeFile(outputPath, buffer);
  console.log(`Saved to ${outputPath} (${buffer.length} bytes)`);
}

// Usage
const { generationId } = await gamma.generate({
  content: "Sales deck for Q1 review",
  outputFormat: "presentation",
  exportAs: "pdf",
});

await downloadExport(generationId, "./output/q1-review.pdf");
```

### Step 5: Sharing Configuration

```typescript
// Configure who can access the generated gamma
const { generationId } = await gamma.generate({
  content: "Internal strategy document",
  outputFormat: "document",
  sharingOptions: {
    // Workspace members
    workspaceAccess: "comment",  // noAccess | view | comment | edit | fullAccess

    // External (non-workspace) visitors
    externalAccess: "noAccess",  // Lock down for internal docs

    // Share with specific people via email
    emailOptions: {
      emails: ["partner@example.com"],
      accessLevel: "view",
    },
  },
});
```

### Step 6: curl Reference

```bash
# Generate from template
curl -X POST "https://public-api.gamma.app/v1.0/generations/from-template" \
  -H "X-API-KEY: ${GAMMA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "gammaId": "your_template_gamma_id",
    "prompt": "Create a proposal for Acme Corp focusing on cloud services",
    "exportAs": "pdf",
    "themeId": "theme_abc123",
    "imageOptions": { "style": "photorealistic" },
    "sharingOptions": {
      "workspaceAccess": "edit",
      "externalAccess": "view"
    }
  }'

# Poll for result
curl "https://public-api.gamma.app/v1.0/generations/${GEN_ID}" \
  -H "X-API-KEY: ${GAMMA_API_KEY}" | jq '{status, gammaUrl, exportUrl, creditsUsed}'
```

## Export Format Comparison

| Format | Best For | Fidelity | Editable? |
|--------|----------|----------|-----------|
| PDF | Sharing, printing | High | No |
| PPTX | Editing in PowerPoint/Slides | Medium (layout shifts possible) | Yes |
| PNG | Thumbnails, social media | High (single image) | No |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Template must have exactly one page" | Multi-page template | Edit template to single page |
| Empty `exportUrl` | `exportAs` not specified | Add `exportAs` to generation request |
| Download URL expired | Too slow to download | Download immediately after completion |
| 422 on template generation | Invalid `gammaId` | Verify template ID from Gamma app URL |

## Resources

- [Create from Template](https://developers.gamma.app/reference/create-from-template)
- [Template Parameters Explained](https://developers.gamma.app/guides/create-from-template-api-parameters-explained)
- [Receive Generated File URLs](https://developers.gamma.app/reference/get-gamma-file-urls)

## Next Steps

Proceed to `gamma-common-errors` for troubleshooting API issues.
