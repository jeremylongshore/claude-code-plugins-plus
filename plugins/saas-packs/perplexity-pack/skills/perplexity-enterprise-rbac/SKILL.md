---
name: perplexity-enterprise-rbac
description: |
  Configure Perplexity API key scoping, per-team model access, cost controls,
  and search domain restrictions for enterprise deployments.
  Trigger with phrases like "perplexity enterprise", "perplexity RBAC",
  "perplexity team access", "perplexity roles", "perplexity permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, rbac]

---
# Perplexity Enterprise RBAC

## Overview
Control access to Perplexity Sonar API at the organizational level. Perplexity does not have built-in RBAC -- you implement access control through: separate API keys per team/environment, a gateway that enforces model and budget policies, and domain restrictions for compliance.

## Access Control Strategy

| Layer | Mechanism | Perplexity Support |
|-------|-----------|-------------------|
| Authentication | API key per team | Yes (multiple keys) |
| Model restriction | Gateway enforcement | Build yourself |
| Budget cap | Per-key monthly limit | Via dashboard |
| Domain restriction | `search_domain_filter` | Yes (per-request) |
| Rate limiting | Gateway + key limits | Yes (per-key RPM) |

## Prerequisites
- Perplexity API account with admin access
- Separate API keys per team/environment
- Gateway or middleware for policy enforcement

## Instructions

### Step 1: Create Per-Team API Keys
Generate separate keys at [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api):

```
Key: pplx-support-bot-prod     → Budget: $200/mo, sonar only
Key: pplx-research-team        → Budget: $1000/mo, sonar + sonar-pro
Key: pplx-data-team            → Budget: $500/mo, sonar only
Key: pplx-executive-reports    → Budget: $300/mo, sonar-pro
```

### Step 2: Gateway with Policy Enforcement
```typescript
// perplexity-gateway.ts
import OpenAI from "openai";

interface TeamPolicy {
  apiKey: string;
  allowedModels: string[];
  maxTokensPerRequest: number;
  maxRequestsPerMinute: number;
  requiredDomainFilter?: string[];  // Force search to specific domains
  blockedDomainFilter?: string[];   // Block specific domains
}

const TEAM_POLICIES: Record<string, TeamPolicy> = {
  support: {
    apiKey: process.env.PPLX_KEY_SUPPORT!,
    allowedModels: ["sonar"],
    maxTokensPerRequest: 512,
    maxRequestsPerMinute: 30,
  },
  research: {
    apiKey: process.env.PPLX_KEY_RESEARCH!,
    allowedModels: ["sonar", "sonar-pro", "sonar-reasoning-pro"],
    maxTokensPerRequest: 4096,
    maxRequestsPerMinute: 50,
  },
  compliance: {
    apiKey: process.env.PPLX_KEY_COMPLIANCE!,
    allowedModels: ["sonar", "sonar-pro"],
    maxTokensPerRequest: 2048,
    maxRequestsPerMinute: 20,
    requiredDomainFilter: ["sec.gov", "edgar.sec.gov", "law.cornell.edu"],
  },
  marketing: {
    apiKey: process.env.PPLX_KEY_MARKETING!,
    allowedModels: ["sonar"],
    maxTokensPerRequest: 1024,
    maxRequestsPerMinute: 20,
    blockedDomainFilter: ["-competitor1.com", "-competitor2.com"],
  },
};

function enforcePolicy(
  team: string,
  requestedModel: string,
  requestedTokens: number
): { client: OpenAI; model: string; maxTokens: number; domainFilter?: string[] } {
  const policy = TEAM_POLICIES[team];
  if (!policy) throw new Error(`Unknown team: ${team}`);

  if (!policy.allowedModels.includes(requestedModel)) {
    console.warn(`Team ${team} not allowed ${requestedModel}, using ${policy.allowedModels[0]}`);
  }

  const model = policy.allowedModels.includes(requestedModel)
    ? requestedModel
    : policy.allowedModels[0];

  const maxTokens = Math.min(requestedTokens, policy.maxTokensPerRequest);

  return {
    client: new OpenAI({ apiKey: policy.apiKey, baseURL: "https://api.perplexity.ai" }),
    model,
    maxTokens,
    domainFilter: policy.requiredDomainFilter || policy.blockedDomainFilter,
  };
}
```

### Step 3: Enforced Search with Domain Restrictions
```typescript
async function teamSearch(
  team: string,
  query: string,
  requestedModel: string = "sonar"
) {
  const { client, model, maxTokens, domainFilter } = enforcePolicy(
    team, requestedModel, 2048
  );

  const response = await client.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
    max_tokens: maxTokens,
    ...(domainFilter && { search_domain_filter: domainFilter }),
  } as any);

  return {
    answer: response.choices[0].message.content,
    citations: (response as any).citations || [],
    model: response.model,
    team,
    tokens: response.usage?.total_tokens,
  };
}

// Usage
const result = await teamSearch("compliance", "latest SEC filing for AAPL", "sonar-pro");
// -> Uses sonar-pro (allowed for compliance team)
// -> Searches only sec.gov, edgar.sec.gov, law.cornell.edu

const supportResult = await teamSearch("support", "How to reset password", "sonar-pro");
// -> Downgrades to sonar (support team only allowed sonar)
```

### Step 4: Usage Tracking per Team
```typescript
class TeamUsageTracker {
  private usage: Map<string, Array<{ timestamp: number; tokens: number; model: string; cost: number }>> = new Map();

  record(team: string, tokens: number, model: string) {
    const entries = this.usage.get(team) || [];
    const cost = model === "sonar-pro" ? tokens * 0.000009 : tokens * 0.000001;
    entries.push({ timestamp: Date.now(), tokens, model, cost });
    this.usage.set(team, entries);
  }

  getDailySummary(team: string) {
    const today = new Date().toDateString();
    const entries = (this.usage.get(team) || []).filter(
      (e) => new Date(e.timestamp).toDateString() === today
    );
    return {
      team,
      queries: entries.length,
      totalTokens: entries.reduce((s, e) => s + e.tokens, 0),
      estimatedCost: entries.reduce((s, e) => s + e.cost, 0).toFixed(4),
      modelBreakdown: {
        sonar: entries.filter((e) => e.model === "sonar").length,
        "sonar-pro": entries.filter((e) => e.model === "sonar-pro").length,
      },
    };
  }
}
```

### Step 5: Key Rotation Schedule
Rotate API keys every 90 days. Name keys with quarter (`pplx-research-2026Q1`) for tracking.

```bash
set -euo pipefail
# 1. Generate new key at perplexity.ai/settings/api
# 2. Deploy new key alongside old key (24-hour overlap)
# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $NEW_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
# 4. Remove old key from perplexity.ai/settings/api
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401` for a team | Key expired or revoked | Regenerate key for that team |
| Model downgrade unexpected | Policy restricting access | Check team's `allowedModels` |
| Compliance citations from wrong domain | Domain filter not applied | Verify `requiredDomainFilter` in policy |
| Budget exceeded | Team over monthly cap | Alert team lead, increase cap or throttle |

## Output
- Per-team API key management
- Gateway enforcing model and token policies
- Domain-restricted search for compliance teams
- Usage tracking and cost allocation per team

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [API Key Management](https://www.perplexity.ai/settings/api)

## Next Steps
For migration planning, see `perplexity-migration-deep-dive`.
