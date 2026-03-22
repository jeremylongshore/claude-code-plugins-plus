---
name: groq-enterprise-rbac
description: |
  Configure Groq organization management, API key scoping, spending controls, and team access patterns.
  Trigger with phrases like "groq organization", "groq RBAC",
  "groq enterprise", "groq team access", "groq spending limits", "groq multi-team".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, rbac]

---
# Groq Enterprise Access Management

## Overview
Manage team access to Groq's inference API through API key strategy, model-level routing controls, spending limits, and usage monitoring. Groq uses flat API keys (`gsk_` prefix) with no built-in scoping -- access control is implemented at the application layer.

## Groq Access Model
- **API keys** are per-organization, not per-user
- **No built-in scopes** -- every key has full API access
- **Rate limits** are per-organization, shared across all keys
- **Spending limits** are configurable in the Groq Console
- **Projects** allow creating isolated API keys with separate limits

## Instructions

### Step 1: API Key Strategy
```typescript
// Create separate keys per team/service via Groq Console Projects
// Each project gets its own API key and can have independent rate limits

// Key naming convention: {team}-{environment}-{purpose}
const KEY_REGISTRY = {
  // Each team gets a separate Groq Project
  "chatbot-prod":         "gsk_...",  // Project: chatbot-production
  "chatbot-staging":      "gsk_...",  // Project: chatbot-staging
  "analytics-prod":       "gsk_...",  // Project: analytics-production
  "batch-processor":      "gsk_...",  // Project: batch-processing
} as const;
```

### Step 2: Application-Level Model Access Control
```typescript
// Since Groq keys don't have model scoping, implement it in your gateway
interface TeamConfig {
  allowedModels: string[];
  maxTokensPerRequest: number;
  monthlyBudgetUsd: number;
  rateLimitRPM: number;
}

const TEAM_CONFIGS: Record<string, TeamConfig> = {
  chatbot: {
    allowedModels: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    maxTokensPerRequest: 2048,
    monthlyBudgetUsd: 200,
    rateLimitRPM: 60,
  },
  analytics: {
    allowedModels: ["llama-3.1-8b-instant"],  // Only cheapest model
    maxTokensPerRequest: 512,
    monthlyBudgetUsd: 50,
    rateLimitRPM: 30,
  },
  research: {
    allowedModels: [
      "llama-3.3-70b-versatile",
      "llama-3.1-8b-instant",
      "meta-llama/llama-4-scout-17b-16e-instruct",
    ],
    maxTokensPerRequest: 4096,
    monthlyBudgetUsd: 500,
    rateLimitRPM: 120,
  },
};

function validateRequest(team: string, model: string, maxTokens: number): void {
  const config = TEAM_CONFIGS[team];
  if (!config) throw new Error(`Unknown team: ${team}`);
  if (!config.allowedModels.includes(model)) {
    throw new Error(`Team ${team} not authorized for model ${model}`);
  }
  if (maxTokens > config.maxTokensPerRequest) {
    throw new Error(`max_tokens ${maxTokens} exceeds limit ${config.maxTokensPerRequest} for team ${team}`);
  }
}
```

### Step 3: Groq API Gateway
```typescript
import Groq from "groq-sdk";
import PQueue from "p-queue";

// Per-team rate limiting
const teamQueues = new Map<string, PQueue>();

function getTeamQueue(team: string): PQueue {
  if (!teamQueues.has(team)) {
    const config = TEAM_CONFIGS[team];
    teamQueues.set(team, new PQueue({
      intervalCap: config?.rateLimitRPM || 30,
      interval: 60_000,
      concurrency: 5,
    }));
  }
  return teamQueues.get(team)!;
}

// Gateway function: validates, rate-limits, and proxies to Groq
async function groqGateway(
  team: string,
  messages: any[],
  model: string,
  maxTokens: number
) {
  // Validate permissions
  validateRequest(team, model, maxTokens);

  // Check budget
  const monthlySpend = await getTeamMonthlySpend(team);
  const config = TEAM_CONFIGS[team];
  if (monthlySpend >= config.monthlyBudgetUsd) {
    throw new Error(`Team ${team} monthly budget of $${config.monthlyBudgetUsd} exhausted`);
  }

  // Rate-limited execution
  const queue = getTeamQueue(team);
  return queue.add(async () => {
    const groq = new Groq({ apiKey: getTeamApiKey(team) });
    const result = await groq.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
    });

    // Track usage
    await recordTeamUsage(team, model, result.usage!);
    return result;
  });
}
```

### Step 4: Spending Controls
```markdown
## Groq Console Setup (per organization)

1. Go to console.groq.com > Organization > Billing
2. Set monthly spending cap
3. Configure alerts at 50%, 80%, 95% thresholds
4. Enable auto-pause when cap is reached

## Application-Level Controls (per team)
```

```typescript
// Track spending per team
const teamSpending = new Map<string, number>();

async function recordTeamUsage(
  team: string,
  model: string,
  usage: any
): Promise<void> {
  const pricing: Record<string, { input: number; output: number }> = {
    "llama-3.1-8b-instant": { input: 0.05, output: 0.08 },
    "llama-3.3-70b-versatile": { input: 0.59, output: 0.79 },
    "meta-llama/llama-4-scout-17b-16e-instruct": { input: 0.11, output: 0.34 },
  };

  const price = pricing[model] || { input: 0.10, output: 0.10 };
  const cost =
    (usage.prompt_tokens / 1_000_000) * price.input +
    (usage.completion_tokens / 1_000_000) * price.output;

  const current = teamSpending.get(team) || 0;
  teamSpending.set(team, current + cost);

  // Alert at thresholds
  const budget = TEAM_CONFIGS[team].monthlyBudgetUsd;
  const pct = ((current + cost) / budget) * 100;

  if (pct >= 95) {
    console.error(`[ALERT] Team ${team} at ${pct.toFixed(0)}% of monthly budget!`);
  } else if (pct >= 80) {
    console.warn(`[WARN] Team ${team} at ${pct.toFixed(0)}% of monthly budget`);
  }
}
```

### Step 5: API Key Rotation
```bash
set -euo pipefail
# Zero-downtime key rotation process:

# 1. Create new key in Groq Console (same Project)
#    Name: chatbot-prod-2026-04

# 2. Deploy new key alongside old key
#    Both keys are valid simultaneously

# 3. Update secret manager
#    AWS: aws secretsmanager update-secret --secret-id groq/chatbot-prod --secret-string "gsk_new_..."
#    GCP: echo -n "gsk_new_..." | gcloud secrets versions add groq-chatbot-prod --data-file=-

# 4. Restart services to pick up new key

# 5. Monitor for 24h -- verify no requests on old key

# 6. Delete old key in Groq Console
```

### Step 6: Usage Dashboard Query
```typescript
// Weekly usage report per team
function weeklyReport(records: Array<{ team: string; model: string; cost: number; tokens: number }>) {
  const byTeam: Record<string, { cost: number; tokens: number; topModel: string }> = {};

  for (const r of records) {
    if (!byTeam[r.team]) byTeam[r.team] = { cost: 0, tokens: 0, topModel: "" };
    byTeam[r.team].cost += r.cost;
    byTeam[r.team].tokens += r.tokens;
  }

  console.table(
    Object.entries(byTeam).map(([team, data]) => ({
      team,
      cost: `$${data.cost.toFixed(2)}`,
      tokens: data.tokens.toLocaleString(),
      budget: `$${TEAM_CONFIGS[team]?.monthlyBudgetUsd || "N/A"}`,
    }))
  );
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 rate_limit_exceeded` | Org-level RPM/TPM hit | Teams share org limits; reduce aggregate volume |
| `401 invalid_api_key` | Key deleted or rotated | Update secret manager, restart services |
| Budget exhausted | Monthly cap reached | Increase cap or wait for billing cycle reset |
| Wrong model used | No server-side enforcement | Validate model against team config before calling Groq |

## Resources
- [Groq Projects](https://console.groq.com/docs/projects)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq API Keys](https://console.groq.com/keys)

## Next Steps
For migration strategies, see `groq-migration-deep-dive`.
