---
name: openevidence-debug-bundle
description: |
  Generate comprehensive debug information for OpenEvidence integration issues.
  Use when troubleshooting complex problems, preparing support tickets,
  or conducting post-incident analysis.
  Trigger with phrases like "openevidence debug", "openevidence troubleshoot",
  "openevidence support bundle", "diagnose openevidence".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Generate comprehensive diagnostic information for troubleshooting OpenEvidence integration issues without exposing PHI.

## Prerequisites
- OpenEvidence SDK installed
- Access to application logs
- Command-line access
- curl installed

## Instructions

### Step 1: Environment Check Script
```bash
#!/bin/bash
set -euo pipefail
# scripts/openevidence-debug.sh

echo "=== OpenEvidence Debug Bundle ==="
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# 1. Environment Variables (masked)
echo "=== Environment Configuration ==="
echo "OPENEVIDENCE_API_KEY: ${OPENEVIDENCE_API_KEY:+[SET - ${#OPENEVIDENCE_API_KEY} chars]}"
echo "OPENEVIDENCE_ORG_ID: ${OPENEVIDENCE_ORG_ID:+[SET - ${#OPENEVIDENCE_ORG_ID} chars]}"
echo "OPENEVIDENCE_BASE_URL: ${OPENEVIDENCE_BASE_URL:-https://api.openevidence.com}"
echo "OPENEVIDENCE_TIMEOUT: ${OPENEVIDENCE_TIMEOUT:-30000}ms"  # 30000: 30 seconds in ms
echo "NODE_ENV: ${NODE_ENV:-not set}"
echo ""

# 2. SDK Version
echo "=== SDK Version ==="
npm list @openevidence/sdk 2>/dev/null || pip show openevidence 2>/dev/null || echo "SDK not found"
echo ""

# 3. Node/Python Version
echo "=== Runtime Version ==="
node --version 2>/dev/null || echo "Node.js not found"
python3 --version 2>/dev/null || echo "Python not found"
echo ""

# 4. Connectivity Test
echo "=== Connectivity Test ==="
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  "${OPENEVIDENCE_BASE_URL:-https://api.openevidence.com}/health" 2>/dev/null)
echo "Health endpoint: HTTP ${HEALTH_STATUS}"

DNS_CHECK=$(dig +short api.openevidence.com 2>/dev/null || echo "DNS lookup failed")
echo "DNS resolution: ${DNS_CHECK}"
echo ""

# 5. TLS Check
echo "=== TLS Configuration ==="
openssl s_client -connect api.openevidence.com:443 -brief 2>/dev/null | head -5 || echo "TLS check failed"  # 443: HTTPS port
echo ""

# 6. Rate Limit Status
echo "=== Rate Limit Status ==="
curl -s -D - \
  -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  "${OPENEVIDENCE_BASE_URL:-https://api.openevidence.com}/v1/rate-limit" 2>/dev/null \
  | grep -i "x-ratelimit" || echo "Could not retrieve rate limit headers"
echo ""

echo "=== Debug Bundle Complete ==="
```

### Step 2: Programmatic Debug Collection
```typescript
// src/debug/debug-bundle.ts
import { OpenEvidenceClient } from '@openevidence/sdk';
import { execSync } from 'child_process';

interface DebugBundle {
  timestamp: string;
  environment: EnvironmentInfo;
  connectivity: ConnectivityInfo;
  sdkInfo: SDKInfo;
  recentErrors: ErrorSummary[];
  metrics: MetricsSummary;
}

interface EnvironmentInfo {
  nodeVersion: string;
  sdkVersion: string;
  apiKeySet: boolean;
  apiKeyLength: number;
  orgIdSet: boolean;
  baseUrl: string;
  timeout: number;
}

interface ConnectivityInfo {
  healthStatus: number | null;
  latencyMs: number | null;
  dnsResolution: boolean;
  tlsVersion: string | null;
}

interface SDKInfo {
  version: string;
  features: string[];
}

interface ErrorSummary {
  code: string;
  count: number;
  lastOccurred: string;
}

interface MetricsSummary {
  totalRequests: number;
  successRate: number;
  avgLatencyMs: number;
  p99LatencyMs: number;
}

export async function generateDebugBundle(): Promise<DebugBundle> {
  const timestamp = new Date().toISOString();

  // Gather environment info
  const environment = gatherEnvironmentInfo();

  // Test connectivity
  const connectivity = await testConnectivity();

  // Get SDK info
  const sdkInfo = getSDKInfo();

  // Summarize recent errors (from in-memory store or logs)
  const recentErrors = await summarizeRecentErrors();

  // Gather metrics
  const metrics = await gatherMetrics();

  return {
    timestamp,
    environment,
    connectivity,
    sdkInfo,
    recentErrors,
    metrics,
  };
}

function gatherEnvironmentInfo(): EnvironmentInfo {
  return {
    nodeVersion: process.version,
    sdkVersion: getPackageVersion('@openevidence/sdk'),
    apiKeySet: !!process.env.OPENEVIDENCE_API_KEY,
    apiKeyLength: process.env.OPENEVIDENCE_API_KEY?.length || 0,
    orgIdSet: !!process.env.OPENEVIDENCE_ORG_ID,
    baseUrl: process.env.OPENEVIDENCE_BASE_URL || 'https://api.openevidence.com',
    timeout: parseInt(process.env.OPENEVIDENCE_TIMEOUT || '30000'),  # 30000: 30 seconds in ms
  };
}

async function testConnectivity(): Promise<ConnectivityInfo> {
  const baseUrl = process.env.OPENEVIDENCE_BASE_URL || 'https://api.openevidence.com';
  const startTime = Date.now();

  try {
    const response = await fetch(`${baseUrl}/health`, {
      headers: { Authorization: `Bearer ${process.env.OPENEVIDENCE_API_KEY}` },
    });

    return {
      healthStatus: response.status,
      latencyMs: Date.now() - startTime,
      dnsResolution: true,
      tlsVersion: 'TLS 1.2+', // Inferred from successful HTTPS
    };
  } catch (error: any) {
    return {
      healthStatus: null,
      latencyMs: null,
      dnsResolution: error.code !== 'ENOTFOUND',
      tlsVersion: null,
    };
  }
}

function getSDKInfo(): SDKInfo {
  return {
    version: getPackageVersion('@openevidence/sdk'),
    features: ['clinical-query', 'deep-consult', 'webhooks'],
  };
}

function getPackageVersion(pkg: string): string {
  try {
    const result = execSync(`npm list ${pkg} --json 2>/dev/null`, { encoding: 'utf8' });
    const json = JSON.parse(result);
    return json.dependencies?.[pkg]?.version || 'unknown';
  } catch {
    return 'unknown';
  }
}

async function summarizeRecentErrors(): Promise<ErrorSummary[]> {
  // This would typically pull from your error tracking system
  // Placeholder implementation
  return [];
}

async function gatherMetrics(): Promise<MetricsSummary> {
  // This would typically pull from your metrics system
  // Placeholder implementation
  return {
    totalRequests: 0,
    successRate: 0,
    avgLatencyMs: 0,
    p99LatencyMs: 0,
  };
}
```

### Step 3: Sanitized Log Extraction
```typescript
// src/debug/log-sanitizer.ts
// IMPORTANT: Removes PHI before including in debug bundle

const PHI_PATTERNS = [
  /\b\d{3}-\d{2}-\d{4}\b/g,           // SSN
  /\b[A-Z]\d{8}\b/gi,                  // MRN patterns
  /\b\d{10,}\b/g,                      // Long numbers (potential IDs)
  /patient[_\s]*(name|id|dob)/gi,      // Patient fields
  /\b(male|female),?\s*\d{1,3}/gi,    // Demographics
  /"name"\s*:\s*"[^"]+"/gi,           // Name fields in JSON
  /"dob"\s*:\s*"[^"]+"/gi,            // DOB fields
  /"mrn"\s*:\s*"[^"]+"/gi,            // MRN fields
];

export function sanitizeLogs(logs: string): string {
  let sanitized = logs;

  for (const pattern of PHI_PATTERNS) {
    sanitized = sanitized.replace(pattern, '[REDACTED]');
  }

  return sanitized;
}

export function extractSanitizedLogs(
  logSource: string,
  timeRange: { start: Date; end: Date },
  maxLines: number = 1000  # 1000: 1 second in ms
): string[] {
  // Implementation depends on your logging infrastructure
  // Example with file-based logs:

  const logs: string[] = [];
  // Read logs, filter by time range, sanitize each line
  // ...

  return logs.map(sanitizeLogs).slice(0, maxLines);
}
```

### Step 4: Support Ticket Generator
```typescript
// src/debug/support-ticket.ts
import { generateDebugBundle, DebugBundle } from './debug-bundle';
import { sanitizeLogs, extractSanitizedLogs } from './log-sanitizer';

interface SupportTicket {
  subject: string;
  description: string;
  debugBundle: DebugBundle;
  sanitizedLogs: string[];
  stepsToReproduce: string[];
  expectedBehavior: string;
  actualBehavior: string;
}

export async function generateSupportTicket(
  issue: {
    summary: string;
    stepsToReproduce: string[];
    expectedBehavior: string;
    actualBehavior: string;
  }
): Promise<SupportTicket> {
  const bundle = await generateDebugBundle();

  const logs = extractSanitizedLogs(
    '/var/log/app/openevidence.log',
    { start: new Date(Date.now() - 3600000), end: new Date() },  # 3600000 = configured value
    500  # HTTP 500 Internal Server Error
  );

  return {
    subject: `[OpenEvidence Integration] ${issue.summary}`,
    description: `
## Issue Summary
${issue.summary}

## Environment
- Node Version: ${bundle.environment.nodeVersion}
- SDK Version: ${bundle.environment.sdkVersion}
- Base URL: ${bundle.environment.baseUrl}
- Timeout: ${bundle.environment.timeout}ms

## Connectivity
- Health Status: ${bundle.connectivity.healthStatus || 'Failed'}
- Latency: ${bundle.connectivity.latencyMs || 'N/A'}ms
- DNS Resolution: ${bundle.connectivity.dnsResolution ? 'OK' : 'Failed'}

## Recent Errors
${bundle.recentErrors.map(e => `- ${e.code}: ${e.count} occurrences (last: ${e.lastOccurred})`).join('\n') || 'None recorded'}
`,
    debugBundle: bundle,
    sanitizedLogs: logs,
    stepsToReproduce: issue.stepsToReproduce,
    expectedBehavior: issue.expectedBehavior,
    actualBehavior: issue.actualBehavior,
  };
}
```

## Output
- Environment configuration status
- Connectivity test results
- SDK version information
- Sanitized logs (no PHI)
- Formatted support ticket

## Diagnostic Checklist
- [ ] API key is set and correct length
- [ ] Organization ID is configured
- [ ] Health endpoint returns 200
- [ ] DNS resolves api.openevidence.com
- [ ] TLS handshake succeeds
- [ ] Rate limits have headroom
- [ ] No recent 5xx errors

## Error Handling
| Issue | Check | Resolution |
|-------|-------|------------|
| No connectivity | DNS, firewall | Check network config |
| Auth failures | API key format | Regenerate key in dashboard |
| Timeouts | Latency test | Increase timeout, check network |
| PHI in logs | Log sanitizer | Audit logging configuration |

## Examples

### Quick Debug Command
```bash
# Run bash debug script
chmod +x scripts/openevidence-debug.sh
./scripts/openevidence-debug.sh > debug-bundle.txt
```

### Generate Support Ticket
```typescript
const ticket = await generateSupportTicket({
  summary: 'Clinical queries timing out after SDK upgrade',
  stepsToReproduce: [
    '1. Upgrade @openevidence/sdk to v2.0.0',
    '2. Make clinical query request',
    '3. Request times out after 30s',
  ],
  expectedBehavior: 'Response within 10s',
  actualBehavior: 'Timeout after configured limit',
});

console.log(JSON.stringify(ticket, null, 2));
```

## Resources
- [OpenEvidence Support](mailto:support@openevidence.com)
- [OpenEvidence Status](https://status.openevidence.com/)

## Next Steps
For rate limit management, see `openevidence-rate-limits`.