# Deepgram Incident Runbook - Implementation Details

## Initial Triage Script

```bash
#!/bin/bash
echo "=== Deepgram Incident Triage ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Check Deepgram status page
echo "1. Checking Deepgram Status..."
curl -s https://status.deepgram.com/api/v2/status.json | jq '.status.indicator'

# 2. Check our error rate
echo "2. Recent Error Rate (last 5 min)..."
curl -s http://localhost:9090/api/v1/query \
  --data-urlencode 'query=sum(rate(deepgram_transcription_requests_total{status="error"}[5m]))/sum(rate(deepgram_transcription_requests_total[5m]))' \
  | jq '.data.result[0].value[1]'

# 3. Check latency
echo "3. P95 Latency (last 5 min)..."
curl -s http://localhost:9090/api/v1/query \
  --data-urlencode 'query=histogram_quantile(0.95,sum(rate(deepgram_transcription_latency_seconds_bucket[5m]))by(le))' \
  | jq '.data.result[0].value[1]'

# 4. Quick connectivity test
echo "4. API Connectivity Test..."
curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" \
  -X GET 'https://api.deepgram.com/v1/projects' \
  -H "Authorization: Token $DEEPGRAM_API_KEY"
```

## SEV1: Complete Outage - Fallback Activation

```typescript
import { FallbackManager } from './fallback';

const fallback = new FallbackManager();

// Activate fallback mode
await fallback.activate({
  reason: 'SEV1: Deepgram API outage',
  mode: 'queue', // Queue requests for later
  notifyUsers: true,
});

// Or switch to backup provider
await fallback.switchProvider('backup-stt-provider');
```

## SEV2: Major Degradation - Investigation

```typescript
import { createClient } from '@deepgram/sdk';

async function investigateDegradation() {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const testUrls = [
    'https://static.deepgram.com/examples/nasa-podcast.wav',
    'https://your-test-audio.com/sample1.wav',
    'https://your-test-audio.com/sample2.wav',
  ];

  console.log('Testing transcription across multiple samples...\n');
  const results = await Promise.allSettled(
    testUrls.map(async (url) => {
      const startTime = Date.now();
      const { result, error } = await client.listen.prerecorded.transcribeUrl({ url }, { model: 'nova-2' });
      return { url, success: !error, latency: Date.now() - startTime, error: error?.message, requestId: result?.metadata?.request_id };
    })
  );

  const successful = results.filter(r => r.status === 'fulfilled' && r.value.success);
  const failed = results.filter(r => r.status === 'rejected' || !r.value?.success);
  console.log(`Success: ${successful.length}/${results.length}`);
  console.log(`Failed: ${failed.length}/${results.length}`);

  // Test different models
  console.log('\nTesting different models...');
  for (const model of ['nova-2', 'nova', 'base']) {
    const { error } = await client.listen.prerecorded.transcribeUrl({ url: testUrls[0] }, { model });
    console.log(`  ${model}: ${error ? 'FAIL' : 'OK'}`);
  }
}
```

## SEV3: Minor Degradation - Graceful Config

```typescript
const gracefulConfig = {
  timeout: 60000,
  retryConfig: { maxRetries: 5, baseDelay: 2000, maxDelay: 30000 },
  model: 'nova', // Simpler model for faster processing
  features: { diarization: false, smartFormat: true },
};
```

## Communication Template

```markdown
## Incident: Deepgram Service Outage
**Status:** Investigating
**Severity:** SEV1
**Started:** [TIME]
**Impact:** All transcription services unavailable

### Current Actions
- [ ] Verified Deepgram status page shows incident
- [ ] Contacted Deepgram support
- [ ] Activated fallback queueing
- [ ] Notified affected customers

### Next Update
In 15 minutes or when status changes.
```

## Post-Incident Review Template

```markdown
## Post-Incident Review: [INCIDENT-ID]

### Timeline
- **HH:MM** - First alert triggered
- **HH:MM** - Incident acknowledged
- **HH:MM** - Root cause identified
- **HH:MM** - Mitigation applied
- **HH:MM** - Service restored

### Impact
- Duration: X hours Y minutes
- Affected requests: N
- Failed transcriptions: N

### Action Items
| Item | Owner | Due Date |
|------|-------|----------|
| [Action] | [Name] | [Date] |
```

## Diagnostic Commands

```bash
# API connectivity
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -X GET 'https://api.deepgram.com/v1/projects' \
  -H "Authorization: Token $DEEPGRAM_API_KEY"

# Test transcription
curl -X POST 'https://api.deepgram.com/v1/listen?model=nova-2' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://static.deepgram.com/examples/nasa-podcast.wav"}'

# Kubernetes checks
kubectl get pods -l app=deepgram-service
kubectl logs -l app=deepgram-service --tail=100
kubectl top pods -l app=deepgram-service
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
