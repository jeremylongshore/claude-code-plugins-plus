---
name: cohere-enterprise-rbac
description: |
  Configure Cohere enterprise API key management, role-based access, and org controls.
  Use when implementing multi-team API key management, per-team usage limits,
  or setting up organization-level controls for Cohere.
  Trigger with phrases like "cohere enterprise", "cohere RBAC",
  "cohere team keys", "cohere org management", "cohere access control".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Enterprise RBAC

## Overview
Configure enterprise-grade access control for Cohere API v2 with multi-team API key management, per-team model/budget restrictions, and audit trails.

## Prerequisites
- Cohere production API keys
- Understanding of your team/service structure
- Secret management infrastructure

## Cohere Access Model

Cohere uses **API key-based** access control (no built-in RBAC or SSO). Enterprise patterns are implemented in your application layer.

| Cohere Feature | Availability |
|----------------|-------------|
| API key auth | All tiers |
| Multiple API keys | Via dashboard |
| Per-key rate limits | Production: 1000/min |
| Usage dashboard | dashboard.cohere.com |
| SSO/SAML | Not available (API key only) |
| Per-key scoping | Not available |

## Instructions

### Step 1: Multi-Team Key Strategy

```typescript
// Each team gets their own API key for tracking and revocation
interface TeamConfig {
  name: string;
  apiKeyEnvVar: string;
  allowedModels: string[];
  maxTokensPerCall: number;
  dailyBudgetUSD: number;
}

const teamConfigs: Record<string, TeamConfig> = {
  search: {
    name: 'Search Team',
    apiKeyEnvVar: 'CO_API_KEY_SEARCH',
    allowedModels: ['embed-v4.0', 'rerank-v3.5', 'command-r-08-2024'],
    maxTokensPerCall: 1000,
    dailyBudgetUSD: 50,
  },
  chatbot: {
    name: 'Chatbot Team',
    apiKeyEnvVar: 'CO_API_KEY_CHATBOT',
    allowedModels: ['command-a-03-2025', 'command-r7b-12-2024'],
    maxTokensPerCall: 4096,
    dailyBudgetUSD: 200,
  },
  ml: {
    name: 'ML Team',
    apiKeyEnvVar: 'CO_API_KEY_ML',
    allowedModels: ['embed-v4.0', 'embed-multilingual-v3.0'],
    maxTokensPerCall: 500,
    dailyBudgetUSD: 100,
  },
};
```

### Step 2: Team-Scoped Client Factory

```typescript
import { CohereClientV2 } from 'cohere-ai';

const clients = new Map<string, CohereClientV2>();

export function getCohereForTeam(teamId: string): CohereClientV2 {
  if (!clients.has(teamId)) {
    const config = teamConfigs[teamId];
    if (!config) throw new Error(`Unknown team: ${teamId}`);

    const apiKey = process.env[config.apiKeyEnvVar];
    if (!apiKey) throw new Error(`${config.apiKeyEnvVar} not set for team ${teamId}`);

    clients.set(teamId, new CohereClientV2({ token: apiKey }));
  }
  return clients.get(teamId)!;
}
```

### Step 3: Model Access Enforcement

```typescript
function enforceModelAccess(teamId: string, requestedModel: string): void {
  const config = teamConfigs[teamId];
  if (!config) throw new Error(`Unknown team: ${teamId}`);

  if (!config.allowedModels.includes(requestedModel)) {
    throw new Error(
      `Team ${config.name} is not authorized to use model ${requestedModel}. ` +
      `Allowed: ${config.allowedModels.join(', ')}`
    );
  }
}

// Enforced chat wrapper
export async function teamChat(
  teamId: string,
  message: string,
  model: string
): Promise<string> {
  enforceModelAccess(teamId, model);

  const config = teamConfigs[teamId];
  const cohere = getCohereForTeam(teamId);

  const response = await cohere.chat({
    model,
    messages: [{ role: 'user', content: message }],
    maxTokens: config.maxTokensPerCall,
  });

  return response.message?.content?.[0]?.text ?? '';
}
```

### Step 4: Per-Team Budget Enforcement

```typescript
class TeamBudgetTracker {
  private dailySpend = new Map<string, number>();
  private lastReset = new Date();

  track(teamId: string, tokens: { input: number; output: number }): void {
    // Reset daily at midnight
    const now = new Date();
    if (now.getDate() !== this.lastReset.getDate()) {
      this.dailySpend.clear();
      this.lastReset = now;
    }

    const current = this.dailySpend.get(teamId) ?? 0;
    // Rough cost estimate per 1M tokens (check cohere.com/pricing)
    const cost = (tokens.input / 1_000_000) * 0.5 + (tokens.output / 1_000_000) * 1.5;
    this.dailySpend.set(teamId, current + cost);
  }

  canProceed(teamId: string): boolean {
    const config = teamConfigs[teamId];
    if (!config) return false;
    const spent = this.dailySpend.get(teamId) ?? 0;
    return spent < config.dailyBudgetUSD;
  }

  getSpend(teamId: string): number {
    return this.dailySpend.get(teamId) ?? 0;
  }
}

const budgetTracker = new TeamBudgetTracker();

// Budget-enforced call
export async function budgetedChat(teamId: string, message: string, model: string): Promise<string> {
  if (!budgetTracker.canProceed(teamId)) {
    throw new Error(`Team ${teamId} has exceeded daily budget of $${teamConfigs[teamId].dailyBudgetUSD}`);
  }

  const response = await teamChat(teamId, message, model);

  // Track usage after successful call
  // Note: actual usage comes from response.usage.billedUnits
  return response;
}
```

### Step 5: API Gateway Middleware

```typescript
import { Request, Response, NextFunction } from 'express';

// Extract team from auth header or JWT
function extractTeamId(req: Request): string {
  const apiKey = req.headers['x-api-key'] as string;
  // Map API keys to teams (store in DB, not code)
  const teamMap = new Map<string, string>([
    ['search-api-key-hash', 'search'],
    ['chatbot-api-key-hash', 'chatbot'],
    ['ml-api-key-hash', 'ml'],
  ]);

  const teamId = teamMap.get(apiKey);
  if (!teamId) throw new Error('Invalid API key');
  return teamId;
}

function cohereAccessControl(allowedEndpoints: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      const teamId = extractTeamId(req);

      // Check budget
      if (!budgetTracker.canProceed(teamId)) {
        return res.status(429).json({ error: 'Daily budget exceeded' });
      }

      // Attach team context
      (req as any).cohereTeam = teamId;
      next();
    } catch (err) {
      res.status(403).json({ error: (err as Error).message });
    }
  };
}

// Usage
app.post('/api/chat', cohereAccessControl(['chat']), chatHandler);
app.post('/api/embed', cohereAccessControl(['embed']), embedHandler);
```

### Step 6: Audit Trail

```typescript
interface CohereAccessLog {
  timestamp: Date;
  teamId: string;
  endpoint: string;
  model: string;
  tokensUsed: { input: number; output: number };
  costEstimate: number;
  success: boolean;
  errorCode?: number;
}

async function logAccess(entry: CohereAccessLog): Promise<void> {
  // Write to your audit database
  await db.cohereAccessLog.insert(entry);

  // Alert on suspicious patterns
  if (entry.costEstimate > 10) {
    console.warn(`High-cost call: team=${entry.teamId} cost=$${entry.costEstimate.toFixed(2)}`);
  }
}

// Usage reporting query
// SELECT team_id, SUM(cost_estimate), COUNT(*) as calls
// FROM cohere_access_log
// WHERE timestamp > NOW() - INTERVAL '24 hours'
// GROUP BY team_id
// ORDER BY SUM(cost_estimate) DESC;
```

## Key Rotation Per Team

```bash
# Rotate a team's API key
# 1. Generate new key at dashboard.cohere.com
# 2. Update the team's secret
aws secretsmanager update-secret \
  --secret-id cohere/search-team/api-key \
  --secret-string "new-key-here"

# 3. Restart team's services
kubectl rollout restart deployment/search-service

# 4. Verify and revoke old key
# 5. Update audit log with rotation event
```

## Output
- Multi-team API key management with separate keys per team
- Model access enforcement (search team cannot use chat models)
- Per-team daily budget limits with automatic cutoff
- Audit trail for all Cohere API calls with team attribution
- API gateway middleware for access control

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Team key missing | Env var not set | Check secret manager |
| Model access denied | Not in allowedModels | Update team config |
| Budget exceeded | High usage | Increase limit or optimize |
| Key rotation gap | Old key revoked too early | Overlap keys during rotation |

## Resources
- [Cohere API Keys](https://dashboard.cohere.com/api-keys)
- [Cohere Pricing](https://cohere.com/pricing)
- [Cohere Rate Limits](https://docs.cohere.com/docs/rate-limits)

## Next Steps
For major migrations, see `cohere-migration-deep-dive`.
