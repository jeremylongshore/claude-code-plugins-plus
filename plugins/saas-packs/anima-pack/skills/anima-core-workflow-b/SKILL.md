---
name: anima-core-workflow-b
description: |
  Clone websites to React/HTML code and customize Anima output with AI.
  Use when converting live websites to code, customizing generated components,
  or building design-system-aware code from URL screenshots.
  Trigger: "anima website to code", "anima URL clone", "anima AI customization",
  "website to react", "clone website to code".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, website-cloning]
compatible-with: claude-code
---

# Anima Core Workflow B — Website-to-Code & AI Customization

## Overview

Secondary workflow: use Anima to clone live websites into React/HTML code and customize generated output with AI-powered code modification. Anima supports URL-to-code conversion alongside Figma-to-code.

## Prerequisites

- Completed `anima-install-auth` setup
- Understanding of Anima's code generation settings

## Instructions

### Step 1: Website-to-Code Conversion

```typescript
// src/workflows/website-to-code.ts
// Anima can clone any public website and generate React or HTML code

import { Anima } from '@animaapp/anima-sdk';

const anima = new Anima({
  auth: { token: process.env.ANIMA_TOKEN! },
});

// Note: URL-to-code may use a different API endpoint
// Check docs.animaapp.com for current availability
async function cloneWebsiteToReact(url: string, outputDir: string) {
  // Anima's website-to-code feature captures the page and generates code
  // This is available via the Anima Playground or API (partner access)

  // For Figma-based workflow, use the Figma plugin to import website screenshots
  // then generate code from the imported frames
  console.log(`Cloning ${url} to React components...`);

  // Process via Figma intermediary:
  // 1. Use Anima Figma plugin to capture website layout
  // 2. Generate code from the captured frames
  // 3. Customize with AI post-processing
}
```

### Step 2: Post-Generation Customization

```typescript
// src/workflows/customize-output.ts
import fs from 'fs';
import path from 'path';

interface CustomizationRule {
  pattern: RegExp;
  replacement: string;
  description: string;
}

// Apply project-specific customizations to Anima output
function customizeGeneratedCode(
  files: Array<{ fileName: string; content: string }>,
  rules: CustomizationRule[],
): Array<{ fileName: string; content: string }> {
  return files.map(file => {
    let content = file.content;
    for (const rule of rules) {
      content = content.replace(rule.pattern, rule.replacement);
    }
    return { ...file, content };
  });
}

// Common customization rules
const PROJECT_RULES: CustomizationRule[] = [
  {
    pattern: /className="([^"]+)"/g,
    replacement: 'className={cn("$1")}',
    description: 'Wrap Tailwind classes with cn() utility',
  },
  {
    pattern: /import React from 'react'/g,
    replacement: "import React from 'react';\nimport { cn } from '@/lib/utils'",
    description: 'Add cn import for className merging',
  },
  {
    pattern: /export default function (\w+)/g,
    replacement: 'export const $1: React.FC = function $1',
    description: 'Use React.FC type annotation',
  },
];
```

### Step 3: Design Token Mapper

```typescript
// src/workflows/token-mapper.ts
// Map Anima's raw Tailwind classes to your design system tokens

interface TokenMap {
  colors: Record<string, string>;     // Anima color → your token
  spacing: Record<string, string>;    // Anima spacing → your token
  typography: Record<string, string>; // Anima font → your token
}

const tokenMap: TokenMap = {
  colors: {
    'bg-\\[#1a1a2e\\]': 'bg-primary',
    'text-\\[#e94560\\]': 'text-accent',
    'bg-\\[#16213e\\]': 'bg-surface',
  },
  spacing: {
    'p-\\[24px\\]': 'p-6',
    'gap-\\[16px\\]': 'gap-4',
    'mt-\\[32px\\]': 'mt-8',
  },
  typography: {
    'text-\\[32px\\]': 'text-3xl',
    'font-\\[600\\]': 'font-semibold',
  },
};

function applyDesignTokens(content: string, map: TokenMap): string {
  let result = content;
  for (const category of Object.values(map)) {
    for (const [from, to] of Object.entries(category)) {
      result = result.replace(new RegExp(from, 'g'), to);
    }
  }
  return result;
}
```

### Step 4: Multi-Component Output Organizer

```typescript
// src/workflows/organizer.ts
import fs from 'fs';
import path from 'path';

function organizeGeneratedFiles(
  files: Array<{ fileName: string; content: string }>,
  baseDir: string,
): void {
  // Organize by component type
  const structure: Record<string, string> = {
    '.tsx': 'components',
    '.vue': 'components',
    '.css': 'styles',
    '.ts': 'types',
    '.html': 'pages',
  };

  for (const file of files) {
    const ext = path.extname(file.fileName);
    const subDir = structure[ext] || 'misc';
    const dir = path.join(baseDir, subDir);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, file.fileName), file.content);
  }

  // Generate barrel export
  const components = files.filter(f => f.fileName.endsWith('.tsx'));
  if (components.length > 0) {
    const exports = components.map(f => {
      const name = path.basename(f.fileName, '.tsx');
      return `export { default as ${name} } from './${name}';`;
    });
    fs.writeFileSync(
      path.join(baseDir, 'components', 'index.ts'),
      exports.join('\n') + '\n'
    );
  }
}
```

## Output

- Website cloning to React/HTML via Figma intermediary
- Post-generation customization rules engine
- Design token mapper for project consistency
- File organizer with barrel exports

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| URL not accessible | Website blocks scraping | Use Figma plugin to capture manually |
| Output doesn't match design | Complex animations/interactions | Simplify to static layout first |
| Token mapping misses | New colors/spacing in design | Update token map after each generation |

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)
- [Anima Playground](https://www.animaapp.com)
- [Anima Blog: GenAI Customization](https://www.animaapp.com/blog/genai/genai-figma-to-code-6-examples-of-how-to-use-animas-new-ai-code-customization/)

## Next Steps

For common errors and debugging, see `anima-common-errors`.
