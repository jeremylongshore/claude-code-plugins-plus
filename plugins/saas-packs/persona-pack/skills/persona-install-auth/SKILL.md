---
name: persona-install-auth
description: |
  Configure Persona API authentication with sandbox and production API keys.
  Use when setting up identity verification, configuring API credentials,
  or initializing Persona in your project.
  Trigger with phrases like "install persona", "setup persona",
  "persona auth", "persona API key", "KYC setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, authentication]
compatible-with: claude-code, codex, openclaw
---

# Persona Install & Auth

## Overview
Set up Persona API authentication. Persona uses Bearer token auth with environment-prefixed API keys (`persona_sandbox_*` for testing, `persona_production_*` for live). No SDK required -- direct REST API calls with any HTTP client.

## Prerequisites
- Persona account at [withpersona.com](https://withpersona.com)
- At least one Inquiry Template configured in the Persona Dashboard
- Node.js 18+ or Python 3.9+

## Instructions

### Step 1: Get API Keys
```text
1. Log into dashboard.withpersona.com
2. Go to Settings > API Keys
3. Copy your sandbox key (starts with persona_sandbox_)
4. For production: copy production key (starts with persona_production_)
```

### Step 2: Configure Environment
```bash
# .env — never commit
PERSONA_API_KEY=persona_sandbox_xxxxxxxxxxxxxxxxxxxxxxxx
PERSONA_API_VERSION=2023-01-05

# .gitignore
echo '.env' >> .gitignore
```

### Step 3: Install HTTP Client
```bash
set -euo pipefail
# Node.js
npm install axios dotenv

# Python
pip install requests python-dotenv
```

### Step 4: Verify Connection (Node.js)
```typescript
import axios from 'axios';

const persona = axios.create({
  baseURL: 'https://withpersona.com/api/v1',
  headers: {
    'Authorization': `Bearer ${process.env.PERSONA_API_KEY}`,
    'Persona-Version': process.env.PERSONA_API_VERSION || '2023-01-05',
    'Content-Type': 'application/json',
  },
});

async function verify() {
  const { data } = await persona.get('/inquiries?page[size]=1');
  console.log(`Connected! Found ${data.data.length} inquiry(ies).`);
}
verify().catch(console.error);
```

### Step 5: Verify Connection (Python)
```python
import os, requests
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.environ['PERSONA_API_KEY']}",
    "Persona-Version": os.environ.get("PERSONA_API_VERSION", "2023-01-05"),
}

resp = requests.get("https://withpersona.com/api/v1/inquiries?page[size]=1", headers=headers)
resp.raise_for_status()
print(f"Connected! Status: {resp.status_code}")
```

## Output
- API key configured and verified
- HTTP client set up with correct headers
- Successful test call to Persona API

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Verify key in Dashboard > Settings > API Keys |
| `403 Forbidden` | Key doesn't match environment | Use `persona_sandbox_*` for testing |
| `400 Missing Persona-Version` | Version header not set | Add `Persona-Version: 2023-01-05` header |
| Connection refused | Network/firewall issue | Ensure HTTPS to withpersona.com is allowed |

## Resources
- [Persona API Introduction](https://docs.withpersona.com/api-introduction)
- [API Keys](https://docs.withpersona.com/api-keys)
- [API Quickstart](https://docs.withpersona.com/api-quickstart-tutorial)

## Next Steps
Create your first inquiry: `persona-hello-world`
