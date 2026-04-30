---
name: onenote-sdk-patterns
description: 'Production SDK patterns for OneNote Graph API: retry logic, batch requests,
  and safe file uploads.

  Use when building production OneNote integrations that need rate limit handling
  and reliable uploads.

  Trigger with "onenote sdk patterns", "onenote retry logic", "onenote batch requests".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote SDK Patterns

## Overview

Production-grade patterns for the OneNote Graph API. The two biggest production issues are rate limits (600 requests per 60 seconds per user, 10,000 per 10 minutes per tenant) and silent upload failures where files >4MB return 200 OK with an empty response body — the page is never created but no error is raised.

This skill provides middleware chains, retry decorators, batch request patterns, and silent failure detection for both TypeScript and Python.

## Prerequisites

- Completed `onenote-install-auth` — working Graph API authentication
- Understanding of async/await patterns in your target language
- Node.js 18+ or Python 3.10+

## Instructions

### Pattern 1: Retry Middleware with Retry-After Header Parsing (TypeScript)

The Graph API returns a `Retry-After` header (in seconds) with 429 responses. Hardcoding a fixed retry delay wastes time or hits limits again.

```typescript
import { Client, ClientOptions } from "@microsoft/microsoft-graph-client";

class RetryHandler {
  private maxRetries = 3;

  async execute(
    context: { request: Request; options: RequestInit },
    next: (context: any) => Promise<Response>
  ): Promise<Response> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await next(context);

        if (response.status === 429) {
          const retryAfter = response.headers.get("Retry-After");
          const waitSeconds = retryAfter ? parseInt(retryAfter, 10) : 30;
          console.warn(
            `Rate limited (429). Retry-After: ${waitSeconds}s. ` +
            `Attempt ${attempt + 1}/${this.maxRetries + 1}`
          );
          await new Promise((r) => setTimeout(r, waitSeconds * 1000));
          continue;
        }

        if (response.status === 502 || response.status === 503) {
          const backoff = Math.pow(2, attempt) * 1000;
          console.warn(
            `Server error (${response.status}). Backing off ${backoff}ms.`
          );
          await new Promise((r) => setTimeout(r, backoff));
          continue;
        }

        return response;
      } catch (err) {
        lastError = err as Error;
        if (attempt < this.maxRetries) {
          const backoff = Math.pow(2, attempt) * 1000;
          await new Promise((r) => setTimeout(r, backoff));
        }
      }
    }
    throw lastError ?? new Error("Max retries exceeded");
  }
}
```

### Pattern 2: Retry Decorator (Python)

```python
import asyncio
import functools
from typing import TypeVar, Callable, Any

T = TypeVar("T")

def retry_graph(max_retries: int = 3):
    """Decorator for Graph API calls with rate limit awareness."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_code = getattr(e, "status_code", None) or getattr(e, "code", 0)

                    if error_code == 429:
                        # Parse Retry-After from response headers
                        retry_after = getattr(e, "retry_after", 30)
                        print(f"Rate limited. Waiting {retry_after}s "
                              f"(attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(retry_after)
                    elif error_code in (502, 503, 504):
                        backoff = (2 ** attempt) * 1.0
                        print(f"Server error {error_code}. Backoff {backoff}s.")
                        await asyncio.sleep(backoff)
                    else:
                        raise  # Non-retryable error
            raise last_exception
        return wrapper
    return decorator

# Usage:
@retry_graph(max_retries=3)
async def list_notebooks(client):
    return await client.me.onenote.notebooks.get()
```

### Pattern 3: Rate Limit Tracker

Track request counts locally to proactively avoid 429 responses instead of reacting to them.

```typescript
class RateLimitTracker {
  private userRequests: { timestamp: number }[] = [];
  private tenantRequests: { timestamp: number }[] = [];

  // Graph limits for OneNote
  private readonly USER_LIMIT = 600;     // per 60 seconds
  private readonly USER_WINDOW = 60_000; // 60 seconds in ms
  private readonly TENANT_LIMIT = 10_000; // per 10 minutes
  private readonly TENANT_WINDOW = 600_000; // 10 minutes in ms

  canMakeRequest(): { allowed: boolean; waitMs: number } {
    const now = Date.now();

    // Prune expired entries
    this.userRequests = this.userRequests.filter(
      (r) => now - r.timestamp < this.USER_WINDOW
    );
    this.tenantRequests = this.tenantRequests.filter(
      (r) => now - r.timestamp < this.TENANT_WINDOW
    );

    if (this.userRequests.length >= this.USER_LIMIT) {
      const oldest = this.userRequests[0].timestamp;
      return { allowed: false, waitMs: this.USER_WINDOW - (now - oldest) };
    }

    if (this.tenantRequests.length >= this.TENANT_LIMIT) {
      const oldest = this.tenantRequests[0].timestamp;
      return { allowed: false, waitMs: this.TENANT_WINDOW - (now - oldest) };
    }

    return { allowed: true, waitMs: 0 };
  }

  recordRequest(): void {
    const now = Date.now();
    this.userRequests.push({ timestamp: now });
    this.tenantRequests.push({ timestamp: now });
  }
}

// Usage in middleware:
const tracker = new RateLimitTracker();

async function rateLimitedRequest<T>(fn: () => Promise<T>): Promise<T> {
  const check = tracker.canMakeRequest();
  if (!check.allowed) {
    console.warn(`Proactive rate limit pause: ${check.waitMs}ms`);
    await new Promise((r) => setTimeout(r, check.waitMs));
  }
  tracker.recordRequest();
  return fn();
}
```

### Pattern 4: Batch Requests ($batch Endpoint)

Reduce round trips by batching up to 20 Graph requests into a single HTTP call.

```typescript
// Batch request to fetch multiple pages in parallel
const batchBody = {
  requests: [
    { id: "1", method: "GET", url: `/me/onenote/pages/${pageId1}` },
    { id: "2", method: "GET", url: `/me/onenote/pages/${pageId2}` },
    { id: "3", method: "GET", url: `/me/onenote/pages/${pageId3}` },
  ],
};

const batchResponse = await client
  .api("/$batch")
  .post(batchBody);

// Each response has its own status code — some may fail while others succeed
for (const resp of batchResponse.responses) {
  if (resp.status === 200) {
    console.log(`Page ${resp.id}: ${resp.body.title}`);
  } else {
    console.error(`Page ${resp.id} failed: ${resp.status} — ${resp.body?.error?.message}`);
  }
}
```

**Batch limits:** Maximum 20 requests per batch. Requests within a batch count individually toward rate limits. Use `dependsOn` for sequential ordering within a batch.

### Pattern 5: Safe File Upload with Silent Failure Detection

Files larger than 4MB return 200 OK with an empty response body. The page is never created. You must check the response body after every upload.

```typescript
const MAX_UPLOAD_SIZE = 4 * 1024 * 1024; // 4MB

async function safeCreatePage(
  client: Client,
  sectionId: string,
  htmlContent: string,
  attachments?: { name: string; contentType: string; data: Buffer }[]
): Promise<{ success: boolean; pageId?: string; error?: string }> {
  // Calculate total payload size
  const htmlSize = Buffer.byteLength(htmlContent, "utf-8");
  const attachmentSize = attachments?.reduce((sum, a) => sum + a.data.length, 0) ?? 0;
  const totalSize = htmlSize + attachmentSize;

  if (totalSize > MAX_UPLOAD_SIZE) {
    return {
      success: false,
      error: `Payload ${(totalSize / 1024 / 1024).toFixed(1)}MB exceeds 4MB limit. ` +
        `Split content or upload images as URLs instead of inline data.`,
    };
  }

  const response = await client
    .api(`/me/onenote/sections/${sectionId}/pages`)
    .header("Content-Type", "text/html")
    .post(htmlContent);

  // CRITICAL: Check for silent failure — 200 with empty body
  if (!response || !response.id) {
    return {
      success: false,
      error: "Silent upload failure: API returned 200 but response body is empty. " +
        "This typically means the content was too large or contained invalid binary data.",
    };
  }

  return { success: true, pageId: response.id };
}
```

### Pattern 6: Token Refresh Middleware

```typescript
import { DeviceCodeCredential } from "@azure/identity";

class TokenRefreshMiddleware {
  private credential: DeviceCodeCredential;
  private cachedToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor(credential: DeviceCodeCredential) {
    this.credential = credential;
  }

  async getValidToken(scopes: string[]): Promise<string> {
    const now = Date.now();
    // Refresh 5 minutes before expiry to avoid mid-request failures
    const REFRESH_BUFFER = 5 * 60 * 1000;

    if (this.cachedToken && this.tokenExpiry > now + REFRESH_BUFFER) {
      return this.cachedToken;
    }

    const tokenResponse = await this.credential.getToken(scopes);
    if (!tokenResponse) {
      throw new Error("Failed to acquire token — user may need to re-authenticate");
    }

    this.cachedToken = tokenResponse.token;
    this.tokenExpiry = tokenResponse.expiresOnTimestamp;
    return this.cachedToken;
  }
}
```

### Pattern 7: Structured Error Extraction

```typescript
interface GraphError {
  statusCode: number;
  code: string;
  message: string;
  requestId: string;
  diagnostics: string;
  retryable: boolean;
}

function extractGraphError(error: any): GraphError {
  const statusCode = error.statusCode ?? error.code ?? 0;
  const body = error.body ? JSON.parse(error.body) : error;
  const innerError = body?.error ?? {};

  return {
    statusCode,
    code: innerError.code ?? "Unknown",
    message: innerError.message ?? error.message ?? "No message",
    requestId: error.headers?.get?.("request-id") ?? "unavailable",
    diagnostics: error.headers?.get?.("x-ms-ags-diagnostic") ?? "",
    retryable: [429, 502, 503, 504].includes(statusCode),
  };
}
```

## Output

After applying these patterns you will have:
- Automatic retry with Retry-After header parsing (not hardcoded delays)
- Proactive rate limit tracking that pauses before hitting limits
- Batch requests reducing API round trips by up to 20x
- Silent upload failure detection that catches the 200-with-empty-body trap
- Token refresh middleware that renews tokens before expiry
- Structured error extraction for consistent logging and alerting

## Error Handling

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| 429 rate limit | HTTP status code | Parse `Retry-After` header, wait exact seconds |
| Silent upload failure | 200 status but `response.id` is undefined | Log error, check payload size, retry with smaller content |
| Token expired mid-batch | 401 on individual batch response | Refresh token, retry failed batch items only |
| Tenant quota exceeded | 429 with long Retry-After (>60s) | Switch to batch requests, reduce concurrency |
| 502 Bad Gateway | HTTP status code | Exponential backoff, max 3 retries |

## Examples

**Complete production client setup:**
```typescript
const tracker = new RateLimitTracker();
const tokenMiddleware = new TokenRefreshMiddleware(credential);

async function graphRequest<T>(fn: () => Promise<T>): Promise<T> {
  const check = tracker.canMakeRequest();
  if (!check.allowed) {
    await new Promise((r) => setTimeout(r, check.waitMs));
  }
  tracker.recordRequest();

  try {
    return await fn();
  } catch (error) {
    const parsed = extractGraphError(error);
    if (parsed.retryable) {
      console.warn(`Retryable error: ${parsed.code} — ${parsed.message}`);
      // RetryHandler will handle the actual retry
    }
    throw error;
  }
}
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [OneNote Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Graph API Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [OneNote Get Content](https://learn.microsoft.com/en-us/graph/onenote-get-content)

## Next Steps

- See `onenote-common-errors` for a complete error decoder covering every status code
- Use `onenote-local-dev-loop` to test these patterns without hitting live rate limits
- See `onenote-hello-world` if you need to verify basic connectivity first
