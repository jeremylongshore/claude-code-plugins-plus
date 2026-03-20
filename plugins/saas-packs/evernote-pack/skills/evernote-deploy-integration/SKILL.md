---
name: evernote-deploy-integration
description: |
  Deploy Evernote integrations to production environments.
  Use when deploying to cloud platforms, configuring production,
  or setting up deployment pipelines.
  Trigger with phrases like "deploy evernote", "evernote production deploy",
  "release evernote", "evernote cloud deployment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Deploy Integration

## Overview
Deploy Evernote integrations to production environments including Docker containers, AWS ECS/Lambda, Google Cloud Run, and Kubernetes, with proper secrets management and health checks.

## Prerequisites
- CI/CD pipeline configured (see `evernote-ci-integration`)
- Production API credentials approved by Evernote
- Cloud platform account (AWS, GCP, or Azure)
- Docker installed for containerized deployments

## Instructions

### Step 1: Docker Deployment

Create a multi-stage Dockerfile that builds the app and produces a minimal production image. Set `NODE_ENV=production` and configure the Evernote SDK for production endpoints.

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
ENV NODE_ENV=production EVERNOTE_SANDBOX=false
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Step 2: Google Cloud Run Deployment

Deploy the Docker image to Cloud Run with secrets mounted from Secret Manager. Cloud Run scales to zero when idle, making it cost-effective for webhook receivers.

```bash
gcloud run deploy evernote-app \
  --image gcr.io/PROJECT/evernote-app:latest \
  --set-secrets EVERNOTE_CONSUMER_KEY=evernote-key:latest \
  --set-secrets EVERNOTE_CONSUMER_SECRET=evernote-secret:latest \
  --allow-unauthenticated \
  --region us-central1
```

### Step 3: AWS Lambda (Serverless)

Package the webhook handler as a Lambda function behind API Gateway. Use AWS Secrets Manager for credentials. Lambda is ideal for event-driven Evernote integrations (webhook processing, scheduled sync).

### Step 4: Kubernetes Deployment

Create a Deployment with ConfigMap for non-secret settings and Kubernetes Secrets for API credentials. Include liveness and readiness probes that verify Evernote API connectivity.

### Step 5: Deployment Verification

After deployment, verify: health check endpoint returns `connected`, a test note can be created and retrieved, webhook endpoint is reachable, and monitoring is reporting metrics.

For the full Dockerfile, Cloud Run config, Lambda handler, Kubernetes manifests, and deployment verification scripts, see [Implementation Guide](references/implementation-guide.md).

## Output
- Multi-stage Dockerfile for production builds
- Google Cloud Run deployment with Secret Manager integration
- AWS Lambda handler for serverless webhook processing
- Kubernetes Deployment, Service, and Secret manifests
- Deployment verification checklist and script

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid consumer key` in production | Using sandbox credentials | Verify `EVERNOTE_SANDBOX=false` and production key |
| Secret not mounted | Missing cloud secret resource | Create secret in Secret Manager/AWS Secrets Manager |
| Health check failing | Evernote API unreachable from cloud | Check network/firewall rules, verify DNS resolution |
| Cold start timeout | Lambda initialization too slow | Increase timeout, use provisioned concurrency |

## Resources
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)

## Next Steps
For webhook handling, see `evernote-webhooks-events`.

## Examples

**Cloud Run webhook**: Deploy a webhook receiver to Cloud Run that processes Evernote note change notifications, syncs changes to a database, and scales to zero between events.

**Lambda batch processor**: Deploy a scheduled Lambda that runs nightly to export all notes tagged "archive" to S3, using the sync API to fetch only changed notes since the last run.
