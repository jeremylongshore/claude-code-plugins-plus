---
name: anima-common-errors
description: |
  Diagnose and fix common Anima SDK design-to-code errors.
  Use when encountering Figma token errors, code generation failures,
  node not found issues, or output quality problems.
  Trigger: "anima error", "anima not working", "anima debug", "figma to code error".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, troubleshooting]
compatible-with: claude-code
---

# Anima Common Errors

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

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Figma API Reference](https://www.figma.com/developers/api)

## Next Steps

For collecting debug data, see `anima-debug-bundle`.
