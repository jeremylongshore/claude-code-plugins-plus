# Deepgram Deploy Integration - Implementation Details

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for the complete deployment configurations.

## Dockerfile
```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 deepgram
USER deepgram
COPY --from=builder --chown=deepgram:nodejs /app/dist ./dist
COPY --from=builder --chown=deepgram:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=deepgram:nodejs /app/package.json ./
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

## Docker Compose
```yaml
version: '3.8'
services:
  deepgram-service:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
    secrets:
      - deepgram_key
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
secrets:
  deepgram_key:
    file: ./secrets/deepgram-api-key.txt
volumes:
  redis-data:
```

## Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deepgram-service
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
              value: "production"
            - name: DEEPGRAM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: deepgram-secrets
                  key: api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: deepgram-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: deepgram-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## AWS Lambda (Serverless)
```yaml
service: deepgram-transcription
provider:
  name: aws
  runtime: nodejs20.x
  memorySize: 512
  timeout: 30
functions:
  transcribe:
    handler: dist/handlers/transcribe.handler
    events:
      - http:
          path: /transcribe
          method: post
          cors: true
  transcribeAsync:
    handler: dist/handlers/transcribe-async.handler
    events:
      - sqs:
          arn: !GetAtt TranscriptionQueue.Arn
    timeout: 300
    reservedConcurrency: 10
```

## Lambda Handler
```typescript
import { APIGatewayProxyHandler } from 'aws-lambda';
import { SecretsManager } from '@aws-sdk/client-secrets-manager';
import { createClient } from '@deepgram/sdk';

const secretsManager = new SecretsManager({});
let deepgramKey: string | null = null;

async function getApiKey(): Promise<string> {
  if (deepgramKey) return deepgramKey;
  const { SecretString } = await secretsManager.getSecretValue({
    SecretId: process.env.DEEPGRAM_SECRET_ARN!,
  });
  deepgramKey = JSON.parse(SecretString!).apiKey;
  return deepgramKey!;
}

export const handler: APIGatewayProxyHandler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    const { audioUrl, options = {} } = body;
    if (!audioUrl) return { statusCode: 400, body: JSON.stringify({ error: 'audioUrl required' }) };

    const apiKey = await getApiKey();
    const client = createClient(apiKey);
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: 'nova-2', smart_format: true, ...options }
    );

    if (error) return { statusCode: 500, body: JSON.stringify({ error: error.message }) };
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript: result.results.channels[0].alternatives[0].transcript,
        metadata: result.metadata,
      }),
    };
  } catch (err) {
    return { statusCode: 500, body: JSON.stringify({ error: 'Internal server error' }) };
  }
};
```

## Google Cloud Run & Vercel Deployment
See the Google Cloud Build and Vercel edge function configurations in the full deployment guide.

## Deploy Script
```bash
#!/bin/bash
set -e
ENVIRONMENT=$1
if [ -z "$ENVIRONMENT" ]; then
  echo "Usage: ./deploy.sh <staging|production>"
  exit 1
fi
echo "Deploying to $ENVIRONMENT..."
npm run build
npm test
case $ENVIRONMENT in
  staging) kubectl apply -f k8s/staging/ && kubectl rollout status deployment/deepgram-service -n staging ;;
  production) kubectl apply -f k8s/production/ && kubectl rollout status deployment/deepgram-service -n production ;;
  *) echo "Unknown environment: $ENVIRONMENT"; exit 1 ;;
esac
npm run smoke-test
echo "Deployment complete!"
```
