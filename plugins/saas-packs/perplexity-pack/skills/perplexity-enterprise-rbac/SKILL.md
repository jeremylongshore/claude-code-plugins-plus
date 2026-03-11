---
name: perplexity-enterprise-rbac
description: |
  Configure Perplexity enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Perplexity.
  Trigger with phrases like "perplexity SSO", "perplexity RBAC",
  "perplexity enterprise", "perplexity roles", "perplexity permissions", "perplexity SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Enterprise RBAC

## Overview
Manage access to Perplexity's AI search API through API key scoping and per-query cost controls. Perplexity charges per query with pricing varying by model -- `sonar` (lightweight) costs less per query than `sonar-pro` (deeper research). Access control centers on creating scoped API keys with model restrictions, rate limits, and monthly budget caps to prevent teams from inadvertently using expensive models.

## Prerequisites
- Perplexity API account at docs.perplexity.ai
- API key with organization admin access
- Understanding of model pricing tiers (sonar vs sonar-pro)

## Instructions

### Step 1: Create Model-Restricted API Keys
```bash
# Key for the support bot (lightweight model only, low cost)
curl -X POST https://api.perplexity.ai/v1/api-keys \
  -H "Authorization: Bearer $PPLX_ADMIN_KEY" \
  -d '{
    "name": "support-bot-prod",
    "allowed_models": ["sonar"],
    "rate_limit_rpm": 100,
    "monthly_budget_usd": 200
  }'

# Key for the research team (full model access)
curl -X POST https://api.perplexity.ai/v1/api-keys \
  -H "Authorization: Bearer $PPLX_ADMIN_KEY" \
  -d '{
    "name": "research-team",
    "allowed_models": ["sonar", "sonar-pro"],
    "rate_limit_rpm": 60,
    "monthly_budget_usd": 1000
  }'
```

### Step 2: Implement a Gateway with Query Routing
```typescript
// pplx-gateway.ts - Route queries to appropriate model by team
const TEAM_CONFIG: Record<string, { model: string; maxTokens: number }> = {
  support:    { model: 'sonar',     maxTokens: 512 },
  sales:      { model: 'sonar',     maxTokens: 1024 },
  research:   { model: 'sonar-pro', maxTokens: 4096 },
};

function getModelForTeam(team: string): { model: string; maxTokens: number } {
  return TEAM_CONFIG[team] || TEAM_CONFIG.support;
}
```

### Step 3: Configure Search Domain Restrictions
```bash
# Restrict search to approved sources for compliance
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PPLX_API_KEY" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "latest SEC filing for AAPL"}],
    "search_domain_filter": ["sec.gov", "edgar.sec.gov"],
    "return_citations": true
  }'
```

### Step 4: Monitor Usage and Cost
```bash
# Check API usage by key
curl https://api.perplexity.ai/v1/usage \
  -H "Authorization: Bearer $PPLX_ADMIN_KEY" | \
  jq '.keys[] | {name, queries_today, cost_today_usd, budget_remaining}'
```

### Step 5: Enforce Key Rotation
Rotate API keys every 90 days. Label keys with creation date (`research-team-2026Q1`) for easy tracking. Create new key, deploy, then delete old key after 24-hour overlap.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 invalid_api_key` | Key revoked or expired | Generate new key |
| `403 model_not_allowed` | Key restricted from sonar-pro | Use sonar or request broader key |
| `429 rate_limited` | RPM cap exceeded | Add backoff or increase rate limit |
| Budget cap reached | Monthly spend exhausted | Increase budget or wait for cycle reset |

## Examples
```bash
# Quick cost check: estimate monthly spend from today's usage
curl -s https://api.perplexity.ai/v1/usage \
  -H "Authorization: Bearer $PPLX_ADMIN_KEY" | \
  jq '{daily_cost: .total_cost_today, projected_monthly: (.total_cost_today * 30)}'
```
