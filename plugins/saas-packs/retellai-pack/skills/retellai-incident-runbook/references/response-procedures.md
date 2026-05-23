# Incident Response Procedures

## Immediate Actions by Error Type

### 401/403 - Authentication

```bash
set -euo pipefail
# Verify API key is set
kubectl get secret retellai-secrets -o jsonpath='{.data.api-key}' | base64 -d

# Check if key was rotated
# → Verify in Retell AI dashboard

# Remediation: Update secret and restart pods
kubectl create secret generic retellai-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/retellai-integration
```

### 429 - Rate Limited

```bash
set -euo pipefail
# Check rate limit headers
curl -v https://api.retellai.com 2>&1 | grep -i rate

# Enable request queuing
kubectl set env deployment/retellai-integration RATE_LIMIT_MODE=queue

# Long-term: Contact Retell AI for limit increase
```

### 500/503 - Retell AI Errors

```bash
set -euo pipefail
# Enable graceful degradation
kubectl set env deployment/retellai-integration RETELLAI_FALLBACK=true

# Notify users of degraded service
# Update status page

# Monitor Retell AI status for resolution
```

## Communication Templates

### Internal (Slack)

```
🔴 P1 INCIDENT: Retell AI Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Current action: [What is being done]
Next update: [Time]
Incident commander: @[name]
```

### External (Status Page)

```
Retell AI Integration Issue

There are issues with the Retell AI integration.
Some users may experience [specific impact].

The team is actively investigating and will provide updates.

Last updated: [timestamp]
```

## Post-Incident Evidence Collection

```bash
set -euo pipefail
# Generate debug bundle
./scripts/retellai-debug-bundle.sh

# Export relevant logs
kubectl logs -l app=retellai-integration --since=1h > incident-logs.txt

# Capture metrics
curl "localhost:9090/api/v1/query_range?query=retellai_errors_total&start=2h" > metrics.json
```

## Postmortem Template

```markdown
## Incident: Retell AI [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]

### Summary
[1-2 sentence description]

### Timeline
- HH:MM - [Event]
- HH:MM - [Event]

### Root Cause
[Technical explanation]

### Impact
- Users affected: N
- Revenue impact: $X

### Action Items
- [ ] [Preventive measure] - Owner - Due date
```
