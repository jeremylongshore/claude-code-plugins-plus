---
name: figma-common-errors
description: |
  Diagnose and fix common Figma REST API and Plugin API errors.
  Use when encountering HTTP errors, plugin sandbox crashes,
  or unexpected API responses from Figma.
  Trigger with phrases like "figma error", "fix figma",
  "figma not working", "figma 403", "figma 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Common Errors

## Overview
Quick reference for the most common Figma REST API and Plugin API errors, with exact error messages and working solutions.

## Prerequisites
- Figma API credentials configured
- Access to your application logs or browser console

## Instructions

### Step 1: Identify the Error Category

#### REST API HTTP Errors

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 400 | Bad Request | Malformed request, invalid node IDs | Verify node ID format (`pageId:nodeId`, e.g., `0:1`) |
| 403 | Forbidden | Invalid token, wrong scopes, no file access | Regenerate PAT with correct scopes; verify file sharing |
| 404 | Not Found | Wrong file key, deleted file, wrong endpoint | Check file key from URL; verify file exists |
| 429 | Rate Limited | Too many requests | Read `Retry-After` header; implement backoff |
| 500 | Internal Server Error | Figma server issue | Retry with exponential backoff; check status.figma.com |

### Step 2: Diagnose Specific Errors

#### 403 Forbidden -- Token Issues
```bash
# Test your token
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me
# 200 = token valid, 403 = invalid/expired

# Check what scopes your request needs
# file_content:read  -> GET /v1/files/:key
# file_comments:read -> GET /v1/files/:key/comments
# file_variables:read -> GET /v1/files/:key/variables/local
# webhooks:write     -> POST /v2/webhooks
```

Common 403 causes:
- PAT expired (90-day maximum lifetime)
- Token missing required scope (e.g., using `file_content:read` but calling comments endpoint)
- File not shared with the token owner
- OAuth token not refreshed after expiry

#### 429 Rate Limited
```typescript
// Figma returns these headers on 429:
// Retry-After: <seconds>            -- wait this long before retrying
// X-Figma-Rate-Limit-Type: <type>   -- "low" or "high" tier
// X-Figma-Plan-Tier: <plan>         -- your plan level

async function handleRateLimit(response: Response) {
  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    const limitType = response.headers.get('X-Figma-Rate-Limit-Type');
    console.warn(`Rate limited (${limitType}). Retrying in ${retryAfter}s`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return true; // signal to retry
  }
  return false;
}
```

#### 404 Not Found
```bash
# Verify your file key is correct
# URL format: https://www.figma.com/design/<FILE_KEY>/<file-name>
# The file key is the string between /design/ and the next /

# Test the file key
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq '.name // "FILE NOT FOUND"'
```

#### Images Endpoint Returns `null`
```typescript
// GET /v1/images/:key returns null for nodes that cannot render
const images = await exportImages(['0:1', '0:2']);

for (const [nodeId, url] of Object.entries(images)) {
  if (url === null) {
    // Node failed to render. Common causes:
    // - Node is invisible (visibility: false)
    // - Node has 0% opacity
    // - Node ID does not exist in the file
    // - Node has no visual content (e.g., an empty frame)
    console.error(`Failed to render node ${nodeId}`);
  }
}
```

### Step 3: Plugin API Errors

| Error | Context | Cause | Solution |
|-------|---------|-------|----------|
| `figma is not defined` | Node.js / browser | Running plugin code outside Figma sandbox | Plugin code only runs inside Figma desktop app |
| `Cannot read property of undefined` | Plugin | Accessing deleted node reference | Re-query node: `figma.getNodeById(id)` |
| `Plugin timed out` | Plugin | Operation took too long | Use `figma.commitUndo()` and batch operations |
| `Quota exceeded` | Plugin | Too many nodes created | Limit to ~5000 nodes per operation |
| `Permission denied` | Plugin | Missing `manifest.json` permission | Add required permission to `permissions` array |

### Step 4: Quick Diagnostic Script
```bash
#!/bin/bash
echo "=== Figma API Diagnostics ==="

# 1. Check Figma service status
echo -n "Figma Status: "
curl -s -o /dev/null -w "%{http_code}" https://www.figma.com && echo " OK" || echo " DOWN"

# 2. Validate token
echo -n "Token Valid: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me

# 3. Check file access
echo -n "File Access: "
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq -r '.name // "FAILED"'

# 4. Check env vars
echo "FIGMA_PAT: ${FIGMA_PAT:+SET (${#FIGMA_PAT} chars)}"
echo "FIGMA_FILE_KEY: ${FIGMA_FILE_KEY:-NOT SET}"
```

## Output
- Identified error cause from status code and headers
- Applied targeted fix
- Verified resolution with diagnostic commands

## Examples

### Error Wrapper with Actionable Messages
```typescript
function diagnoseFigmaError(status: number, body: string): string {
  switch (status) {
    case 403: return 'Auth failed. Check: (1) PAT not expired (2) correct scopes (3) file shared with you';
    case 404: return 'Not found. Check: (1) file key from URL (2) file not deleted (3) node IDs valid';
    case 429: return 'Rate limited. Implement exponential backoff with Retry-After header';
    case 500: return 'Figma server error. Check status.figma.com and retry with backoff';
    default: return `Unexpected ${status}: ${body}`;
  }
}
```

## Resources
- [Figma Status Page](https://status.figma.com)
- [Figma REST API Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [Figma API Scopes](https://developers.figma.com/docs/rest-api/scopes/)

## Next Steps
For comprehensive debugging, see `figma-debug-bundle`.
