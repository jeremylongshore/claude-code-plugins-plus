---
name: ideogram-enterprise-rbac
description: |
  Implement team-based access control and credit management for Ideogram.
  Use when managing multiple teams with separate budgets, enforcing content policies,
  or implementing API key isolation for enterprise Ideogram usage.
  Trigger with phrases like "ideogram RBAC", "ideogram enterprise",
  "ideogram teams", "ideogram permissions", "ideogram multi-tenant".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, rbac, enterprise]

---
# Ideogram Enterprise RBAC

## Overview
Implement team-based access control for Ideogram's API. Since Ideogram uses a single API key per account with no built-in roles or scopes, enterprise access control must be implemented at the application layer: separate API keys per team, proxy-based content filtering, per-team budget limits, and usage tracking.

## Architecture

```
┌──────────────────────────────────────────┐
│  Application Proxy Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Marketing│  │ Product  │  │ Social │ │
│  │ API Key  │  │ API Key  │  │API Key │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       └──────────────┼────────────┘      │
│                      ▼                   │
│  ┌────────────────────────────────────┐  │
│  │ Content Filter + Budget Enforcer   │  │
│  └──────────────────┬─────────────────┘  │
└─────────────────────┼────────────────────┘
                      ▼
          Ideogram API (api.ideogram.ai)
```

## Instructions

### Step 1: Team Configuration
```typescript
interface TeamConfig {
  name: string;
  apiKey: string;             // Separate Ideogram API key per team
  dailyBudgetUSD: number;
  allowedStyles: string[];
  allowedModels: string[];
  maxConcurrency: number;
  contentPolicy: "strict" | "moderate" | "permissive";
}

const TEAM_CONFIGS: Record<string, TeamConfig> = {
  marketing: {
    name: "Marketing",
    apiKey: process.env.IDEOGRAM_KEY_MARKETING!,
    dailyBudgetUSD: 20,
    allowedStyles: ["DESIGN", "REALISTIC"],
    allowedModels: ["V_2", "V_2_TURBO"],
    maxConcurrency: 5,
    contentPolicy: "strict",
  },
  product: {
    name: "Product Design",
    apiKey: process.env.IDEOGRAM_KEY_PRODUCT!,
    dailyBudgetUSD: 50,
    allowedStyles: ["DESIGN", "REALISTIC", "RENDER_3D", "GENERAL"],
    allowedModels: ["V_2", "V_2_TURBO"],
    maxConcurrency: 8,
    contentPolicy: "moderate",
  },
  social: {
    name: "Social Media",
    apiKey: process.env.IDEOGRAM_KEY_SOCIAL!,
    dailyBudgetUSD: 10,
    allowedStyles: ["DESIGN", "ANIME", "GENERAL"],
    allowedModels: ["V_2_TURBO"],
    maxConcurrency: 3,
    contentPolicy: "strict",
  },
};
```

### Step 2: Content Policy Enforcement
```typescript
interface ContentCheck {
  allowed: boolean;
  reason?: string;
}

const BLOCKED_TERMS: Record<string, RegExp[]> = {
  strict: [
    /\b(competitor|trademark|brand)\b/i,
    /\b(violent|weapon|blood|gore)\b/i,
    /\b(nsfw|nude|explicit)\b/i,
  ],
  moderate: [
    /\b(nsfw|nude|explicit)\b/i,
  ],
  permissive: [],
};

function checkContentPolicy(prompt: string, policy: "strict" | "moderate" | "permissive"): ContentCheck {
  const patterns = BLOCKED_TERMS[policy] ?? [];
  for (const pattern of patterns) {
    if (pattern.test(prompt)) {
      return { allowed: false, reason: `Blocked by ${policy} policy: ${pattern.source}` };
    }
  }
  if (prompt.length > 10000) {
    return { allowed: false, reason: "Prompt exceeds 10,000 character limit" };
  }
  return { allowed: true };
}
```

### Step 3: Budget Enforcer
```typescript
const dailySpend = new Map<string, number>();

function trackSpend(teamId: string, model: string, numImages: number = 1) {
  const costPerImage: Record<string, number> = {
    V_2_TURBO: 0.05, V_2: 0.08, V_2A_TURBO: 0.025, V_2A: 0.04,
  };

  const cost = (costPerImage[model] ?? 0.08) * numImages;
  const current = dailySpend.get(teamId) ?? 0;
  dailySpend.set(teamId, current + cost);

  return current + cost;
}

function checkBudget(teamId: string): { allowed: boolean; remaining: number } {
  const config = TEAM_CONFIGS[teamId];
  if (!config) return { allowed: false, remaining: 0 };

  const spent = dailySpend.get(teamId) ?? 0;
  const remaining = config.dailyBudgetUSD - spent;

  return { allowed: remaining > 0, remaining };
}

// Reset daily at midnight
setInterval(() => {
  dailySpend.clear();
  console.log("Daily budget counters reset");
}, 86400000);
```

### Step 4: Team-Scoped Proxy
```typescript
async function teamGenerate(
  teamId: string,
  prompt: string,
  options: { style_type?: string; model?: string; aspect_ratio?: string } = {}
) {
  const config = TEAM_CONFIGS[teamId];
  if (!config) throw new Error(`Unknown team: ${teamId}`);

  // Check content policy
  const contentCheck = checkContentPolicy(prompt, config.contentPolicy);
  if (!contentCheck.allowed) {
    throw new Error(`Content blocked: ${contentCheck.reason}`);
  }

  // Check style permission
  const style = options.style_type ?? "AUTO";
  if (style !== "AUTO" && !config.allowedStyles.includes(style)) {
    throw new Error(`Style ${style} not allowed for team ${config.name}`);
  }

  // Check model permission
  const model = options.model ?? config.allowedModels[0];
  if (!config.allowedModels.includes(model)) {
    throw new Error(`Model ${model} not allowed for team ${config.name}`);
  }

  // Check budget
  const budget = checkBudget(teamId);
  if (!budget.allowed) {
    throw new Error(`Daily budget exceeded for team ${config.name}. Remaining: $${budget.remaining.toFixed(2)}`);
  }

  // Generate using team's API key
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": config.apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model,
        style_type: style,
        aspect_ratio: options.aspect_ratio ?? "ASPECT_1_1",
        magic_prompt_option: "AUTO",
      },
    }),
  });

  if (!response.ok) throw new Error(`Ideogram API error: ${response.status}`);

  // Track spending
  trackSpend(teamId, model);

  return response.json();
}
```

### Step 5: Usage Dashboard Data
```typescript
function teamUsageReport() {
  const report = [];
  for (const [teamId, config] of Object.entries(TEAM_CONFIGS)) {
    const spent = dailySpend.get(teamId) ?? 0;
    report.push({
      team: config.name,
      dailyBudget: config.dailyBudgetUSD,
      spent: spent.toFixed(2),
      remaining: (config.dailyBudgetUSD - spent).toFixed(2),
      utilization: `${((spent / config.dailyBudgetUSD) * 100).toFixed(0)}%`,
    });
  }
  console.table(report);
  return report;
}
```

### Step 6: Key Rotation Schedule
```
Quarterly key rotation process:
1. Create new API key in Ideogram dashboard for each team
2. Update secrets in your secret manager
3. Deploy with new keys to staging, verify
4. Deploy to production
5. Monitor for 48 hours
6. Delete old keys from Ideogram dashboard
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Budget exceeded | Daily limit hit | Wait for reset or increase limit |
| Style not allowed | Team policy restriction | Use an allowed style type |
| Content blocked | Prompt failed policy | Rephrase to comply with team policy |
| Key not set | Missing env variable | Check team-specific key config |

## Output
- Per-team API key isolation
- Content policy enforcement (strict/moderate/permissive)
- Daily budget tracking with automatic enforcement
- Team-scoped generation proxy
- Usage dashboard data for reporting

## Resources
- [Ideogram API Setup](https://developer.ideogram.ai/ideogram-api/api-setup)
- [API Pricing](https://ideogram.ai/features/api-pricing)
- Enterprise: `partnership@ideogram.ai`

## Next Steps
For migration strategies, see `ideogram-migration-deep-dive`.
