---
name: snowflake-deploy-integration
description: |
  Deploy Snowflake-powered applications with proper connection management and secrets.
  Use when deploying apps that query Snowflake, configuring connection pools
  for serverless/container platforms, or managing Snowflake credentials in production.
  Trigger with phrases like "deploy snowflake", "snowflake serverless",
  "snowflake production deploy", "snowflake Cloud Run", "snowflake Lambda".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(aws:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Deploy Integration

## Overview

Deploy applications that connect to Snowflake on serverless platforms, containers, and VMs with proper connection lifecycle management.

## Prerequisites

- Snowflake service account with key pair auth
- Platform CLI installed (gcloud, aws, docker)
- Application tested against staging Snowflake

## Instructions

### Step 1: Connection Management for Serverless

```typescript
// src/snowflake/serverless-connection.ts
import snowflake from 'snowflake-sdk';

let cachedConnection: snowflake.Connection | null = null;

/**
 * Reuse connection across Lambda/Cloud Function invocations.
 * Serverless containers may be reused — avoid reconnecting every call.
 */
export async function getConnection(): Promise<snowflake.Connection> {
  if (cachedConnection?.isUp()) {
    return cachedConnection;
  }

  const conn = snowflake.createConnection({
    account: process.env.SNOWFLAKE_ACCOUNT!,
    username: process.env.SNOWFLAKE_USER!,
    authenticator: 'SNOWFLAKE_JWT',
    privateKey: process.env.SNOWFLAKE_PRIVATE_KEY!,
    warehouse: process.env.SNOWFLAKE_WAREHOUSE!,
    database: process.env.SNOWFLAKE_DATABASE!,
    schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC',
    clientSessionKeepAlive: true,  // Keep session alive between invocations
  });

  await new Promise<void>((resolve, reject) => {
    conn.connect((err) => (err ? reject(err) : resolve()));
  });

  cachedConnection = conn;
  return conn;
}
```

### Step 2: Google Cloud Run Deployment

```dockerfile
# Dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
ENV NODE_ENV=production
CMD ["node", "dist/index.js"]
```

```bash
#!/bin/bash
# deploy-cloud-run.sh
PROJECT_ID="${GCP_PROJECT_ID}"
SERVICE_NAME="snowflake-api"
REGION="us-central1"

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy with Snowflake credentials from Secret Manager
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --set-secrets="SNOWFLAKE_ACCOUNT=snowflake-account:latest,\
SNOWFLAKE_USER=snowflake-user:latest,\
SNOWFLAKE_PRIVATE_KEY=snowflake-private-key:latest" \
  --set-env-vars="SNOWFLAKE_WAREHOUSE=PROD_ANALYTICS_WH,\
SNOWFLAKE_DATABASE=PROD_DB,\
SNOWFLAKE_SCHEMA=PUBLIC" \
  --min-instances=1 \
  --max-instances=10 \
  --timeout=300
```

### Step 3: AWS Lambda Deployment

```typescript
// lambda/handler.ts
import { getConnection } from './snowflake/serverless-connection';

export async function handler(event: any) {
  try {
    const conn = await getConnection();
    const rows = await new Promise<any[]>((resolve, reject) => {
      conn.execute({
        sqlText: 'SELECT COUNT(*) AS total FROM orders WHERE order_date = CURRENT_DATE()',
        complete: (err, stmt, rows) => (err ? reject(err) : resolve(rows || [])),
      });
    });
    return { statusCode: 200, body: JSON.stringify(rows[0]) };
  } catch (error: any) {
    return { statusCode: 500, body: JSON.stringify({ error: error.message }) };
  }
}
```

```bash
# Store Snowflake private key in AWS Secrets Manager
aws secretsmanager create-secret \
  --name snowflake/prod/private-key \
  --secret-string "$(cat rsa_key.p8)"

# Lambda environment variables
aws lambda update-function-configuration \
  --function-name snowflake-api \
  --environment "Variables={
    SNOWFLAKE_ACCOUNT=myorg-myaccount,
    SNOWFLAKE_USER=svc_lambda,
    SNOWFLAKE_WAREHOUSE=PROD_ANALYTICS_WH,
    SNOWFLAKE_DATABASE=PROD_DB
  }" \
  --timeout 300
```

### Step 4: Docker Compose for Self-Hosted

```yaml
# docker-compose.yml
services:
  snowflake-app:
    build: .
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PRIVATE_KEY_PATH=/run/secrets/snowflake_key
      - SNOWFLAKE_WAREHOUSE=PROD_ANALYTICS_WH
      - SNOWFLAKE_DATABASE=PROD_DB
    secrets:
      - snowflake_key
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

secrets:
  snowflake_key:
    file: ./rsa_key.p8  # Never commit this file
```

### Step 5: Health Check Endpoint

```typescript
// src/health.ts
import { getConnection } from './snowflake/serverless-connection';

export async function healthCheck() {
  const start = Date.now();
  try {
    const conn = await getConnection();
    const rows = await new Promise<any[]>((resolve, reject) => {
      conn.execute({
        sqlText: 'SELECT 1 AS health_check',
        complete: (err, _, rows) => (err ? reject(err) : resolve(rows || [])),
      });
    });
    return {
      status: 'healthy',
      snowflake: { connected: true, latencyMs: Date.now() - start },
    };
  } catch (error: any) {
    return {
      status: 'degraded',
      snowflake: { connected: false, error: error.message, latencyMs: Date.now() - start },
    };
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start timeout | Warehouse resuming | Set `min-instances=1` or pre-warm warehouse |
| Connection refused in container | Wrong network config | Check DNS resolution for `*.snowflakecomputing.com` |
| Secret not found | Missing secret binding | Verify secret manager config |
| `privateKey` format error | Key has headers/newlines | Strip PEM headers or use file path |
| Session expired | Long-running serverless | Set `clientSessionKeepAlive: true` |

## Resources

- [Node.js Connection Options](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-options)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda/latest/dg/)

## Next Steps

For event-driven patterns, see `snowflake-webhooks-events`.
