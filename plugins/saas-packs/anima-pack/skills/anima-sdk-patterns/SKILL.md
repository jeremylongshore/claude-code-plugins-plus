---
name: anima-sdk-patterns
description: 'Apply production-ready patterns for the Anima SDK design-to-code pipeline.

  Use when building reusable Anima client wrappers, implementing output caching,

  or establishing team standards for design-to-code automation.

  Trigger: "anima SDK patterns", "anima best practices", "anima code patterns".

  '
allowed-tools: Read, Write, Edit
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- patterns
compatibility: Designed for Claude Code
---
# Anima SDK Patterns

## Overview

Production patterns for `@animaapp/anima-sdk`: singleton client, generation caching, output normalization, and configurable settings presets.

## Prerequisites

- Pin the Anima SDK and TypeScript runtime versions, define the supported framework presets, and provide a sandbox Figma file containing synthetic components for tests and examples.
- Inject `ANIMA_TOKEN` and any Figma credentials from a secret manager at runtime. Authentication failures must be distinguishable from generation failures; never hard-code, log, cache, or include credentials in generated output or receipts.
- Make `.anima-cache` private to the worker, exclude it from version control and artifact uploads, and define a retention/deletion policy. Cache keys may identify a request, but cached design source and generated content must not be sent to telemetry.
- Set an allowlist for input file/node IDs and output paths, a maximum cache size, a bounded retry count, and an owner-approved normalization configuration before enabling the wrapper in CI or production.

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

## Error Handling

- Fail fast with a redacted configuration error when `ANIMA_TOKEN` is missing or rejected, and do not retry 401/403 responses. Check Figma file/node permissions separately from Anima authentication so an operator can correct the smallest scope.
- Treat cache misses as normal, but treat malformed JSON, schema drift, a settings-hash mismatch, or a cache entry outside the approved directory as a cache failure: quarantine or delete that entry and regenerate from the sandbox-approved request rather than trusting it.
- Retry only bounded transient network, timeout, 429, and 5xx failures with exponential backoff and jitter. Cap total attempts and elapsed time; use a request fingerprint to make a resume idempotent and never retry a whole batch when only selected nodes failed.
- If normalization or type-checking fails, retain the raw result only in the private quarantine area, block publication, and report rule IDs plus file counts. Never write generated source, design contents, personal data, or exception payloads to logs.
- On process interruption or partial cache writes, use atomic replacement and restore the previous valid entry. A rollback removes quarantined artifacts, revokes temporary access, and records only the digest, stage, and retention/deletion result.

## Examples

The wrapper can keep a sandbox run deterministic while avoiding duplicate generation:

```typescript
const settings = PRESETS.nextjs;
const fileKey = 'synthetic-design-system';
const nodeId = 'button-primary-fixture';
const cache = new AnimaCache('/var/lib/anima-cache/sandbox');

const cached = cache.get(fileKey, nodeId, settings);
const files = cached?.files ?? (await getAnimaClient().generateCode({
  fileKey,
  nodesId: [nodeId],
  settings,
})).files;

if (!cached) cache.set(fileKey, nodeId, settings, files);
const normalized = normalizeOutput(files, {
  componentNameCase: 'PascalCase',
  addBarrelExport: true,
  wrapWithCn: false,
  addTypeAnnotations: true,
});
console.log(JSON.stringify({ fileKey, nodeCount: 1, files: normalized.length, contactsExported: 0 }));
```

The acceptance receipt for this fixture is `cache=miss|hit; source=synthetic; files=bounded; contacts_exported=0; secret_scan=pass`. A production run additionally requires an approved file/node allowlist, a reviewed diff, and a tested rollback reference before the normalized files are published.

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
