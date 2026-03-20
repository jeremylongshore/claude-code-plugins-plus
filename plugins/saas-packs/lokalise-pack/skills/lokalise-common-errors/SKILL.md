---
name: lokalise-common-errors
description: |
  Diagnose and fix Lokalise common errors and exceptions.
  Use when encountering Lokalise errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "lokalise error", "fix lokalise",
  "lokalise not working", "debug lokalise", "lokalise 401", "lokalise 429".
allowed-tools: Read, Grep, Bash(curl:*), Bash(lokalise2:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Common Errors

## Overview

Every Lokalise API error returns a JSON body with a consistent structure. This skill covers the error response format, diagnosis of each HTTP status code (401, 400, 404, 429, 413, 500, 503), diagnostic curl commands for rapid troubleshooting, and a reusable error handling wrapper for the Node SDK.

## Prerequisites

- `curl` available for diagnostic commands
- `@lokalise/node-api` SDK installed for the error wrapper
- API token stored in `LOKALISE_API_TOKEN` environment variable
- `jq` installed for parsing JSON responses (optional but recommended)

## Instructions

### 1. Understand the Error Response Format

All Lokalise API errors return this structure:

```json
{
  "error": {
    "message": "Human-readable error description",
    "code": 401
  }
}
```

The `code` field mirrors the HTTP status code. The `message` field provides specifics. When using the Node SDK, errors are thrown as exceptions with `error.code`, `error.message`, and `error.headers` properties.

### 2. Diagnose by Status Code

#### 401 Unauthorized — Invalid or Missing API Token

```json
{"error": {"message": "Invalid `X-Api-Token` header", "code": 401}}
```

**Causes:**
- Token is incorrect, expired, or revoked
- `X-Api-Token` header missing from request
- Token copied with leading/trailing whitespace

**Fix:**

```bash
# Verify your token works
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/teams"

# Expected: 200
# If 401: regenerate token at https://app.lokalise.com/profile#apitokens
```

```bash
# Check for whitespace in token
echo -n "$LOKALISE_API_TOKEN" | xxd | head -2
# Look for 0a (newline) or 20 (space) at start/end
```

#### 400 Bad Request — Validation Errors

```json
{"error": {"message": "Invalid parameter `platform` - must be one of: ios, android, web, other", "code": 400}}
```

**Common 400 causes:**
- Invalid `project_id` format (must be `{number}.{alphanumeric}`)
- Missing required fields in POST/PUT body
- Invalid language ISO code
- Key name exceeding 256 characters
- Invalid platform value (must be `ios`, `android`, `web`, or `other`)

**Fix:**

```bash
# Validate project ID format
curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}" | jq '.project_id'

# List valid languages for a project
curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/languages" \
  | jq '.languages[].lang_iso'
```

#### 404 Not Found — Resource Does Not Exist

```json
{"error": {"message": "Project not found", "code": 404}}
```

**Causes:**
- Project ID is wrong or project was deleted
- Key, translation, or webhook ID does not exist
- Token lacks access to the specified project (appears as 404, not 403)

**Fix:**

```bash
# List all accessible projects to find the correct ID
curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects?limit=100" \
  | jq '.projects[] | {project_id, name}'

# Verify a specific key exists
curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/keys/${KEY_ID}" \
  | jq '.key_id // .error'
```

#### 429 Too Many Requests — Rate Limited

```json
{"error": {"message": "Too many requests", "code": 429}}
```

The response includes a `Retry-After` header indicating seconds to wait.

**Fix:** See `lokalise-rate-limits` skill for full implementation. Quick recovery:

```bash
# Check current rate limit status on any request
curl -s -D - -o /dev/null \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects" 2>&1 \
  | grep -i "x-ratelimit\|retry-after"

# Output:
# X-RateLimit-Limit: 6
# X-RateLimit-Remaining: 5
# X-RateLimit-Reset: 1700000001
```

#### 413 Payload Too Large — Request Body Exceeds Limit

```json
{"error": {"message": "Request entity too large", "code": 413}}
```

**Causes:**
- File upload exceeds 50 MB
- Bulk key creation with too many keys in one request (max 500)
- Translation value exceeds character limit

**Fix:**
- Split bulk operations into batches of 500 items
- Compress files before upload or split into smaller files
- For large translation values, check if the content truly belongs in a translation key

#### 500 Internal Server Error / 503 Service Unavailable

```json
{"error": {"message": "Internal server error", "code": 500}}
```

**These are Lokalise-side issues.** Do not retry immediately in a tight loop.

**Fix:**

```bash
# Check Lokalise status page
curl -s "https://status.lokalise.com/api/v2/status.json" | jq '.status'

# If status is operational, retry after 30 seconds
# If status shows incident, wait for resolution
```

Retry strategy for 500/503: wait 30 seconds, retry up to 3 times, then alert.

### 3. Run Diagnostic Commands

Quick health check script to diagnose the most common issues in sequence:

```bash
#!/bin/bash
# lokalise-diagnose.sh — Run against your environment
TOKEN="${LOKALISE_API_TOKEN}"
PROJECT="${LOKALISE_PROJECT_ID}"

echo "=== 1. Token validation ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Api-Token: $TOKEN" \
  "https://api.lokalise.com/api2/teams")
if [ "$STATUS" = "200" ]; then
  echo "Token: VALID"
else
  echo "Token: INVALID (HTTP $STATUS)"
  exit 1
fi

echo "=== 2. Project access ==="
curl -s -H "X-Api-Token: $TOKEN" \
  "https://api.lokalise.com/api2/projects/$PROJECT" \
  | jq '{project_id: .project_id, name: .name, team_id: .team_id}'

echo "=== 3. Rate limit status ==="
curl -s -D /dev/stderr -o /dev/null \
  -H "X-Api-Token: $TOKEN" \
  "https://api.lokalise.com/api2/projects" 2>&1 \
  | grep -i "x-ratelimit"

echo "=== 4. Key count ==="
curl -s -H "X-Api-Token: $TOKEN" \
  "https://api.lokalise.com/api2/projects/$PROJECT/keys?limit=1" \
  | jq '.project_id as $p | {project: $p, total_keys: .keys | length}'
```

### 4. Build a Reusable Error Handling Wrapper

Wrap all SDK calls with structured error handling:

```typescript
import { LokaliseApi } from "@lokalise/node-api";

interface LokaliseError {
  code: number;
  message: string;
  headers?: Record<string, string>;
}

function isLokaliseError(error: unknown): error is LokaliseError {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    "message" in error
  );
}

async function lokaliseCall<T>(
  fn: () => Promise<T>,
  context: string
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (!isLokaliseError(error)) throw error;

    switch (error.code) {
      case 401:
        throw new Error(
          `[${context}] Authentication failed. ` +
          `Regenerate token at https://app.lokalise.com/profile#apitokens`
        );
      case 400:
        throw new Error(
          `[${context}] Invalid request: ${error.message}. ` +
          `Check parameter values and required fields.`
        );
      case 404:
        throw new Error(
          `[${context}] Resource not found: ${error.message}. ` +
          `Verify the project/key/resource ID exists and token has access.`
        );
      case 429:
        console.warn(`[${context}] Rate limited. See lokalise-rate-limits.`);
        throw error; // Let the rate limit handler deal with retries
      case 413:
        throw new Error(
          `[${context}] Payload too large: ${error.message}. ` +
          `Split into smaller batches (max 500 items per request).`
        );
      case 500:
      case 503:
        throw new Error(
          `[${context}] Lokalise server error (${error.code}). ` +
          `Check https://status.lokalise.com — retry after 30s.`
        );
      default:
        throw new Error(
          `[${context}] Lokalise error ${error.code}: ${error.message}`
        );
    }
  }
}

// Usage
const lokalise = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

const keys = await lokaliseCall(
  () => lokalise.keys().list({ project_id: projectId, limit: 500 }),
  "listKeys"
);
```

## Output

- Identified error cause and specific fix for the HTTP status code encountered
- Diagnostic curl commands validated against live API
- Reusable error wrapper providing actionable messages per error type

## Error Handling

| Code | Error | Root Cause | Resolution |
|------|-------|-----------|------------|
| 401 | Invalid API Token | Token wrong, expired, or whitespace | Regenerate at Lokalise profile |
| 400 | Bad Request | Invalid params, missing fields | Check API docs for required fields |
| 404 | Not Found | Wrong ID or no access | List resources to find correct ID |
| 429 | Rate Limited | Exceeded 6 req/sec | Honor `Retry-After`, use queue |
| 413 | Payload Too Large | Body > 50 MB or > 500 items | Split into batches |
| 500 | Internal Server Error | Lokalise-side failure | Check status page, retry after 30s |
| 503 | Service Unavailable | Lokalise maintenance/outage | Check status page, wait |

## Examples

### Quick Token Check (One-Liner)

```bash
curl -s -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/teams" | jq '.teams[0].name // "INVALID TOKEN"'
```

### SDK Error Inspection

```typescript
try {
  await lokalise.keys().list({ project_id: "invalid" });
} catch (e: any) {
  console.log("Code:", e.code);       // 400
  console.log("Message:", e.message); // "Invalid project ID format"
  console.log("Headers:", e.headers); // rate limit headers
}
```

### CLI Diagnostics

```bash
# Verify CLI token
lokalise2 project list --token "$LOKALISE_API_TOKEN" --format json | jq '.[0].name'

# Test with verbose output
lokalise2 --debug file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$PROJECT_ID" \
  --format json \
  --dest ./locales/
```

## Resources

- [Lokalise API Error Codes](https://developers.lokalise.com/reference/api-errors)
- [Lokalise Status Page](https://status.lokalise.com)
- [Lokalise Community Forum](https://community.lokalise.com)
- [@lokalise/node-api Error Handling](https://github.com/lokalise/node-lokalise-api#error-handling)

## Next Steps

For building resilient integrations that handle errors automatically, see `lokalise-rate-limits`. For debugging translation data issues, see `lokalise-data-handling`.
