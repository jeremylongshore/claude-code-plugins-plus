---
name: cohere-common-errors
description: |
  Diagnose and fix Cohere API v2 errors and exceptions.
  Use when encountering Cohere errors, debugging failed requests,
  or troubleshooting CohereError, CohereTimeoutError, rate limits.
  Trigger with phrases like "cohere error", "fix cohere",
  "cohere not working", "debug cohere", "cohere 429", "cohere 400".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Common Errors

## Overview
Quick reference for real Cohere API v2 errors with exact messages, causes, and fixes.

## Prerequisites
- `cohere-ai` SDK installed
- `CO_API_KEY` configured
- Access to error logs

## Error Reference

### 400 — Bad Request: Missing Required Field

```
CohereError: model is required
```

**Cause:** API v2 requires `model` for all endpoints (Chat, Embed, Rerank, Classify).

**Fix:**
```typescript
// Wrong (v1 style)
await cohere.chat({ messages: [...] });

// Correct (v2)
await cohere.chat({ model: 'command-a-03-2025', messages: [...] });
```

---

### 400 — Embed: Missing embedding_types

```
CohereError: embedding_types is required for embed models v3 and higher
```

**Fix:**
```typescript
await cohere.embed({
  model: 'embed-v4.0',
  texts: ['hello'],
  inputType: 'search_document',
  embeddingTypes: ['float'],  // Required for v3+
});
```

---

### 400 — Embed: Missing input_type

```
CohereError: input_type is required for embed models v3 and higher
```

**Fix:** Use one of: `search_document`, `search_query`, `classification`, `clustering`, `image`.

---

### 401 — Invalid API Token

```
CohereError: invalid api token
```

**Cause:** `CO_API_KEY` is missing, wrong, or revoked.

**Fix:**
```bash
# Verify key is set
echo $CO_API_KEY

# Test directly
curl -H "Authorization: Bearer $CO_API_KEY" \
  https://api.cohere.com/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"command-r7b-12-2024","messages":[{"role":"user","content":"hi"}]}'
```

---

### 429 — Rate Limit Exceeded

```
CohereError: You are using a Trial key, which is limited to N calls/minute
```

**Rate limits by key type:**

| Key Type | Chat | Embed | Rerank | Other |
|----------|------|-------|--------|-------|
| Trial | 20/min | 5/min | 5/min | 1000/month |
| Production | 1000/min | 1000/min | 1000/min | Unlimited |

**Fix:**
```typescript
import { CohereError } from 'cohere-ai';

try {
  await cohere.chat({ model: 'command-a-03-2025', messages: [...] });
} catch (err) {
  if (err instanceof CohereError && err.statusCode === 429) {
    // Back off and retry
    await new Promise(r => setTimeout(r, 60_000)); // wait 60s for trial keys
    // retry...
  }
}
```

---

### 400 — Classify: Too Few Examples

```
CohereError: each unique label requires at least 2 examples
```

**Fix:**
```typescript
await cohere.classify({
  model: 'embed-english-v3.0',
  inputs: ['This product is amazing'],
  examples: [
    // Need at least 2 examples PER label
    { text: 'I love it', label: 'positive' },
    { text: 'Great product', label: 'positive' },
    { text: 'Terrible', label: 'negative' },
    { text: 'Worst ever', label: 'negative' },
  ],
});
```

---

### 400 — Rerank: Too Many Documents

```
CohereError: too many documents, max is 1000
```

**Fix:** Batch your documents:
```typescript
async function batchRerank(query: string, docs: string[], topN = 10) {
  const BATCH = 1000;
  let allResults: any[] = [];

  for (let i = 0; i < docs.length; i += BATCH) {
    const batch = docs.slice(i, i + BATCH);
    const resp = await cohere.rerank({
      model: 'rerank-v3.5',
      query,
      documents: batch,
      topN,
    });
    allResults.push(
      ...resp.results.map(r => ({ ...r, index: r.index + i }))
    );
  }

  return allResults.sort((a, b) => b.relevanceScore - a.relevanceScore).slice(0, topN);
}
```

---

### 400 — Chat: response_format with documents

```
CohereError: response_format is not supported with documents or tools
```

**Cause:** `response_format: { type: 'json_object' }` cannot be combined with `documents` or `tools`.

**Fix:** Use either JSON mode OR document/tool mode, not both. For structured RAG output, parse the text response yourself.

---

### 500/503 — Server Error

```
CohereError: internal server error
```

**Fix:** Retry with exponential backoff. If persistent, check [status.cohere.com](https://status.cohere.com).

---

### CohereTimeoutError

```
CohereTimeoutError: Request timed out
```

**Fix:** The SDK has a default timeout. Increase it or reduce payload:
```typescript
const cohere = new CohereClientV2({
  token: process.env.CO_API_KEY,
  timeoutInSeconds: 120, // default is lower
});
```

## Diagnostic Commands

```bash
# Check Cohere service status
curl -s https://status.cohere.com/api/v2/status.json | jq '.status'

# Verify API key works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $CO_API_KEY" \
  https://api.cohere.com/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"command-r7b-12-2024","messages":[{"role":"user","content":"ping"}]}'

# Check installed SDK version
npm list cohere-ai 2>/dev/null || pip show cohere 2>/dev/null
```

## Error Handling Wrapper

```typescript
import { CohereError, CohereTimeoutError } from 'cohere-ai';

function diagnoseCohereError(err: unknown): string {
  if (err instanceof CohereTimeoutError) {
    return 'TIMEOUT: Increase timeoutInSeconds or reduce input size';
  }
  if (err instanceof CohereError) {
    switch (err.statusCode) {
      case 400: return `BAD_REQUEST: ${err.message}`;
      case 401: return 'AUTH: Check CO_API_KEY';
      case 429: return 'RATE_LIMIT: Back off or upgrade key';
      case 500: return 'SERVER: Retry later, check status.cohere.com';
      default:  return `UNKNOWN (${err.statusCode}): ${err.message}`;
    }
  }
  return `UNEXPECTED: ${String(err)}`;
}
```

## Resources
- [Cohere Error Codes](https://docs.cohere.com/reference/errors)
- [Cohere Status Page](https://status.cohere.com)
- [Rate Limits](https://docs.cohere.com/docs/rate-limits)
- [API v1 to v2 Migration](https://docs.cohere.com/docs/migrating-v1-to-v2)

## Next Steps
For comprehensive debugging, see `cohere-debug-bundle`.
