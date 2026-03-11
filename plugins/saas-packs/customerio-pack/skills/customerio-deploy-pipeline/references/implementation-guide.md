# Customer.io Deploy Pipeline - Implementation Guide

### Step 1: Google Cloud Run Deployment
```yaml
# .github/workflows/deploy-cloud-run.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  SERVICE_NAME: customerio-service

jobs:
  deploy:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev

      - name: Build and Push
        run: |
          docker build -t ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/services/${{ env.SERVICE_NAME }}:${{ github.sha }} .
          docker push ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/services/${{ env.SERVICE_NAME }}:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --image ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/services/${{ env.SERVICE_NAME }}:${{ github.sha }} \
            --region ${{ env.REGION }} \
            --platform managed \
            --set-secrets CUSTOMERIO_SITE_ID=customerio-site-id:latest,CUSTOMERIO_API_KEY=customerio-api-key:latest \
            --allow-unauthenticated
```

### Step 2: Vercel Deployment
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "CUSTOMERIO_SITE_ID": "@customerio-site-id",
    "CUSTOMERIO_API_KEY": "@customerio-api-key"
  },
  "functions": {
    "api/**/*.ts": {
      "memory": 256,
      "maxDuration": 10
    }
  }
}
```

```typescript
// api/customerio/identify.ts
import { TrackClient, RegionUS } from '@customerio/track';
import type { VercelRequest, VercelResponse } from '@vercel/node';

const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionUS }
);

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { userId, attributes } = req.body;
    await client.identify(userId, attributes);
    res.status(200).json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
}
```

### Step 3: AWS Lambda Deployment
```yaml
# serverless.yml
service: customerio-integration

provider:
  name: aws
  runtime: nodejs20.x
  region: us-east-1
  environment:
    CUSTOMERIO_SITE_ID: ${ssm:/customerio/site-id}
    CUSTOMERIO_API_KEY: ${ssm:/customerio/api-key}

functions:
  identify:
    handler: src/handlers/identify.handler
    events:
      - http:
          path: /identify
          method: post

  track:
    handler: src/handlers/track.handler
    events:
      - http:
          path: /track
          method: post

  webhook:
    handler: src/handlers/webhook.handler
    events:
      - http:
          path: /webhook
          method: post
```

```typescript
// src/handlers/identify.ts
import { APIGatewayProxyHandler } from 'aws-lambda';
import { TrackClient, RegionUS } from '@customerio/track';

const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionUS }
);

export const handler: APIGatewayProxyHandler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    await client.identify(body.userId, body.attributes);

    return {
      statusCode: 200,
      body: JSON.stringify({ success: true })
    };
  } catch (error: any) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
```

### Step 4: Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customerio-service
  labels:
    app: customerio-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: customerio-service
  template:
    metadata:
      labels:
        app: customerio-service
    spec:
      containers:
        - name: customerio-service
          image: gcr.io/PROJECT_ID/customerio-service:latest
          ports:
            - containerPort: 8080
          env:
            - name: CUSTOMERIO_SITE_ID
              valueFrom:
                secretKeyRef:
                  name: customerio-secrets
                  key: site-id
            - name: CUSTOMERIO_API_KEY
              valueFrom:
                secretKeyRef:
                  name: customerio-secrets
                  key: api-key
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
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
      targetPort: 8080
  type: ClusterIP
```

### Step 5: Health Check Endpoint
```typescript
// src/health.ts
import { TrackClient, RegionUS } from '@customerio/track';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    customerio: { status: string; latency?: number };
    database?: { status: string; latency?: number };
  };
  version: string;
  uptime: number;
}

const startTime = Date.now();

export async function healthCheck(): Promise<HealthStatus> {
  const checks: HealthStatus['checks'] = {
    customerio: { status: 'unknown' }
  };

  // Check Customer.io connectivity
  try {
    const start = Date.now();
    const client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );

    await client.identify('health-check', { _health_check: true });
    checks.customerio = {
      status: 'healthy',
      latency: Date.now() - start
    };
  } catch (error) {
    checks.customerio = { status: 'unhealthy' };
  }

  const allHealthy = Object.values(checks).every(c => c.status === 'healthy');

  return {
    status: allHealthy ? 'healthy' : 'degraded',
    checks,
    version: process.env.APP_VERSION || '1.0.0',
    uptime: Date.now() - startTime
  };
}
```

### Step 6: Blue-Green Deployment
```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

set -e

CURRENT=$(gcloud run services describe customerio-service --region=us-central1 --format='value(status.traffic[0].revisionName)')
NEW_TAG="v$(date +%Y%m%d%H%M%S)"

echo "Current revision: $CURRENT"
echo "Deploying new revision: $NEW_TAG"

# Deploy new revision with no traffic
gcloud run deploy customerio-service \
  --image gcr.io/$PROJECT_ID/customerio-service:$NEW_TAG \
  --region us-central1 \
  --no-traffic

# Run smoke tests against new revision
NEW_URL=$(gcloud run services describe customerio-service --region=us-central1 --format='value(status.url)')
if ! curl -s "$NEW_URL/health" | grep -q '"status":"healthy"'; then
  echo "Health check failed, rolling back"
  exit 1
fi

# Gradually shift traffic
echo "Shifting 10% traffic to new revision"
gcloud run services update-traffic customerio-service \
  --region us-central1 \
  --to-revisions LATEST=10

sleep 60

echo "Shifting 50% traffic"
gcloud run services update-traffic customerio-service \
  --region us-central1 \
  --to-revisions LATEST=50

sleep 60

echo "Shifting 100% traffic"
gcloud run services update-traffic customerio-service \
  --region us-central1 \
  --to-revisions LATEST=100

echo "Deployment complete"
```
