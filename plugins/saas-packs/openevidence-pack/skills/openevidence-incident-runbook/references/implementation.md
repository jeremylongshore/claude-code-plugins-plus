# OpenEvidence Incident Runbook - Implementation Details

## Incident Response by Error Type

### 401/403 - Authentication Errors
```bash
kubectl get secret openevidence-secrets -o jsonpath='{.data.api-key}' | base64 -d | wc -c
kubectl create secret generic openevidence-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/clinical-evidence-api
```

### 429 - Rate Limited
```bash
curl -s -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" https://api.openevidence.com/v1/rate-limit | jq
kubectl set env deployment/clinical-evidence-api RATE_LIMIT_MODE=queue
```

### 500/503 - OpenEvidence Server Errors
```bash
kubectl set env deployment/clinical-evidence-api OPENEVIDENCE_FALLBACK=true
./scripts/notify-clinical-degraded.sh
```

## Fallback Procedures
```typescript
const FALLBACK_RESPONSE = {
  answer: 'Clinical evidence service is temporarily unavailable. Please consult UpToDate, DynaMed, or current clinical guidelines directly.',
  citations: [], confidence: 0, fallback: true,
};
```

## Communication Templates

### Internal Slack
```
:red_circle: **P1 INCIDENT: OpenEvidence Clinical AI**
**Status:** INVESTIGATING
**Impact:** Clinical queries returning errors/degraded
**Fallback:** Graceful degradation enabled
```

## Evidence Collection
```bash
#!/bin/bash
INCIDENT_ID=${1:-$(date +%Y%m%d-%H%M)}
OUTPUT_DIR="incidents/${INCIDENT_ID}"
mkdir -p "$OUTPUT_DIR"
kubectl logs -l app=clinical-evidence-api --since=2h > "$OUTPUT_DIR/app-logs.txt"
# Export metrics, alerts, sanitize PHI
```

## Postmortem Template
Structured postmortem including: Summary, Clinical Impact, Timeline, Root Cause, Contributing Factors, What Went Well, Action Items, Lessons Learned.

## Quick Reference Commands
```bash
curl -sf https://api.yourhealthcare.com/health/openevidence | jq '.status' || echo "UNHEALTHY"
kubectl set env deployment/clinical-evidence-api OPENEVIDENCE_FALLBACK=true  # Enable
kubectl set env deployment/clinical-evidence-api OPENEVIDENCE_FALLBACK=false # Disable
kubectl rollout restart deployment/clinical-evidence-api
```
