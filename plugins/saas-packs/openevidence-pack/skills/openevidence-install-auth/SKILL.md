---
name: openevidence-install-auth
description: |
  Install and configure OpenEvidence SDK/API authentication.
  Use when setting up a new OpenEvidence integration.
  Trigger: "install openevidence", "setup openevidence", "openevidence auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Install & Auth

## Overview
Set up OpenEvidence Medical AI API for clinical decision support and evidence-based queries.

## Prerequisites
- OpenEvidence account and API access
- API key/credentials from OpenEvidence dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @openevidence/sdk
# API key from OpenEvidence developer portal
```

### Step 2: Configure Authentication
```bash
export OPENEVIDENCE_API_KEY="your-api-key-here"
echo 'OPENEVIDENCE_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import { OpenEvidenceClient } from '@openevidence/sdk';
const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  organization: process.env.OPENEVIDENCE_ORG_ID
});
const result = await client.query({ question: 'What are first-line treatments for Type 2 diabetes?' });
console.log(`Answer: ${result.answer.substring(0, 100)}...`);
console.log(`Citations: ${result.citations.length} references`);
```

### Step 4: Verify Connection (Python)
```python
import openevidence
client = openevidence.Client(api_key=os.environ['OPENEVIDENCE_API_KEY'])
result = client.query(question='What are first-line treatments for Type 2 diabetes?')
print(f'Answer: {result.answer[:100]}...')
print(f'Citations: {len(result.citations)} references')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [OpenEvidence Documentation](https://www.openevidence.com)

## Next Steps
After auth, proceed to `openevidence-hello-world`.
