---
name: documenso-debug-bundle
description: |
  Comprehensive debugging toolkit for Documenso integrations.
  Use when troubleshooting complex issues, gathering diagnostic information,
  or creating support tickets for Documenso problems.
  Trigger with phrases like "debug documenso", "documenso diagnostics",
  "troubleshoot documenso", "documenso support ticket".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, debugging]

---
# Documenso Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

Comprehensive debugging tools for Documenso integration issues. Includes diagnostic scripts, curl debug commands, environment verification, and support ticket templates.

## Prerequisites

- Documenso SDK installed
- Access to logs and configuration
- `curl` and `jq` available

## Instructions

### Step 1: Quick Connectivity Test

```bash
#!/bin/bash
set -euo pipefail

echo "=== Documenso Connectivity Test ==="

# 1. Check API key is set
if [ -z "${DOCUMENSO_API_KEY:-}" ]; then
  echo "FAIL: DOCUMENSO_API_KEY not set"
  exit 1
fi
echo "OK: API key set (${#DOCUMENSO_API_KEY} chars)"

# 2. Test authentication
BASE="${DOCUMENSO_BASE_URL:-https://app.documenso.com/api/v1}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  "$BASE/documents?page=1&perPage=1")

if [ "$STATUS" = "200" ]; then
  echo "OK: API authentication successful"
elif [ "$STATUS" = "401" ]; then
  echo "FAIL: Invalid API key (401)"
  exit 1
elif [ "$STATUS" = "403" ]; then
  echo "FAIL: Insufficient permissions (403) — try a team API key"
  exit 1
else
  echo "WARN: Unexpected status $STATUS"
fi

# 3. Check latency
LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  "$BASE/documents?page=1&perPage=1")
echo "Latency: ${LATENCY}s"

# 4. List recent documents
echo "=== Recent Documents ==="
curl -s -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  "$BASE/documents?page=1&perPage=5" | jq '.documents[] | {id, title, status, createdAt}'
```

### Step 2: TypeScript Diagnostic Script

```typescript
// scripts/documenso-diagnose.ts
import { Documenso } from "@documenso/sdk-typescript";

async function diagnose() {
  const results: Array<{ test: string; status: "PASS" | "FAIL"; detail: string }> = [];

  // Test 1: API key
  const apiKey = process.env.DOCUMENSO_API_KEY;
  if (!apiKey) {
    results.push({ test: "API Key", status: "FAIL", detail: "DOCUMENSO_API_KEY not set" });
    return results;
  }
  results.push({ test: "API Key", status: "PASS", detail: `Set (${apiKey.length} chars)` });

  // Test 2: Connection
  const client = new Documenso({
    apiKey,
    ...(process.env.DOCUMENSO_BASE_URL && { serverURL: process.env.DOCUMENSO_BASE_URL }),
  });

  try {
    const start = Date.now();
    const { documents } = await client.documents.findV0({ page: 1, perPage: 1 });
    const latency = Date.now() - start;
    results.push({
      test: "Connection",
      status: "PASS",
      detail: `${latency}ms, ${documents.length} documents returned`,
    });
  } catch (err: any) {
    results.push({
      test: "Connection",
      status: "FAIL",
      detail: `${err.statusCode ?? "unknown"}: ${err.message}`,
    });
  }

  // Test 3: Create + Delete (write access)
  try {
    const doc = await client.documents.createV0({ title: "[DIAG] Test Document" });
    await client.documents.deleteV0(doc.documentId);
    results.push({ test: "Write Access", status: "PASS", detail: "Create+delete OK" });
  } catch (err: any) {
    results.push({
      test: "Write Access",
      status: "FAIL",
      detail: err.message,
    });
  }

  // Print report
  console.log("\n=== Documenso Diagnostic Report ===");
  for (const r of results) {
    console.log(`  [${r.status}] ${r.test}: ${r.detail}`);
  }
  const failures = results.filter((r) => r.status === "FAIL").length;
  console.log(`\n${results.length} tests, ${failures} failures\n`);

  return results;
}

diagnose();
```

Run: `npx tsx scripts/documenso-diagnose.ts`

### Step 3: Debug Logging Wrapper

```typescript
// src/documenso/debug-client.ts
import { Documenso } from "@documenso/sdk-typescript";

export function createDebugClient(): Documenso {
  const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });

  // Proxy to log all method calls
  return new Proxy(client, {
    get(target, prop) {
      const value = (target as any)[prop];
      if (typeof value === "object" && value !== null) {
        return new Proxy(value, {
          get(innerTarget, innerProp) {
            const method = (innerTarget as any)[innerProp];
            if (typeof method === "function") {
              return async (...args: any[]) => {
                const start = Date.now();
                console.log(`[DOCUMENSO] ${String(prop)}.${String(innerProp)}(`, JSON.stringify(args).slice(0, 200), ")");
                try {
                  const result = await method.apply(innerTarget, args);
                  console.log(`[DOCUMENSO] OK in ${Date.now() - start}ms`);
                  return result;
                } catch (err: any) {
                  console.error(`[DOCUMENSO] FAIL in ${Date.now() - start}ms: ${err.statusCode} ${err.message}`);
                  throw err;
                }
              };
            }
            return method;
          },
        });
      }
      return value;
    },
  });
}
```

### Step 4: Support Ticket Template

When filing an issue on [GitHub](https://github.com/documenso/documenso/issues) or [Discord](https://documenso.com/discord):

```markdown
## Environment
- Documenso: Cloud / Self-hosted v[version]
- SDK: @documenso/sdk-typescript v[version]
- Node.js: [version]
- OS: [os]

## Issue Description
[What you expected vs what happened]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]

## API Request (sanitized)
- Method: POST /api/v2/documents
- Status: [HTTP status]
- Response: [error body, no secrets]

## Diagnostic Output
[Paste output from documenso-diagnose.ts]

## Logs
[Relevant log lines, sanitized]
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Diagnostic timeout | Slow API or network | Check connectivity, increase timeout |
| Write test fails | Read-only key or no team access | Use team API key with write permissions |
| Self-hosted unreachable | Docker container down | `docker ps`, check container logs |
| Latency > 5s | Network or infrastructure issue | Check if self-hosted DB is overloaded |

## Resources

- [Documenso GitHub Issues](https://github.com/documenso/documenso/issues)
- [Documenso Discord](https://documenso.com/discord)
- [Status Page](https://status.documenso.com)
- [API Reference](https://openapi.documenso.com/)

## Next Steps

For rate limit handling, see `documenso-rate-limits`.
