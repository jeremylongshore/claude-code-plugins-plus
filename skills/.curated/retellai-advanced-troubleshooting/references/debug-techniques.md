# Advanced Debug Techniques

## Comprehensive Debug Bundle Script

```bash
#!/bin/bash
set -euo pipefail
# advanced-retellai-debug.sh

BUNDLE="retellai-advanced-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"/{logs,metrics,network,config,traces}

# 1. Extended logs (1 hour window)
kubectl logs -l app=retellai-integration --since=1h > "$BUNDLE/logs/pods.log"
journalctl -u retellai-service --since "1 hour ago" > "$BUNDLE/logs/system.log"

# 2. Metrics dump
curl -s localhost:9090/api/v1/query?query=retellai_requests_total > "$BUNDLE/metrics/requests.json"
curl -s localhost:9090/api/v1/query?query=retellai_errors_total > "$BUNDLE/metrics/errors.json"

# 3. Network capture (30 seconds)
timeout 30 tcpdump -i any port 443 -w "$BUNDLE/network/capture.pcap" &

# 4. Distributed traces
curl -s localhost:16686/api/traces?service=retellai > "$BUNDLE/traces/jaeger.json"

# 5. Configuration state
kubectl get cm retellai-config -o yaml > "$BUNDLE/config/configmap.yaml"
kubectl get secret retellai-secrets -o yaml > "$BUNDLE/config/secrets-redacted.yaml"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Advanced debug bundle: $BUNDLE.tar.gz"
```

## Layer-by-Layer Testing

```typescript
// Test each layer independently
async function diagnoseRetellAIIssue(): Promise<DiagnosisReport> {
  const results: DiagnosisResult[] = [];

  // Layer 1: Network connectivity
  results.push(await testNetworkConnectivity());

  // Layer 2: DNS resolution
  results.push(await testDNSResolution('api.retellai.com'));

  // Layer 3: TLS handshake
  results.push(await testTLSHandshake('api.retellai.com'));

  // Layer 4: Authentication
  results.push(await testAuthentication());

  // Layer 5: API response
  results.push(await testAPIResponse());

  // Layer 6: Response parsing
  results.push(await testResponseParsing());

  return { results, firstFailure: results.find(r => !r.success) };
}
```

## Minimal Reproduction

```typescript
// Strip down to absolute minimum
async function minimalRepro(): Promise<void> {
  // 1. Fresh client, no customization
  const client = new RetellAIClient({
    apiKey: process.env.RETELLAI_API_KEY!,
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
// Detect memory leaks in Retell AI client usage
const heapUsed: number[] = [];

setInterval(() => {
  const usage = process.memoryUsage();
  heapUsed.push(usage.heapUsed);

  // Alert on sustained growth
  if (heapUsed.length > 60) { // 1 hour at 1/min
    const trend = heapUsed[59] - heapUsed[0];
    if (trend > 100 * 1024 * 1024) { // 100MB growth
      console.warn('Potential memory leak in retellai integration');
    }
  }
}, 60000);
```

## Race Condition Detection

```typescript
// Detect concurrent access issues
class RetellAIConcurrencyChecker {
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

## Support Escalation Template

```markdown
## Retell AI Support Escalation

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
- [ ] Debug bundle (retellai-advanced-debug-*.tar.gz)
- [ ] Minimal reproduction code
- [ ] Timing analysis
- [ ] Network capture (if relevant)

### Workarounds Attempted
1. [Workaround 1] - Result: [outcome]
2. [Workaround 2] - Result: [outcome]
```
