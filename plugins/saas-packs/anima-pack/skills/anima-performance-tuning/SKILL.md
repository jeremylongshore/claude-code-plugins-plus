---
name: anima-performance-tuning
description: |
  Optimize Anima code generation performance with caching, parallelism, and output tuning.
  Use when reducing generation latency, optimizing batch component generation,
  or improving generated code quality for production use.
  Trigger: "anima performance", "anima slow", "anima optimization", "anima caching".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, performance]
compatible-with: claude-code
---

# Anima Performance Tuning

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Single component generation | < 10s | Depends on complexity |
| Batch (10 components) | < 2 min | With rate limit delays |
| Cache hit | < 10ms | File-based cache |
| Full design system (50 components) | < 15 min | Sequential with 6s delays |

## Instructions

### Step 1: File-Based Generation Cache

```typescript
// src/performance/cache.ts
import crypto from 'crypto';
import fs from 'fs';

class GenerationCache {
  private dir: string;

  constructor(cacheDir = '.anima-cache') {
    this.dir = cacheDir;
    fs.mkdirSync(cacheDir, { recursive: true });
  }

  private hash(fileKey: string, nodeId: string, settings: any): string {
    return crypto.createHash('md5').update(`${fileKey}:${nodeId}:${JSON.stringify(settings)}`).digest('hex');
  }

  async getOrGenerate(
    anima: any,
    params: any,
    maxAgeMs: number = 3600000, // 1 hour
  ): Promise<any> {
    const key = this.hash(params.fileKey, params.nodesId[0], params.settings);
    const path = `${this.dir}/${key}.json`;

    if (fs.existsSync(path)) {
      const stat = fs.statSync(path);
      if (Date.now() - stat.mtimeMs < maxAgeMs) {
        return JSON.parse(fs.readFileSync(path, 'utf8'));
      }
    }

    const result = await anima.generateCode(params);
    fs.writeFileSync(path, JSON.stringify(result));
    return result;
  }

  clearOlderThan(maxAgeMs: number): number {
    let cleared = 0;
    for (const file of fs.readdirSync(this.dir)) {
      const path = `${this.dir}/${file}`;
      if (Date.now() - fs.statSync(path).mtimeMs > maxAgeMs) {
        fs.unlinkSync(path);
        cleared++;
      }
    }
    return cleared;
  }
}

export { GenerationCache };
```

### Step 2: Incremental Generation (Only Changed Components)

```typescript
// src/performance/incremental.ts
// Only regenerate components whose Figma nodes changed

async function getNodeLastModified(fileKey: string, nodeId: string): Promise<string> {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${nodeId}`,
    { headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN! } }
  );
  const data = await res.json();
  return data.lastModified;
}

async function generateOnlyChanged(
  anima: any,
  fileKey: string,
  nodeIds: string[],
  lastModifiedCache: Map<string, string>,
): Promise<string[]> {
  const changed: string[] = [];

  for (const nodeId of nodeIds) {
    const lastMod = await getNodeLastModified(fileKey, nodeId);
    if (lastMod !== lastModifiedCache.get(nodeId)) {
      changed.push(nodeId);
      lastModifiedCache.set(nodeId, lastMod);
    }
  }

  console.log(`${changed.length}/${nodeIds.length} components changed — regenerating`);
  return changed;
}
```

### Step 3: Output Size Optimization

```typescript
// src/performance/output-opt.ts
// Post-process generated code for smaller bundle size

function optimizeOutput(content: string): string {
  return content
    .replace(/\/\*[\s\S]*?\*\//g, '')         // Remove block comments
    .replace(/^\s*\/\/.*$/gm, '')              // Remove line comments
    .replace(/\n{3,}/g, '\n\n')               // Collapse multiple blank lines
    .trim();
}
```

## Output

- File-based generation cache with TTL
- Incremental generation (only changed components)
- Output size optimization via post-processing

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)
- [Figma API Nodes](https://www.figma.com/developers/api#get-file-nodes-endpoint)

## Next Steps

For cost optimization, see `anima-cost-tuning`.
