---
name: anima-sdk-patterns
description: |
  Apply production-ready patterns for the Anima SDK design-to-code pipeline.
  Use when building reusable Anima client wrappers, implementing output caching,
  or establishing team standards for design-to-code automation.
  Trigger: "anima SDK patterns", "anima best practices", "anima code patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, patterns]
compatible-with: claude-code
---

# Anima SDK Patterns

## Overview

Production patterns for `@animaapp/anima-sdk`: singleton client, generation caching, output normalization, and configurable settings presets.

## Instructions

### Step 1: Singleton Client with Configuration

```typescript
// src/anima/client.ts
import { Anima } from '@animaapp/anima-sdk';

let instance: Anima | null = null;

export function getAnimaClient(): Anima {
  if (!instance) {
    if (!process.env.ANIMA_TOKEN) throw new Error('ANIMA_TOKEN not set');
    instance = new Anima({ auth: { token: process.env.ANIMA_TOKEN } });
  }
  return instance;
}

// Preset configurations for different project needs
export const PRESETS = {
  nextjs: { language: 'typescript' as const, framework: 'react' as const, styling: 'tailwind' as const, uiLibrary: 'shadcn' as const },
  vite: { language: 'typescript' as const, framework: 'react' as const, styling: 'tailwind' as const },
  vue: { language: 'typescript' as const, framework: 'vue' as const, styling: 'tailwind' as const },
  static: { language: 'javascript' as const, framework: 'html' as const, styling: 'css' as const },
} as const;
```

### Step 2: Generation Cache

```typescript
// src/anima/cache.ts
import crypto from 'crypto';
import fs from 'fs';

interface CacheEntry {
  files: Array<{ fileName: string; content: string }>;
  generatedAt: string;
  settingsHash: string;
}

class AnimaCache {
  private cacheDir: string;

  constructor(cacheDir: string = '.anima-cache') {
    this.cacheDir = cacheDir;
    fs.mkdirSync(cacheDir, { recursive: true });
  }

  private getKey(fileKey: string, nodeId: string, settings: object): string {
    const hash = crypto.createHash('md5')
      .update(`${fileKey}:${nodeId}:${JSON.stringify(settings)}`)
      .digest('hex');
    return hash;
  }

  get(fileKey: string, nodeId: string, settings: object): CacheEntry | null {
    const key = this.getKey(fileKey, nodeId, settings);
    const path = `${this.cacheDir}/${key}.json`;
    if (!fs.existsSync(path)) return null;
    return JSON.parse(fs.readFileSync(path, 'utf8'));
  }

  set(fileKey: string, nodeId: string, settings: object, files: any[]): void {
    const key = this.getKey(fileKey, nodeId, settings);
    const entry: CacheEntry = {
      files,
      generatedAt: new Date().toISOString(),
      settingsHash: key,
    };
    fs.writeFileSync(`${this.cacheDir}/${key}.json`, JSON.stringify(entry));
  }
}

export { AnimaCache };
```

### Step 3: Output Normalizer

```typescript
// src/anima/normalizer.ts
// Normalize Anima output to match project conventions

interface NormalizationConfig {
  componentNameCase: 'PascalCase' | 'kebab-case';
  addBarrelExport: boolean;
  wrapWithCn: boolean;
  addTypeAnnotations: boolean;
}

function normalizeOutput(
  files: Array<{ fileName: string; content: string }>,
  config: NormalizationConfig,
): Array<{ fileName: string; content: string }> {
  return files.map(file => {
    let content = file.content;

    if (config.wrapWithCn && file.fileName.endsWith('.tsx')) {
      // Add cn() import and wrap className strings
      if (!content.includes("import { cn }")) {
        content = content.replace(
          /^(import .+\n)/m,
          "$1import { cn } from '@/lib/utils';\n"
        );
      }
    }

    if (config.addTypeAnnotations && file.fileName.endsWith('.tsx')) {
      content = content.replace(
        /export default function (\w+)\(\)/g,
        'export default function $1(): React.ReactElement'
      );
    }

    return { fileName: file.fileName, content };
  });
}

export { normalizeOutput, NormalizationConfig };
```

### Step 4: Error Recovery Pattern

```typescript
// src/anima/retry.ts
async function generateWithRetry(
  anima: Anima,
  params: any,
  maxRetries: number = 3,
): Promise<any> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await anima.generateCode(params);
    } catch (err: any) {
      if (attempt === maxRetries) throw err;
      const delay = 2000 * Math.pow(2, attempt - 1);
      console.log(`Generation failed, retry ${attempt}/${maxRetries} in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

## Output

- Singleton client with preset configurations
- File-based generation cache (avoid redundant API calls)
- Output normalizer for project convention matching
- Retry pattern for API resilience

## Resources

- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)
- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)

## Next Steps

Apply patterns in `anima-core-workflow-a` for automated design pipelines.
