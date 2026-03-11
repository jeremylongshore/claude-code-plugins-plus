---
name: exa-enterprise-rbac
description: |
  Configure Exa enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Exa.
  Trigger with phrases like "exa SSO", "exa RBAC",
  "exa enterprise", "exa roles", "exa permissions", "exa SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Enterprise RBAC

## Overview
Manage access to Exa AI search API through API key scoping and team-level controls. Exa is an API-first product with per-search pricing, so access control centers on API key management, rate limiting, and domain restrictions rather than traditional user roles. Each key can be scoped to specific search types (neural, keyword, auto) and rate-limited independently.

## Prerequisites
- Exa API account with team plan
- Dashboard access at dashboard.exa.ai
- At least one API key with management permissions

## Instructions

### Step 1: Create Scoped API Keys per Use Case
```bash
# Create a key for the RAG pipeline (high volume, neural search only)
curl -X POST https://api.exa.ai/v1/api-keys \
  -H "Authorization: Bearer $EXA_ADMIN_KEY" \
  -d '{
    "name": "rag-pipeline-prod",
    "allowed_endpoints": ["search", "get-contents"],
    "rate_limit_rpm": 300,
    "monthly_search_limit": 50000
  }'

# Create a restricted key for the internal tool (low volume)
curl -X POST https://api.exa.ai/v1/api-keys \
  -H "Authorization: Bearer $EXA_ADMIN_KEY" \
  -d '{
    "name": "internal-research-tool",
    "rate_limit_rpm": 30,
    "monthly_search_limit": 5000
  }'
```

### Step 2: Implement Key-Based Access in Your Gateway
```typescript
// exa-proxy.ts - Route requests through your gateway
const KEY_PERMISSIONS: Record<string, { maxResults: number; allowedTypes: string[] }> = {
  'rag-pipeline':    { maxResults: 10, allowedTypes: ['neural', 'auto'] },
  'research-tool':   { maxResults: 25, allowedTypes: ['neural', 'keyword', 'auto'] },
  'marketing-team':  { maxResults: 5,  allowedTypes: ['keyword'] },
};

function validateRequest(keyName: string, searchType: string, numResults: number): boolean {
  const perms = KEY_PERMISSIONS[keyName];
  if (!perms) return false;
  return perms.allowedTypes.includes(searchType) && numResults <= perms.maxResults;
}
```

### Step 3: Set Domain Restrictions
Restrict search results to approved domains for compliance-sensitive teams:
```bash
# Only allow searches from vetted sources
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{
    "query": "enterprise security best practices",
    "includeDomains": ["nist.gov", "owasp.org", "sans.org"],
    "numResults": 10
  }'
```

### Step 4: Monitor Usage and Rotate Keys
```bash
# Check usage per API key
curl https://api.exa.ai/v1/usage \
  -H "Authorization: Bearer $EXA_ADMIN_KEY" | \
  jq '.keys[] | {name, searches_this_month, cost_usd}'

# Rotate a key (create new, then delete old)
NEW_KEY=$(curl -s -X POST https://api.exa.ai/v1/api-keys \
  -H "Authorization: Bearer $EXA_ADMIN_KEY" \
  -d '{"name": "rag-pipeline-prod-v2"}' | jq -r '.key')
echo "Update services with new key, then delete old key"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401` on search | Invalid or revoked API key | Regenerate key in dashboard |
| `429 rate limited` | Exceeded RPM on key | Increase rate limit or add request queue |
| Monthly limit hit | Search budget exhausted | Upgrade plan or wait for billing cycle reset |
| Empty results | Domain filter too restrictive | Widen `includeDomains` or remove filter |

## Examples
```bash
# Quick test: verify API key works and check remaining quota
curl -s https://api.exa.ai/v1/usage \
  -H "x-api-key: $EXA_API_KEY" | jq '{searches_remaining, plan, rate_limit}'
```
