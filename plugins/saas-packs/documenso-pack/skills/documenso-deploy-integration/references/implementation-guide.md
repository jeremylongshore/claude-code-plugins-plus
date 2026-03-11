# Documenso Deploy Integration - Implementation Guide

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Build the application
FROM base AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 appuser

# Copy built assets
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json

USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  signing-service:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DOCUMENSO_API_KEY=${DOCUMENSO_API_KEY}
      - DOCUMENSO_BASE_URL=${DOCUMENSO_BASE_URL:-https://app.documenso.com/api/v2/}
      - DOCUMENSO_WEBHOOK_SECRET=${DOCUMENSO_WEBHOOK_SECRET}
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis-data:
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: signing-service
  labels:
    app: signing-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: signing-service
  template:
    metadata:
      labels:
        app: signing-service
    spec:
      containers:
        - name: signing-service
          image: your-registry/signing-service:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: "production"
            - name: DOCUMENSO_API_KEY
              valueFrom:
                secretKeyRef:
                  name: documenso-secrets
                  key: api-key
            - name: DOCUMENSO_WEBHOOK_SECRET
              valueFrom:
                secretKeyRef:
                  name: documenso-secrets
                  key: webhook-secret
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
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
      imagePullSecrets:
        - name: registry-credentials
```

### Service & Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: signing-service
spec:
  selector:
    app: signing-service
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: signing-service
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - signing.yourapp.com
      secretName: signing-tls
  rules:
    - host: signing.yourapp.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: signing-service
                port:
                  number: 80
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: documenso-secrets
type: Opaque
stringData:
  api-key: ${DOCUMENSO_API_KEY}
  webhook-secret: ${DOCUMENSO_WEBHOOK_SECRET}
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: signing-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: signing-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## AWS Lambda Deployment

```typescript
// handler.ts
import { Documenso } from "@documenso/sdk-typescript";
import { APIGatewayProxyHandler } from "aws-lambda";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

export const createDocument: APIGatewayProxyHandler = async (event) => {
  try {
    const body = JSON.parse(event.body ?? "{}");

    const doc = await documenso.documents.createV0({
      title: body.title,
    });

    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documentId: doc.documentId }),
    };
  } catch (error: any) {
    return {
      statusCode: error.statusCode ?? 500,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ error: error.message }),
    };
  }
};

export const webhookHandler: APIGatewayProxyHandler = async (event) => {
  const secret = event.headers["x-documenso-secret"];
  if (secret !== process.env.DOCUMENSO_WEBHOOK_SECRET) {
    return { statusCode: 401, body: "Unauthorized" };
  }

  const payload = JSON.parse(event.body ?? "{}");
  console.log("Webhook received:", payload.event);

  // Process webhook...

  return { statusCode: 200, body: JSON.stringify({ received: true }) };
};
```

### SAM Template

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    Runtime: nodejs20.x
    Environment:
      Variables:
        DOCUMENSO_API_KEY: !Ref DocumensoApiKey
        DOCUMENSO_WEBHOOK_SECRET: !Ref DocumensoWebhookSecret

Parameters:
  DocumensoApiKey:
    Type: AWS::SSM::Parameter::Value<String>
    Default: /signing-service/documenso-api-key
  DocumensoWebhookSecret:
    Type: AWS::SSM::Parameter::Value<String>
    Default: /signing-service/documenso-webhook-secret

Resources:
  CreateDocumentFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: dist/
      Handler: handler.createDocument
      Events:
        Api:
          Type: Api
          Properties:
            Path: /documents
            Method: post

  WebhookFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: dist/
      Handler: handler.webhookHandler
      Events:
        Api:
          Type: Api
          Properties:
            Path: /webhooks/documenso
            Method: post
```

## Google Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/signing-service:$COMMIT_SHA', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/signing-service:$COMMIT_SHA']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'signing-service'
      - '--image=gcr.io/$PROJECT_ID/signing-service:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--set-env-vars=NODE_ENV=production'
      - '--set-secrets=DOCUMENSO_API_KEY=documenso-api-key:latest,DOCUMENSO_WEBHOOK_SECRET=documenso-webhook-secret:latest'
      - '--min-instances=1'
      - '--max-instances=10'

images:
  - 'gcr.io/$PROJECT_ID/signing-service:$COMMIT_SHA'
```

## Environment Configuration

```typescript
// src/config.ts
interface Config {
  nodeEnv: string;
  port: number;
  documenso: {
    apiKey: string;
    baseUrl: string;
    webhookSecret: string;
  };
}

export function loadConfig(): Config {
  const config: Config = {
    nodeEnv: process.env.NODE_ENV ?? "development",
    port: parseInt(process.env.PORT ?? "3000"),
    documenso: {
      apiKey: requireEnv("DOCUMENSO_API_KEY"),
      baseUrl:
        process.env.DOCUMENSO_BASE_URL ??
        "https://app.documenso.com/api/v2/",
      webhookSecret: process.env.DOCUMENSO_WEBHOOK_SECRET ?? "",
    },
  };

  return config;
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}
```
