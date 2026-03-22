---
name: salesforce-deploy-integration
description: |
  Deploy Salesforce-connected applications to Heroku, Vercel, and Cloud Run with proper credential management.
  Use when deploying Salesforce-powered applications to production,
  configuring platform-specific secrets, or setting up Heroku Connect.
  Trigger with phrases like "deploy salesforce app", "salesforce Heroku",
  "salesforce production deploy", "salesforce Cloud Run", "Heroku Connect".
allowed-tools: Read, Write, Edit, Bash(heroku:*), Bash(vercel:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Deploy Integration

## Overview
Deploy Salesforce-connected Node.js applications to Heroku (native SF integration), Vercel, or Cloud Run with JWT authentication and proper secrets management.

## Prerequisites
- Salesforce Connected App with JWT Bearer flow
- RSA key pair for server-to-server auth
- Platform CLI installed (heroku, vercel, or gcloud)
- Application tested against sandbox

## Instructions

### Heroku Deployment (Recommended for Salesforce)

Heroku has native Salesforce integration via Heroku Connect (bi-directional data sync).

```bash
# Create Heroku app
heroku create my-sf-app

# Set Salesforce credentials as config vars
heroku config:set SF_LOGIN_URL=https://login.salesforce.com
heroku config:set SF_CLIENT_ID=3MVG9...
heroku config:set SF_USERNAME=integration@yourcompany.com
heroku config:set SF_JWT_KEY="$(cat server.key)"

# Deploy
git push heroku main

# Optional: Add Heroku Connect for bi-directional sync
heroku addons:create herokuconnect:demo
heroku connect:authorize
# Map sObjects: Account, Contact, Opportunity → Postgres tables
```

### Vercel Deployment (Serverless)

```bash
# Add Salesforce secrets
vercel env add SF_LOGIN_URL production
vercel env add SF_CLIENT_ID production
vercel env add SF_USERNAME production
vercel env add SF_JWT_KEY production  # Paste private key content

# Deploy
vercel --prod
```

```json
{
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

```typescript
// api/salesforce/accounts.ts — Vercel serverless function
import jsforce from 'jsforce';

export default async function handler(req, res) {
  const conn = new jsforce.Connection({
    loginUrl: process.env.SF_LOGIN_URL,
  });

  // JWT auth — no password needed
  await conn.authorize({
    grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
    client_id: process.env.SF_CLIENT_ID!,
    username: process.env.SF_USERNAME!,
    privateKey: process.env.SF_JWT_KEY!,
  });

  const accounts = await conn.query(
    'SELECT Id, Name, Industry FROM Account ORDER BY CreatedDate DESC LIMIT 10'
  );

  res.json({ accounts: accounts.records });
}
```

### Google Cloud Run

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["npm", "start"]
```

```bash
# Store JWT key in Secret Manager
echo -n "$(cat server.key)" | gcloud secrets create sf-jwt-key --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/sf-service

gcloud run deploy sf-service \
  --image gcr.io/$PROJECT_ID/sf-service \
  --region us-central1 \
  --platform managed \
  --set-env-vars SF_LOGIN_URL=https://login.salesforce.com \
  --set-env-vars SF_CLIENT_ID=3MVG9... \
  --set-env-vars SF_USERNAME=integration@yourcompany.com \
  --set-secrets=SF_JWT_KEY=sf-jwt-key:latest
```

### Health Check Pattern

```typescript
// health.ts — include in every deployment
export async function healthCheck() {
  const conn = new jsforce.Connection({ loginUrl: process.env.SF_LOGIN_URL });

  try {
    await conn.authorize({ /* JWT params */ });
    const limits = await conn.request('/services/data/v59.0/limits/');
    const apiRemaining = limits.DailyApiRequests.Remaining;

    return {
      status: apiRemaining > 1000 ? 'healthy' : 'degraded',
      salesforce: {
        connected: true,
        instance: conn.instanceUrl,
        apiRemaining,
      },
    };
  } catch (error: any) {
    return {
      status: 'unhealthy',
      salesforce: { connected: false, error: error.message },
    };
  }
}
```

## Output
- Application deployed to production platform
- JWT authentication configured (no passwords in config)
- Salesforce secrets stored in platform-native secrets manager
- Health check endpoint verifying Salesforce connectivity
- API limit monitoring active

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `INVALID_GRANT` on deploy | JWT key format issue | Ensure full private key including headers |
| Cold start timeout | Connection + auth on every request | Cache connection or use connection pooling |
| Health check fails | Wrong SF_LOGIN_URL | `login.salesforce.com` for prod, `test.salesforce.com` for sandbox |
| Secret not found | Wrong secret name | Verify with platform-specific secret list command |

## Resources
- [Heroku Connect](https://devcenter.heroku.com/articles/heroku-connect)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [JWT Bearer Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm)

## Next Steps
For event handling, see `salesforce-webhooks-events`.
