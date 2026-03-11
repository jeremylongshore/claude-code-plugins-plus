# Speak Prod Checklist - Implementation Guide

Detailed implementation reference for the speak-prod-checklist skill.

## Instructions

### Step 1: Pre-Deployment Configuration
- [ ] Production API keys in secure vault
- [ ] Environment variables set in deployment platform
- [ ] API key scopes are minimal (least privilege)
- [ ] Webhook endpoints configured with HTTPS
- [ ] Webhook secrets stored securely
- [ ] Audio storage configured with encryption

### Step 2: Code Quality Verification
- [ ] All tests passing (`npm test`)
- [ ] No hardcoded credentials
- [ ] Error handling covers all Speak error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate (no PII)
- [ ] Audio handling follows privacy guidelines

### Step 3: Language Learning Feature Checklist
- [ ] All target languages tested
- [ ] Speech recognition works in all browsers
- [ ] Pronunciation scoring accurate
- [ ] AI tutor responses appropriate
- [ ] Session timeouts handled gracefully
- [ ] Progress tracking persists correctly

### Step 4: Infrastructure Setup
- [ ] Health check endpoint includes Speak connectivity
- [ ] Monitoring/alerting configured for:
  - [ ] API latency
  - [ ] Speech recognition success rate
  - [ ] Session completion rate
  - [ ] Error rates by type
- [ ] Circuit breaker pattern implemented
- [ ] Graceful degradation configured
- [ ] CDN configured for audio assets

### Step 5: Documentation Requirements
- [ ] Incident runbook created
- [ ] Key rotation procedure documented
- [ ] Rollback procedure documented
- [ ] On-call escalation path defined
- [ ] User support FAQ for common issues

### Step 6: Deploy with Gradual Rollout

```bash
# Pre-flight checks
echo "=== Speak Production Pre-flight ==="

# Check staging health
curl -f https://staging.example.com/health | jq '.services.speak'

# Check Speak service status
curl -s https://status.speak.com/api/status | jq '.status'

# Verify production credentials work
curl -X POST https://api.speak.com/v1/health \
  -H "Authorization: Bearer ${SPEAK_API_KEY_PROD}" \
  -H "X-App-ID: ${SPEAK_APP_ID_PROD}" | jq

echo "=== Starting Deployment ==="

# Gradual rollout - start with canary (10%)
kubectl apply -f k8s/production.yaml
kubectl set image deployment/speak-integration app=image:new --record
kubectl rollout pause deployment/speak-integration

echo "Canary deployed. Monitoring for 10 minutes..."
sleep 600

# Check canary metrics
echo "Checking error rates..."
curl -s "localhost:9090/api/v1/query?query=rate(speak_errors_total[5m])" | jq

# Check lesson completion rate
curl -s "localhost:9090/api/v1/query?query=speak_lesson_completion_rate[5m]" | jq

# If healthy, continue rollout to 50%
echo "Canary healthy. Continuing to 50%..."
kubectl rollout resume deployment/speak-integration
kubectl rollout pause deployment/speak-integration
sleep 300

# Complete rollout to 100%
echo "50% healthy. Completing rollout..."
kubectl rollout resume deployment/speak-integration
kubectl rollout status deployment/speak-integration

echo "=== Deployment Complete ==="
```


## Health Check Implementation

```typescript
// api/health.ts
interface SpeakHealthStatus {
  connected: boolean;
  latencyMs: number;
  speechRecognition: boolean;
  tutorAvailable: boolean;
}

async function checkSpeakHealth(): Promise<SpeakHealthStatus> {
  const start = Date.now();

  try {
    // Test basic connectivity
    await speakClient.health.check();

    // Test speech recognition (with sample audio)
    const speechOk = await testSpeechRecognition();

    // Test tutor availability
    const tutorOk = await testTutorConnection();

    return {
      connected: true,
      latencyMs: Date.now() - start,
      speechRecognition: speechOk,
      tutorAvailable: tutorOk,
    };
  } catch (error) {
    return {
      connected: false,
      latencyMs: Date.now() - start,
      speechRecognition: false,
      tutorAvailable: false,
    };
  }
}

app.get('/health', async (req, res) => {
  const speakStatus = await checkSpeakHealth();

  const isHealthy = speakStatus.connected &&
    speakStatus.speechRecognition &&
    speakStatus.tutorAvailable;

  res.status(isHealthy ? 200 : 503).json({
    status: isHealthy ? 'healthy' : 'degraded',
    services: {
      speak: speakStatus,
    },
    timestamp: new Date().toISOString(),
  });
});
```


## Rollback Procedure

```bash
#!/bin/bash
# rollback-speak.sh

echo "=== Emergency Rollback ==="

# Immediate rollback
kubectl rollout undo deployment/speak-integration
kubectl rollout status deployment/speak-integration

# Verify rollback
curl -f https://api.yourapp.com/health | jq

# If Speak completely down, enable fallback mode
if [ "$1" == "--fallback" ]; then
  kubectl set env deployment/speak-integration SPEAK_FALLBACK_MODE=true
  echo "Fallback mode enabled - offline lessons available"
fi

echo "=== Rollback Complete ==="
```


## Alert Configuration

| Alert | Condition | Severity |
|-------|-----------|----------|
| Speak API Down | Health check fails 3x | P1 |
| High Error Rate | Error rate > 5% | P2 |
| Speech Recognition Failing | Success rate < 90% | P2 |
| High Latency | p95 > 3000ms | P2 |
| Auth Failures | 401/403 errors > 0 | P1 |
| Session Abandonment | Abandon rate > 20% | P3 |


## Production Monitoring Dashboard

```yaml
# grafana-speak-dashboard.yaml
panels:
  - title: "Lesson Sessions"
    query: "sum(speak_sessions_active)"

  - title: "Speech Recognition Success Rate"
    query: "rate(speak_speech_success_total[5m]) / rate(speak_speech_total[5m]) * 100"

  - title: "Average Pronunciation Score"
    query: "avg(speak_pronunciation_score)"

  - title: "API Latency (p95)"
    query: "histogram_quantile(0.95, rate(speak_api_latency_bucket[5m]))"

  - title: "Error Rate by Type"
    query: "sum by (error_type) (rate(speak_errors_total[5m]))"

  - title: "Lesson Completion Rate"
    query: "rate(speak_lessons_completed[5m]) / rate(speak_lessons_started[5m]) * 100"
```


## Detailed Examples

### Smoke Test Suite
```typescript
async function productionSmokeTest(): Promise<TestResults> {
  const tests = [
    { name: 'API Health', fn: testApiHealth },
    { name: 'Speech Recognition', fn: testSpeechRecognition },
    { name: 'AI Tutor', fn: testTutorResponse },
    { name: 'Session Lifecycle', fn: testSessionLifecycle },
    { name: 'Pronunciation Scoring', fn: testPronunciationScoring },
  ];

  const results = [];
  for (const test of tests) {
    try {
      await test.fn();
      results.push({ name: test.name, passed: true });
    } catch (error) {
      results.push({ name: test.name, passed: false, error });
    }
  }

  return results;
}
```

