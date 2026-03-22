---
name: anima-core-workflow-a
description: |
  Build automated Figma-to-React pipeline with the Anima SDK.
  Use when automating design handoff, building CI/CD design-to-code workflows,
  or creating a design system code generator from Figma components.
  Trigger: "anima design pipeline", "figma to react pipeline",
  "automated design handoff", "anima component generator".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, react, automation]
compatible-with: claude-code
---

# Anima Core Workflow A — Figma-to-React Pipeline

## Overview

Primary workflow: automated pipeline that watches a Figma file, generates React components whenever the design changes, and integrates them into your codebase. This replaces manual design handoff with continuous design-to-code automation.

## Prerequisites

- Completed `anima-install-auth` setup
- Figma file with organized components (auto-layout recommended)
- React project (Next.js, Vite, or CRA)

## Instructions

### Step 1: Design System Scanner

```typescript
// src/pipeline/figma-scanner.ts
import { Anima } from '@animaapp/anima-sdk';

interface FigmaComponent {
  nodeId: string;
  name: string;
  type: 'COMPONENT' | 'FRAME' | 'COMPONENT_SET';
}

const anima = new Anima({
  auth: { token: process.env.ANIMA_TOKEN! },
});

// Fetch all top-level components from a Figma page
async function scanFigmaComponents(fileKey: string): Promise<FigmaComponent[]> {
  const response = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/components`,
    { headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN! } }
  );
  const data = await response.json();

  return data.meta.components.map((comp: any) => ({
    nodeId: comp.node_id,
    name: comp.name,
    type: comp.containing_frame?.type || 'COMPONENT',
  }));
}
```

### Step 2: Batch Code Generator

```typescript
// src/pipeline/batch-generator.ts
import { Anima } from '@animaapp/anima-sdk';
import fs from 'fs';
import path from 'path';

const anima = new Anima({
  auth: { token: process.env.ANIMA_TOKEN! },
});

interface GenerationConfig {
  fileKey: string;
  outputDir: string;
  settings: {
    language: 'typescript' | 'javascript';
    framework: 'react' | 'vue' | 'html';
    styling: 'tailwind' | 'css' | 'styled-components';
    uiLibrary?: 'none' | 'mui' | 'antd' | 'shadcn';
  };
}

async function generateComponentBatch(
  config: GenerationConfig,
  nodeIds: string[],
): Promise<{ generated: number; failed: string[] }> {
  const failed: string[] = [];
  let generated = 0;

  fs.mkdirSync(config.outputDir, { recursive: true });

  // Generate each component (Anima processes one node at a time)
  for (const nodeId of nodeIds) {
    try {
      const { files } = await anima.generateCode({
        fileKey: config.fileKey,
        figmaToken: process.env.FIGMA_TOKEN!,
        nodesId: [nodeId],
        settings: config.settings,
      });

      for (const file of files) {
        const filePath = path.join(config.outputDir, file.fileName);
        fs.writeFileSync(filePath, file.content);
        console.log(`Generated: ${file.fileName}`);
      }
      generated++;
    } catch (err) {
      console.error(`Failed to generate node ${nodeId}:`, err);
      failed.push(nodeId);
    }

    // Rate limit: Anima API has per-minute limits
    await new Promise(r => setTimeout(r, 2000));
  }

  return { generated, failed };
}

export { generateComponentBatch, GenerationConfig };
```

### Step 3: Figma Change Detection

```typescript
// src/pipeline/change-detector.ts
interface FileVersion {
  id: string;
  created_at: string;
  label: string;
}

async function getLatestVersion(fileKey: string): Promise<FileVersion> {
  const response = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/versions`,
    { headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN! } }
  );
  const data = await response.json();
  return data.versions[0];
}

// Check if file changed since last generation
let lastVersionId = '';

async function hasDesignChanged(fileKey: string): Promise<boolean> {
  const latest = await getLatestVersion(fileKey);
  if (latest.id !== lastVersionId) {
    lastVersionId = latest.id;
    return true;
  }
  return false;
}

export { hasDesignChanged, getLatestVersion };
```

### Step 4: Full Pipeline Runner

```typescript
// src/pipeline/run.ts
import { scanFigmaComponents } from './figma-scanner';
import { generateComponentBatch, GenerationConfig } from './batch-generator';
import { hasDesignChanged } from './change-detector';

const config: GenerationConfig = {
  fileKey: process.env.FIGMA_FILE_KEY!,
  outputDir: './src/components/generated',
  settings: {
    language: 'typescript',
    framework: 'react',
    styling: 'tailwind',
    uiLibrary: 'shadcn',
  },
};

async function runPipeline() {
  console.log('Scanning Figma file for components...');
  const components = await scanFigmaComponents(config.fileKey);
  console.log(`Found ${components.length} components`);

  console.log('Generating code...');
  const result = await generateComponentBatch(
    config,
    components.map(c => c.nodeId)
  );

  console.log(`\nPipeline complete: ${result.generated} generated, ${result.failed.length} failed`);
}

// Watch mode: re-generate on design changes
async function watchMode() {
  console.log('Watching for Figma design changes...');
  setInterval(async () => {
    if (await hasDesignChanged(config.fileKey)) {
      console.log('Design changed — regenerating...');
      await runPipeline();
    }
  }, 60000); // Check every minute
}

runPipeline().catch(console.error);
```

## Output

- Automated Figma component scanning and enumeration
- Batch code generation for entire design systems
- Change detection for continuous design-to-code sync
- Watch mode for iterative design development

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many API calls | Add 2s delay between component generations |
| Component not renderable | Figma node is group, not frame | Ensure components use auto-layout |
| Inconsistent output | Complex nested structures | Flatten deep nesting in Figma |
| Missing styles | Custom fonts not available | Map fonts in Anima settings |

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)
- [Figma API Components](https://www.figma.com/developers/api#components)
- [Anima Blog](https://www.animaapp.com/blog/design-to-code/)

## Next Steps

For website-to-code cloning, see `anima-core-workflow-b`.
