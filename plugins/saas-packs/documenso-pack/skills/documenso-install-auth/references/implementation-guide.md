# Documenso Install Auth - Implementation Guide

# Documenso Install & Auth

## Overview
Set up Documenso SDK and configure API authentication for document signing integration.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, yarn, pip, or uv)
- Documenso account (cloud or self-hosted)
- API key from Documenso dashboard

## Instructions

### Step 1: Install SDK

**TypeScript/Node.js:**
```bash
# npm
npm add @documenso/sdk-typescript

# pnpm
pnpm add @documenso/sdk-typescript

# yarn
yarn add @documenso/sdk-typescript

# bun
bun add @documenso/sdk-typescript
```

**Python:**
```bash
# pip
pip install documenso_sdk

# uv (recommended)
uv add documenso_sdk

# poetry
poetry add documenso_sdk
```

### Step 2: Get API Key

1. Log into Documenso dashboard at https://app.documenso.com
2. Click your avatar in the top right corner
3. Select "User settings" (or "Team settings" for team APIs)
4. Navigate to "API tokens" tab
5. Click "Create API Key"
6. Copy the generated key (shown only once)

### Step 3: Configure Authentication

```bash
# Set environment variable
export DOCUMENSO_API_KEY="your-api-key"

# Or create .env file
echo 'DOCUMENSO_API_KEY=your-api-key' >> .env
```

### Step 4: Verify Connection

**TypeScript:**
```typescript
import { Documenso } from "@documenso/sdk-typescript";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

// Verify connection by listing documents
async function verifyConnection() {
  try {
    const documents = await documenso.documents.findV0({});
    console.log("Connection successful!");
    console.log(`Found ${documents.documents?.length ?? 0} documents`);
    return true;
  } catch (error) {
    console.error("Connection failed:", error);
    return false;
  }
}

verifyConnection();
```

**Python:**
```python
import os
from documenso_sdk import Documenso

documenso = Documenso(
    api_key=os.environ.get("DOCUMENSO_API_KEY")
)

# Verify connection
try:
    documents = documenso.documents.find_v0()
    print(f"Connection successful! Found {len(documents.documents)} documents")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Generate new key in dashboard |
| 401 Unauthorized | Missing or malformed key | Check API key format and env var |
| 403 Forbidden | Key lacks required permissions | Use team API key for team resources |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |
| Network Error | Firewall blocking | Ensure outbound HTTPS to api.documenso.com |

## API Endpoints

| Environment | Base URL |
|-------------|----------|
| Production | `https://app.documenso.com/api/v2/` |
| Staging | `https://stg-app.documenso.com/api/v2/` |
| Self-hosted | `https://your-instance.com/api/v2/` |

## Custom Base URL (Self-Hosted)

```typescript
const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
  serverURL: "https://your-documenso-instance.com/api/v2/",
});
```

## Resources
- [Documenso API Documentation](https://docs.documenso.com/developers/public-api)
- [TypeScript SDK](https://github.com/documenso/sdk-typescript)
- [Python SDK](https://github.com/documenso/sdk-python)
- [API Reference](https://openapi.documenso.com/)

## Next Steps
After successful auth, proceed to `documenso-hello-world` for your first document.
