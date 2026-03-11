---
name: langchain-incident-runbook
description: |
  Incident response procedures for LangChain production issues.
  Use when responding to production incidents, diagnosing outages,
  or implementing emergency procedures for LLM applications.
  Trigger with phrases like "langchain incident", "langchain outage",
  "langchain production issue", "langchain emergency", "langchain down".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Incident Runbook

## Overview
Standard operating procedures for responding to LangChain production incidents with diagnosis, mitigation, and recovery steps.

## Prerequisites
- Access to production infrastructure
- Monitoring dashboards configured
- LangSmith or equivalent tracing
- On-call rotation established

## Incident Classification

### Severity Levels
| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| SEV1 | Complete outage | 15 min | All LLM calls failing |
| SEV2 | Major degradation | 30 min | 50%+ error rate, >10s latency |
| SEV3 | Minor degradation | 2 hours | <10% errors, slow responses |
| SEV4 | Low impact | 24 hours | Intermittent issues |

## Runbook: LLM Provider Outage

### Detection
```bash
set -euo pipefail
# Check if LLM provider is responding
curl -s https://status.openai.com/api/v2/status.json | jq '.status.indicator'
curl -s https://status.anthropic.com/api/v2/status.json | jq '.status.indicator'

# Check your error rate
# Prometheus query:
# sum(rate(langchain_llm_requests_total{status="error"}[5m])) / sum(rate(langchain_llm_requests_total[5m]))
```

### Diagnosis
```python
# Quick diagnostic script
import asyncio
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

async def diagnose_providers():
    """Check all configured providers."""
    results = {}

    # Test OpenAI
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", request_timeout=10)
        await llm.ainvoke("test")
        results["openai"] = "OK"
    except Exception as e:
        results["openai"] = f"FAIL: {e}"

    # Test Anthropic
    try:
        llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", timeout=10)  # 20241022 = date/version stamp
        await llm.ainvoke("test")
        results["anthropic"] = "OK"
    except Exception as e:
        results["anthropic"] = f"FAIL: {e}"

    return results

# Run
print(asyncio.run(diagnose_providers()))
```

### Mitigation: Enable Fallback
```python
# Emergency fallback configuration
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Original
llm = ChatOpenAI(model="gpt-4o-mini")

# With fallback
primary = ChatOpenAI(model="gpt-4o-mini", max_retries=1, request_timeout=5)
fallback = ChatAnthropic(model="claude-3-haiku-20240307")  # 20240307 = configured value

llm = primary.with_fallbacks([fallback])
```

### Recovery
1. Monitor provider status page
2. Gradually remove fallback when primary recovers
3. Document incident in post-mortem

---

## Runbook: High Error Rate

### Detection
```bash
# Check recent errors in logs
grep -i "error" /var/log/langchain/app.log | tail -50

# Check LangSmith for failed traces
# Navigate to: https://smith.langchain.com/o/YOUR_ORG/projects/YOUR_PROJECT/runs?filter=error%3Atrue
```

### Diagnosis
```python
# Analyze error distribution
from collections import Counter
import json

def analyze_errors(log_file: str) -> dict:
    """Analyze error patterns from logs."""
    errors = []

    with open(log_file) as f:
        for line in f:
            if "error" in line.lower():
                try:
                    log = json.loads(line)
                    errors.append(log.get("error_type", "unknown"))
                except:
                    pass

    return dict(Counter(errors).most_common(10))

# Common error types and causes
ERROR_CAUSES = {
    "RateLimitError": "Exceeded API quota - reduce load or increase limits",
    "AuthenticationError": "Invalid API key - check secrets",
    "Timeout": "Network issues or overloaded provider",
    "OutputParserException": "LLM output format changed - check prompts",
    "ValidationError": "Schema mismatch - update Pydantic models",
}
```

### Mitigation
```python
# 1. Reduce load
# Scale down instances or enable circuit breaker

# 2. Emergency rate limiting
from functools import wraps
import time

def emergency_rate_limit(calls_per_minute: int = 10):
    """Emergency rate limiter decorator."""
    interval = 60.0 / calls_per_minute
    last_call = [0]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
            last_call[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 3. Enable caching for repeated queries
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
set_llm_cache(InMemoryCache())
```

---

## Runbook: Memory/Performance Issues

### Detection
```bash
# Check memory usage
ps aux | grep python | head -5

# Check for memory leaks
# Prometheus: process_resident_memory_bytes
```

### Diagnosis
```python
# Memory profiling
import tracemalloc

tracemalloc.start()

# Run your chain
chain.invoke({"input": "test"})

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 memory allocations:")
for stat in top_stats[:10]:
    print(stat)
```

### Mitigation
```python
# 1. Clear caches
from langchain_core.globals import set_llm_cache
set_llm_cache(None)

# 2. Reduce batch sizes
# Change from: chain.batch(inputs, config={"max_concurrency": 50})
# To: chain.batch(inputs, config={"max_concurrency": 10})

# 3. Restart pods gracefully
# kubectl rollout restart deployment/langchain-api
```

---

## Runbook: Cost Spike

### Detection
```bash
# Check token usage
# Prometheus: sum(increase(langchain_llm_tokens_total[1h]))

# OpenAI usage dashboard
# https://platform.openai.com/usage
```

### Diagnosis
```python
# Identify high-cost operations
def analyze_costs(traces: list) -> dict:
    """Analyze cost from trace data."""
    by_chain = {}

    for trace in traces:
        chain_name = trace.get("name", "unknown")
        tokens = trace.get("total_tokens", 0)

        if chain_name not in by_chain:
            by_chain[chain_name] = {"count": 0, "tokens": 0}

        by_chain[chain_name]["count"] += 1
        by_chain[chain_name]["tokens"] += tokens

    return sorted(by_chain.items(), key=lambda x: x[1]["tokens"], reverse=True)
```

### Mitigation
```python
# 1. Emergency budget limit
class BudgetExceeded(Exception):
    pass

daily_spend = 0
DAILY_LIMIT = 100.0  # $100

def check_budget(cost: float):
    global daily_spend
    daily_spend += cost
    if daily_spend > DAILY_LIMIT:
        raise BudgetExceeded(f"Daily limit ${DAILY_LIMIT} exceeded")

# 2. Switch to cheaper model
# gpt-4o -> gpt-4o-mini (30x cheaper)
# claude-3-5-sonnet -> claude-3-haiku (12x cheaper)

# 3. Enable aggressive caching
```

---

## Incident Response Checklist

### During Incident
- [ ] Acknowledge incident in Slack/PagerDuty
- [ ] Identify severity level
- [ ] Start incident channel/call
- [ ] Begin diagnosis
- [ ] Implement mitigation
- [ ] Communicate status to stakeholders
- [ ] Document timeline

### Post-Incident
- [ ] Verify full recovery
- [ ] Update status page
- [ ] Schedule post-mortem
- [ ] Write incident report
- [ ] Create follow-up tickets
- [ ] Update runbooks

## Resources
- [OpenAI Status](https://status.openai.com)
- [Anthropic Status](https://status.anthropic.com)
- [LangSmith](https://smith.langchain.com)
- [PagerDuty Best Practices](https://response.pagerduty.com/)

## Next Steps
Use `langchain-debug-bundle` for detailed evidence collection.

## Instructions

1. Assess the current state of the Langchain Incident Runbook configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Langchain Incident Runbook |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply langchain incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain incident runbook for production environments with multiple constraints and team-specific requirements.