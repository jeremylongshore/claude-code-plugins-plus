---
name: anima-hello-world
description: |
  Generate React/Vue/HTML code from a Figma design using the Anima SDK.
  Use when testing design-to-code conversion, learning Anima's code output format,
  or building your first automated design-to-code pipeline.
  Trigger: "anima hello world", "anima example", "figma to react",
  "figma to code", "anima generate code".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, react, code-generation]
compatible-with: claude-code
---

# Anima Hello World

## Overview

Generate production-ready React, Vue, or HTML code from a Figma design using the `@animaapp/anima-sdk`. This example converts a Figma component into clean TypeScript React with Tailwind CSS.

## Prerequisites

- Completed `anima-install-auth` setup
- A Figma file with at least one frame/component
- Know your file key and node ID

## Instructions

### Step 1: Generate React + Tailwind Code

```typescript
// src/hello-world.ts
import { Anima } from '@animaapp/anima-sdk';
import fs from 'fs';
import path from 'path';

const anima = new Anima({
  auth: { token: process.env.ANIMA_TOKEN! },
});

async function generateReactComponent() {
  const { files } = await anima.generateCode({
    fileKey: process.env.FIGMA_FILE_KEY!,     // From Figma URL
    figmaToken: process.env.FIGMA_TOKEN!,
    nodesId: [process.env.FIGMA_NODE_ID!],    // e.g., '1:2'
    settings: {
      language: 'typescript',
      framework: 'react',
      styling: 'tailwind',
      uiLibrary: 'none',  // or 'mui', 'antd', 'shadcn'
    },
  });

  // Write generated files to disk
  const outputDir = './generated';
  fs.mkdirSync(outputDir, { recursive: true });

  for (const file of files) {
    const filePath = path.join(outputDir, file.fileName);
    fs.writeFileSync(filePath, file.content);
    console.log(`Generated: ${filePath} (${file.content.length} chars)`);
  }

  return files;
}

generateReactComponent().catch(console.error);
```

### Step 2: Try Different Framework Outputs

```typescript
// Generate Vue + Tailwind
const vueFiles = await anima.generateCode({
  fileKey: process.env.FIGMA_FILE_KEY!,
  figmaToken: process.env.FIGMA_TOKEN!,
  nodesId: ['1:2'],
  settings: {
    language: 'typescript',
    framework: 'vue',
    styling: 'tailwind',
  },
});

// Generate HTML + CSS (no framework)
const htmlFiles = await anima.generateCode({
  fileKey: process.env.FIGMA_FILE_KEY!,
  figmaToken: process.env.FIGMA_TOKEN!,
  nodesId: ['1:2'],
  settings: {
    language: 'javascript',
    framework: 'html',
    styling: 'css',
  },
});

// Generate React + shadcn/ui
const shadcnFiles = await anima.generateCode({
  fileKey: process.env.FIGMA_FILE_KEY!,
  figmaToken: process.env.FIGMA_TOKEN!,
  nodesId: ['1:2'],
  settings: {
    language: 'typescript',
    framework: 'react',
    styling: 'tailwind',
    uiLibrary: 'shadcn',
  },
});
```

### Step 3: Inspect Generated Output

```typescript
// The generated files array contains:
interface GeneratedFile {
  fileName: string;    // e.g., 'HeroSection.tsx', 'styles.css'
  content: string;     // Full file content
  type: string;        // 'component', 'style', 'asset'
}

// Example output structure for React + Tailwind:
// generated/
// ├── HeroSection.tsx       # React component with Tailwind classes
// ├── Button.tsx            # Child components
// └── types.ts              # TypeScript interfaces (if applicable)
```

### Step 4: Integrate into Existing Project

```bash
# Copy generated files into your project
cp -r generated/components/* src/components/design/

# Install any missing dependencies
npm install  # Anima generates standard React/Vue code — no special deps
```

## Settings Reference

| Setting | Options | Default |
|---------|---------|---------|
| `language` | `typescript`, `javascript` | `typescript` |
| `framework` | `react`, `vue`, `html` | `react` |
| `styling` | `tailwind`, `css`, `styled-components` | `tailwind` |
| `uiLibrary` | `none`, `mui`, `antd`, `shadcn` | `none` |

## Output

- Generated React/Vue/HTML files from Figma design
- Clean TypeScript with Tailwind CSS classes
- Files ready to drop into existing project
- Multiple framework outputs compared

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `File not found` | Wrong Figma file key | Extract key from URL after `/file/` |
| `Node not found` | Wrong node ID | Use Figma's "Copy link" on the frame |
| Empty `files` array | Node has no renderable content | Select a frame/component, not a page |
| Malformed output | Complex nested auto-layout | Simplify Figma structure; use components |

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)
- [Anima Blog: Figma to React](https://www.animaapp.com/blog/design-to-code/how-to-export-figma-to-react/)

## Next Steps

Proceed to `anima-local-dev-loop` for iterative design-to-code development.
