---
name: supabase-advanced-troubleshooting
description: |
  Supabase advanced debugging for hard-to-diagnose issues.
  Use when debugging complex Supabase issues that resist standard troubleshooting.
  Trigger with phrases like "supabase hard bug", "supabase mystery error",
  "supabase impossible to debug", "difficult supabase issue".
allowed-tools: Read, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Advanced Troubleshooting

## Overview
Deep debugging techniques for complex Supabase issues that resist standard troubleshooting.

## Prerequisites
- supabase-install-auth completed
- Standard troubleshooting already attempted
- Access to production logs and metrics
- Network capture tools available (tcpdump, Wireshark)

## Instructions

### Step 1: Evidence Collection Framework

### Comprehensive Debug Bundle
```bash
#!/bin/bash
# advanced-supabase-debug.sh

BUNDLE="supabase-advanced-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"/{logs,metrics,network,config,traces}

# 1. Extended logs (1 hour window)
kubectl logs -l app=supabase-integration --since=1h > "$BUNDLE/logs/pods.log"
journalctl -u supabase-service --since "1 hour ago" > "$BUNDLE/logs/system.log"

# 2. Metrics dump
curl -s localhost:9090/api/v1/query?query=supabase_requests_total > "$BUNDLE/metrics/requests.json"
curl -s localhost:9090/api/v1/query?query=supabase_errors_total > "$BUNDLE/metrics/errors.json"

# 3. Network capture (30 seconds)
timeout 30 tcpdump -i any port 443 -w "$BUNDLE/network/capture.pcap" &

# 4. Distributed traces
curl -s localhost:16686/api/traces?service=supabase > "$BUNDLE/traces/jaeger.json"

# 5. Configuration state
kubectl get cm supabase-config -o yaml > "$BUNDLE/config/configmap.yaml"
kubectl get secret supabase-secrets -o yaml > "$BUNDLE/config/secrets-redacted.yaml"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Advanced debug bundle: $BUNDLE.tar.gz"
```

## Systematic Isolation

### Layer-by-Layer Testing

```typescript
// Test each layer independently
async function diagnoseSupabaseIssue(): Promise<DiagnosisReport> {
  const results: DiagnosisResult[] = [];

  // Layer 1: Network connectivity
  results.push(await testNetworkConnectivity());

  // Layer 2: DNS resolution
  results.push(await testDNSResolution('api.supabase.com'));

  // Layer 3: TLS handshake
  results.push(await testTLSHandshake('api.supabase.com'));

  // Layer 4: Authentication
  results.push(await testAuthentication());

  // Layer 5: API response
  results.push(await testAPIResponse());

  // Layer 6: Response parsing
  results.push(await testResponseParsing());

  return { results, firstFailure: results.find(r => !r.success) };
}
```

### Minimal Reproduction

```typescript
// Strip down to absolute minimum
async function minimalRepro(): Promise<void> {
  // 1. Fresh client, no customization
  const client = new SupabaseClient({
    apiKey: process.env.SUPABASE_API_KEY!,
  });

  // 2. Simplest possible call
  try {
    const result = await client.ping();
    console.log('Ping successful:', result);
  } catch (error) {
    console.error('Ping failed:', {
      message: error.message,
      code: error.code,
      stack: error.stack,
    });
  }
}
```

## Timing Analysis

```typescript
class TimingAnalyzer {
  private timings: Map<string, number[]> = new Map();

  async measure<T>(label: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      return await fn();
    } finally {
      const duration = performance.now() - start;
      const existing = this.timings.get(label) || [];
      existing.push(duration);
      this.timings.set(label, existing);
    }
  }

  report(): TimingReport {
    const report: TimingReport = {};
    for (const [label, times] of this.timings) {
      report[label] = {
        count: times.length,
        min: Math.min(...times),
        max: Math.max(...times),
        avg: times.reduce((a, b) => a + b, 0) / times.length,
        p95: this.percentile(times, 95),
      };
    }
    return report;
  }
}
```

## Memory and Resource Analysis

```typescript
// Detect memory leaks in Supabase client usage
const heapUsed: number[] = [];

setInterval(() => {
  const usage = process.memoryUsage();
  heapUsed.push(usage.heapUsed);

  // Alert on sustained growth
  if (heapUsed.length > 60) { // 1 hour at 1/min
    const trend = heapUsed[59] - heapUsed[0];
    if (trend > 100 * 1024 * 1024) { // 100MB growth
      console.warn('Potential memory leak in supabase integration');
    }
  }
}, 60000);
```

## Race Condition Detection

```typescript
// Detect concurrent access issues
class SupabaseConcurrencyChecker {
  private inProgress: Set<string> = new Set();

  async execute<T>(key: string, fn: () => Promise<T>): Promise<T> {
    if (this.inProgress.has(key)) {
      console.warn(`Concurrent access detected for ${key}`);
    }

    this.inProgress.add(key);
    try {
      return await fn();
    } finally {
      this.inProgress.delete(key);
    }
  }
}
```

### Step 2: Support Escalation Template

```markdown
## Supabase Support Escalation

**Severity:** P[1-4]
**Request ID:** [from error response]
**Timestamp:** [ISO 8601]

### Issue Summary
[One paragraph description]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]

### Expected vs Actual
- Expected: [behavior]
- Actual: [behavior]

### Evidence Attached
- [ ] Debug bundle (supabase-advanced-debug-*.tar.gz)
- [ ] Minimal reproduction code
- [ ] Timing analysis
- [ ] Network capture (if relevant)

### Workarounds Attempted
1. [Workaround 1] - Result: [outcome]
2. [Workaround 2] - Result: [outcome]
```

## Output
- Debug bundle with logs, metrics, and traces
- Minimal reproduction case
- Timing analysis report
- Support escalation with evidence

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Intermittent failure | Race condition | Use concurrency checker |
| Memory growth | Leak in client usage | Monitor heap, analyze GC |
| Timeout variations | Network or DNS | Layer-by-layer testing |
| Inconsistent results | Caching issues | Clear all caches, test fresh |

## Examples

### Heap Snapshot Analysis

```typescript
import v8 from 'v8';
import fs from 'fs';

// Take heap snapshot when issue occurs
function captureHeapSnapshot(reason: string) {
  const filename = `heap-${Date.now()}-${reason}.heapsnapshot`;
  const snapshotStream = v8.writeHeapSnapshot(filename);
  console.log(`Heap snapshot written to ${snapshotStream}`);
}
```

## Resources
- [Supabase Support](https://supabase.com/docs/support)
- [Debugging Guide](https://supabase.com/docs/debugging)
- [Community Forums](https://community.supabase.com)

## Next Steps
For load testing, see `supabase-load-scale`.