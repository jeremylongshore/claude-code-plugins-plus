---
name: anima-common-errors
description: 'Diagnose and fix common Anima SDK design-to-code errors.

  Use when encountering Figma token errors, code generation failures,

  node not found issues, or output quality problems.

  Trigger: "anima error", "anima not working", "anima debug", "figma to code error".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- troubleshooting
compatibility: Designed for Claude Code
---
# Anima Common Errors

## Overview

Use this guide to diagnose design-to-code failures without widening design-file
access or leaking tokens. Start from a reproducible file/node/settings tuple
and use a least-privilege development credential for all verification.

## Prerequisites

- A sanitized error record with the design file identifier, node identifier,
  selected generation settings, timestamp, and request ID where available.
- Scoped Anima and Figma credentials held in a secret store; never paste a
  personal access token into a ticket, source file, or shared diagnostic log.
- A staging or disposable design fixture so fixes can be reproduced without
  mutating a production design file.

## Instructions

1. Classify the failure as authentication, file/node resolution, generator
   configuration, timeout/rate limit, or rendered-output quality.
2. Reproduce it with the smallest approved frame/component and the diagnostic
   commands, capturing only sanitized results.
3. Correct the matching design input, entitlement, or generation configuration
   and rerun only that fixture.
4. Validate the generated file location, lint/build result, and visual review
   before updating a broader component set.

## Error Reference

### Authentication Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `Invalid Anima token` | Token not provisioned or expired | Request new token from Anima team |
| `Invalid Figma token` | PAT expired or revoked | Generate new PAT: Figma > Settings > Access Tokens |
| `Unauthorized` | Token lacks file access | Ensure Figma PAT has file read permission |

### File & Node Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `File not found` | Wrong file key | Extract from Figma URL: `figma.com/file/{KEY}/...` |
| `Node not found` | Invalid node ID | Copy node link from Figma: right-click > Copy link |
| `No renderable content` | Selected a page or group | Select a frame, component, or component set |
| Empty `files` array | Node is empty or hidden | Unhide layers; ensure node has visible content |

### Code Generation Errors

```typescript
// Common generation error handler
async function safeGenerate(anima: Anima, params: any) {
  try {
    return await anima.generateCode(params);
  } catch (err: any) {
    if (err.message?.includes('rate limit')) {
      console.error('Rate limited — wait 60s before retrying');
    } else if (err.message?.includes('timeout')) {
      console.error('Generation timed out — simplify the Figma node');
    } else if (err.message?.includes('Invalid settings')) {
      console.error('Invalid settings combo — check framework/styling/uiLibrary compatibility');
    } else {
      console.error('Generation error:', err.message);
    }
    return null;
  }
}
```

### Output Quality Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Messy layout | No auto-layout in Figma | Convert frames to auto-layout |
| Wrong colors | Hardcoded hex instead of Figma variables | Use Figma color variables/styles |
| Missing text | Text is inside masked groups | Flatten masks before generating |
| Extra wrappers | Deeply nested groups | Flatten group hierarchy |
| Wrong component names | Unnamed Figma layers | Name layers descriptively |

### Valid Settings Combinations

| Framework | Language | Styling | UI Library |
|-----------|----------|---------|------------|
| `react` | `typescript`, `javascript` | `tailwind`, `css`, `styled-components` | `none`, `mui`, `antd`, `shadcn` |
| `vue` | `typescript`, `javascript` | `tailwind`, `css` | `none` |
| `html` | `javascript` | `css`, `tailwind` | `none` |

## Diagnostic Script

```bash
# Verify Figma token
curl -s "https://api.figma.com/v1/me" \
  -H "X-Figma-Token: ${FIGMA_TOKEN}" | jq '.handle // .err'

# Verify file access
curl -s "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  -H "X-Figma-Token: ${FIGMA_TOKEN}" | jq '.name // .err'
```

## Output

- Error classified and root cause identified
- Valid settings matrix for reference
- Diagnostic commands for token and file verification

## Examples

When a staging generation returns `Node not found`, compare the copied node ID
with the approved Figma link, then run the file-access diagnostic using a scoped
development token. Regenerate only that small frame after correcting the ID and
confirm files are emitted to the expected generated-code directory. If access
is denied, the node remains hidden, or output is empty, stop the run and ask
the file owner to correct permissions or visibility; do not expand the token’s
scope or substitute a personal token to get past the error.

## Error Handling

| Failure | Response |
|---------|----------|
| Token is invalid, expired, or over-scoped | Stop the diagnostic, replace it through managed secret rotation, and avoid logging the value. |
| File or node cannot be resolved | Verify the approved link and visibility with the design owner before retrying. |
| Generator times out or rate-limits | Use bounded backoff or simplify the fixture; do not fan out uncontrolled retries. |
| Generated output is unsafe or wrong | Keep it out of the main branch, correct source design/settings, and rerun targeted validation. |

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Figma API Reference](https://www.figma.com/developers/api)

## Next Steps

For collecting debug data, see `anima-debug-bundle`.
