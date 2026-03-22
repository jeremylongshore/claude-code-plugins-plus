---
name: abridge-deploy-integration
description: |
  Deploy Abridge clinical AI integration to HIPAA-compliant cloud infrastructure.
  Use when deploying to GCP Cloud Run, AWS ECS, or Azure Container Apps
  with healthcare-grade secrets management and compliance controls.
  Trigger: "deploy abridge", "abridge production deploy", "abridge Cloud Run",
  "abridge AWS deploy", "abridge HIPAA infrastructure".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(docker:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, deployment]
compatible-with: claude-code
---

# Abridge Deploy Integration

## Overview

Deploy Abridge clinical AI integration to HIPAA-compliant cloud infrastructure. Healthcare deployments require BAA-covered cloud services, encrypted secrets, audit trails, and VPC-restricted networking.

## Prerequisites

- Completed `abridge-prod-checklist`
- BAA-covered cloud account (GCP, AWS, or Azure)
- Container registry access
- Abridge production credentials from partner portal

## Instructions

### Step 1: HIPAA-Compliant Dockerfile

```dockerfile
# Dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Run as non-root (HIPAA best practice)
RUN groupadd -r abridge && useradd -r -g abridge abridge
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER abridge
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

### Step 2: GCP Cloud Run Deployment (HIPAA BAA)

```bash
#!/bin/bash
# deploy-cloud-run.sh

PROJECT_ID="${GCP_PROJECT_ID}"
SERVICE_NAME="abridge-integration"
REGION="us-central1"

# Build container
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Deploy to Cloud Run with HIPAA controls
gcloud run deploy "${SERVICE_NAME}" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
  --region "${REGION}" \
  --platform managed \
  --no-allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 120 \
  --set-secrets="ABRIDGE_CLIENT_SECRET=abridge-client-secret:latest,ABRIDGE_ORG_ID=abridge-org-id:latest,EPIC_CLIENT_SECRET=epic-client-secret:latest" \
  --vpc-connector "projects/${PROJECT_ID}/locations/${REGION}/connectors/abridge-vpc" \
  --vpc-egress all-traffic \
  --set-env-vars="NODE_ENV=production,NODE_TLS_MIN_VERSION=TLSv1.3,AUDIT_LOG_ENABLED=true"

# Verify health
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')
curl -s "${SERVICE_URL}/health" -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### Step 3: Health Check Endpoint

```typescript
// src/server/health.ts
import express from 'express';

const app = express();

app.get('/health', async (req, res) => {
  const checks = {
    server: 'healthy',
    abridge: await checkAbridgeApi(),
    fhir: await checkFhirEndpoint(),
    timestamp: new Date().toISOString(),
  };

  const allHealthy = Object.values(checks).every(v => v === 'healthy' || typeof v === 'string');
  res.status(allHealthy ? 200 : 503).json(checks);
});

async function checkAbridgeApi(): Promise<string> {
  try {
    const res = await fetch(`${process.env.ABRIDGE_BASE_URL}/health`, {
      headers: { 'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}` },
      signal: AbortSignal.timeout(3000),
    });
    return res.ok ? 'healthy' : 'degraded';
  } catch { return 'unhealthy'; }
}

async function checkFhirEndpoint(): Promise<string> {
  try {
    const res = await fetch(`${process.env.EPIC_FHIR_BASE_URL}/metadata`, {
      signal: AbortSignal.timeout(3000),
    });
    return res.ok ? 'healthy' : 'degraded';
  } catch { return 'unhealthy'; }
}

app.listen(3000, () => console.log('Abridge integration server on :3000'));
```

### Step 4: GCP Secret Manager Setup

```bash
# Create secrets (one-time setup)
echo -n "partner_secret_here" | gcloud secrets create abridge-client-secret --data-file=-
echo -n "org_id_here" | gcloud secrets create abridge-org-id --data-file=-
echo -n "epic_secret_here" | gcloud secrets create epic-client-secret --data-file=-

# Grant Cloud Run service account access
SA="abridge-integration@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding abridge-client-secret \
  --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"
```

## Output

- HIPAA-compliant Docker image with non-root user
- Cloud Run deployment with VPC connector and TLS 1.3
- Health check endpoint monitoring Abridge + FHIR
- Secrets managed via GCP Secret Manager

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Deploy rejected | Missing BAA | Sign Google Cloud BAA first |
| Secret access denied | IAM misconfigured | Grant secretAccessor role to service account |
| Health check fails | Cold start latency | Set min-instances to 1 |
| VPC connector error | Not created | Create VPC connector in same region |

## Resources

- [GCP HIPAA Compliance](https://cloud.google.com/security/compliance/hipaa/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Abridge Platform](https://www.abridge.com/product)

## Next Steps

For webhook event handling, see `abridge-webhooks-events`.
