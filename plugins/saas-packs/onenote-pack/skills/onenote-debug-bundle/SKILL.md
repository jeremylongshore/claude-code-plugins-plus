---
name: onenote-debug-bundle
description: 'Generate comprehensive diagnostic bundles for OneNote Graph API issues
  with request tracing and token analysis.

  Use when debugging OneNote API failures, filing Microsoft support tickets, or analyzing
  permission issues.

  Trigger with "onenote debug", "onenote diagnostic", "onenote support ticket", "graph
  api troubleshoot onenote".

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
# OneNote Debug Bundle

## Overview

When OneNote API calls fail, you need the `request-id` response header (Microsoft support requires it), decoded JWT token claims (to verify granted scopes), the `x-ms-ags-diagnostic` header (internal Graph routing info), and the full error body — all correlated to a single request. This skill generates structured diagnostic bundles for self-diagnosis and Microsoft support ticket filing.

## Prerequisites

- Node.js 18+ or Python 3.10+
- An existing OneNote integration with Graph API calls
- `@microsoft/microsoft-graph-client` or `msgraph-sdk` installed
- Access token available (for token inspection)

## Instructions

### TypeScript Diagnostic Middleware

Intercept all Graph API calls and capture diagnostics automatically:

```typescript
// src/debug/diagnostic-middleware.ts
interface DiagnosticEntry {
  timestamp: string; method: string; url: string; status: number;
  requestId: string | null; agsDiagnostic: string | null;
  retryAfter: string | null; duration_ms: number; error: any | null;
}

const diagnosticLog: DiagnosticEntry[] = [];

export function createDiagnosticMiddleware() {
  return {
    execute: async (context: any) => {
      const start = Date.now();
      const { url, method } = context.request || { url: "unknown", method: "GET" };
      try {
        await context.next();
        const h = context.response?.headers;
        diagnosticLog.push({
          timestamp: new Date().toISOString(), method, url,
          status: context.response?.status || 0,
          requestId: h?.get?.("request-id") || null,
          agsDiagnostic: h?.get?.("x-ms-ags-diagnostic") || null,
          retryAfter: h?.get?.("retry-after") || null,
          duration_ms: Date.now() - start, error: null,
        });
      } catch (err: any) {
        diagnosticLog.push({
          timestamp: new Date().toISOString(), method, url,
          status: err?.statusCode || 0,
          requestId: err?.headers?.["request-id"] || null,
          agsDiagnostic: err?.headers?.["x-ms-ags-diagnostic"] || null,
          retryAfter: err?.headers?.["retry-after"] || null,
          duration_ms: Date.now() - start,
          error: { code: err?.code, message: err?.message, body: err?.body },
        });
        throw err;
      }
    },
  };
}

export function getDiagnosticLog(): DiagnosticEntry[] { return [...diagnosticLog]; }
export function clearDiagnosticLog(): void { diagnosticLog.length = 0; }
```

### Token Claims Inspection (No External Libraries)

Decode a JWT access token to inspect scopes and expiry using only built-in Base64:

```typescript
// src/debug/token-inspector.ts
export function decodeTokenClaims(accessToken: string): Record<string, any> {
  const parts = accessToken.split(".");
  if (parts.length !== 3) throw new Error("Invalid JWT: expected 3 dot-separated parts");
  const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  return JSON.parse(Buffer.from(padded, "base64").toString("utf-8"));
}

export function analyzePermissions(claims: Record<string, any>, required: string[]) {
  const granted = claims.scp ? claims.scp.split(" ") : (claims.roles || []);
  const missing = required.filter((s) => !granted.includes(s));
  const now = Math.floor(Date.now() / 1000);
  const isExpired = claims.exp < now;
  const diff = Math.abs(claims.exp - now);
  const expiresIn = isExpired ? `Expired ${diff}s ago` : `${Math.floor(diff / 60)}m remaining`;
  return { granted, missing, isExpired, expiresIn };
}
```

### Python Diagnostic Context Manager

```python
# debug/diagnostic_capture.py
import json, base64, time
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class DiagnosticCapture:
    timestamp: str; method: str; url: str; status: int
    request_id: Optional[str]; ags_diagnostic: Optional[str]
    retry_after: Optional[str]; duration_ms: float
    error_code: Optional[str]; error_message: Optional[str]

class GraphDiagnostics:
    def __init__(self):
        self.captures: list[DiagnosticCapture] = []

    async def capture_request(self, client, method: str, endpoint: str, **kwargs):
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        start = time.monotonic()
        try:
            response = await client.api(endpoint).get() if method == "GET" \
                else await client.api(endpoint).post(kwargs.get("body"))
            self.captures.append(DiagnosticCapture(
                datetime.now(timezone.utc).isoformat(), method, url, 200,
                None, None, None, round((time.monotonic()-start)*1000, 2), None, None))
            return response
        except Exception as e:
            headers = getattr(e, "headers", {}) or {}
            self.captures.append(DiagnosticCapture(
                datetime.now(timezone.utc).isoformat(), method, url,
                int(getattr(e, "status_code", 0)),
                headers.get("request-id"), headers.get("x-ms-ags-diagnostic"),
                headers.get("retry-after"), round((time.monotonic()-start)*1000, 2),
                str(getattr(e, "code", type(e).__name__)), str(e)))
            raise

    def export_bundle(self, filepath: str, token: Optional[str] = None) -> str:
        bundle = {"bundle_version": "1.0", "generated": datetime.now(timezone.utc).isoformat(),
                  "captures": [asdict(c) for c in self.captures]}
        if token:
            parts = token.split(".")
            bundle["token_claims"] = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        with open(filepath, "w") as f:
            json.dump(bundle, f, indent=2)
        return filepath
```

### Microsoft Support Ticket Template

When filing a support case, include this from the diagnostic bundle:

```
Subject: OneNote Graph API - [Error Code] on [Endpoint]

1. Request ID: [from request-id response header]
2. Timestamp (UTC): [from diagnostic bundle]
3. Tenant ID: [from token claims tid]
4. App ID: [from token claims azp]
5. Endpoint: GET /me/onenote/notebooks
6. HTTP Status: 403
7. Error Code: ErrorAccessDenied
8. Error Message: Access is denied.
9. x-ms-ags-diagnostic: [full header value]
10. Token scopes granted: Notes.Read User.Read
11. Expected scopes: Notes.ReadWrite
12. SDK version: @microsoft/microsoft-graph-client@3.0.7
```

### Common Diagnostic Patterns

**"Why is my 403 happening?"** — Decode token, compare scopes:

```typescript
const claims = decodeTokenClaims(accessToken);
const { missing, isExpired, expiresIn } = analyzePermissions(claims, ["Notes.ReadWrite"]);
if (missing.length > 0) console.error(`Missing scopes: ${missing.join(", ")}`);
if (isExpired) console.error(`Token expired: ${expiresIn}`);
```

**"Which request failed in a batch?"** — Filter diagnostic log:

```typescript
const failures = getDiagnosticLog().filter((e) => e.status >= 400);
failures.forEach((f) => console.error(`[${f.requestId}] ${f.method} ${f.url} -> ${f.status}`));
```

## Output

- `src/debug/diagnostic-middleware.ts` — automatic Graph API call interception
- `src/debug/token-inspector.ts` — JWT decode and permission analysis (zero dependencies)
- `debug/diagnostic_capture.py` — Python diagnostic context manager with bundle export
- Diagnostic bundle JSON file with request-id, token claims, and error details
- Microsoft support ticket template with required fields

## Error Handling

| Debug Issue | Cause | Fix |
|------------|-------|-----|
| `request-id` is null | Response headers not captured | Use diagnostic middleware; direct `fetch` bypasses header capture |
| JWT decode fails | Token is opaque (v1) | Graph tokens should be v2 JWT; check `aud` matches `https://graph.microsoft.com` |
| `scp` claim empty | App-only token (no delegated scopes) | App-only auth deprecated March 2025; switch to delegated |
| `x-ms-ags-diagnostic` missing | Not all errors include it | Optional header; rely on `request-id` for support tickets |
| Wrong tenant in claims | Multi-tenant app resolving wrong | Verify `AZURE_TENANT_ID`; check `tid` claim |

## Examples

```typescript
// Generate diagnostic bundle after a failure
import { getDiagnosticLog } from "./debug/diagnostic-middleware";
import { decodeTokenClaims, analyzePermissions } from "./debug/token-inspector";
import { writeFileSync } from "fs";

const bundle = {
  bundle_version: "1.0", timestamp: new Date().toISOString(),
  log: getDiagnosticLog(),
  token: analyzePermissions(decodeTokenClaims(token), ["Notes.Read", "Notes.ReadWrite"]),
};
writeFileSync(`onenote-debug-${Date.now()}.json`, JSON.stringify(bundle, null, 2));
```

```bash
# Quick scope check from CLI
node -e "
  const t = process.env.GRAPH_TOKEN;
  const p = JSON.parse(Buffer.from(t.split('.')[1].replace(/-/g,'+').replace(/_/g,'/'), 'base64'));
  console.log('Scopes:', p.scp, '| Expires:', new Date(p.exp*1000).toISOString());
"
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Graph API Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)

## Next Steps

- Fix common errors with `onenote-common-errors`
- Tune performance after diagnosing bottlenecks with `onenote-performance-tuning`
- Check rate limit patterns with `onenote-rate-limits`
