---
name: exa-common-errors
description: |
  Diagnose and fix Exa API errors by HTTP code and error tag.
  Use when encountering Exa errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "exa error", "fix exa",
  "exa not working", "debug exa", "exa 429", "exa 401".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, debugging, errors]

---
# Exa Common Errors

## Overview
Quick reference for Exa API errors by HTTP status code and error tag. All error responses include a `requestId` field — include it when contacting Exa support at hello@exa.ai.

## Error Reference

### 400 — Bad Request
| Error Tag | Cause | Solution |
|-----------|-------|----------|
| `INVALID_REQUEST_BODY` | Malformed JSON or missing required fields | Validate JSON structure and required `query` field |
| `INVALID_REQUEST` | Conflicting parameters | Remove contradictory options (e.g., date filters with `company` category) |
| `INVALID_URLS` | Malformed URLs in `getContents` | Ensure URLs have `https://` protocol |
| `INVALID_NUM_RESULTS` | numResults > 100 with highlights | Reduce to <= 100 or remove highlights |
| `INVALID_JSON_SCHEMA` | Bad schema in `summary.schema` | Validate JSON schema syntax |
| `NUM_RESULTS_EXCEEDED` | Exceeds plan limit | Check your plan's max results |
| `NO_CONTENT_FOUND` | No content at provided URLs | Verify URLs are accessible |

### 401 — Unauthorized
```bash
# Verify your API key is set and valid
echo "Key set: ${EXA_API_KEY:+yes}"

# Test with curl
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","numResults":1}'
```

**Fix:** Regenerate API key at [dashboard.exa.ai](https://dashboard.exa.ai).

### 402 — Payment Required
| Error Tag | Cause | Solution |
|-----------|-------|----------|
| `NO_MORE_CREDITS` | Account balance exhausted | Top up at dashboard.exa.ai |
| `API_KEY_BUDGET_EXCEEDED` | Spending limit reached | Increase budget in API key settings |

### 403 — Forbidden
| Error Tag | Cause | Solution |
|-----------|-------|----------|
| `ACCESS_DENIED` | Feature not available on plan | Upgrade plan or contact Exa |
| `FEATURE_DISABLED` | Endpoint not enabled | Check plan capabilities |
| `ROBOTS_FILTER_FAILED` | URL blocked by robots.txt | Use a different URL |
| `PROHIBITED_CONTENT` | Content blocked by moderation | Review query for policy violations |

### 429 — Rate Limited
```typescript
// Default rate limit: 10 QPS (queries per second)
// Error response format: { "error": "rate limit exceeded" }

// Fix: implement exponential backoff
async function searchWithBackoff(exa: Exa, query: string, opts: any) {
  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      return await exa.search(query, opts);
    } catch (err: any) {
      if (err.status !== 429) throw err;
      const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
      console.log(`Rate limited. Waiting ${delay.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Rate limit retries exhausted");
}
```

### 422 — Unprocessable Entity
| Error Tag | Cause | Solution |
|-----------|-------|----------|
| `FETCH_DOCUMENT_ERROR` | URL could not be crawled | Verify URL is accessible and not paywalled |

### 5xx — Server Errors
| Code | Tag | Action |
|------|-----|--------|
| 500 | `DEFAULT_ERROR` / `INTERNAL_ERROR` | Retry after 1-2 seconds |
| 501 | `UNABLE_TO_GENERATE_RESPONSE` | Rephrase query (answer endpoint) |
| 502 | Bad Gateway | Retry with delay |
| 503 | Service Unavailable | Check status page, retry later |

### Content Fetch Errors (per-URL status in getContents)
| Tag | Cause | Resolution |
|-----|-------|-----------|
| `CRAWL_NOT_FOUND` | Content unavailable at URL | Verify URL correctness |
| `CRAWL_TIMEOUT` | Fetch timed out | Retry or increase `livecrawlTimeout` |
| `CRAWL_LIVECRAWL_TIMEOUT` | Live crawl exceeded timeout | Set `livecrawlTimeout: 15000` or use `livecrawl: "fallback"` |
| `SOURCE_NOT_AVAILABLE` | Paywalled or blocked | Try cached content with `livecrawl: "never"` |
| `UNSUPPORTED_URL` | Non-HTTP URL scheme | Use standard HTTPS URLs |

## Quick Diagnostic Script
```bash
set -euo pipefail

echo "=== Exa Diagnostics ==="
echo "API Key: ${EXA_API_KEY:+SET (${#EXA_API_KEY} chars)}"

# Test basic connectivity
echo -n "API connectivity: "
HTTP_CODE=$(curl -s -o /tmp/exa-test.json -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"connectivity test","numResults":1}')
echo "$HTTP_CODE"

if [ "$HTTP_CODE" != "200" ]; then
  echo "Error response:"
  cat /tmp/exa-test.json | python3 -m json.tool 2>/dev/null || cat /tmp/exa-test.json
fi
```

## Instructions
1. Check the HTTP status code from the error response
2. Match the error tag to the tables above
3. Apply the documented solution
4. Include `requestId` from error responses when contacting support

## Resources
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Exa Rate Limits](https://docs.exa.ai/reference/rate-limits)
- [Exa Status Page](https://status.exa.ai)

## Next Steps
For comprehensive debugging, see `exa-debug-bundle`. For rate limit patterns, see `exa-rate-limits`.
