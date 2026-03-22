---
name: linktree-install-auth
description: |
  Install and configure Linktree SDK/API authentication.
  Use when setting up a new Linktree integration.
  Trigger: "install linktree", "setup linktree", "linktree auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Install & Auth

## Overview
Set up Linktree API for programmatic link-in-bio management with 25M+ creators.

## Prerequisites
- Linktree account and API access
- API key/credentials from Linktree dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @linktree/sdk
# or: pip install linktree-sdk
```

### Step 2: Configure Authentication
```bash
export LINKTREE_API_KEY="your-api-key-here"
echo 'LINKTREE_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import { LinktreeClient } from '@linktree/sdk';
const client = new LinktreeClient({ apiKey: process.env.LINKTREE_API_KEY });
const profile = await client.profiles.get('myprofile');
console.log(`Profile: ${profile.username} — ${profile.links.length} links`);
```

### Step 4: Verify Connection (Python)
```python
import linktree
client = linktree.Client(api_key=os.environ['LINKTREE_API_KEY'])
profile = client.profiles.get('myprofile')
print(f'Profile: {profile.username} — {len(profile.links)} links')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [Linktree Documentation](https://linktr.ee/marketplace/developer)

## Next Steps
After auth, proceed to `linktree-hello-world`.
