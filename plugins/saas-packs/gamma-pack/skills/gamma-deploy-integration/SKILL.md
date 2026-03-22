---
name: gamma-deploy-integration
description: |
  Deploy Gamma-integrated applications to production environments.
  Use when deploying to Vercel, AWS, GCP, or other cloud platforms
  with proper secret management and configuration.
  Trigger with phrases like "gamma deploy", "gamma production",
  "gamma vercel", "gamma AWS", "gamma cloud deployment".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(aws:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, deployment]

---
# Gamma Deploy Integration

## Overview
Deploy Gamma-integrated applications to various cloud platforms with proper configuration and secret management.

## Prerequisites
- Completed CI integration
- Cloud platform account (Vercel, AWS, or GCP)
- Production Gamma API key

## Instructions

### Vercel Deployment

#### Step 1: Configure Vercel Project
```bash
set -euo pipefail
# Install Vercel CLI
npm i -g vercel

# Link project
vercel link

# Set environment variable
vercel env add GAMMA_API_KEY production
```

#### Step 2: Create vercel.json
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "env": {
    "GAMMA_API_KEY": "@gamma_api_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

#### Step 3: Deploy
```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

### AWS Lambda Deployment

#### Step 1: Store Secret in AWS Secrets Manager
```bash
aws secretsmanager create-secret \
  --name gamma/api-key \
  --secret-string '{"apiKey":"your-gamma-api-key"}'
```

#### Step 2: Lambda Configuration
```typescript
// lambda/gamma-handler.ts
import { SecretsManager } from '@aws-sdk/client-secrets-manager';
import { GammaClient } from '@gamma/sdk';

const secretsManager = new SecretsManager({ region: 'us-east-1' });
let gamma: GammaClient;

async function getGammaClient() {
  if (!gamma) {
    const secret = await secretsManager.getSecretValue({
      SecretId: 'gamma/api-key',
    });
    const { apiKey } = JSON.parse(secret.SecretString!);
    gamma = new GammaClient({ apiKey });
  }
  return gamma;
}

export async function handler(event: any) {
  const client = await getGammaClient();
  const result = await client.presentations.create({
    title: event.title,
    prompt: event.prompt,
  });
  return { statusCode: 200, body: JSON.stringify(result) };  # HTTP 200 OK
}
```

#### Step 3: SAM Template
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'  # 2010 = configured value
Transform: AWS::Serverless-2016-10-31  # 2016 = configured value

Resources:
  GammaFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: dist/gamma-handler.handler
      Runtime: nodejs20.x
      Timeout: 30
      MemorySize: 256  # 256 bytes
      Policies:
        - SecretsManagerReadWrite
      Environment:
        Variables:
          NODE_ENV: production
```

### Google Cloud Run Deployment

#### Step 1: Store Secret
```bash
echo -n "your-gamma-api-key" | \
  gcloud secrets create gamma-api-key --data-file=-
```

#### Step 2: Dockerfile
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
CMD ["node", "dist/server.js"]
```

#### Step 3: Deploy
```bash
set -euo pipefail
gcloud run deploy gamma-service \
  --image gcr.io/$PROJECT_ID/gamma-service \
  --platform managed \
  --region us-central1 \
  --set-secrets GAMMA_API_KEY=gamma-api-key:latest \
  --allow-unauthenticated
```

### GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm ci && npm run build

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

## Output
- Production deployment on chosen platform
- Secrets securely stored
- Environment variables configured
- Automated deployment pipeline

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing secret | Create secret in platform |
| Timeout | Function too slow | Increase timeout limit |
| Cold start | Lambda initialization | Use provisioned concurrency |
| Permission denied | IAM misconfigured | Update IAM policies |

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Google Cloud Run](https://cloud.google.com/run/docs)

## Next Steps

Proceed to `gamma-webhooks-events` for event handling.