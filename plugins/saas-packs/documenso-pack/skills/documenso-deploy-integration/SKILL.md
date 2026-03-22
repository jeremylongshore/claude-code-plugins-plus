---
name: documenso-deploy-integration
description: |
  Deploy Documenso integrations across different platforms and environments.
  Use when deploying to cloud platforms, containerizing applications,
  or setting up infrastructure for Documenso integrations.
  Trigger with phrases like "deploy documenso", "documenso docker",
  "documenso kubernetes", "documenso cloud deployment".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, deployment, docker, kubernetes]

---
# Documenso Deploy Integration

## Overview

Deploy Documenso-integrated applications and self-hosted Documenso instances to Docker, Kubernetes, serverless, and cloud platforms. Covers both app deployment (your code that uses the Documenso API) and self-hosted Documenso deployment.

## Prerequisites

- Application ready for deployment
- Cloud platform account (AWS, GCP, Azure)
- Docker installed locally
- Completed `documenso-multi-env-setup`

## Instructions

### Step 1: Dockerize Your Documenso Integration

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json .
USER app
EXPOSE 3000
CMD ["node", "dist/server.js"]
# Note: DOCUMENSO_API_KEY injected at runtime, never baked into image
```

### Step 2: Self-Hosted Documenso (Docker Compose)

```yaml
# docker-compose.prod.yml
services:
  documenso:
    image: documenso/documenso:latest
    ports:
      - "3000:3000"
    environment:
      - NEXTAUTH_URL=https://sign.yourcompany.com
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}   # openssl rand -hex 32
      - NEXT_PRIVATE_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - NEXT_PRIVATE_ENCRYPTION_SECONDARY_KEY=${ENCRYPTION_SECONDARY_KEY}
      - NEXT_PUBLIC_WEBAPP_URL=https://sign.yourcompany.com
      - NEXT_PRIVATE_DATABASE_URL=postgresql://documenso:${DB_PASS}@db:5432/documenso
      - NEXT_PRIVATE_DIRECT_DATABASE_URL=postgresql://documenso:${DB_PASS}@db:5432/documenso
      # SMTP
      - NEXT_PRIVATE_SMTP_TRANSPORT=smtp-auth
      - NEXT_PRIVATE_SMTP_HOST=${SMTP_HOST}
      - NEXT_PRIVATE_SMTP_PORT=587
      - NEXT_PRIVATE_SMTP_USERNAME=${SMTP_USER}
      - NEXT_PRIVATE_SMTP_PASSWORD=${SMTP_PASS}
      - NEXT_PRIVATE_SMTP_FROM_ADDRESS=signing@yourcompany.com
      - NEXT_PRIVATE_SMTP_FROM_NAME=YourCompany Signing
      # Signing certificate
      - NEXT_PRIVATE_SIGNING_PASSPHRASE=${CERT_PASSPHRASE}
    volumes:
      - ./certs/signing-cert.p12:/opt/documenso/cert.p12:ro
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: documenso
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: documenso
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U documenso"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```

**Important notes:**
- Documenso container runs as non-root (UID 1001) -- ensure mounted files are readable
- Prisma migrations run automatically on container start
- Documents are stored in PostgreSQL by default (fine for small-to-medium deployments)
- Use a reverse proxy (nginx, Caddy, Traefik) for SSL termination

### Step 3: AWS Lambda (API Integration)

```typescript
// lambda/signing-handler.ts
import { Documenso } from "@documenso/sdk-typescript";
import { SecretsManager } from "@aws-sdk/client-secrets-manager";

const sm = new SecretsManager({ region: "us-east-1" });
let client: Documenso;

async function getClient(): Promise<Documenso> {
  if (!client) {
    const secret = await sm.getSecretValue({ SecretId: "documenso/api-key" });
    client = new Documenso({ apiKey: JSON.parse(secret.SecretString!).apiKey });
  }
  return client;
}

export async function handler(event: any) {
  const documenso = await getClient();
  const { title, signerEmail, signerName } = JSON.parse(event.body);

  const doc = await documenso.documents.createV0({ title });
  await documenso.documentsRecipients.createV0(doc.documentId, {
    email: signerEmail,
    name: signerName,
    role: "SIGNER",
  });
  await documenso.documents.sendV0(doc.documentId);

  return {
    statusCode: 200,
    body: JSON.stringify({ documentId: doc.documentId }),
  };
}
```

### Step 4: Google Cloud Run

```bash
# Store secret
echo -n "$DOCUMENSO_API_KEY" | gcloud secrets create documenso-api-key --data-file=-

# Deploy
gcloud run deploy signing-service \
  --image gcr.io/$PROJECT_ID/signing-service \
  --platform managed \
  --region us-central1 \
  --set-secrets DOCUMENSO_API_KEY=documenso-api-key:latest \
  --memory 256Mi \
  --timeout 30s
```

### Step 5: Health Check Endpoint

```typescript
// src/health.ts — include in every deployment
app.get("/health", async (req, res) => {
  try {
    const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
    await client.documents.findV0({ page: 1, perPage: 1 });
    res.json({ status: "healthy", service: "documenso" });
  } catch (err: any) {
    res.status(503).json({
      status: "unhealthy",
      service: "documenso",
      error: err.message,
    });
  }
});
```

## Deployment Checklist

- [ ] API keys stored in secret manager (not env files)
- [ ] Health check endpoint configured
- [ ] HTTPS enforced (required for webhooks)
- [ ] Self-hosted: signing certificate mounted
- [ ] Self-hosted: secrets generated with `openssl rand -hex 32`
- [ ] Reverse proxy handles SSL termination
- [ ] Container runs as non-root user
- [ ] Monitoring and alerting configured

## Error Handling

| Deployment Issue | Cause | Solution |
|-----------------|-------|----------|
| Container crash on start | Missing env vars | Check all required env vars are set |
| Health check fails | API key invalid | Verify secret manager value |
| Database connection refused | Wrong connection string | Check `NEXT_PRIVATE_DATABASE_URL` |
| Signing certificate error | Wrong passphrase or path | Verify mount path and `SIGNING_PASSPHRASE` |
| Emails not sending | SMTP misconfigured | Check host/port/credentials |

## Resources

- [Documenso Self-Hosting](https://docs.documenso.com/developers/self-hosting/how-to)
- [Self-Hosting Quick Start](https://docs.documenso.com/docs/self-hosting/getting-started/quick-start)
- [Docker README](https://github.com/documenso/documenso/blob/main/docker/README.md)
- [Tips & Common Pitfalls](https://docs.documenso.com/docs/self-hosting/getting-started/tips)

## Next Steps

For webhook configuration, see `documenso-webhooks-events`.
