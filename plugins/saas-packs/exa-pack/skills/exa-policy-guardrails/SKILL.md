---
name: exa-policy-guardrails
description: |
  Implement content policy enforcement, domain filtering, and usage guardrails for Exa.
  Use when setting up content safety rules, restricting search domains,
  or enforcing query and budget policies for Exa integrations.
  Trigger with phrases like "exa policy", "exa content filter",
  "exa guardrails", "exa domain allowlist", "exa content moderation".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, policy, content-moderation]

---
# Exa Policy Guardrails

## Overview
Policy enforcement for Exa neural search integrations. Exa searches the open web, so results may include unreliable sources, competitor content, or inappropriate material. This skill covers domain allowlists/blocklists (via Exa's `includeDomains`/`excludeDomains`), content moderation, query sanitization, freshness policies, and per-user budget enforcement.

## Prerequisites
- `exa-js` installed and configured
- Content policy requirements defined
- Redis for per-user quota tracking (optional)

## Instructions

### Step 1: Domain Filtering (Built-in Exa Feature)
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// Exa supports up to 1200 domains in includeDomains/excludeDomains
const TRUSTED_SOURCES = {
  medical: [
    "pubmed.ncbi.nlm.nih.gov", "who.int", "cdc.gov",
    "nejm.org", "nature.com", "thelancet.com",
  ],
  technical: [
    "github.com", "stackoverflow.com", "developer.mozilla.org",
    "docs.python.org", "nodejs.org", "arxiv.org",
  ],
  news: [
    "reuters.com", "apnews.com", "bbc.com",
    "techcrunch.com", "arstechnica.com",
  ],
};

const BLOCKED_DOMAINS = [
  "competitor1.com", "competitor2.io",
  "spam-farm.com", "content-mill.net",
];

async function policySearch(
  query: string,
  category: keyof typeof TRUSTED_SOURCES | "general"
) {
  const opts: any = {
    type: "auto",
    numResults: 10,
    text: { maxCharacters: 1000 },
    moderation: true,  // Exa's built-in content moderation
  };

  if (category !== "general" && TRUSTED_SOURCES[category]) {
    opts.includeDomains = TRUSTED_SOURCES[category];
  } else {
    opts.excludeDomains = BLOCKED_DOMAINS;
  }

  return exa.searchAndContents(query, opts);
}
```

### Step 2: Query Content Policy
```typescript
const BLOCKED_PATTERNS = [
  /how to (hack|exploit|attack|ddos)/i,
  /(buy|purchase|order)\s+(drugs|weapons|firearms)/i,
  /personal.*(address|phone|ssn|social security)/i,
  /generate.*(malware|ransomware|virus)/i,
];

function validateQuery(input: string): string {
  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(input)) {
      throw new PolicyViolation("Query blocked by content policy");
    }
  }

  // Sanitize
  return input
    .replace(/[<>{}]/g, "")     // strip HTML/template chars
    .replace(/\0/g, "")         // remove null bytes
    .trim()
    .substring(0, 500);         // cap query length
}

class PolicyViolation extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PolicyViolation";
  }
}
```

### Step 3: Freshness Policy
```typescript
// Enforce minimum recency for time-sensitive use cases
function applyFreshnessPolicy(
  opts: any,
  maxAgeDays: number
): any {
  const cutoff = new Date(Date.now() - maxAgeDays * 24 * 60 * 60 * 1000);
  return {
    ...opts,
    startPublishedDate: cutoff.toISOString(),
  };
}

// Usage: only return results from the last 90 days
const results = await exa.searchAndContents("AI regulation updates",
  applyFreshnessPolicy(
    { type: "neural", numResults: 10, text: true },
    90  // max 90 days old
  )
);
```

### Step 4: Per-User Budget Enforcement
```typescript
class ExaUsagePolicy {
  private usage = new Map<string, { count: number; resetAt: number }>();
  private limits: Record<string, number>;

  constructor(limits: Record<string, number> = {
    "free": 10,
    "pro": 100,
    "enterprise": 1000,
  }) {
    this.limits = limits;
  }

  checkQuota(userId: string, tier: string): void {
    const limit = this.limits[tier] || this.limits["free"] || 10;
    const now = Date.now();
    const hourKey = `${userId}:${new Date().toISOString().substring(0, 13)}`;

    let entry = this.usage.get(hourKey);
    if (!entry || entry.resetAt < now) {
      entry = { count: 0, resetAt: now + 3600 * 1000 };
    }

    if (entry.count >= limit) {
      throw new PolicyViolation(
        `Hourly search quota exceeded: ${entry.count}/${limit}`
      );
    }

    entry.count++;
    this.usage.set(hourKey, entry);
  }
}

const usagePolicy = new ExaUsagePolicy();
```

### Step 5: Combined Policy Enforcement
```typescript
async function enforcedSearch(
  userId: string,
  userTier: string,
  rawQuery: string,
  category: keyof typeof TRUSTED_SOURCES | "general" = "general",
  maxAgeDays?: number
) {
  // 1. Check quota
  usagePolicy.checkQuota(userId, userTier);

  // 2. Validate and sanitize query
  const query = validateQuery(rawQuery);

  // 3. Build options with domain policy
  let opts: any = {
    type: "auto",
    numResults: 10,
    text: { maxCharacters: 1000 },
    moderation: true,
  };

  if (category !== "general" && TRUSTED_SOURCES[category]) {
    opts.includeDomains = TRUSTED_SOURCES[category];
  } else {
    opts.excludeDomains = BLOCKED_DOMAINS;
  }

  // 4. Apply freshness policy
  if (maxAgeDays) {
    opts = applyFreshnessPolicy(opts, maxAgeDays);
  }

  // 5. Execute search
  return exa.searchAndContents(query, opts);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Competitor content in results | No domain filtering | Apply `excludeDomains` blocklist |
| Harmful query accepted | No content policy | Validate queries against blocked patterns |
| Stale results displayed | No freshness check | Apply `startPublishedDate` filter |
| API cost overrun | No usage limits | Implement per-user/tier quotas |
| Blocked policy query | False positive | Review and adjust `BLOCKED_PATTERNS` |

## Resources
- [Exa Search Reference](https://docs.exa.ai/reference/search)
- [Exa Domain Filtering](https://docs.exa.ai/reference/search)

## Next Steps
For architecture decisions, see `exa-architecture-variants`. For cost control, see `exa-cost-tuning`.
