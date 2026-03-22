---
name: customerio-deploy-pipeline
description: |
  Deploy Customer.io integrations to production cloud platforms.
  Use when deploying to Cloud Run, Vercel, AWS Lambda, or Kubernetes
  with proper secrets management and health checks.
  Trigger: "deploy customer.io", "customer.io cloud run",
  "customer.io kubernetes", "customer.io lambda", "customer.io vercel".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(gcloud:*), Bash(kubectl:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, deployment, cloud-run, kubernetes]

---
# Customer.io Deploy Pipeline

## Overview

Deploy Customer.io integrations to production: GCP Cloud Run with Secret Manager, Vercel serverless functions, AWS Lambda with SSM, Kubernetes with external secrets, plus health check endpoints and blue-green deployment scripts.

## Prerequisites

- CI/CD pipeline configured (see `customerio-ci-integration`)
- Cloud platform credentials and access
- Production Customer.io credentials in a secrets manager

## Instructions

### Step 1: Deploy to Google Cloud Run

```yaml
# .github/workflows/deploy-cloud-run.yml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # Required for Workload Identity Federation
    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SA }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Build and push
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT }}/cio-service

      - name: Deploy
        run: |
          gcloud run deploy cio-service \
            --image gcr.io/${{ secrets.GCP_PROJECT }}/cio-service \
            --region us-central1 \
            --set-secrets "CUSTOMERIO_SITE_ID=cio-site-id:latest,\
              CUSTOMERIO_TRACK_API_KEY=cio-track-key:latest,\
              CUSTOMERIO_APP_API_KEY=cio-app-key:latest" \
            --set-env-vars "CUSTOMERIO_REGION=us,NODE_ENV=production" \
            --min-instances 1 \
            --max-instances 10 \
            --memory 512Mi \
            --cpu 1 \
            --allow-unauthenticated
```

### Step 2: Health Check Endpoint

```typescript
// routes/health.ts
import { TrackClient, RegionUS } from "customerio-node";
import { Router } from "express";

const router = Router();

router.get("/health", async (_req, res) => {
  const checks: Record<string, { status: string; latency_ms?: number }> = {};

  // Check Track API
  const cio = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );

  const start = Date.now();
  try {
    await cio.identify("health-check", {
      email: "health@internal.example.com",
      _health_check: true,
    });
    checks.track_api = { status: "ok", latency_ms: Date.now() - start };
  } catch (err: any) {
    checks.track_api = { status: `error: ${err.statusCode}` };
  }

  const allOk = Object.values(checks).every((c) => c.status === "ok");

  res.status(allOk ? 200 : 503).json({
    status: allOk ? "healthy" : "degraded",
    checks,
    version: process.env.npm_package_version ?? "unknown",
    uptime_seconds: Math.floor(process.uptime()),
    timestamp: new Date().toISOString(),
  });
});

export default router;
```

### Step 3: Vercel Serverless Functions

```typescript
// api/customerio/identify.ts (Vercel serverless function)
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { userId, attributes } = req.body;
  if (!userId || !attributes?.email) {
    return res.status(400).json({ error: "userId and attributes.email required" });
  }

  try {
    await cio.identify(userId, {
      ...attributes,
      last_seen_at: Math.floor(Date.now() / 1000),
    });
    return res.status(200).json({ success: true });
  } catch (err: any) {
    return res.status(err.statusCode ?? 500).json({ error: err.message });
  }
}
```

### Step 4: Kubernetes Deployment

```yaml
# k8s/customerio-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customerio-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: customerio-service
  template:
    metadata:
      labels:
        app: customerio-service
    spec:
      containers:
        - name: app
          image: gcr.io/my-project/cio-service:latest
          ports:
            - containerPort: 3000
          env:
            - name: CUSTOMERIO_SITE_ID
              valueFrom:
                secretKeyRef:
                  name: customerio-secrets
                  key: site-id
            - name: CUSTOMERIO_TRACK_API_KEY
              valueFrom:
                secretKeyRef:
                  name: customerio-secrets
                  key: track-api-key
            - name: CUSTOMERIO_APP_API_KEY
              valueFrom:
                secretKeyRef:
                  name: customerio-secrets
                  key: app-api-key
            - name: CUSTOMERIO_REGION
              value: "us"
            - name: NODE_ENV
              value: "production"
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: customerio-service
spec:
  selector:
    app: customerio-service
  ports:
    - port: 80
      targetPort: 3000
```

### Step 5: Blue-Green Deployment

```bash
#!/usr/bin/env bash
set -euo pipefail
# scripts/blue-green-deploy.sh

SERVICE="cio-service"
REGION="us-central1"
IMAGE="gcr.io/${GCP_PROJECT}/${SERVICE}:${COMMIT_SHA}"

echo "=== Blue-Green Deploy: ${SERVICE} ==="

# 1. Deploy with no traffic
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --no-traffic \
  --tag "canary"

echo "Deployed canary. Running health check..."

# 2. Health check on canary
CANARY_URL=$(gcloud run services describe "${SERVICE}" \
  --region "${REGION}" --format 'value(status.url)' \
  | sed 's|https://|https://canary---|')

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${CANARY_URL}/health")
if [ "${HEALTH}" != "200" ]; then
  echo "FAIL: Health check returned ${HEALTH}. Aborting."
  exit 1
fi

# 3. Shift traffic: 10% → 50% → 100%
for pct in 10 50 100; do
  echo "Shifting ${pct}% traffic to canary..."
  gcloud run services update-traffic "${SERVICE}" \
    --region "${REGION}" \
    --to-tags "canary=${pct}"
  sleep 30
done

echo "Deploy complete. 100% traffic on new revision."
```

## Deployment Checklist

- [ ] Production secrets in secrets manager (not env files)
- [ ] Health check endpoint responds 200
- [ ] Readiness and liveness probes configured
- [ ] Resource limits set (CPU, memory)
- [ ] Min instances > 0 (avoid cold starts)
- [ ] Blue-green or canary deployment configured
- [ ] Rollback procedure documented
- [ ] Post-deploy smoke test automated

## Error Handling

| Issue | Solution |
|-------|----------|
| Secret not found | Verify secret name in secrets manager |
| Health check timeout | Increase initialDelaySeconds, check CIO connectivity |
| Cold start latency | Set `--min-instances 1` (Cloud Run) or keep-alive |
| Memory OOM | Increase memory limits, check for event queue buildup |

## Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Steps

After deployment, proceed to `customerio-webhooks-events` for webhook handling.
