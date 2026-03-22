---
name: exa-enterprise-rbac
description: |
  Manage Exa API key scoping, team access controls, and domain restrictions.
  Use when implementing multi-key access control, configuring per-team search limits,
  or setting up organization-level Exa governance.
  Trigger with phrases like "exa access control", "exa RBAC",
  "exa enterprise", "exa team keys", "exa permissions".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, rbac, enterprise]

---
# Exa Enterprise RBAC

## Overview
Manage access to Exa search API through API key scoping and application-level controls. Exa is API-key-based (no built-in RBAC), so access control is implemented through multiple API keys per use case, application-layer permission enforcement, domain restrictions per team, and per-key usage monitoring.

## Prerequisites
- Exa API account with team/enterprise plan
- Dashboard access at dashboard.exa.ai
- Multiple API keys for key isolation

## Instructions

### Step 1: Key-Per-Use-Case Architecture
```typescript
// config/exa-keys.ts
import Exa from "exa-js";

// Create separate clients for each use case
const exaClients = {
  // High-volume RAG pipeline — production key with higher limits
  ragPipeline: new Exa(process.env.EXA_KEY_RAG!),

  // Internal research tool — lower volume key
  researchTool: new Exa(process.env.EXA_KEY_RESEARCH!),

  // Customer-facing search — separate key for isolation
  customerSearch: new Exa(process.env.EXA_KEY_CUSTOMER!),
};

export function getExaForUseCase(
  useCase: keyof typeof exaClients
): Exa {
  const client = exaClients[useCase];
  if (!client) throw new Error(`No Exa client for use case: ${useCase}`);
  return client;
}
```

### Step 2: Application-Level Permission Enforcement
```typescript
// middleware/exa-permissions.ts
interface ExaPermissions {
  maxResults: number;
  allowedTypes: ("auto" | "neural" | "keyword" | "fast" | "deep")[];
  allowedCategories: string[];
  includeDomains?: string[];     // restrict to these domains
  dailySearchLimit: number;
}

const ROLE_PERMISSIONS: Record<string, ExaPermissions> = {
  "rag-pipeline": {
    maxResults: 10,
    allowedTypes: ["neural", "auto"],
    allowedCategories: [],
    dailySearchLimit: 10000,
  },
  "research-analyst": {
    maxResults: 25,
    allowedTypes: ["neural", "keyword", "auto", "deep"],
    allowedCategories: ["research paper", "news"],
    dailySearchLimit: 500,
  },
  "marketing-team": {
    maxResults: 5,
    allowedTypes: ["keyword", "auto"],
    allowedCategories: ["company", "news"],
    dailySearchLimit: 100,
  },
  "compliance-team": {
    maxResults: 10,
    allowedTypes: ["keyword", "auto"],
    allowedCategories: [],
    includeDomains: ["nist.gov", "owasp.org", "sans.org", "sec.gov"],
    dailySearchLimit: 200,
  },
};

function validateSearchRequest(
  role: string,
  searchType: string,
  numResults: number,
  category?: string
): { allowed: boolean; reason?: string } {
  const perms = ROLE_PERMISSIONS[role];
  if (!perms) return { allowed: false, reason: "Unknown role" };
  if (!perms.allowedTypes.includes(searchType as any)) {
    return { allowed: false, reason: `Search type ${searchType} not allowed for ${role}` };
  }
  if (numResults > perms.maxResults) {
    return { allowed: false, reason: `Max ${perms.maxResults} results for ${role}` };
  }
  if (category && perms.allowedCategories.length > 0 && !perms.allowedCategories.includes(category)) {
    return { allowed: false, reason: `Category ${category} not allowed for ${role}` };
  }
  return { allowed: true };
}
```

### Step 3: Domain Restrictions per Team
```typescript
// Enforce domain restrictions so compliance-sensitive teams
// only see results from vetted sources
async function enforcedSearch(
  exa: Exa,
  role: string,
  query: string,
  opts: any = {}
) {
  const perms = ROLE_PERMISSIONS[role];
  if (!perms) throw new Error(`Unknown role: ${role}`);

  const validation = validateSearchRequest(
    role,
    opts.type || "auto",
    opts.numResults || 10,
    opts.category
  );
  if (!validation.allowed) throw new Error(validation.reason);

  return exa.searchAndContents(query, {
    ...opts,
    numResults: Math.min(opts.numResults || 10, perms.maxResults),
    type: opts.type || "auto",
    // Merge domain restrictions from role permissions
    includeDomains: perms.includeDomains || opts.includeDomains,
  });
}
```

### Step 4: Per-Key Usage Tracking
```typescript
// Track usage per API key / role for budget enforcement
class KeyUsageTracker {
  private usage = new Map<string, { count: number; resetAt: number }>();

  checkAndIncrement(role: string): void {
    const perms = ROLE_PERMISSIONS[role];
    if (!perms) throw new Error(`Unknown role: ${role}`);

    const now = Date.now();
    const dayStart = new Date().setHours(0, 0, 0, 0);
    let entry = this.usage.get(role);

    if (!entry || entry.resetAt < now) {
      entry = { count: 0, resetAt: dayStart + 24 * 60 * 60 * 1000 };
    }

    if (entry.count >= perms.dailySearchLimit) {
      throw new Error(
        `Daily search limit (${perms.dailySearchLimit}) exceeded for ${role}`
      );
    }

    entry.count++;
    this.usage.set(role, entry);
  }

  getUsage(role: string) {
    const entry = this.usage.get(role);
    const limit = ROLE_PERMISSIONS[role]?.dailySearchLimit || 0;
    return {
      used: entry?.count || 0,
      limit,
      remaining: limit - (entry?.count || 0),
    };
  }
}
```

### Step 5: Key Rotation Procedure
```bash
set -euo pipefail
# 1. Create new key in Exa dashboard (dashboard.exa.ai)
# 2. Deploy new key alongside old key
# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $NEW_EXA_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"key rotation test","numResults":1}'

# 4. Switch traffic to new key
# 5. Monitor for errors
# 6. Revoke old key in dashboard after 24h
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401` on search | Invalid or revoked API key | Regenerate in dashboard |
| `429 rate limited` | Key-level rate limit exceeded | Distribute across keys |
| Daily limit hit | Search budget exhausted | Adjust limits or wait for reset |
| Wrong domain results | Missing domain filter | Apply `includeDomains` per role |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Dashboard](https://dashboard.exa.ai)
- [Exa API Key Usage](https://docs.exa.ai/reference/team-management/get-api-key-usage)

## Next Steps
For policy enforcement, see `exa-policy-guardrails`. For multi-env setup, see `exa-multi-env-setup`.
