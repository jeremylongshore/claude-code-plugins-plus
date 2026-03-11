---
name: perplexity-policy-guardrails
description: |
  Implement Perplexity lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Perplexity integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Perplexity best practices.
  Trigger with phrases like "perplexity policy", "perplexity lint",
  "perplexity guardrails", "perplexity best practices check", "perplexity eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity Policy Guardrails

## Overview
Policy enforcement for Perplexity Sonar API usage. Since Perplexity performs live web searches, guardrails must address query content moderation, citation reliability, cost control, and responsible AI usage.

## Prerequisites
- Perplexity API configured
- Content moderation requirements defined
- Cost monitoring in place

## Instructions

### Step 1: Query Content Moderation

Filter user queries before sending to Perplexity to prevent misuse.

```python
import re

BLOCKED_INTENTS = [
    r"(write|generate|create)\s+(malware|virus|exploit)",
    r"(personal|private)\s+(information|data|address)\s+of\s+",
    r"(bypass|circumvent|hack)\s+(security|firewall|authentication)",
]

def moderate_query(query: str) -> str:
    for pattern in BLOCKED_INTENTS:
        if re.search(pattern, query, re.IGNORECASE):
            raise PolicyViolation("Query blocked by content policy")
    if len(query) > 2000:  # 2000: 2 seconds in ms
        raise PolicyViolation("Query exceeds maximum length")
    return query
```

### Step 2: Model Selection Policy

Route queries to appropriate model tiers to control costs.

```python
class ModelSelectionPolicy:
    RULES = {
        "sonar": {"max_tokens": 4096, "cost_per_request": 0.005},  # 4096: 4 KB
        "sonar-pro": {"max_tokens": 8192, "cost_per_request": 0.025},  # 8192: 8 KB
    }

    def select_model(self, query: str, user_tier: str = "free") -> str:
        if user_tier == "free":
            return "sonar"
        if len(query.split()) > 100 or "detailed" in query.lower():
            return "sonar-pro"
        return "sonar"

    def enforce_token_limit(self, model: str, requested_tokens: int):
        max_tokens = self.RULES[model]["max_tokens"]
        if requested_tokens > max_tokens:
            raise PolicyViolation(f"Requested {requested_tokens} tokens exceeds {model} limit of {max_tokens}")
```

### Step 3: Citation Quality Enforcement

Verify that citations come from trusted sources before displaying to users.

```python
TRUSTED_DOMAINS = {"gov", "edu", "org"}
UNTRUSTED_DOMAINS = {"reddit.com", "quora.com", "medium.com"}

def score_citation_quality(citations: list[str]) -> dict:
    scores = []
    for url in citations:
        domain = extract_domain(url)
        tld = domain.split('.')[-1]
        if tld in TRUSTED_DOMAINS:
            scores.append({"url": url, "trust": "high"})
        elif domain in UNTRUSTED_DOMAINS:
            scores.append({"url": url, "trust": "low"})
        else:
            scores.append({"url": url, "trust": "medium"})
    return {"citations": scores, "high_trust_pct": sum(1 for s in scores if s["trust"] == "high") / max(len(scores), 1)}
```

### Step 4: Per-User Usage Quotas

Limit API consumption to control costs.

```python
class PerplexityQuota:
    def __init__(self, redis_client):
        self.r = redis_client
        self.limits = {"free": 50, "pro": 500, "enterprise": 5000}  # 5000: HTTP 500 Internal Server Error

    def check_and_consume(self, user_id: str, tier: str = "free"):
        key = f"pplx:quota:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
        current = int(self.r.get(key) or 0)
        limit = self.limits.get(tier, 50)
        if current >= limit:
            raise PolicyViolation(f"Daily quota exceeded ({current}/{limit})")
        self.r.incr(key)
        self.r.expire(key, 86400)  # 86400: timeout: 24 hours
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Harmful query sent | No content moderation | Pre-filter with blocked patterns |
| High API costs | Using sonar-pro for simple queries | Route by complexity and user tier |
| Unreliable citations shown | No source filtering | Score and filter citation quality |
| Usage spike | No per-user limits | Implement daily quotas by tier |

## Examples

### Full Policy Pipeline
```python
query = moderate_query(user_input)
quota.check_and_consume(user_id, user_tier)
model = model_policy.select_model(query, user_tier)
result = client.chat.completions.create(model=model, messages=[{"role": "user", "content": query}])
citation_quality = score_citation_quality(result.citations)
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai)
- [Responsible AI Practices](https://docs.perplexity.ai/guides/responsible-use)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale