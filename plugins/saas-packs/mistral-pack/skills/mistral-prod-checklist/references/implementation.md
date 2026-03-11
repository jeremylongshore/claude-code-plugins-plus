# Mistral AI Production Checklist - Implementation Details

## Health Check Endpoint
```typescript
app.get('/health', async (req, res) => {
  const mistralHealth = await checkMistralHealth();
  res.status(mistralHealth.healthy ? 200 : 503).json({
    status: mistralHealth.healthy ? 'healthy' : 'degraded',
    services: { mistral: mistralHealth },
    timestamp: new Date().toISOString(),
  });
});

async function checkMistralHealth() {
  const start = Date.now();
  try { await client.models.list(); return { healthy: true, latencyMs: Date.now() - start }; }
  catch { return { healthy: false, latencyMs: Date.now() - start, error: 'API unreachable' }; }
}
```

## Circuit Breaker
```typescript
class MistralCircuitBreaker {
  private failures = 0;
  private isOpen = false;
  private readonly failureThreshold = 5;
  private readonly resetTimeout = 60000;

  async call<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.isOpen) {
      if (Date.now() - (this.lastFailure?.getTime() || 0) > this.resetTimeout) { this.isOpen = false; this.failures = 0; }
      else { if (fallback) return fallback(); throw new Error('Service temporarily unavailable'); }
    }
    try { const result = await fn(); this.failures = 0; return result; }
    catch (error) {
      this.failures++;
      if (this.failures >= this.failureThreshold) this.isOpen = true;
      if (fallback && this.isOpen) return fallback();
      throw error;
    }
  }
}
```

## Pre-Deployment Verification
```bash
# Test production key
curl -H "Authorization: Bearer ${MISTRAL_API_KEY_PROD}" https://api.mistral.ai/v1/models | jq '.data[].id'

# Check for hardcoded secrets
grep -r "sk-" src/ --include="*.ts" --include="*.js"

# Full verification
npm test && npm run typecheck && npm run lint
```

## Gradual Rollout
```bash
# Deploy canary (10%), monitor 10 min, check errors, expand to 50%, then 100%
kubectl set image deployment/mistral-app app=image:new --record
kubectl rollout pause deployment/mistral-app
# Monitor...
kubectl rollout resume deployment/mistral-app
```

## Rollback Procedure
```bash
kubectl rollout undo deployment/mistral-app
kubectl rollout status deployment/mistral-app
curl -sf https://yourapp.com/health | jq
```
