---
name: canva-advanced-troubleshooting
description: |
  Apply Canva Connect API advanced debugging for hard-to-diagnose issues.
  Use when standard troubleshooting fails, investigating intermittent failures,
  or preparing evidence bundles for Canva developer support.
  Trigger with phrases like "canva hard bug", "canva mystery error",
  "canva impossible to debug", "difficult canva issue", "canva deep debug".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Advanced Troubleshooting

## Overview

Deep debugging for complex Canva Connect API issues — intermittent 5xx errors, stuck export jobs, OAuth token rotation failures, rate limit edge cases, and webhook delivery gaps.

## Systematic Layer Testing

```typescript
interface LayerTest {
  layer: string;
  test: () => Promise<{ pass: boolean; details: string; durationMs: number }>;
}

async function diagnoseCanvaIssue(token: string): Promise<void> {
  const layers: LayerTest[] = [
    {
      layer: 'DNS',
      test: async () => {
        const start = Date.now();
        try {
          const { address } = await import('dns/promises').then(dns => dns.lookup('api.canva.com'));
          return { pass: true, details: `Resolved to ${address}`, durationMs: Date.now() - start };
        } catch (e: any) {
          return { pass: false, details: e.message, durationMs: Date.now() - start };
        }
      },
    },
    {
      layer: 'TLS',
      test: async () => {
        const start = Date.now();
        try {
          const res = await fetch('https://api.canva.com/rest/v1/users/me', {
            method: 'HEAD',
            signal: AbortSignal.timeout(5000),
          });
          return { pass: true, details: `TLS OK, HTTP ${res.status}`, durationMs: Date.now() - start };
        } catch (e: any) {
          return { pass: false, details: e.message, durationMs: Date.now() - start };
        }
      },
    },
    {
      layer: 'Auth',
      test: async () => {
        const start = Date.now();
        const res = await fetch('https://api.canva.com/rest/v1/users/me', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        return {
          pass: res.status === 200,
          details: `HTTP ${res.status}${res.status === 401 ? ' — token expired' : ''}`,
          durationMs: Date.now() - start,
        };
      },
    },
    {
      layer: 'Scope: design:meta:read',
      test: async () => {
        const start = Date.now();
        const res = await fetch('https://api.canva.com/rest/v1/designs?limit=1', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        return {
          pass: res.status === 200,
          details: res.status === 403 ? 'Scope not granted' : `HTTP ${res.status}`,
          durationMs: Date.now() - start,
        };
      },
    },
    {
      layer: 'Scope: design:content:write',
      test: async () => {
        const start = Date.now();
        const res = await fetch('https://api.canva.com/rest/v1/designs', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ design_type: { type: 'custom', width: 100, height: 100 }, title: 'Diag Test' }),
        });
        return {
          pass: res.status === 200,
          details: res.status === 403 ? 'Scope not granted' : `HTTP ${res.status}`,
          durationMs: Date.now() - start,
        };
      },
    },
  ];

  console.log('=== Canva Connect API Layer Diagnostics ===\n');
  for (const { layer, test } of layers) {
    const result = await test();
    const icon = result.pass ? 'PASS' : 'FAIL';
    console.log(`[${icon}] ${layer}: ${result.details} (${result.durationMs}ms)`);
    if (!result.pass) {
      console.log(`  ^ First failure — layers below may fail due to this.\n`);
      break;
    }
  }
}
```

## Export Job Debugging

```typescript
// Debug stuck or failed export jobs
async function debugExportJob(exportId: string, token: string): Promise<void> {
  console.log(`\n=== Export Job Debug: ${exportId} ===`);

  const startTime = Date.now();
  let pollCount = 0;

  while (Date.now() - startTime < 120000) { // 2 min max
    pollCount++;
    const res = await fetch(`https://api.canva.com/rest/v1/exports/${exportId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    const data = await res.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    console.log(`[${elapsed}s] Poll #${pollCount}: status=${data.job.status}`);

    if (data.job.status === 'success') {
      console.log(`URLs (valid 24h): ${data.job.urls.length} files`);
      data.job.urls.forEach((url: string, i: number) => console.log(`  ${i + 1}. ${url.substring(0, 80)}...`));
      return;
    }

    if (data.job.status === 'failed') {
      console.error(`FAILED: ${data.job.error?.code} — ${data.job.error?.message}`);
      console.error('Common causes:');
      if (data.job.error?.code === 'license_required') {
        console.error('  -> Design contains premium elements. User needs Canva Pro.');
      } else if (data.job.error?.code === 'internal_failure') {
        console.error('  -> Canva server error. Retry after a delay.');
      }
      return;
    }

    await new Promise(r => setTimeout(r, 3000));
  }

  console.error('Export timed out after 2 minutes. Possible causes:');
  console.error('  - Very large or complex design');
  console.error('  - Canva export service under load');
  console.error('  - Video/animation exports take longer');
}
```

## Token Lifecycle Debugging

```typescript
async function debugTokenLifecycle(
  clientId: string,
  clientSecret: string,
  refreshToken: string
): Promise<void> {
  console.log('\n=== Token Lifecycle Debug ===');

  // 1. Try to refresh
  const basicAuth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  const res = await fetch('https://api.canva.com/rest/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${basicAuth}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
    }),
  });

  if (res.ok) {
    const data = await res.json();
    console.log(`[PASS] Token refresh successful`);
    console.log(`  Access token length: ${data.access_token.length} chars`);
    console.log(`  Expires in: ${data.expires_in} seconds (${(data.expires_in / 3600).toFixed(1)} hours)`);
    console.log(`  New refresh token: ${data.refresh_token ? 'YES (store this!)' : 'NO'}`);
  } else {
    const error = await res.json();
    console.log(`[FAIL] Token refresh failed: ${error.error}`);
    console.log(`  Description: ${error.error_description}`);
    console.log('');
    console.log('Common causes:');
    console.log('  - Refresh token already used (single-use)');
    console.log('  - User revoked access to your integration');
    console.log('  - Client credentials changed');
    console.log('  - Integration was deleted');
    console.log('');
    console.log('Resolution: User must re-authorize via OAuth flow');
  }
}
```

## Network-Level Debug

```bash
#!/bin/bash
# Capture low-level Canva API interaction

echo "=== Network Debug ==="

# DNS resolution time
echo -n "DNS: "
dig api.canva.com +short +time=5 | tail -1

# TCP + TLS timing
echo "Connection timing:"
curl -w "DNS: %{time_namelookup}s\nTCP: %{time_connect}s\nTLS: %{time_appconnect}s\nTotal: %{time_total}s\n" \
  -o /dev/null -s \
  -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
  "https://api.canva.com/rest/v1/users/me"

# HTTP/2 multiplexing check
echo -n "Protocol: "
curl -sI -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
  "https://api.canva.com/rest/v1/users/me" | grep -i "^http/"
```

## Support Escalation Template

```markdown
## Canva Developer Support Request

**Integration ID:** [from Canva dashboard]
**Severity:** P[1-4]
**Timestamp:** [ISO 8601 when issue first observed]

### Issue Summary
[1-2 sentence description]

### Steps to Reproduce
1. Call POST /v1/exports with design_id: DAVxxx
2. Poll GET /v1/exports/{jobId}
3. Job stays in_progress for > 5 minutes then returns internal_failure

### Expected vs Actual
- Expected: Export completes within 30s
- Actual: Fails with internal_failure after 5 minutes

### Evidence
- Layer diagnostics output (attached)
- Export job ID: EXPxxx
- Response body: { "job": { "status": "failed", "error": { ... } } }

### Environment
- Node.js 20.x
- Region: us-east-1
- Traffic: ~50 exports/hour
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Intermittent 5xx | Canva backend issue | Retry with backoff, file support ticket |
| Export stuck in_progress | Large design or server load | Increase timeout to 120s |
| Token refresh fails | Refresh token already used | Store new refresh token every time |
| Webhook not arriving | URL unreachable from Canva | Check HTTPS, firewall, ngrok |

## Resources

- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Canva Changelog](https://www.canva.dev/docs/connect/changelog/)
- [Canva Developer Community](https://community.canva.dev/)

## Next Steps

For load testing, see `canva-load-scale`.
