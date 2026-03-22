---
name: clickup-common-errors
description: |
  Diagnose and fix ClickUp API v2 errors by HTTP status and error code.
  Use when encountering ClickUp API errors, debugging failed requests,
  or troubleshooting OAUTH_* error codes, 401s, 429s, and 500s.
  Trigger: "clickup error", "fix clickup", "clickup not working",
  "clickup 401", "clickup 429", "OAUTH error", "debug clickup API".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Common Errors

## Overview

Reference for ClickUp API v2 errors. All errors return JSON with `err` (message) and optionally `ECODE` (error code).

## Error Response Format

```json
{
  "err": "Space not found",
  "ECODE": "ITEM_015"
}
```

## HTTP Status Errors

### 400 Bad Request

| Situation | Response | Fix |
|-----------|----------|-----|
| Missing required field | `{"err": "Task name required"}` | Include `name` in request body |
| Invalid field value | `{"err": "Invalid priority"}` | Priority must be 1-4 or null |
| Malformed JSON | `{"err": "Unexpected token"}` | Validate JSON before sending |
| Invalid custom field value | `{"err": "Invalid value for field"}` | Match value to field type |

### 401 Unauthorized — OAuth Errors

| ECODE | Cause | Solution |
|-------|-------|----------|
| OAUTH_017 | Token malformed or missing | Include `Authorization: <token>` header |
| OAUTH_023 | Workspace not authorized for token | User must re-authorize workspace in OAuth flow |
| OAUTH_026 | Token revoked by user | Generate new personal token or re-authenticate |
| OAUTH_027 | Workspace not authorized | Re-authorize via OAuth, ensuring workspace scope |
| OAUTH_029-045 | Various workspace auth failures | Re-run OAuth flow for the specific workspace |

```bash
# Diagnose: verify your token works
curl -s -w "\nHTTP %{http_code}\n" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN"
```

### 403 Forbidden

| Situation | Fix |
|-----------|-----|
| No access to space/folder/list | Verify user has access to that part of the hierarchy |
| Insufficient role permissions | Need admin role for destructive operations |
| Guest access limitation | Guests have restricted API access |

### 404 Not Found

```bash
# Common causes: wrong ID, deleted resource, wrong hierarchy level
# Verify the resource exists:
curl -s https://api.clickup.com/api/v2/task/TASK_ID \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.id, .name'
```

### 429 Rate Limited

Rate limits vary by plan (per token, per minute):
- **Free/Unlimited/Business**: 100 req/min
- **Business Plus**: 1,000 req/min
- **Enterprise**: 10,000 req/min

```bash
# Check rate limit headers on any response
curl -s -D - https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1 | grep -i ratelimit

# Headers returned:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1695000060  (Unix timestamp)
```

### 500/503 Server Errors

Check [ClickUp Status Page](https://status.clickup.com) first.

```bash
# Quick status check
curl -s https://status.clickup.com/api/v2/summary.json | \
  jq '.status.description'
```

## Diagnostic Script

```bash
#!/bin/bash
echo "=== ClickUp API Diagnostics ==="

# 1. Auth check
echo -n "Auth: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN")
[ "$HTTP_CODE" = "200" ] && echo "OK" || echo "FAILED ($HTTP_CODE)"

# 2. Rate limit check
echo -n "Rate limit remaining: "
curl -s -D - https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1 | \
  grep "X-RateLimit-Remaining" | awk '{print $2}'

# 3. Workspace access
echo "Workspaces:"
curl -s https://api.clickup.com/api/v2/team \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq -r '.teams[] | "  \(.id): \(.name)"'
```

## Error Handler Pattern

```typescript
async function handleClickUpError(response: Response): Promise<never> {
  const body = await response.json().catch(() => ({ err: 'Unknown' }));

  switch (response.status) {
    case 401:
      throw new Error(`Auth failed (${body.ECODE}): Re-check token or re-authorize`);
    case 429: {
      const resetAt = response.headers.get('X-RateLimit-Reset');
      const waitMs = resetAt ? (parseInt(resetAt) * 1000 - Date.now()) : 60000;
      throw new Error(`Rate limited. Retry after ${Math.ceil(waitMs / 1000)}s`);
    }
    case 404:
      throw new Error(`Resource not found: ${body.err}`);
    default:
      throw new Error(`ClickUp API ${response.status}: ${body.err}`);
  }
}
```

## Resources

- [ClickUp Common Errors](https://developer.clickup.com/docs/common_errors)
- [ClickUp API Error Handling](https://clickup.com/api/developer-portal/general-errorhandling/)
- [ClickUp Status Page](https://status.clickup.com)

## Next Steps

For comprehensive debugging, see `clickup-debug-bundle`.
