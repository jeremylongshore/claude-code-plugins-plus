---
name: perplexity-policy-guardrails
description: |
  Implement content moderation, model selection policy, citation quality enforcement,
  and per-user usage quotas for Perplexity Sonar API.
  Trigger with phrases like "perplexity policy", "perplexity guardrails",
  "perplexity content moderation", "perplexity usage limits", "perplexity safety".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, perplexity-policy]

---
# Perplexity Policy Guardrails

## Overview
Policy enforcement for Perplexity Sonar API. Since Perplexity performs live web searches, guardrails must address: query content moderation (what users can search for), citation reliability (filtering low-quality sources), cost control (model selection + token limits), and responsible AI usage.

## Policy Pipeline

```
User Query
    │
    ▼
Query Moderation (block harmful queries)
    │
    ▼
PII Sanitization (strip personal data)
    │
    ▼
Quota Check (daily limit by user tier)
    │
    ▼
Model Selection (enforce tier-appropriate model)
    │
    ▼
Perplexity API Call
    │
    ▼
Citation Quality Scoring (filter low-trust sources)
    │
    ▼
Response to User
```

## Prerequisites
- Perplexity API configured
- Content moderation policy defined
- User tier system in place
- Redis for quota tracking (optional: in-memory for simple apps)

## Instructions

### Step 1: Query Content Moderation
```typescript
const BLOCKED_PATTERNS = [
  /\b(write|generate|create)\s+(malware|virus|exploit|ransomware)\b/i,
  /\b(personal|private)\s+(address|phone|ssn)\s+of\s+\w+/i,
  /\b(bypass|circumvent|hack)\s+(security|firewall|authentication)\b/i,
  /\b(how to|tutorial)\s+(stalk|dox|harass)\b/i,
];

const MAX_QUERY_LENGTH = 2000;

class PolicyError extends Error {
  constructor(public code: string, message: string) {
    super(message);
    this.name = "PolicyError";
  }
}

function moderateQuery(query: string): string {
  if (query.length > MAX_QUERY_LENGTH) {
    throw new PolicyError("QUERY_TOO_LONG", `Query exceeds ${MAX_QUERY_LENGTH} characters`);
  }

  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(query)) {
      throw new PolicyError("CONTENT_BLOCKED", "Query blocked by content policy");
    }
  }

  return query;
}
```

### Step 2: Model Selection Policy
```typescript
interface ModelPolicy {
  model: string;
  maxTokens: number;
  costPerRequest: number;
}

const MODEL_POLICIES: Record<string, ModelPolicy> = {
  free:       { model: "sonar",     maxTokens: 256,  costPerRequest: 0.005 },
  basic:      { model: "sonar",     maxTokens: 1024, costPerRequest: 0.005 },
  pro:        { model: "sonar-pro", maxTokens: 2048, costPerRequest: 0.02 },
  enterprise: { model: "sonar-pro", maxTokens: 4096, costPerRequest: 0.02 },
};

function enforceModelPolicy(
  userTier: string,
  requestedModel?: string
): ModelPolicy {
  const policy = MODEL_POLICIES[userTier] || MODEL_POLICIES.free;

  // Prevent free users from using expensive models
  if (requestedModel === "sonar-pro" && !["pro", "enterprise"].includes(userTier)) {
    console.warn(`User tier ${userTier} not allowed sonar-pro, using sonar`);
    return MODEL_POLICIES.free;
  }

  return requestedModel ? { ...policy, model: requestedModel } : policy;
}
```

### Step 3: Per-User Usage Quotas
```typescript
class UsageQuota {
  private usage: Map<string, { count: number; resetAt: number }> = new Map();

  private readonly limits: Record<string, number> = {
    free: 50,
    basic: 200,
    pro: 1000,
    enterprise: 5000,
  };

  check(userId: string, tier: string = "free"): void {
    const key = `${userId}:${new Date().toISOString().slice(0, 10)}`;
    const entry = this.usage.get(key) || { count: 0, resetAt: this.endOfDay() };

    // Reset if past end of day
    if (Date.now() > entry.resetAt) {
      entry.count = 0;
      entry.resetAt = this.endOfDay();
    }

    const limit = this.limits[tier] || this.limits.free;
    if (entry.count >= limit) {
      throw new PolicyError(
        "QUOTA_EXCEEDED",
        `Daily quota exceeded (${entry.count}/${limit}). Resets at midnight UTC.`
      );
    }

    entry.count++;
    this.usage.set(key, entry);
  }

  getUsage(userId: string): { used: number; limit: number; remaining: number } {
    const key = `${userId}:${new Date().toISOString().slice(0, 10)}`;
    const entry = this.usage.get(key);
    const used = entry?.count || 0;
    return { used, limit: 50, remaining: Math.max(0, 50 - used) };
  }

  private endOfDay(): number {
    const d = new Date();
    d.setUTCHours(23, 59, 59, 999);
    return d.getTime();
  }
}
```

### Step 4: Citation Quality Scoring
```typescript
const TRUSTED_TLDS = new Set(["gov", "edu", "org"]);
const HIGH_QUALITY_DOMAINS = new Set([
  "nature.com", "science.org", "arxiv.org", "wikipedia.org",
  "nih.gov", "cdc.gov", "who.int",
]);
const LOW_QUALITY_DOMAINS = new Set([
  "reddit.com", "quora.com", "medium.com", "yahoo.com",
]);

interface CitationQuality {
  url: string;
  trust: "high" | "medium" | "low";
  domain: string;
}

function scoreCitations(citations: string[]): {
  scored: CitationQuality[];
  highTrustPercent: number;
} {
  const scored = citations.map((url) => {
    const domain = new URL(url).hostname;
    const tld = domain.split(".").pop() || "";

    let trust: "high" | "medium" | "low" = "medium";
    if (TRUSTED_TLDS.has(tld) || HIGH_QUALITY_DOMAINS.has(domain)) {
      trust = "high";
    } else if (LOW_QUALITY_DOMAINS.has(domain)) {
      trust = "low";
    }

    return { url, trust, domain };
  });

  const highTrust = scored.filter((s) => s.trust === "high").length;
  return {
    scored,
    highTrustPercent: citations.length > 0 ? highTrust / citations.length : 0,
  };
}
```

### Step 5: Full Policy Pipeline
```typescript
const quota = new UsageQuota();

async function policiedSearch(
  query: string,
  userId: string,
  userTier: string = "free",
  requestedModel?: string
) {
  // 1. Content moderation
  const moderated = moderateQuery(query);

  // 2. PII sanitization
  const { clean } = sanitizeQuery(moderated);

  // 3. Quota check
  quota.check(userId, userTier);

  // 4. Model policy
  const policy = enforceModelPolicy(userTier, requestedModel);

  // 5. API call
  const response = await perplexity.chat.completions.create({
    model: policy.model,
    messages: [{ role: "user", content: clean }],
    max_tokens: policy.maxTokens,
  });

  // 6. Citation quality
  const citations = (response as any).citations || [];
  const quality = scoreCitations(citations);

  return {
    answer: response.choices[0].message.content,
    citations: quality.scored,
    citationQuality: quality.highTrustPercent,
    model: response.model,
    tokens: response.usage?.total_tokens,
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Query blocked | Content moderation triggered | Review patterns, adjust if false positive |
| Quota exceeded | User hit daily limit | Upgrade tier or wait for reset |
| Model downgraded | User tier restricts access | Inform user of tier limitations |
| Low citation quality | All sources from forums | Add `search_domain_filter` for trusted sources |

## Output
- Query content moderation with blocked patterns
- Model selection enforced by user tier
- Per-user daily quotas
- Citation quality scoring and filtering
- Full policy pipeline combining all layers

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Responsible Use](https://www.perplexity.ai/hub)

## Next Steps
For architecture patterns, see `perplexity-architecture-variants`.
