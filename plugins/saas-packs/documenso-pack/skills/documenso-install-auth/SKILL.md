---
name: documenso-install-auth
description: |
  Install and configure Documenso SDK/API authentication.
  Use when setting up a new Documenso integration, configuring API keys,
  or initializing Documenso in your project.
  Trigger with phrases like "install documenso", "setup documenso",
  "documenso auth", "configure documenso API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api, authentication]

---
# Documenso Install & Auth

## Overview

Set up the Documenso SDK and configure API authentication for document signing. Covers the TypeScript SDK (`@documenso/sdk-typescript`), the Python SDK (`documenso-sdk-python`), and raw REST API usage. Documenso exposes two API versions: **v1** (legacy, documents only) and **v2** (envelopes, multi-document, recommended for new work).

## Prerequisites

- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, yarn, pip, or uv)
- Documenso account — cloud at `app.documenso.com` or self-hosted instance
- API key generated from the Documenso dashboard

## Instructions

### Step 1: Install the SDK

**TypeScript / Node.js:**

```bash
npm install @documenso/sdk-typescript
# or
pnpm add @documenso/sdk-typescript
```

**Python:**

```bash
pip install documenso-sdk-python
# or
uv pip install documenso-sdk-python
```

### Step 2: Generate an API Key

1. Log in to your Documenso dashboard (`https://app.documenso.com` or your self-hosted URL).
2. Click your avatar (top-right) and select **User settings** (or **Team settings** for team-scoped keys).
3. Navigate to the **API tokens** tab.
4. Click **Create API Key**, give it a descriptive name (e.g. `ci-pipeline-prod`).
5. Copy the key immediately — it is shown only once.

Team API keys inherit the team's document and template access. Personal keys only access your own documents.

### Step 3: Store the Key Securely

```bash
# .env (never commit this file)
DOCUMENSO_API_KEY=api_xxxxxxxxxxxxxxxxxxxxxxxxxx
```

Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

### Step 4: Initialize the Client

**TypeScript — v2 API (recommended):**

```typescript
import { Documenso } from "@documenso/sdk-typescript";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY!,
  // For self-hosted, override the server URL:
  // serverURL: "https://sign.yourcompany.com/api/v2",
});
```

**TypeScript — v1 REST (legacy):**

```typescript
const BASE = process.env.DOCUMENSO_BASE_URL ?? "https://app.documenso.com/api/v1";
const headers = { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` };

const res = await fetch(`${BASE}/documents`, { headers });
const docs = await res.json();
```

**Python:**

```python
from documenso_sdk_python import Documenso
import os

client = Documenso(api_key=os.environ["DOCUMENSO_API_KEY"])
```

### Step 5: Verify the Connection

```typescript
// verify-connection.ts
import { Documenso } from "@documenso/sdk-typescript";

async function verify() {
  const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
  const { documents } = await client.documents.findV0({ page: 1, perPage: 1 });
  console.log(`Connected — ${documents.length >= 0 ? "OK" : "FAIL"}`);
}
verify().catch(console.error);
```

Run with `npx tsx verify-connection.ts`.

## API Endpoints

| Environment | Base URL (v2) | Base URL (v1, legacy) |
|-------------|---------------|-----------------------|
| Cloud production | `https://app.documenso.com/api/v2` | `https://app.documenso.com/api/v1` |
| Cloud staging | `https://stg-app.documenso.com/api/v2` | `https://stg-app.documenso.com/api/v1` |
| Self-hosted | `https://your-instance.com/api/v2` | `https://your-instance.com/api/v1` |

## Self-Hosted Base URL Override

```typescript
const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY!,
  serverURL: process.env.DOCUMENSO_BASE_URL, // e.g. "https://sign.acme.com/api/v2"
});
```

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| Unauthorized | 401 | Invalid or expired API key | Regenerate key in dashboard |
| Forbidden | 403 | Personal key accessing team resources | Use team-scoped API key |
| Module not found | N/A | SDK not installed | Run `npm install @documenso/sdk-typescript` |
| Network error | N/A | Firewall or DNS issue | Verify outbound HTTPS to `app.documenso.com` |
| `ERR_INVALID_URL` | N/A | Bad `serverURL` value | Include protocol and path: `https://host/api/v2` |

## Security Checklist

- [ ] API key stored in environment variable, never in source code
- [ ] `.env` is listed in `.gitignore`
- [ ] CI secrets use masked/encrypted storage (GitHub Secrets, Vault, etc.)
- [ ] Team keys rotated on employee offboarding
- [ ] Self-hosted instances use HTTPS with valid TLS certificates

## Resources

- [Documenso API Documentation](https://docs.documenso.com/developers/public-api)
- [TypeScript SDK](https://github.com/documenso/sdk-typescript)
- [Python SDK](https://github.com/documenso/sdk-python)
- [OpenAPI Reference (v2)](https://openapi.documenso.com/)
- [Self-Hosting Guide](https://docs.documenso.com/developers/self-hosting)

## Next Steps

After successful auth, proceed to `documenso-hello-world` for your first document.
