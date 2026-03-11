---
name: groq-enterprise-rbac
description: |
  Configure Groq enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Groq.
  Trigger with phrases like "groq SSO", "groq RBAC",
  "groq enterprise", "groq roles", "groq permissions", "groq SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Groq Enterprise RBAC

## Overview
Manage access to Groq's ultra-fast LPU inference API through API key scoping and organization-level controls. Groq's per-token pricing is extremely low (orders of magnitude cheaper than GPU-based providers), but its speed makes runaway usage easy. Access control centers on API key management with per-key rate limits (requests per minute and tokens per minute), model restrictions, and organization-level spending caps.

## Prerequisites
- Groq Cloud account at console.groq.com
- Organization created with billing configured
- At least one API key with organization admin scope

## Instructions

### Step 1: Create Rate-Limited API Keys per Team
```bash
# Key for the chatbot team (high RPM, small model)
curl -X POST https://api.groq.com/openai/v1/api-keys \
  -H "Authorization: Bearer $GROQ_ADMIN_KEY" \
  -d '{
    "name": "chatbot-prod",
    "allowed_models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "requests_per_minute": 500,
    "tokens_per_minute": 100000
  }'

# Key for batch processing (lower RPM but higher token limit)
curl -X POST https://api.groq.com/openai/v1/api-keys \
  -H "Authorization: Bearer $GROQ_ADMIN_KEY" \
  -d '{
    "name": "batch-processor",
    "allowed_models": ["llama-3.1-8b-instant"],
    "requests_per_minute": 60,
    "tokens_per_minute": 500000
  }'
```

### Step 2: Implement Model-Level Access Control
```typescript
// groq-gateway.ts - Enforce model restrictions before forwarding
const TEAM_MODEL_ACCESS: Record<string, string[]> = {
  chatbot:    ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'],
  analytics:  ['llama-3.1-8b-instant'],  // Cheapest model only
  research:   ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
};

function validateModelAccess(team: string, model: string): boolean {
  return TEAM_MODEL_ACCESS[team]?.includes(model) ?? false;
}
```

### Step 3: Set Organization Spending Limits
In the Groq Console > Organization > Billing:
- Set monthly spending cap (e.g., $500/month)
- Configure alerts at $100, $250, $400 thresholds
- Enable auto-pause when cap is reached (prevents surprise bills)

### Step 4: Monitor Key Usage
```bash
# Check usage across all API keys
curl https://api.groq.com/openai/v1/usage \
  -H "Authorization: Bearer $GROQ_ADMIN_KEY" | \
  jq '.usage_by_key[] | {key_name, requests_today, tokens_today, estimated_cost_usd}'
```

### Step 5: Rotate Keys with Zero Downtime
```bash
# 1. Create replacement key with same permissions
# 2. Deploy new key to services
# 3. Monitor for 24h to confirm no traffic on old key
# 4. Delete old key
curl -X DELETE "https://api.groq.com/openai/v1/api-keys/OLD_KEY_ID" \
  -H "Authorization: Bearer $GROQ_ADMIN_KEY"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 rate_limit_exceeded` | RPM or TPM cap hit | Groq rate limits are strict; add exponential backoff |
| `401 invalid_api_key` | Key deleted or expired | Generate new key in Groq Console |
| `model_not_available` | Model not in key's allowed list | Create key with broader model access |
| Spending cap paused API | Monthly budget reached | Increase cap or wait for billing cycle |

## Examples
```bash
# Quick health check: list available models for your key
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | jq '.data[].id'
```

```bash
# Estimate monthly cost from current daily usage
DAILY=$(curl -s https://api.groq.com/openai/v1/usage \
  -H "Authorization: Bearer $GROQ_ADMIN_KEY" | jq '.total_cost_today')
echo "Projected monthly cost: \$$(echo "$DAILY * 30" | bc)"
```
