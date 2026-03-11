# Speak Incident Runbook - Implementation Guide

Detailed implementation reference for the speak-incident-runbook skill.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Speak API unreachable, all lessons failing |
| P2 | Degraded service | < 1 hour | High latency, speech recognition failing |
| P3 | Minor impact | < 4 hours | Specific language unavailable, slow scoring |
| P4 | No user impact | Next business day | Monitoring gaps, minor bugs |


## Quick Triage

```bash
#!/bin/bash
# speak-triage.sh

echo "=== Speak Quick Triage ==="
echo "Time: $(date)"
echo ""

# 1. Check Speak status
echo "1. Speak Status Page:"
curl -s https://status.speak.com/api/status | jq '.status'
echo ""

# 2. Check our integration health
echo "2. Our Health Check:"
curl -s https://api.yourapp.com/health | jq '.services.speak'
echo ""

# 3. Check active sessions
echo "3. Active Sessions:"
curl -s "localhost:9090/api/v1/query?query=speak_active_sessions" | jq '.data.result[0].value[1]'
echo ""

# 4. Check error rate (last 5 min)
echo "4. Error Rate (5m):"
curl -s "localhost:9090/api/v1/query?query=rate(speak_api_errors_total[5m])" | jq '.data.result'
echo ""

# 5. Check lesson completion rate
echo "5. Lesson Completion Rate (1h):"
curl -s "localhost:9090/api/v1/query?query=rate(speak_lessons_completed_total[1h])/rate(speak_lessons_started_total[1h])" | jq '.data.result[0].value[1]'
echo ""

# 6. Recent error logs
echo "6. Recent Errors:"
kubectl logs -l app=speak-integration --since=5m 2>/dev/null | grep -i error | tail -10
```


## Decision Tree

```
Speak API returning errors?
├─ YES: Is status.speak.com showing incident?
│   ├─ YES → Wait for Speak to resolve. Enable fallback/offline mode.
│   └─ NO → Our integration issue. Check credentials, config, code.
└─ NO: Are lessons working?
    ├─ YES: Is speech recognition working?
    │   ├─ YES → Likely resolved or intermittent. Monitor.
    │   └─ NO → Audio processing issue. Check audio infrastructure.
    └─ NO → Our service issue. Check pods, memory, database.
```


## Immediate Actions by Error Type

### 401/403 - Authentication Failures
```bash
# Verify API credentials are set
kubectl get secret speak-secrets -o jsonpath='{.data.api-key}' | base64 -d | head -c 10
echo "..."

# Check if credentials were rotated
# → Verify in Speak developer dashboard

# Remediation: Update secret and restart pods
kubectl create secret generic speak-secrets \
  --from-literal=api-key=NEW_KEY \
  --from-literal=app-id=APP_ID \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/speak-integration
```

### 429 - Rate Limited
```bash
# Check current rate limit status
curl -v https://api.speak.com/v1/health \
  -H "Authorization: Bearer ${SPEAK_API_KEY}" 2>&1 | grep -i "rate"

# Enable request queuing/throttling
kubectl set env deployment/speak-integration SPEAK_RATE_LIMIT_MODE=queue

# For persistent issues, contact Speak for limit increase
```

### 500/503 - Speak Server Errors
```bash
# Enable graceful degradation (offline lessons if available)
kubectl set env deployment/speak-integration SPEAK_FALLBACK_MODE=true

# Enable cached responses
kubectl set env deployment/speak-integration SPEAK_CACHE_ONLY=true

# Update status page for users
# Monitor Speak status for resolution
```

### Speech Recognition Failures
```bash
# Check audio processing service
kubectl get pods -l component=audio-processor

# Check audio queue depth
curl -s "localhost:9090/api/v1/query?query=speak_audio_queue_depth"

# Scale audio processors if needed
kubectl scale deployment/audio-processor --replicas=5

# Verify audio storage is accessible
gsutil ls gs://your-audio-bucket/
```


## Communication Templates

### Internal (Slack)
```
🔴 P1 INCIDENT: Speak Language Learning
Status: INVESTIGATING
Impact: Users cannot start or complete lessons
Languages affected: All
Current action: Checking Speak API status and our integration
Next update: [Time + 15 min]
Incident commander: @[name]
War room: #speak-incident-[date]
```

### External (Status Page)
```
Language Learning Service Disruption

We are experiencing issues with our language learning features.
Users may be unable to:
- Start new lessons
- Complete pronunciation exercises
- Access speech recognition

We are actively working with our service provider to resolve this issue.
Offline vocabulary practice remains available.

Last updated: [timestamp]
```

### User Notification (In-App)
```
We're experiencing technical difficulties with live lessons.
While we work on a fix, you can:
• Practice vocabulary flashcards (offline)
• Review previous lesson notes
• Listen to saved audio examples

We'll notify you when full service is restored.
```


## Fallback Modes

### Enable Offline Mode
```typescript
// Fallback when Speak API is unavailable
async function getLesson(config: LessonConfig): Promise<Lesson> {
  if (process.env.SPEAK_FALLBACK_MODE === 'true') {
    return getOfflineLesson(config);
  }

  try {
    return await speakService.startSession(config);
  } catch (error) {
    if (isApiUnavailable(error)) {
      console.warn('Speak API unavailable, using fallback');
      return getOfflineLesson(config);
    }
    throw error;
  }
}
```

### Cached Responses
```typescript
// Serve cached content when API is slow/unavailable
async function getTutorPrompt(sessionId: string): Promise<TutorPrompt> {
  const cacheKey = `prompt:${sessionId}`;

  // Try cache first during incidents
  if (process.env.SPEAK_CACHE_ONLY === 'true') {
    const cached = await cache.get(cacheKey);
    if (cached) return cached;
    throw new Error('Prompt not in cache during incident');
  }

  // Normal flow with cache fallback
  try {
    const prompt = await speakService.tutor.getPrompt(sessionId);
    await cache.set(cacheKey, prompt, 3600);
    return prompt;
  } catch (error) {
    const cached = await cache.get(cacheKey);
    if (cached) return cached;
    throw error;
  }
}
```


## Post-Incident

### Evidence Collection
```bash
#!/bin/bash
# collect-speak-incident-evidence.sh

INCIDENT_DIR="speak-incident-$(date +%Y%m%d-%H%M)"
mkdir -p "$INCIDENT_DIR"

# Export logs
kubectl logs -l app=speak-integration --since=2h > "$INCIDENT_DIR/logs.txt"

# Export metrics
curl "localhost:9090/api/v1/query_range?query=speak_api_errors_total&start=$(date -d '2 hours ago' +%s)&end=$(date +%s)&step=60" > "$INCIDENT_DIR/errors.json"

curl "localhost:9090/api/v1/query_range?query=speak_lessons_started_total&start=$(date -d '2 hours ago' +%s)&end=$(date +%s)&step=60" > "$INCIDENT_DIR/lessons.json"

# Capture current state
kubectl get pods -l app=speak-integration -o yaml > "$INCIDENT_DIR/pods.yaml"
kubectl get events --sort-by='.lastTimestamp' > "$INCIDENT_DIR/events.txt"

# Generate debug bundle
./speak-debug-bundle.sh
mv speak-debug-*.tar.gz "$INCIDENT_DIR/"

echo "Evidence collected in $INCIDENT_DIR"
```

### Postmortem Template
```markdown
## Incident: Speak [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Affected Users:** N (X% of daily active learners)

### Summary
[1-2 sentence description of what happened]

### User Impact
- Lessons affected: N
- Languages affected: [list]
- Features unavailable: [list]
- Estimated learning time lost: X hours

### Timeline
- HH:MM - [Event]
- HH:MM - Alert fired
- HH:MM - Incident declared
- HH:MM - [Mitigation action]
- HH:MM - Service restored

### Root Cause
[Technical explanation]

### Contributing Factors
- [Factor 1]
- [Factor 2]

### Action Items
| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | [Preventive measure] | @name | [date] |
| P2 | [Improvement] | @name | [date] |

### Lessons Learned
- What went well: [list]
- What could be improved: [list]
```

