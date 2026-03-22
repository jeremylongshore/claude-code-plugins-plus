---
name: gamma-debug-bundle
description: |
  Comprehensive debugging toolkit for Gamma integration issues.
  Use when you need detailed diagnostics, request tracing,
  or systematic debugging of Gamma API problems.
  Trigger with phrases like "gamma debug bundle", "gamma diagnostics",
  "gamma trace", "gamma inspect", "gamma detailed logs".
allowed-tools: Read, Write, Edit, Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, api, debugging, tracing]

---
# Gamma Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

Debugging toolkit for Gamma API integration issues. Includes connectivity tests, request tracing, diagnostic scripts, and support ticket templates. Gamma uses a REST API at `https://public-api.gamma.app/v1.0/` with `X-API-KEY` header authentication.

## Prerequisites

- Active Gamma integration
- Node.js 18+ or Python 3.10+
- `curl` and `jq` available

## Instructions

### Step 1: Quick Connectivity Test (curl)

```bash
#!/bin/bash
set -euo pipefail
echo "=== Gamma API Diagnostic ==="

# 1. Check API key
if [ -z "${GAMMA_API_KEY:-}" ]; then
  echo "FAIL: GAMMA_API_KEY not set"; exit 1
fi
echo "OK: API key set (${#GAMMA_API_KEY} chars, prefix: ${GAMMA_API_KEY:0:4}...)"

# 2. Test authentication via /themes endpoint
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-KEY: $GAMMA_API_KEY" \
  "https://public-api.gamma.app/v1.0/themes")
if [ "$STATUS" = "200" ]; then
  echo "OK: Authentication successful"
elif [ "$STATUS" = "401" ]; then
  echo "FAIL: Invalid API key (401)"
elif [ "$STATUS" = "403" ]; then
  echo "FAIL: Account not on Pro+ plan (403)"
else
  echo "WARN: Unexpected status $STATUS"
fi

# 3. Check latency
echo "--- Latency (3 samples) ---"
for i in 1 2 3; do
  LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
    -H "X-API-KEY: $GAMMA_API_KEY" \
    "https://public-api.gamma.app/v1.0/themes")
  echo "  Request $i: ${LATENCY}s"
done

# 4. List themes (verify API access)
echo "--- Workspace Themes ---"
curl -s -H "X-API-KEY: $GAMMA_API_KEY" \
  "https://public-api.gamma.app/v1.0/themes" | jq '.[].name' 2>/dev/null || echo "Could not parse themes"
```

### Step 2: TypeScript Diagnostic Script

```typescript
// scripts/gamma-diagnose.ts
const BASE = "https://public-api.gamma.app/v1.0";
const headers = {
  "X-API-KEY": process.env.GAMMA_API_KEY!,
  "Content-Type": "application/json",
};

interface TestResult {
  test: string;
  status: "PASS" | "FAIL";
  detail: string;
  latencyMs?: number;
}

async function diagnose(): Promise<TestResult[]> {
  const results: TestResult[] = [];

  // Test 1: API key set
  if (!process.env.GAMMA_API_KEY) {
    results.push({ test: "API Key", status: "FAIL", detail: "GAMMA_API_KEY not set" });
    return results;
  }
  results.push({
    test: "API Key",
    status: "PASS",
    detail: `Set (${process.env.GAMMA_API_KEY.length} chars)`,
  });

  // Test 2: Authentication
  try {
    const start = Date.now();
    const res = await fetch(`${BASE}/themes`, { headers });
    const latency = Date.now() - start;
    if (res.ok) {
      const themes = await res.json();
      results.push({
        test: "Authentication",
        status: "PASS",
        detail: `OK, ${themes.length} themes available`,
        latencyMs: latency,
      });
    } else {
      results.push({
        test: "Authentication",
        status: "FAIL",
        detail: `HTTP ${res.status}: ${await res.text()}`,
      });
    }
  } catch (err: any) {
    results.push({ test: "Authentication", status: "FAIL", detail: err.message });
  }

  // Test 3: Folders endpoint
  try {
    const start = Date.now();
    const res = await fetch(`${BASE}/folders`, { headers });
    results.push({
      test: "Folders API",
      status: res.ok ? "PASS" : "FAIL",
      detail: res.ok ? `${(await res.json()).length} folders` : `HTTP ${res.status}`,
      latencyMs: Date.now() - start,
    });
  } catch (err: any) {
    results.push({ test: "Folders API", status: "FAIL", detail: err.message });
  }

  // Test 4: Generation (dry-run style — creates a minimal generation)
  try {
    const start = Date.now();
    const res = await fetch(`${BASE}/generations`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        content: "Diagnostic test: one card about testing",
        outputFormat: "presentation",
      }),
    });
    if (res.ok) {
      const { generationId } = await res.json();
      results.push({
        test: "Generation API",
        status: "PASS",
        detail: `Started: ${generationId}`,
        latencyMs: Date.now() - start,
      });
      // Note: this consumes credits — skip in automated tests
    } else {
      results.push({
        test: "Generation API",
        status: "FAIL",
        detail: `HTTP ${res.status}: ${await res.text()}`,
      });
    }
  } catch (err: any) {
    results.push({ test: "Generation API", status: "FAIL", detail: err.message });
  }

  // Print report
  console.log("\n=== Gamma Diagnostic Report ===");
  for (const r of results) {
    const latency = r.latencyMs ? ` (${r.latencyMs}ms)` : "";
    console.log(`  [${r.status}] ${r.test}: ${r.detail}${latency}`);
  }
  const failures = results.filter((r) => r.status === "FAIL").length;
  console.log(`\n${results.length} tests, ${failures} failures\n`);

  return results;
}

diagnose();
```

Run: `npx tsx scripts/gamma-diagnose.ts`

### Step 3: Debug Client with Request Logging

```typescript
// src/gamma/debug-client.ts
export function createDebugGammaClient(apiKey: string) {
  const base = "https://public-api.gamma.app/v1.0";
  const headers = { "X-API-KEY": apiKey, "Content-Type": "application/json" };

  async function debugRequest(method: string, path: string, body?: unknown) {
    const start = Date.now();
    const url = `${base}${path}`;
    console.log(`[GAMMA] ${method} ${path}`, body ? JSON.stringify(body).slice(0, 200) : "");

    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    const duration = Date.now() - start;
    const responseText = await res.text();
    const status = res.ok ? "OK" : "ERROR";

    console.log(`[GAMMA] ${status} ${res.status} in ${duration}ms`);
    if (!res.ok) {
      console.log(`[GAMMA] Response: ${responseText.slice(0, 500)}`);
    }

    if (!res.ok) throw new Error(`Gamma ${res.status}: ${responseText}`);
    return JSON.parse(responseText);
  }

  return {
    generate: (body: any) => debugRequest("POST", "/generations", body),
    poll: (id: string) => debugRequest("GET", `/generations/${id}`),
    listThemes: () => debugRequest("GET", "/themes"),
    listFolders: () => debugRequest("GET", "/folders"),
  };
}
```

### Step 4: Support Ticket Template

```markdown
## Environment
- Node.js: [version]
- OS: [os]
- API version: v1.0

## Issue Description
[What you expected vs what happened]

## API Request
- Endpoint: POST /v1.0/generations
- Status: [HTTP status]
- Response: [error body, sanitized]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]

## Diagnostic Output
[Paste output from gamma-diagnose.ts]

## Additional Context
- Account plan: [Pro/Ultra/Teams/Business]
- Credit balance: [approximate]
```

## Common Issues Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| 401 on all requests | Bad API key | Verify key at gamma.app/settings |
| 403 Forbidden | Not on Pro+ plan | Upgrade at gamma.app/pricing |
| 429 Too Many Requests | Rate limit | Add backoff; contact Gamma support for higher limits |
| Generation `status: "failed"` | Content too complex | Simplify content, reduce card count |
| Empty `exportUrl` | No `exportAs` in request | Add `exportAs: "pdf"` to generation |
| Timeout on poll | Very complex generation | Increase poll timeout beyond 3 min |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `GAMMA_API_KEY required` | Missing env var | Set `GAMMA_API_KEY` in `.env` |
| Diagnostic generation fails | No credits | Check credit balance at gamma.app |
| Network timeout | Connectivity issue | Check DNS resolution for `public-api.gamma.app` |

## Resources

- [Gamma Developer Docs](https://developers.gamma.app/)
- [Gamma Support](https://gamma.app/support)
- [API Changelog](https://developers.gamma.app/changelog)

## Next Steps

Proceed to `gamma-rate-limits` for rate limit management.
