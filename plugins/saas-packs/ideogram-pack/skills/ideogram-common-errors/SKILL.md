---
name: ideogram-common-errors
description: |
  Diagnose and fix Ideogram API errors and exceptions.
  Use when encountering Ideogram errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "ideogram error", "fix ideogram",
  "ideogram not working", "debug ideogram", "ideogram 422", "ideogram 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, debugging, errors]

---
# Ideogram Common Errors

## Overview
Quick reference for the most common Ideogram API errors, their root causes, and proven fixes. All Ideogram endpoints return standard HTTP status codes with JSON error bodies.

## Prerequisites
- Ideogram API key configured
- Access to request/response logs
- `curl` available for manual testing

## Error Reference

### 401 -- Authentication Failed
```
HTTP 401 Unauthorized
```
**Cause:** Missing, invalid, or revoked API key.

**Fix:**
```bash
set -euo pipefail
# Verify the key is set and not empty
echo "Key length: ${#IDEOGRAM_API_KEY}"

# Test auth directly
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"test","model":"V_2_TURBO"}}'
```

**Common mistakes:**
- Using `Authorization: Bearer` instead of `Api-Key` header
- Whitespace or newlines in the key string
- Key was regenerated in dashboard but not updated in `.env`

---

### 422 -- Safety Check Failed
```json
{"error": "Prompt or provided image failed the safety checks"}
```
**Cause:** Prompt text or uploaded image triggered Ideogram's content filter.

**Fix:**
- Remove brand names, celebrity names, or trademarked terms
- Avoid violent, sexual, or politically sensitive content
- Remove explicit references to real people
- Rephrase with neutral descriptors

```typescript
// Pre-screen prompts before sending to API
const FLAGGED_PATTERNS = [
  /\b(coca.?cola|nike|apple|disney)\b/i,
  /\b(celebrity|politician|president)\b/i,
];

function isPromptSafe(prompt: string): boolean {
  return !FLAGGED_PATTERNS.some(p => p.test(prompt));
}
```

---

### 429 -- Rate Limited
```
HTTP 429 Too Many Requests
```
**Cause:** More than 10 in-flight requests (default limit).

**Fix:**
```typescript
async function rateLimitedGenerate(prompt: string) {
  const maxRetries = 5;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await generateImage(prompt);
    } catch (err: any) {
      if (err.status !== 429) throw err;
      const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
      console.warn(`Rate limited. Retry in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Rate limit retries exhausted");
}
```

---

### 400 -- Bad Request
```json
{"error": "Invalid input"}
```
**Cause:** Invalid parameter values in request body.

**Common issues:**
| Parameter | Wrong | Correct |
|-----------|-------|---------|
| aspect_ratio | `"16:9"` | `"ASPECT_16_9"` (legacy) or `"16x9"` (V3) |
| style_type | `"realistic"` | `"REALISTIC"` (uppercase enum) |
| model | `"v2"` | `"V_2"` (underscore + uppercase) |
| num_images | `10` | `1`-`4` (max 4 per request) |
| resolution | Used with `aspect_ratio` | Use one or the other, not both |

---

### 402 -- Insufficient Credits
```
HTTP 402 Payment Required
```
**Cause:** API credit balance is depleted.

**Fix:**
1. Log into [ideogram.ai](https://ideogram.ai) > Settings > API Beta
2. Check current balance and top-up settings
3. Increase auto top-up amount or manually add credits
4. Default: auto top-up $20 when balance drops below $10

---

### Expired Image URL
```
HTTP 403 or 404 when downloading generated image
```
**Cause:** Ideogram image URLs are temporary (expire after ~1 hour).

**Fix:**
```typescript
// ALWAYS download immediately after generation
async function generateAndSave(prompt: string): Promise<string> {
  const result = await generateImage(prompt);
  const imageUrl = result.data[0].url;

  // Download within seconds, not later
  const response = await fetch(imageUrl);
  if (!response.ok) throw new Error(`Image download failed: ${response.status}`);

  const buffer = Buffer.from(await response.arrayBuffer());
  const path = `./images/gen-${result.data[0].seed}.png`;
  writeFileSync(path, buffer);
  return path;
}
```

---

### Mask Size Mismatch (Edit Endpoint)
```json
{"error": "Invalid input"}
```
**Cause:** Mask image dimensions do not match source image dimensions.

**Fix:**
```bash
set -euo pipefail
# Check dimensions match
identify source.png  # e.g., 1024x1024
identify mask.png    # Must also be 1024x1024

# Resize mask to match source
convert mask.png -resize 1024x1024! mask-resized.png
```

---

### Multipart Form Errors (V3 Endpoints)
**Cause:** V3 endpoints (`/v1/ideogram-v3/*`) require multipart form data, not JSON.

**Fix:**
```typescript
// WRONG for V3 endpoints:
fetch(url, { body: JSON.stringify({...}), headers: { "Content-Type": "application/json" } });

// CORRECT for V3 endpoints:
const form = new FormData();
form.append("prompt", "...");
form.append("aspect_ratio", "1x1");
fetch(url, { body: form, headers: { "Api-Key": key } });
// Do NOT set Content-Type -- FormData handles the boundary
```

## Quick Diagnostic Script
```bash
set -euo pipefail
echo "=== Ideogram Diagnostics ==="
echo "API Key set: ${IDEOGRAM_API_KEY:+YES}"
echo "Key length: ${#IDEOGRAM_API_KEY}"

# Test connectivity
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"test circle","model":"V_2_TURBO","magic_prompt_option":"OFF"}}')

echo "API Response: $STATUS"
case $STATUS in
  200) echo "OK: Auth and generation working" ;;
  401) echo "ERROR: Invalid API key" ;;
  402) echo "ERROR: Insufficient credits" ;;
  422) echo "ERROR: Safety filter (try different prompt)" ;;
  429) echo "ERROR: Rate limited (wait and retry)" ;;
  *)   echo "ERROR: Unexpected status $STATUS" ;;
esac
```

## Error Handling
| Error | HTTP | Root Cause | Fix |
|-------|------|-----------|-----|
| Auth failed | 401 | Bad `Api-Key` header | Verify key, check header name |
| Safety filter | 422 | Flagged prompt/image | Rephrase prompt |
| Rate limited | 429 | >10 in-flight requests | Exponential backoff |
| Bad params | 400 | Wrong enum values | Use exact enum strings |
| No credits | 402 | Balance depleted | Top up in dashboard |
| URL expired | 403/404 | Late download | Download immediately |

## Output
- Identified error root cause
- Applied fix with verification
- Diagnostic output confirming resolution

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [API Overview](https://developer.ideogram.ai/ideogram-api/api-overview)

## Next Steps
For comprehensive debugging, see `ideogram-debug-bundle`.
