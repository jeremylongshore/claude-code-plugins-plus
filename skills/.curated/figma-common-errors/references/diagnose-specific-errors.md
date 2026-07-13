# Step 2: Diagnose Specific Errors

Deep-dive reference for the `figma-common-errors` skill — extracted from the 'Step 2: Diagnose Specific Errors' step of the workflow.

## 403 Forbidden -- Token Issues

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

## 429 Rate Limited

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

## 404 Not Found

```bash
# Verify your file key is correct
# URL format: https://www.figma.com/design/<FILE_KEY>/<file-name>
# The file key is the string between /design/ and the next /

# Test the file key
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq '.name // "FILE NOT FOUND"'
```

## Images Endpoint Returns `null`

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
