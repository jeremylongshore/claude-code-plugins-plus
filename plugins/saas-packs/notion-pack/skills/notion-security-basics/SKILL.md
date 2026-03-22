---
name: notion-security-basics
description: |
  Apply Notion API security best practices for tokens, permissions, and access control.
  Use when securing integration tokens, configuring least-privilege capabilities,
  or auditing Notion security configuration.
  Trigger with phrases like "notion security", "notion secrets",
  "secure notion", "notion API key security", "notion permissions".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Security Basics

## Overview
Security best practices for Notion integration tokens, page-level permissions, and webhook verification.

## Prerequisites
- Notion integration created at notion.so/my-integrations
- Understanding of environment variables
- Access to deployment platform for secrets management

## Instructions

### Step 1: Token Management
```bash
# Tokens start with ntn_ (new) or secret_ (legacy)
# NEVER commit tokens to git

# .gitignore
.env
.env.local
.env.*.local

# .env (local only)
NOTION_TOKEN=ntn_your_secret_here
```

```typescript
// Always load from environment
import { Client } from '@notionhq/client';

if (!process.env.NOTION_TOKEN) {
  throw new Error('NOTION_TOKEN is required');
}

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// NEVER do this:
// const notion = new Client({ auth: 'ntn_actual_token_here' }); // Exposed in source!
```

### Step 2: Least-Privilege Capabilities
Configure integration capabilities at https://www.notion.so/my-integrations:

| Capability | When Needed |
|------------|-------------|
| Read content | Reading pages, databases, blocks |
| Update content | Modifying existing pages and blocks |
| Insert content | Creating new pages and appending blocks |
| Read comments | Listing and reading comments |
| Create comments | Adding comments to pages/blocks |
| Read user information (with email) | Only if you need user emails |
| Read user information (without email) | Default for user references |

**Best practice:** Only enable capabilities your integration actually uses. A read-only dashboard integration should not have Insert or Update capabilities.

### Step 3: Page-Level Access Control
Notion uses page-level sharing, not workspace-wide access:

```typescript
// Integration can ONLY access pages explicitly shared with it
// Even workspace-level tokens respect page sharing

// This will 404 if the page isn't shared:
try {
  await notion.pages.retrieve({ page_id: 'unshared-page-id' });
} catch (error) {
  // error.code === 'object_not_found'
  // Cannot distinguish "doesn't exist" from "not shared" — by design
}
```

**Sharing hierarchy:**
- Share a parent page to grant access to all children
- Sharing a child page alone does NOT grant access to its parent
- Removing integration access from a parent removes it from all children

### Step 4: Token Rotation
```bash
# 1. Generate new token at notion.so/my-integrations
#    (Click integration → "Regenerate" under Internal Integration Secret)

# 2. Update in your secret manager FIRST
# AWS:
aws secretsmanager update-secret --secret-id notion-token --secret-string "ntn_new_token"
# GCP:
echo -n "ntn_new_token" | gcloud secrets versions add notion-token --data-file=-

# 3. Deploy/restart with new token

# 4. Verify new token works
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq .name

# 5. Old token is automatically invalidated on regeneration
```

### Step 5: Webhook Security
```typescript
// Notion webhooks require verification of the webhook URL
// Configure webhook at: https://www.notion.so/my-integrations

// Verify webhook events come from Notion:
// 1. Only accept requests from Notion's IP ranges
// 2. Validate the payload structure matches Notion's schema
// 3. Use HTTPS endpoints only

import express from 'express';

const app = express();

app.post('/webhooks/notion',
  express.json(),
  async (req, res) => {
    // Notion verifies your endpoint during setup with a verification request
    if (req.body.type === 'url_verification') {
      // Echo the challenge back
      return res.json({ challenge: req.body.challenge });
    }

    // Process actual events
    const event = req.body;
    console.log(`Event: ${event.type}`, event.data);

    // Always respond 200 quickly — process async
    res.status(200).json({ ok: true });
  }
);
```

### Step 6: Git Secret Scanning
```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for Notion tokens
        run: |
          if grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}" --include="*.ts" --include="*.js" --include="*.json" .; then
            echo "ERROR: Notion token found in source code!"
            exit 1
          fi
```

## Output
- Tokens stored securely in environment variables
- Integration capabilities set to minimum required
- Page-level access properly configured
- Token rotation procedure documented
- Webhook endpoint secured

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in source code | Git scanning, grep | Rotate immediately, add to .gitignore |
| Over-privileged integration | Capability audit | Remove unused capabilities |
| Unshared pages returning 404 | Application logs | Document required page sharing |
| Token never rotated | Token age tracking | Schedule quarterly rotation |

## Examples

### Separate Read/Write Integrations
```typescript
// Create two integrations with different capabilities:
// "my-app-reader" — Read content only
// "my-app-writer" — Read + Update + Insert

const readerNotion = new Client({ auth: process.env.NOTION_READ_TOKEN });
const writerNotion = new Client({ auth: process.env.NOTION_WRITE_TOKEN });

// Use reader for dashboards, search, data export
const pages = await readerNotion.databases.query({ database_id: dbId });

// Use writer only when mutations are needed
await writerNotion.pages.update({ page_id: pageId, properties: { ... } });
```

## Resources
- [Notion API Authorization](https://developers.notion.com/docs/authorization)
- [Best Practices for API Keys](https://developers.notion.com/docs/best-practices-for-handling-api-keys)
- [Integration Capabilities](https://developers.notion.com/docs/create-a-notion-integration)

## Next Steps
For production deployment, see `notion-prod-checklist`.
