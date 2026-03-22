---
name: bamboohr-install-auth
description: |
  Install and configure BambooHR API authentication with HTTP Basic Auth.
  Use when setting up a new BambooHR integration, configuring API keys,
  or initializing BambooHR REST API access in your project.
  Trigger with phrases like "install bamboohr", "setup bamboohr",
  "bamboohr auth", "configure bamboohr API key", "bamboohr credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, authentication]
compatible-with: claude-code
---

# BambooHR Install & Auth

## Overview

Set up BambooHR REST API authentication. BambooHR uses HTTP Basic Authentication — your API key is the username, and the password can be any arbitrary string (typically `x`).

**Base URL pattern:**

```
https://api.bamboohr.com/api/gateway.php/{companyDomain}/v1/
```

Where `{companyDomain}` is your BambooHR subdomain (e.g., `acmecorp` from `acmecorp.bamboohr.com`).

## Prerequisites

- Node.js 18+ or Python 3.10+
- BambooHR account with API access enabled
- API key generated from BambooHR (Account > API Keys)
- Company subdomain from your BambooHR URL

## Instructions

### Step 1: Generate an API Key

1. Log in to BambooHR at `https://{companyDomain}.bamboohr.com`
2. Click your profile icon > **API Keys**
3. Click **Add New Key**, give it a descriptive name
4. Copy the key immediately — it is only shown once

### Step 2: Configure Environment Variables

```bash
# Required
export BAMBOOHR_API_KEY="your-api-key-here"
export BAMBOOHR_COMPANY_DOMAIN="yourcompany"

# Create .env file for local development
cat > .env << 'EOF'
BAMBOOHR_API_KEY=your-api-key-here
BAMBOOHR_COMPANY_DOMAIN=yourcompany
EOF

# IMPORTANT: Add to .gitignore
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 3: Install HTTP Client

```bash
# Node.js — no BambooHR-specific SDK needed; use fetch or axios
npm install dotenv

# Python
pip install requests python-dotenv
```

### Step 4: Verify Connection

**TypeScript / Node.js:**

```typescript
import 'dotenv/config';

const COMPANY = process.env.BAMBOOHR_COMPANY_DOMAIN!;
const API_KEY = process.env.BAMBOOHR_API_KEY!;
const BASE_URL = `https://api.bamboohr.com/api/gateway.php/${COMPANY}/v1`;

// BambooHR uses HTTP Basic Auth: API key as username, "x" as password
const headers = {
  'Authorization': `Basic ${Buffer.from(`${API_KEY}:x`).toString('base64')}`,
  'Accept': 'application/json',
};

// Test: fetch the employee directory
const res = await fetch(`${BASE_URL}/employees/directory`, { headers });

if (res.ok) {
  const data = await res.json();
  console.log(`Connected. ${data.employees?.length ?? 0} employees found.`);
} else {
  console.error(`Auth failed: ${res.status} ${res.statusText}`);
  const errHeader = res.headers.get('X-BambooHR-Error-Message');
  if (errHeader) console.error(`Detail: ${errHeader}`);
}
```

**Python:**

```python
import os, requests
from dotenv import load_dotenv

load_dotenv()

COMPANY = os.environ["BAMBOOHR_COMPANY_DOMAIN"]
API_KEY = os.environ["BAMBOOHR_API_KEY"]
BASE_URL = f"https://api.bamboohr.com/api/gateway.php/{COMPANY}/v1"

# HTTP Basic Auth: API key as username, "x" as password
response = requests.get(
    f"{BASE_URL}/employees/directory",
    auth=(API_KEY, "x"),
    headers={"Accept": "application/json"},
)

if response.ok:
    data = response.json()
    print(f"Connected. {len(data.get('employees', []))} employees found.")
else:
    print(f"Auth failed: {response.status_code}")
    print(response.headers.get("X-BambooHR-Error-Message", ""))
```

**Quick curl test:**

```bash
curl -s -u "${BAMBOOHR_API_KEY}:x" \
  "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/directory" \
  -H "Accept: application/json" | head -c 200
```

## Output

- Environment variables configured (`BAMBOOHR_API_KEY`, `BAMBOOHR_COMPANY_DOMAIN`)
- `.env` file created and git-ignored
- Successful API response from `/employees/directory`

## Error Handling

| HTTP Status | Header | Cause | Solution |
|-------------|--------|-------|----------|
| 401 | `X-BambooHR-Error-Message` | Invalid or missing API key | Regenerate key in BambooHR dashboard |
| 403 | `X-BambooHR-Error-Message` | Key lacks permissions for endpoint | Use an admin-level API key |
| 404 | — | Wrong company domain in URL | Verify subdomain matches `{x}.bamboohr.com` |
| 503 | `Retry-After` | Rate limited or service unavailable | Wait for `Retry-After` seconds and retry |

## Enterprise Considerations

- **Key rotation**: Generate a new key, update env vars, verify, then delete the old key
- **Audit trail**: Each API key is tied to a user; BambooHR logs which key made each request
- **IP allowlisting**: BambooHR does not support IP restrictions on API keys
- **SSO/OAuth**: BambooHR supports OpenID Connect for browser login, but API access requires API keys
- **Multi-tenant**: Store per-company credentials in a secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault)

## Resources

- [BambooHR API Getting Started](https://documentation.bamboohr.com/docs/getting-started)
- [BambooHR Authentication Docs](https://documentation.bamboohr.com/docs)
- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)

## Next Steps

After successful auth, proceed to `bamboohr-hello-world` for your first employee data retrieval.
