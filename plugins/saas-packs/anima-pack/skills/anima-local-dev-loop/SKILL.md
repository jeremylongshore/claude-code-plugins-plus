---
name: anima-local-dev-loop
description: |
  Set up iterative design-to-code development loop with Anima SDK.
  Use when rapidly iterating on Figma-to-code output, comparing framework outputs,
  or building a local preview server for generated components.
  Trigger: "anima local dev", "anima dev loop", "anima preview", "anima iteration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, development]
compatible-with: claude-code
---

# Anima Local Dev Loop

## Overview

Iterative development workflow for Anima design-to-code: generate from Figma, preview in browser, tweak settings, regenerate. Includes side-by-side comparison of React vs Vue vs HTML output.

## Instructions

### Step 1: Project Setup

```bash
mkdir anima-dev && cd anima-dev
npm init -y
npm install @animaapp/anima-sdk dotenv
npm install -D vite @vitejs/plugin-react typescript
```

### Step 2: Generate and Preview Script

```typescript
// scripts/generate-preview.ts
import { Anima } from '@animaapp/anima-sdk';
import fs from 'fs';
import 'dotenv/config';

const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

const SETTINGS_PRESETS = {
  'react-tailwind': { language: 'typescript' as const, framework: 'react' as const, styling: 'tailwind' as const },
  'react-shadcn': { language: 'typescript' as const, framework: 'react' as const, styling: 'tailwind' as const, uiLibrary: 'shadcn' as const },
  'vue-tailwind': { language: 'typescript' as const, framework: 'vue' as const, styling: 'tailwind' as const },
  'html-css': { language: 'javascript' as const, framework: 'html' as const, styling: 'css' as const },
};

async function generateWithPreset(preset: keyof typeof SETTINGS_PRESETS, nodeId: string) {
  const settings = SETTINGS_PRESETS[preset];
  const outputDir = `./generated/${preset}`;
  fs.mkdirSync(outputDir, { recursive: true });

  const { files } = await anima.generateCode({
    fileKey: process.env.FIGMA_FILE_KEY!,
    figmaToken: process.env.FIGMA_TOKEN!,
    nodesId: [nodeId],
    settings,
  });

  for (const file of files) {
    fs.writeFileSync(`${outputDir}/${file.fileName}`, file.content);
  }
  console.log(`${preset}: ${files.length} files generated`);
}

// Compare all presets
async function compareOutputs(nodeId: string) {
  for (const preset of Object.keys(SETTINGS_PRESETS) as Array<keyof typeof SETTINGS_PRESETS>) {
    await generateWithPreset(preset, nodeId);
    await new Promise(r => setTimeout(r, 2000)); // Rate limit
  }
  console.log('\nAll presets generated in ./generated/');
}

const nodeId = process.argv[2] || '1:2';
compareOutputs(nodeId).catch(console.error);
```

### Step 3: Development Scripts

```json
{
  "scripts": {
    "generate": "tsx scripts/generate-preview.ts",
    "generate:node": "tsx scripts/generate-preview.ts",
    "preview": "vite",
    "dev": "npm run generate && npm run preview"
  }
}
```

## Output

- Multi-preset code generation comparison
- Side-by-side React/Vue/HTML output for same design
- Vite preview server for instant component viewing
- Iterative generate-preview-tweak loop

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many generations | Add 2s delay between calls |
| Different outputs each run | Anima AI variation | Pin settings; use consistent node IDs |

## Resources

- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)
- [Vite](https://vitejs.dev/)

## Next Steps

For SDK patterns and best practices, see `anima-sdk-patterns`.
