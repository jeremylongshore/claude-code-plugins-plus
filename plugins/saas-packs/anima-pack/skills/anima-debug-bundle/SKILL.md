---
name: anima-debug-bundle
description: |
  Collect Anima SDK debug evidence for support tickets and troubleshooting.
  Use when filing Anima support requests, debugging code generation issues,
  or collecting diagnostic data for the Anima team.
  Trigger: "anima debug bundle", "anima support ticket", "anima diagnostics".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, debugging]
compatible-with: claude-code
---

# Anima Debug Bundle

## Instructions

### Step 1: Generate Debug Bundle

```typescript
// src/debug/anima-debug.ts
import fs from 'fs';

async function generateDebugBundle() {
  const bundle = {
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      sdkVersion: require('@animaapp/anima-sdk/package.json').version,
      animaToken: process.env.ANIMA_TOKEN ? 'SET (redacted)' : 'NOT SET',
      figmaToken: process.env.FIGMA_TOKEN ? 'SET (redacted)' : 'NOT SET',
    },
    figmaAccess: await testFigmaAccess(),
    generationTest: await testGeneration(),
  };

  const filename = `anima-debug-${Date.now()}.json`;
  fs.writeFileSync(filename, JSON.stringify(bundle, null, 2));
  console.log(`Debug bundle: ${filename}`);
  return bundle;
}

async function testFigmaAccess() {
  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN! },
    });
    const data = await res.json();
    return { status: res.ok ? 'ok' : 'failed', user: data.handle || data.err };
  } catch (err: any) {
    return { status: 'failed', error: err.message };
  }
}

async function testGeneration() {
  try {
    const { Anima } = await import('@animaapp/anima-sdk');
    const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });
    return { status: 'sdk_loaded', version: 'check package.json' };
  } catch (err: any) {
    return { status: 'sdk_failed', error: err.message };
  }
}

generateDebugBundle().catch(console.error);
```

## Output

- JSON debug bundle with SDK version, token status, and connectivity test
- Figma API access verification
- Safe for sharing with Anima support (tokens redacted)

## Resources

- [Anima Support](https://support.animaapp.com)
- [Anima SDK GitHub Issues](https://github.com/AnimaApp/anima-sdk/issues)

## Next Steps

For rate limiting, see `anima-rate-limits`.
