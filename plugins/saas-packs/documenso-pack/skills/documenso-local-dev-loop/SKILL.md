---
name: documenso-local-dev-loop
description: |
  Set up local development environment and testing workflow for Documenso.
  Use when configuring dev environment, setting up test workflows,
  or establishing rapid iteration patterns with Documenso.
  Trigger with phrases like "documenso local dev", "documenso development",
  "test documenso locally", "documenso dev environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, testing, workflow]

---
# Documenso Local Dev Loop

## Overview

Configure a fast local development environment for Documenso integrations. Covers project structure, environment configs, self-hosted Documenso via Docker, test utilities, and cleanup scripts.

## Prerequisites

- Completed `documenso-install-auth` setup
- Node.js 18+ with TypeScript
- Docker (for self-hosted local Documenso)

## Instructions

### Step 1: Project Structure

```
my-signing-app/
├── src/
│   └── documenso/
│       ├── client.ts          # Configured SDK client
│       ├── documents.ts       # Document operations
│       ├── recipients.ts      # Recipient management
│       └── webhooks.ts        # Webhook handlers
├── scripts/
│   ├── verify-connection.ts   # Quick health check
│   ├── create-test-doc.ts     # Generate test documents
│   └── cleanup-test-docs.ts   # Remove test data
├── tests/
│   └── integration/
│       ├── document.test.ts
│       └── template.test.ts
├── .env.development
├── .env.test
└── .env.production
```

### Step 2: Environment Configuration

**.env.development:**

```bash
DOCUMENSO_API_KEY=api_dev_xxxxxxxxxxxx
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2
DOCUMENSO_WEBHOOK_SECRET=whsec_dev_xxxxxxxxxxxx
LOG_LEVEL=debug
```

**.env.test:**

```bash
DOCUMENSO_API_KEY=api_test_xxxxxxxxxxxx
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2
DOCUMENSO_WEBHOOK_SECRET=whsec_test_xxxxxxxxxxxx
LOG_LEVEL=warn
```

### Step 3: Client Wrapper with Dev Helpers

```typescript
// src/documenso/client.ts
import { Documenso } from "@documenso/sdk-typescript";

let _client: Documenso | null = null;

export function getClient(): Documenso {
  if (!_client) {
    _client = new Documenso({
      apiKey: process.env.DOCUMENSO_API_KEY!,
      ...(process.env.DOCUMENSO_BASE_URL && {
        serverURL: process.env.DOCUMENSO_BASE_URL,
      }),
    });
  }
  return _client;
}

// Dev helper: list recent documents for debugging
export async function listRecentDocs(limit = 5) {
  const client = getClient();
  const { documents } = await client.documents.findV0({
    page: 1,
    perPage: limit,
    orderByColumn: "createdAt",
    orderByDirection: "desc",
  });
  return documents;
}
```

### Step 4: Self-Hosted Local Documenso (Docker)

```bash
# Pull the official Documenso Docker image
docker pull documenso/documenso:latest

# Create docker-compose.local.yml
```

```yaml
# docker-compose.local.yml
services:
  documenso:
    image: documenso/documenso:latest
    ports:
      - "3000:3000"
    environment:
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=local-dev-secret-change-me
      - NEXT_PRIVATE_ENCRYPTION_KEY=local-encryption-key
      - NEXT_PRIVATE_ENCRYPTION_SECONDARY_KEY=local-secondary-key
      - NEXT_PUBLIC_WEBAPP_URL=http://localhost:3000
      - NEXT_PRIVATE_DATABASE_URL=postgresql://documenso:password@db:5432/documenso
      - NEXT_PRIVATE_DIRECT_DATABASE_URL=postgresql://documenso:password@db:5432/documenso
      - NEXT_PRIVATE_SMTP_TRANSPORT=smtp-auth
      - NEXT_PRIVATE_SMTP_HOST=mailhog
      - NEXT_PRIVATE_SMTP_PORT=1025
    depends_on:
      - db
      - mailhog

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: documenso
      POSTGRES_PASSWORD: password
      POSTGRES_DB: documenso
    volumes:
      - pgdata:/var/lib/postgresql/data

  mailhog:
    image: mailhog/mailhog
    ports:
      - "8025:8025"  # Web UI for email inspection
      - "1025:1025"

volumes:
  pgdata:
```

```bash
docker compose -f docker-compose.local.yml up -d
# Documenso at http://localhost:3000
# MailHog at http://localhost:8025 (view sent emails)
```

**.env.local (for self-hosted dev):**

```bash
DOCUMENSO_API_KEY=api_local_xxxxxxxxxxxx
DOCUMENSO_BASE_URL=http://localhost:3000/api/v2
```

### Step 5: Quick Verification Script

```typescript
// scripts/verify-connection.ts
import { getClient } from "../src/documenso/client";

async function verify() {
  const client = getClient();
  try {
    const { documents } = await client.documents.findV0({ page: 1, perPage: 1 });
    console.log("Connection OK");
    console.log(`Documents accessible: ${documents.length >= 0 ? "yes" : "no"}`);
  } catch (err: any) {
    console.error(`Connection FAILED: ${err.message}`);
    if (err.statusCode === 401) console.error("Check DOCUMENSO_API_KEY");
    process.exit(1);
  }
}
verify();
```

### Step 6: Test Cleanup Script

```typescript
// scripts/cleanup-test-docs.ts
import { getClient } from "../src/documenso/client";

async function cleanup() {
  const client = getClient();
  const { documents } = await client.documents.findV0({ page: 1, perPage: 100 });

  const testDocs = documents.filter((d: any) =>
    d.title.startsWith("[TEST]") || d.title.startsWith("Hello World")
  );

  for (const doc of testDocs) {
    if (doc.status === "DRAFT") {
      await client.documents.deleteV0(doc.id);
      console.log(`Deleted: ${doc.title} (${doc.id})`);
    } else {
      console.log(`Skipped (${doc.status}): ${doc.title}`);
    }
  }
  console.log(`Cleaned up ${testDocs.filter((d: any) => d.status === "DRAFT").length} test docs`);
}
cleanup();
```

### Step 7: Development Scripts (package.json)

```json
{
  "scripts": {
    "dev:verify": "tsx scripts/verify-connection.ts",
    "dev:test-doc": "tsx scripts/create-test-doc.ts",
    "dev:cleanup": "tsx scripts/cleanup-test-docs.ts",
    "dev:local": "docker compose -f docker-compose.local.yml up -d",
    "dev:local:stop": "docker compose -f docker-compose.local.yml down",
    "test:integration": "vitest run tests/integration/"
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `ECONNREFUSED localhost:3000` | Docker not running | Run `docker compose up -d` |
| `401 on staging` | Wrong API key for env | Check `.env.development` key matches staging |
| Stale test data | Tests didn't clean up | Run `npm run dev:cleanup` |
| Rate limited in tests | Too many requests | Add `await delay(500)` between API calls |
| Emails not arriving | SMTP misconfigured | Check MailHog at `localhost:8025` |

## Resources

- [Documenso Self-Hosting](https://docs.documenso.com/developers/self-hosting/how-to)
- [Developer Quickstart](https://docs.documenso.com/docs/developers/local-development/quickstart)
- [Environment Variables Reference](https://docs.documenso.com/docs/self-hosting/configuration/environment)
- [MailHog](https://github.com/mailhog/MailHog)

## Next Steps

Apply patterns in `documenso-sdk-patterns` for production-ready code structure.
