# Juicebox Deploy Integration - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Configure Secret Management

#### AWS Secrets Manager
```bash
# Store API key
aws secretsmanager create-secret \
  --name juicebox/api-key \
  --secret-string '{"apiKey":"jb_prod_xxxx"}'
```

```typescript
// lib/secrets.ts
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

export async function getJuiceboxApiKey(): Promise<string> {
  const client = new SecretsManager({ region: process.env.AWS_REGION });
  const result = await client.getSecretValue({
    SecretId: 'juicebox/api-key'
  });
  return JSON.parse(result.SecretString!).apiKey;
}
```

#### Google Secret Manager
```bash
# Store API key
echo -n "jb_prod_xxxx" | gcloud secrets create juicebox-api-key --data-file=-
```

```typescript
// lib/secrets.ts
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

export async function getJuiceboxApiKey(): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/${process.env.GOOGLE_CLOUD_PROJECT}/secrets/juicebox-api-key/versions/latest`
  });
  return version.payload!.data!.toString();
}
```

### Step 2: Create Deployment Configuration

#### Docker Deployment
```dockerfile
# Dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/

# Don't include secrets in image
ENV JUICEBOX_API_KEY=""

CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - JUICEBOX_API_KEY=${JUICEBOX_API_KEY}
    secrets:
      - juicebox_api_key

secrets:
  juicebox_api_key:
    external: true
```

#### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juicebox-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: juicebox-app
  template:
    metadata:
      labels:
        app: juicebox-app
    spec:
      containers:
        - name: app
          image: your-registry/juicebox-app:latest
          env:
            - name: JUICEBOX_API_KEY
              valueFrom:
                secretKeyRef:
                  name: juicebox-secrets
                  key: api-key
          resources:
            limits:
              memory: "256Mi"
              cpu: "500m"
```

### Step 3: Configure Health Checks
```typescript
// routes/health.ts
import { Router } from 'express';
import { JuiceboxClient } from '@juicebox/sdk';

const router = Router();

router.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

router.get('/health/ready', async (req, res) => {
  try {
    const client = new JuiceboxClient({
      apiKey: process.env.JUICEBOX_API_KEY!
    });
    await client.auth.me();
    res.json({ status: 'ready', juicebox: 'connected' });
  } catch (error) {
    res.status(503).json({ status: 'not ready', error: error.message });
  }
});

export default router;
```

### Step 4: Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-staging}
VERSION=$(git rev-parse --short HEAD)

echo "Deploying version $VERSION to $ENVIRONMENT"

# Build
npm run build
docker build -t juicebox-app:$VERSION .

# Push to registry
docker tag juicebox-app:$VERSION your-registry/juicebox-app:$VERSION
docker push your-registry/juicebox-app:$VERSION

# Deploy
if [ "$ENVIRONMENT" == "production" ]; then
  kubectl set image deployment/juicebox-app \
    app=your-registry/juicebox-app:$VERSION \
    --namespace production
else
  kubectl set image deployment/juicebox-app \
    app=your-registry/juicebox-app:$VERSION \
    --namespace staging
fi

# Wait for rollout
kubectl rollout status deployment/juicebox-app --namespace $ENVIRONMENT

echo "Deployment complete"
```
