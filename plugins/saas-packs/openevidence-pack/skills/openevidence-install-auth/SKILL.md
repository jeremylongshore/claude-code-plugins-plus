---
name: openevidence-install-auth
description: |
  Install and configure OpenEvidence API authentication.
  Use when setting up a new OpenEvidence integration, configuring API credentials,
  or initializing OpenEvidence in your healthcare application.
  Trigger with phrases like "install openevidence", "setup openevidence",
  "openevidence auth", "configure openevidence API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Install & Auth

## Overview
Set up OpenEvidence API access and configure authentication for clinical decision support queries.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- OpenEvidence Enterprise API access (contact sales@openevidence.com)
- Signed BAA (Business Associate Agreement) for PHI handling
- API credentials from OpenEvidence dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @openevidence/sdk

# Python
pip install openevidence
```

### Step 2: Configure Authentication
```bash
# Set environment variables (NEVER commit to git)
export OPENEVIDENCE_API_KEY="oe_live_***"
export OPENEVIDENCE_ORG_ID="org_***"

# Or create .env file
cat >> .env << 'EOF'
OPENEVIDENCE_API_KEY=oe_live_***
OPENEVIDENCE_ORG_ID=org_***
OPENEVIDENCE_ENVIRONMENT=production
EOF
```

### Step 3: Add to .gitignore
```bash
# Prevent credential exposure
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
echo '.env.*.local' >> .gitignore
```

### Step 4: Verify Connection
```typescript
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  orgId: process.env.OPENEVIDENCE_ORG_ID,
});

// Test connection with a simple query
async function verifyConnection() {
  try {
    const health = await client.health.check();
    console.log('OpenEvidence connection verified:', health.status);
    return true;
  } catch (error) {
    console.error('Connection failed:', error.message);
    return false;
  }
}

verifyConnection();
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variables configured with API credentials
- .gitignore updated to prevent credential exposure
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in OpenEvidence dashboard |
| Missing BAA | No signed Business Associate Agreement | Contact OpenEvidence compliance team |
| Organization Not Found | Wrong org_id | Check organization settings in dashboard |
| Network Error | Firewall blocking | Ensure outbound HTTPS to api.openevidence.com |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  orgId: process.env.OPENEVIDENCE_ORG_ID,
  timeout: 30000, // 30 second timeout for clinical queries  # 30000: 30 seconds in ms
  retries: 3,
});

export default client;
```

### Python Setup
```python
import os
from openevidence import OpenEvidenceClient

client = OpenEvidenceClient(
    api_key=os.environ.get('OPENEVIDENCE_API_KEY'),
    org_id=os.environ.get('OPENEVIDENCE_ORG_ID'),
    timeout=30,
    max_retries=3
)
```

### Environment-Based Configuration
```typescript
const environments = {
  development: {
    baseUrl: 'https://api.sandbox.openevidence.com',
    timeout: 60000,  # 60000: 1 minute in ms
  },
  staging: {
    baseUrl: 'https://api.staging.openevidence.com',
    timeout: 45000,  # 45000 = configured value
  },
  production: {
    baseUrl: 'https://api.openevidence.com',
    timeout: 30000,  # 30000: 30 seconds in ms
  },
};

const env = process.env.NODE_ENV || 'development';
const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  ...environments[env],
});
```

## Resources
- [OpenEvidence](https://www.openevidence.com/)
- [OpenEvidence API Terms](https://www.openevidence.com/policies/api)
- [OpenEvidence Security](https://www.openevidence.com/security)

## Next Steps
After successful auth, proceed to `openevidence-hello-world` for your first clinical query.