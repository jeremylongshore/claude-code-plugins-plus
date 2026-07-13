# Deployment Steps

## Gradual Rollout Procedure

```bash
set -euo pipefail
# Pre-flight checks
curl -f https://staging.example.com/health
curl -s https://status.retellai.com

# Gradual rollout - start with canary (10%)
kubectl apply -f k8s/production.yaml
kubectl set image deployment/retellai-integration app=image:new --record
kubectl rollout pause deployment/retellai-integration

# Monitor canary traffic for 10 minutes
sleep 600
# Check error rates and latency before continuing

# If healthy, continue rollout to 50%
kubectl rollout resume deployment/retellai-integration
kubectl rollout pause deployment/retellai-integration
sleep 300

# Complete rollout to 100%
kubectl rollout resume deployment/retellai-integration
kubectl rollout status deployment/retellai-integration
```

## Health Check Implementation

```typescript
async function healthCheck(): Promise<{ status: string; retellai: any }> {
  const start = Date.now();
  try {
    await retellaiClient.ping();
    return { status: 'healthy', retellai: { connected: true, latencyMs: Date.now() - start } };
  } catch (error) {
    return { status: 'degraded', retellai: { connected: false, latencyMs: Date.now() - start } };
  }
}
```

## Immediate Rollback

```bash
set -euo pipefail
kubectl rollout undo deployment/retellai-integration
kubectl rollout status deployment/retellai-integration
```
