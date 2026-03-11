---
name: exa-policy-guardrails
description: |
  Implement Exa lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Exa integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Exa best practices.
  Trigger with phrases like "exa policy", "exa lint",
  "exa guardrails", "exa best practices check", "exa eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Policy Guardrails

## Overview
Policy enforcement for Exa neural search integrations. Exa searches the open web, which means results may include inappropriate content, competitors' sites, or unreliable sources that need filtering before user presentation.

## Prerequisites
- Exa API configured
- Content filtering requirements defined
- Understanding of domain allowlist/blocklist patterns

## Instructions

### Step 1: Domain Allowlist/Blocklist Filtering

Control which sources appear in search results to prevent showing competitor content or unreliable sites.

```python
DOMAIN_BLOCKLIST = [
    "competitor1.com", "competitor2.io",
    "spam-farm.com", "content-mill.net"
]

DOMAIN_ALLOWLIST_FOR_MEDICAL = [
    "pubmed.ncbi.nlm.nih.gov", "who.int",
    "cdc.gov", "nejm.org", "nature.com"
]

def filter_results(results, blocklist=None, allowlist=None):
    filtered = []
    for r in results.results:
        domain = extract_domain(r.url)
        if blocklist and domain in blocklist:
            continue
        if allowlist and domain not in allowlist:
            continue
        filtered.append(r)
    return filtered

def enforce_search_policy(query: str, category: str = "general"):
    results = exa.search(query, num_results=20)
    if category == "medical":
        return filter_results(results, allowlist=DOMAIN_ALLOWLIST_FOR_MEDICAL)
    return filter_results(results, blocklist=DOMAIN_BLOCKLIST)
```

### Step 2: Query Content Policy

Block or sanitize queries that could return harmful content.

```python
BLOCKED_QUERY_PATTERNS = [
    r'how to (hack|exploit|attack)',
    r'(drugs|weapons)\s+(buy|purchase|order)',
    r'personal.*(address|phone|ssn)',
]

def validate_query(query: str) -> str:
    import re
    for pattern in BLOCKED_QUERY_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            raise PolicyViolation(f"Query blocked by content policy")
    return query
```

### Step 3: Result Freshness Policy

Enforce minimum recency for time-sensitive use cases.

```python
from datetime import datetime, timedelta

def enforce_freshness(results, max_age_days: int = 365):  # 365 days = 1 year
    cutoff = datetime.now() - timedelta(days=max_age_days)
    fresh = []
    for r in results.results:
        if r.published_date and datetime.fromisoformat(r.published_date) >= cutoff:
            fresh.append(r)
    if not fresh:
        raise PolicyViolation(f"No results found within {max_age_days} day freshness window")
    return fresh
```

### Step 4: API Usage Budget Enforcement

Prevent excessive API consumption with per-user and per-project quotas.

```python
class ExaUsagePolicy:
    def __init__(self, redis_client):
        self.r = redis_client
        self.limits = {"per_user_hourly": 100, "per_project_daily": 5000}  # 5000: 5 seconds in ms

    def check_quota(self, user_id: str, project_id: str):
        user_key = f"exa:quota:{user_id}:{datetime.now().strftime('%Y-%m-%d-%H')}"
        user_count = int(self.r.get(user_key) or 0)
        if user_count >= self.limits["per_user_hourly"]:
            raise PolicyViolation(f"User hourly quota exceeded ({user_count})")
        proj_key = f"exa:quota:proj:{project_id}:{datetime.now().strftime('%Y-%m-%d')}"
        proj_count = int(self.r.get(proj_key) or 0)
        if proj_count >= self.limits["per_project_daily"]:
            raise PolicyViolation(f"Project daily quota exceeded")

    def record_usage(self, user_id: str, project_id: str):
        for key, ttl in [
            (f"exa:quota:{user_id}:{datetime.now().strftime('%Y-%m-%d-%H')}", 3600),  # 3600: timeout: 1 hour
            (f"exa:quota:proj:{project_id}:{datetime.now().strftime('%Y-%m-%d')}", 86400)  # 86400: timeout: 24 hours
        ]:
            self.r.incr(key)
            self.r.expire(key, ttl)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Competitor content in results | No domain filtering | Apply blocklist before displaying |
| Harmful query accepted | No content policy | Validate queries against blocked patterns |
| Stale results shown | No freshness check | Enforce date cutoff on results |
| API cost overrun | No usage limits | Implement per-user/project quotas |

## Examples

### Combined Policy Check
```python
query = validate_query(user_input)
usage_policy.check_quota(user_id, project_id)
results = exa.search(query, num_results=15)
filtered = filter_results(results, blocklist=DOMAIN_BLOCKLIST)
fresh = enforce_freshness(filtered, max_age_days=90)
usage_policy.record_usage(user_id, project_id)
```

## Resources
- [Exa API Docs](https://docs.exa.ai)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale