---
name: deepgram-deploy-integration
description: |
  Deploy Deepgram integrations to production environments.
  Use when deploying to cloud platforms, configuring containers,
  or setting up Deepgram in Docker/Kubernetes/serverless.
  Trigger: "deploy deepgram", "deepgram docker", "deepgram kubernetes",
  "deepgram production deploy", "deepgram cloud run", "deepgram lambda".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, deployment, docker, kubernetes, serverless]

---
# Deepgram Deploy Integration

## Overview
Deploy Deepgram transcription services to Docker, Kubernetes, AWS Lambda, and Google Cloud Run. Includes production Dockerfile, K8s manifests with secret management, serverless handlers for event-driven transcription, and health check patterns.

## Prerequisites
- Working Deepgram integration (tested locally)
- Production API key in secret manager
- Container registry access (Docker Hub, ECR, GCR)
- Target platform CLI installed

## Instructions

### Step 1: Production Dockerfile

```dockerfile
# Multi-stage build for minimal production image
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-alpine AS runtime

# Security: non-root user
RUN addgroup -g 1001 -S app && adduser -S app -u 1001
WORKDIR /app

# Production dependencies only
COPY package*.json ./
RUN npm ci --production && npm cache clean --force

# Copy built application
COPY --from=builder /app/dist ./dist

# Health check (tests Deepgram connectivity)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget -q --spider http://localhost:3000/health || exit 1

USER app
EXPOSE 3000

CMD ["node", "dist/server.js"]
```

### Step 2: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  deepgram-service:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - DEEPGRAM_MODEL=nova-3
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### Step 3: Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deepgram-service
  labels:
    app: deepgram-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deepgram-service
  template:
    metadata:
      labels:
        app: deepgram-service
    spec:
      containers:
        - name: deepgram-service
          image: your-registry/deepgram-service:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: production
            - name: DEEPGRAM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: deepgram-secrets
                  key: api-key
            - name: DEEPGRAM_MODEL
              value: nova-3
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: deepgram-service
spec:
  selector:
    app: deepgram-service
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: deepgram-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: deepgram-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

```bash
# Create secret
kubectl create secret generic deepgram-secrets \
  --from-literal=api-key=$DEEPGRAM_API_KEY

# Deploy
kubectl apply -f k8s/
```

### Step 4: AWS Lambda Handler

```typescript
// lambda/handler.ts
import { createClient } from '@deepgram/sdk';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import type { S3Event } from 'aws-lambda';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
const s3 = new S3Client({});

// Trigger: S3 upload of audio file -> Lambda -> Deepgram -> Store result
export async function handler(event: S3Event) {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key);

    console.log(`Processing: s3://${bucket}/${key}`);

    // Get audio from S3
    const { Body } = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    const audio = Buffer.from(await Body!.transformToByteArray());

    // Transcribe
    const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
      audio,
      {
        model: 'nova-3',
        smart_format: true,
        diarize: true,
        utterances: true,
      }
    );

    if (error) {
      console.error(`Transcription failed for ${key}:`, error.message);
      throw error;
    }

    console.log(`Transcribed ${key}: ${result.metadata.duration}s, ` +
      `${result.results.channels[0].alternatives[0].words?.length} words`);

    return {
      statusCode: 200,
      body: JSON.stringify({
        file: key,
        duration: result.metadata.duration,
        transcript: result.results.channels[0].alternatives[0].transcript,
        request_id: result.metadata.request_id,
      }),
    };
  }
}
```

### Step 5: Google Cloud Run

```typescript
// server.ts — Cloud Run entry point
import express from 'express';
import { createClient } from '@deepgram/sdk';

const app = express();
app.use(express.json({ limit: '50mb' }));

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

app.post('/transcribe', async (req, res) => {
  try {
    const { url, model = 'nova-3', diarize = false } = req.body;

    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      { url },
      { model, smart_format: true, diarize }
    );

    if (error) return res.status(502).json({ error: error.message });

    res.json({
      transcript: result.results.channels[0].alternatives[0].transcript,
      confidence: result.results.channels[0].alternatives[0].confidence,
      duration: result.metadata.duration,
      request_id: result.metadata.request_id,
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/health', async (req, res) => {
  try {
    const { error } = await deepgram.manage.getProjects();
    res.json({ status: error ? 'degraded' : 'healthy' });
  } catch {
    res.status(503).json({ status: 'unhealthy' });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Listening on port ${port}`));
```

```bash
# Deploy to Cloud Run
gcloud run deploy deepgram-service \
  --source . \
  --set-env-vars DEEPGRAM_API_KEY=$(gcloud secrets versions access latest --secret deepgram-key) \
  --memory 512Mi \
  --timeout 300 \
  --concurrency 50 \
  --min-instances 1 \
  --max-instances 10
```

### Step 6: Deploy Script

```bash
#!/bin/bash
set -euo pipefail

ENV="${1:?Usage: deploy.sh <staging|production>}"

echo "Deploying to $ENV..."

# Build
npm ci && npm run build && npm test

# Build container
docker build -t deepgram-service:$ENV .

# Deploy based on target
case $ENV in
  staging)
    kubectl --context staging apply -f k8s/
    kubectl --context staging rollout status deployment/deepgram-service
    ;;
  production)
    kubectl --context production apply -f k8s/
    kubectl --context production rollout status deployment/deepgram-service
    ;;
esac

# Post-deploy smoke test
echo "Running smoke test..."
ENDPOINT=$(kubectl get svc deepgram-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -sf "http://$ENDPOINT/health" || { echo "SMOKE TEST FAILED"; exit 1; }
echo "Deploy successful."
```

## Output
- Production Dockerfile (multi-stage, non-root, health check)
- Docker Compose with Redis for caching
- Kubernetes manifests (Deployment, Service, HPA, Secret)
- AWS Lambda handler (S3 trigger -> Deepgram -> result)
- Cloud Run service with health check
- Environment-aware deploy script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Container OOM | Memory limit too low | Increase to 512Mi+ |
| Health check failing | Service not ready yet | Increase `initialDelaySeconds` |
| Lambda timeout | Audio too long | Increase timeout to 300s, or use callback |
| Cloud Run 429 | Too many concurrent requests | Decrease `--concurrency` flag |
| Secret not found | K8s secret missing | Create secret before deploying |

## Resources
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [AWS Lambda Node.js](https://docs.aws.amazon.com/lambda/latest/dg/lambda-nodejs.html)
- [Cloud Run Quickstart](https://cloud.google.com/run/docs/quickstarts)
