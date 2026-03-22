---
name: figma-advanced-troubleshooting
description: |
  Deep debugging for Figma API issues: network analysis, response inspection, and support escalation.
  Use when standard troubleshooting fails, diagnosing intermittent failures,
  or preparing detailed evidence for Figma support.
  Trigger with phrases like "figma hard bug", "figma mystery error",
  "figma deep debug", "figma intermittent failure", "figma support ticket".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Advanced Troubleshooting

## Overview
Deep debugging techniques for complex Figma REST API issues that resist standard error handling: intermittent failures, unexpected response shapes, rate limit edge cases, and large file timeouts.

## Prerequisites
- Access to application logs
- `curl` with verbose mode for network inspection
- Figma API credentials for testing

## Instructions

### Step 1: Verbose Request Inspection
```bash
# Full HTTP request/response trace for a Figma API call
curl -v -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1" 2>&1 \
  | tee figma-debug-trace.txt

# Extract key diagnostic info:
# - TLS version and cipher
# - Response status and headers
# - Timing breakdown
curl -w "
DNS:        %{time_namelookup}s
Connect:    %{time_connect}s
TLS:        %{time_appconnect}s
TTFB:       %{time_starttransfer}s
Total:      %{time_total}s
Size:       %{size_download} bytes
Status:     %{http_code}
" -s -o /dev/null \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1"
```

### Step 2: Response Shape Validation
```typescript
// Figma API responses can be unexpectedly shaped when:
// - File is empty or newly created
// - Nodes have been deleted between requests
// - Plugin data is corrupted

function validateFileResponse(data: any): string[] {
  const issues: string[] = [];

  if (!data.document) issues.push('Missing document root');
  if (!data.document?.children?.length) issues.push('Document has no pages');
  if (typeof data.name !== 'string') issues.push('Missing file name');
  if (!data.version) issues.push('Missing version field');

  // Check for null nodes (deleted between list and fetch)
  if (data.nodes) {
    for (const [id, node] of Object.entries(data.nodes)) {
      if (node === null) issues.push(`Null node: ${id} (deleted or invisible)`);
    }
  }

  // Check images response for null renders
  if (data.images) {
    for (const [id, url] of Object.entries(data.images)) {
      if (url === null) issues.push(`Image render failed for node: ${id}`);
    }
  }

  return issues;
}
```

### Step 3: Rate Limit Edge Cases
```typescript
// Problem: Figma rate limits are per-user, per-minute, but the exact
// limit is not published and varies by plan tier and seat type.

// Diagnostic: measure your actual limit by counting successful requests
async function measureRateLimit(token: string): Promise<{
  requestsMade: number;
  firstRateLimitAt: number | null;
  retryAfter: number | null;
}> {
  let count = 0;
  let rateLimitAt: number | null = null;
  let retryAfter: number | null = null;

  // Make requests until rate limited (use a read-only endpoint)
  while (count < 200) {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': token },
    });

    if (res.status === 429) {
      rateLimitAt = count;
      retryAfter = parseInt(res.headers.get('Retry-After') || '0');
      break;
    }

    count++;
    // Small delay to avoid instant burst
    await new Promise(r => setTimeout(r, 100));
  }

  return { requestsMade: count, firstRateLimitAt: rateLimitAt, retryAfter };
}
```

### Step 4: Large File Debugging
```typescript
// Large Figma files (1000+ components) can cause:
// - Response timeouts (>30s)
// - Memory issues (100+ MB JSON)
// - Rate limits from repeated retries

// Strategy: chunk the file by page
async function fetchLargeFileSafely(fileKey: string, token: string) {
  // 1. Get file metadata with depth=1 (just pages, not children)
  const meta = await fetch(
    `https://api.figma.com/v1/files/${fileKey}?depth=1`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  console.log(`File: ${meta.name}, Pages: ${meta.document.children.length}`);

  // 2. Fetch each page's content individually
  const results = [];
  for (const page of meta.document.children) {
    console.log(`Fetching page: ${page.name} (${page.id})`);

    const pageData = await fetch(
      `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${page.id}`,
      { headers: { 'X-Figma-Token': token } }
    ).then(r => r.json());

    results.push({ pageId: page.id, pageName: page.name, data: pageData });

    // Respect rate limits between page fetches
    await new Promise(r => setTimeout(r, 500));
  }

  return results;
}
```

### Step 5: Support Escalation Template
```markdown
## Figma API Support Request

**Account email:** [your-email]
**Plan tier:** [Starter/Professional/Organization/Enterprise]
**Endpoint:** [e.g., GET /v1/files/:key]
**File key:** [file key, not sensitive]

### Issue Description
[1-2 sentences describing the problem]

### Reproduction Steps
1. Call `GET https://api.figma.com/v1/files/FILE_KEY?depth=1`
2. Observe: [expected vs actual behavior]

### Diagnostic Data
- HTTP status: [status code]
- Response headers: [relevant headers, especially rate limit]
- Response time: [from curl timing]
- Frequency: [every time / intermittent / specific conditions]

### Request/Response (redacted)
```
curl -v -H "X-Figma-Token: [REDACTED]" \
  "https://api.figma.com/v1/files/FILE_KEY?depth=1"

HTTP/2 [status]
x-figma-rate-limit-type: [value]
retry-after: [value]
```

### Environment
- Node.js: [version]
- OS: [os]
- Region: [your server region]
- Behind proxy: [yes/no]
```

## Output
- Verbose request/response traces captured
- Response shape issues identified
- Rate limit behavior measured
- Large file handled with page-level chunking
- Support ticket prepared with diagnostic data

## Error Handling
| Issue | Diagnostic | Solution |
|-------|-----------|----------|
| Intermittent 500s | Track frequency and timing | Log every request; report pattern to Figma |
| Slow responses | curl timing breakdown | Check if DNS/TLS is the bottleneck |
| Null image renders | Validate node visibility | Check node opacity and visibility in Figma |
| Memory crash | Large file JSON | Use `depth=1` + per-page `/nodes` calls |

## Resources
- [Figma Developer Forum](https://forum.figma.com/)
- [Figma Support](https://help.figma.com/hc/en-us/requests/new)
- [Figma Status Page](https://status.figma.com)

## Next Steps
For load testing, see `figma-load-scale`.
