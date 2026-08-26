---
name: anima-debug-bundle
description: 'Collect Anima SDK debug evidence for support tickets and troubleshooting.

  Use when filing Anima support requests, debugging code generation issues,

  or collecting diagnostic data for the Anima team.

  Trigger: "anima debug bundle", "anima support ticket", "anima diagnostics".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Grep
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- debugging
compatibility: Designed for Claude Code
---
# Anima Debug Bundle

## Overview

Collect a narrowly scoped, redactable diagnostic artifact for a reproducible
Anima or Figma integration failure. Review the file locally before sharing it:
token-presence indicators are acceptable; credential values, private design
content, and personal identity data are not.

## Prerequisites

- A scoped development credential and a disposable/staging design fixture that
  reproduces the issue without exposing a customer or private production file.
- The expected file/node/settings tuple, timestamp, and sanitized error or
  request ID to correlate the bundle with the reported issue.
- A support-sharing review process and an owner able to rotate credentials if a
  diagnostic artifact is found to contain sensitive material.

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

## Examples

When generation fails against a staging component, run the bundle generator
with scoped credentials and inspect the JSON before attaching it to a support
ticket. Confirm that it contains SDK version, token state, and sanitized
connectivity result—but not token values, the full design payload, or a private
file name. Attach the bundle with the problem timestamp and request ID. If the
review finds sensitive content or the test cannot reproduce safely, do not
upload the file; quarantine it, rotate an exposed credential if needed, reduce
the captured fields, and regenerate the diagnostic.

## Error Handling

| Failure | Response |
|---------|----------|
| Diagnostic credentials are missing or invalid | Stop the run and correct the managed secret binding without printing values. |
| Figma or SDK check fails | Record only status/error category and attach the sanitized context to the incident. |
| Bundle contains sensitive data | Quarantine it, rotate affected credentials, improve redaction, and regenerate. |
| Issue cannot be reproduced in staging | Escalate with minimal non-sensitive metadata rather than collecting production design content. |

## Resources

- [Anima Support](https://support.animaapp.com)
- [Anima SDK GitHub Issues](https://github.com/AnimaApp/anima-sdk/issues)

## Next Steps

For rate limiting, see `anima-rate-limits`.
