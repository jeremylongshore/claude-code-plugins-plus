---
name: ideogram-enterprise-rbac
description: |
  Configure Ideogram enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Ideogram.
  Trigger with phrases like "ideogram SSO", "ideogram RBAC",
  "ideogram enterprise", "ideogram roles", "ideogram permissions", "ideogram SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram Enterprise RBAC

## Overview
Control access to Ideogram's AI image generation API through API key management and credit-based budgets. Ideogram uses credit-based pricing where each image generation costs credits based on model quality and resolution (standard vs HD, different aspect ratios).

## Prerequisites
- Ideogram API account with team plan
- Dashboard access at ideogram.ai
- API key with admin-level permissions

## Instructions

### Step 1: Create Purpose-Scoped API Keys
```bash
set -euo pipefail
# Key for the marketing team (standard quality, moderate budget)
curl -X POST https://api.ideogram.ai/v1/api-keys \
  -H "Authorization: Bearer $IDEOGRAM_ADMIN_KEY" \
  -d '{
    "name": "marketing-team",
    "monthly_credit_limit": 5000,  # 5000: 5 seconds in ms
    "allowed_models": ["V_2"],
    "rate_limit_rpm": 30
  }'

# Key for the product team (HD quality, higher budget)
curl -X POST https://api.ideogram.ai/v1/api-keys \
  -H "Authorization: Bearer $IDEOGRAM_ADMIN_KEY" \
  -d '{
    "name": "product-design",
    "monthly_credit_limit": 15000,  # 15000 = configured value
    "allowed_models": ["V_2", "V_2_TURBO"],
    "rate_limit_rpm": 60
  }'
```

### Step 2: Enforce Content Safety via Proxy
```typescript
// ideogram-proxy.ts - Pre-screen prompts before sending to API
const BLOCKED_TERMS = ['brand_competitor', 'trademark_name', 'offensive_term'];

function sanitizePrompt(prompt: string, team: string): { allowed: boolean; reason?: string } {
  for (const term of BLOCKED_TERMS) {
    if (prompt.toLowerCase().includes(term)) {
      return { allowed: false, reason: `Blocked term: ${term}` };
    }
  }
  return { allowed: true };
}
```

### Step 3: Set Resolution and Quality Limits per Team
```typescript
const TEAM_LIMITS: Record<string, { maxResolution: string; allowedStyles: string[] }> = {
  marketing:  { maxResolution: 'RESOLUTION_1024_1024', allowedStyles: ['REALISTIC', 'DESIGN'] },
  social:     { maxResolution: 'RESOLUTION_1024_576',  allowedStyles: ['REALISTIC'] },
  product:    { maxResolution: 'RESOLUTION_1024_1024', allowedStyles: ['REALISTIC', 'DESIGN', 'RENDER_3D'] },
};
```

### Step 4: Monitor Credit Consumption
```bash
set -euo pipefail
# Check usage per API key
curl https://api.ideogram.ai/v1/usage \
  -H "Authorization: Bearer $IDEOGRAM_ADMIN_KEY" | \
  jq '.keys[] | {name, credits_used, credits_remaining, images_generated}'
```

### Step 5: Rotate Keys Quarterly
Create replacement keys with identical permissions, update consuming applications, then delete old keys after confirming zero traffic on them for 48 hours.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `402` credit exhausted | Monthly credit limit hit | Increase limit or wait for cycle reset |
| `403` model not allowed | Key restricted from that model | Create key with broader model access |
| `429` rate limited | RPM cap exceeded | Reduce concurrency or increase rate limit |
| Content policy violation | Prompt triggers safety filter | Rephrase prompt, avoid trademarked terms |

## Examples

**Basic usage**: Apply ideogram enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize ideogram enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Ideogram Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack