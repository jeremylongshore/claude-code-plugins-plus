---
name: abridge-debug-bundle
description: |
  Collect Abridge debug evidence for support tickets and troubleshooting.
  Use when filing Abridge support tickets, collecting diagnostic data,
  or preparing evidence for escalation to Abridge engineering.
  Trigger: "abridge debug bundle", "abridge support ticket",
  "abridge diagnostics", "collect abridge evidence".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, debugging]
compatible-with: claude-code
---

# Abridge Debug Bundle

## Overview

Collect HIPAA-safe diagnostic data for Abridge support tickets. All PHI is automatically redacted before bundle creation.

## Prerequisites

- Abridge credentials configured
- Access to application logs
- Node.js or bash for running diagnostic scripts

## Instructions

### Step 1: Generate Debug Bundle

```typescript
// src/debug/abridge-debug-bundle.ts
import fs from 'fs';
import { execSync } from 'child_process';

interface DebugBundle {
  timestamp: string;
  environment: Record<string, string>;
  connectivity: Record<string, any>;
  recentErrors: any[];
  sessionDiagnostics: any[];
  fhirStatus: any;
}

async function generateDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: collectEnvironment(),
    connectivity: await testConnectivity(),
    recentErrors: await collectRecentErrors(),
    sessionDiagnostics: await collectSessionDiagnostics(),
    fhirStatus: await checkFhirStatus(),
  };

  // Redact PHI before saving
  const sanitized = redactPhi(JSON.stringify(bundle, null, 2));
  const filename = `abridge-debug-${Date.now()}.json`;
  fs.writeFileSync(filename, sanitized);
  console.log(`Debug bundle saved: ${filename}`);

  return bundle;
}

function collectEnvironment(): Record<string, string> {
  return {
    nodeVersion: process.version,
    platform: process.platform,
    abridgeBaseUrl: process.env.ABRIDGE_BASE_URL || 'NOT SET',
    orgId: process.env.ABRIDGE_ORG_ID ? 'SET (redacted)' : 'NOT SET',
    clientSecret: process.env.ABRIDGE_CLIENT_SECRET ? 'SET (redacted)' : 'NOT SET',
    fhirBaseUrl: process.env.EPIC_FHIR_BASE_URL || 'NOT SET',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  };
}

async function testConnectivity(): Promise<Record<string, any>> {
  const results: Record<string, any> = {};
  const endpoints = [
    { name: 'abridge_api', url: `${process.env.ABRIDGE_BASE_URL}/health` },
    { name: 'fhir_server', url: `${process.env.EPIC_FHIR_BASE_URL}/metadata` },
  ];

  for (const ep of endpoints) {
    try {
      const start = Date.now();
      const res = await fetch(ep.url, { signal: AbortSignal.timeout(5000) });
      results[ep.name] = { status: res.status, latency_ms: Date.now() - start };
    } catch (err) {
      results[ep.name] = { status: 'UNREACHABLE', error: (err as Error).message };
    }
  }
  return results;
}

function redactPhi(text: string): string {
  return text
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN-REDACTED]')
    .replace(/\b\d{10}\b/g, '[MRN-REDACTED]')
    .replace(/"(name|patient_name|given|family)":\s*"[^"]+"/g, '"$1": "[REDACTED]"')
    .replace(/\b\d{1,2}\/\d{1,2}\/\d{2,4}\b/g, '[DOB-REDACTED]');
}
```

### Step 2: Session-Level Diagnostics

```typescript
async function collectSessionDiagnostics(): Promise<any[]> {
  const api = AbridgeApiClient.getInstance().http;
  try {
    const { data } = await api.get('/encounters/sessions', {
      params: { status: 'error', limit: 10, order: 'desc' },
    });
    return data.sessions.map((s: any) => ({
      session_id: s.session_id,
      status: s.status,
      error_code: s.error_code,
      specialty: s.specialty,
      created_at: s.created_at,
      segment_count: s.segment_count,
      // No PHI fields included
    }));
  } catch {
    return [{ error: 'Could not fetch session diagnostics' }];
  }
}
```

### Step 3: Bash Quick Diagnostic

```bash
#!/bin/bash
# scripts/abridge-quick-diag.sh

echo "=== Abridge Quick Diagnostics $(date -Iseconds) ==="

echo -e "\n--- Environment ---"
echo "ABRIDGE_BASE_URL: ${ABRIDGE_BASE_URL:-NOT SET}"
echo "ABRIDGE_ORG_ID: ${ABRIDGE_ORG_ID:+SET (redacted)}"
echo "ABRIDGE_CLIENT_SECRET: ${ABRIDGE_CLIENT_SECRET:+SET (redacted)}"

echo -e "\n--- Connectivity ---"
echo -n "API Health: "
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" \
  -H "Authorization: Bearer $ABRIDGE_CLIENT_SECRET" \
  -H "X-Org-Id: $ABRIDGE_ORG_ID" \
  "$ABRIDGE_BASE_URL/health"

echo -e "\n\n--- TLS Info ---"
echo | openssl s_client -connect "$(echo $ABRIDGE_BASE_URL | sed 's|https://||'):443" 2>/dev/null \
  | openssl x509 -noout -subject -dates 2>/dev/null

echo -e "\n--- DNS Resolution ---"
dig +short "$(echo $ABRIDGE_BASE_URL | sed 's|https://||')" 2>/dev/null || echo "dig not available"

echo -e "\n=== Diagnostics Complete ==="
```

## Output

- `abridge-debug-{timestamp}.json` file with all PHI redacted
- Environment configuration status
- Connectivity test results with latency
- Recent error sessions (metadata only, no PHI)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Bundle contains PHI | Redaction regex missed a pattern | Add pattern to `redactPhi()` function |
| Cannot reach API | Network/firewall issue | Check DNS, TLS cert, firewall rules |
| Empty error list | No recent errors | Good sign — check if issue is client-side |

## Resources

- [Abridge Support](https://support.abridge.com)
- [HIPAA Minimum Necessary Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/minimum-necessary-requirement/)

## Next Steps

For rate limiting patterns, see `abridge-rate-limits`.
