# OpenEvidence Deploy Integration - Implementation Details

## Multi-Environment Configuration
```typescript
export const environments: Record<string, OpenEvidenceEnvConfig> = {
  development: { baseUrl: 'https://api.sandbox.openevidence.com', timeout: 60000, retries: 1, secretPath: 'local' },
  staging: { baseUrl: 'https://api.sandbox.openevidence.com', timeout: 45000, retries: 2, secretPath: 'projects/staging/secrets/openevidence' },
  production: { baseUrl: 'https://api.openevidence.com', timeout: 30000, retries: 3, secretPath: 'projects/production/secrets/openevidence' },
};
```

## GitHub Actions Deploy Workflow
Full CI/CD pipeline with test, build, deploy-staging, and deploy-production jobs including canary rollout (10% traffic, monitor 5 min, then full rollout).

## Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clinical-evidence-api
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: api
          image: gcr.io/PROJECT_ID/clinical-evidence-api:VERSION
          env:
            - name: OPENEVIDENCE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openevidence-secrets
                  key: api-key
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
          readinessProbe:
            httpGet:
              path: /health/openevidence
              port: 8080
```

## Health Check Endpoint
```typescript
router.get('/health/openevidence', async (req, res) => {
  const startTime = Date.now();
  try {
    const client = new OpenEvidenceClient({ apiKey: process.env.OPENEVIDENCE_API_KEY!, baseUrl: getConfig().baseUrl });
    await client.health.check();
    res.json({ status: 'healthy', latencyMs: Date.now() - startTime });
  } catch (error: any) {
    res.status(503).json({ status: 'unhealthy', error: error.message });
  }
});
```

## Rollback Procedure
```bash
#!/bin/bash
set -e
SERVICE_NAME="clinical-evidence-api"
PREVIOUS=$(gcloud run revisions list --service $SERVICE_NAME --region $REGION --format 'value(metadata.name)' --limit 2 | tail -1)
gcloud run services update-traffic $SERVICE_NAME --region $REGION --to-revisions $PREVIOUS=100
```
