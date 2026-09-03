---
name: orcarouter-cost-observability
description: |
  Track and control LLM spend through OrcaRouter's per-request cost and
  observability data. Use when building a cost dashboard, setting budget
  alerts, understanding per-model spend, or auditing agent usage. Triggers:
  "orcarouter cost", "llm spend", "cost tracking", "budget", "observability",
  "usage dashboard".
  Trigger with "orcarouter-cost-observability" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- cost
- observability
- budgets
- analytics
compatibility: Designed for Claude Code
---
# OrcaRouter Cost & Observability

## Overview

Understand and control what OrcaRouter costs you. OrcaRouter bills the upstream provider's published per-token price with no per-token markup (see [Billing & usage](https://docs.orcarouter.ai/operations/billing-and-usage)).

Per-request cost is available two ways: opt in with the `X-OrcaRouter-Include-Cost: true` header and read `usage.cost_usd` inline on the response, or look the settled amount up after the fact with `GET /v1/generation?id=<request-id>` using the `X-Orca-Request-Id` header. This skill covers reading the cost field, aggregating spend, and setting budget controls.

## Prerequisites

- An OrcaRouter API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY`
- Python 3.8+ / Node.js 18+ (for aggregation) or a logging pipeline
- The `orcarouter-install-auth` setup

## Instructions

1. Send `X-OrcaRouter-Include-Cost: true` on each completion to get `usage.cost_usd` back inline.
2. Log `usage`, `model`, and any `metadata.agent` tag per request.
3. Aggregate spend per model and per agent in your pipeline.
4. Set budget controls in the OrcaRouter console (spend caps, alerts, `cap_cost` firewall verdicts).
5. Query `GET /v1/dashboard/billing/usage` and `GET /v1/generation` for totals and per-request reconciliation.

## Reading Per-Request Cost

The inline cost is opt-in per request. With the header set, the response `usage` object carries `cost_usd`:

```bash
curl -s https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-OrcaRouter-Include-Cost: true" \
  -d '{"model":"orcarouter/fusion","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}' \
  | jq '{model: .model, tokens: .usage.total_tokens, cost_usd: .usage.cost_usd}'
```

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

# OpenAI SDK sends unknown headers via extra_headers
r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
    extra_headers={"X-OrcaRouter-Include-Cost": "true"},  # opt-in per-request cost header
)
usage = r.usage
print(f"tokens: {usage.total_tokens}")
print(f"cost USD: {usage.cost_usd}")   # only present when the header opt-in is sent
```

## Settled-Cost Lookup

The inline figure is computed when the response is emitted; settlement commits afterward. For the authoritative billed amount, look the request up by id:

```bash
curl -s "https://api.orcarouter.ai/v1/generation?id=$REQUEST_ID" \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" | jq '.data | {total_cost, cost_currency, model}'
```

Every response carries an `X-Orca-Request-Id` header you can pass to this endpoint. If the two figures disagree, the lookup is right. See [Per-request cost](https://docs.orcarouter.ai/operations/per-request-cost).

## Aggregating Spend

```python
import json, collections

def record_spend(log_lines, bucket_by="model"):
    agg = collections.defaultdict(lambda: {"requests": 0, "cost": 0.0, "tokens": 0})
    for line in log_lines:
        e = json.loads(line)
        key = e.get(bucket_by, "unknown")
        agg[key]["requests"] += 1
        agg[key]["cost"] += e.get("cost_usd", 0.0)
        agg[key]["tokens"] += e.get("total_tokens", 0)
    return agg

# Each log line: {"model": "openai/gpt-4o-mini", "cost_usd": 1.2e-05, "total_tokens": 103, "agent": "code-assistant"}
```

## Tagging Spend by Agent

```python
r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Run the test suite"}],
    max_tokens=300,
    extra_headers={"X-OrcaRouter-Include-Cost": "true"},
    extra_body={"metadata": {"agent": "ci-bot", "request_id": "req_42"}},
)
print(f"{r.usage.cost_usd} USD for agent ci-bot")
```

Attributing cost per agent is the foundation of a budget-alerting system.

## Budget Controls

- Set a spend cap or alert threshold in the OrcaRouter console
- Choose routing tiers (`orcarouter/fusion-flash`, `orcarouter/fusion-mini`) as a cost lever
- Pin cheaper models for high-volume, low-complexity work
- Use `orcarouter/free` for CI and smoke tests where latency is not critical
- For agents, use the firewall `cap_cost` verdict as a per-run spend circuit breaker (see [Cap per-run cost](https://docs.orcarouter.ai/security/firewall/cap-cost))

## Output

A working observability setup returns per-request `usage.cost_usd` (when the opt-in header is sent) and token counts, aggregated spend per model/agent, and (with console controls) budget alerts when thresholds are hit.

## Examples

```text
aggregate spend:
  openai/gpt-4o-mini: 142 requests, $1.71e-03, 14,626 tokens
  ci-bot (agent):     57 requests, $6.84e-04
```

More cost patterns (SQL aggregation, alert wiring, tier-based budgeting): `references/cost-patterns.md`.

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 402 | Insufficient credits | Top up or switch to a cheaper routing tier |
| 429 | Rate limit or budget cap reached | Wait or raise the cap; check `Retry-After` |
| 401 | Invalid key | Verify `ORCAROUTER_API_KEY` |

## Enterprise Considerations

- The inline `cost_usd` field is opt-in per request; if it is absent you did not send `X-OrcaRouter-Include-Cost: true` or the response had no usage object — absent never means "free"
- For exact billing, reconcile against `GET /v1/generation`; the inline figure can differ from the settled amount
- Tag every request with `agent`/`request_id` for attributable spend
- Combine per-agent budgets with gateway governance (see `orcarouter-agent-security`) so a runaway agent is blocked, not just billed
- Zero-markup inference means the returned cost reflects provider pricing, simplifying financial controls

## References

- SQL aggregation and alert wiring: `references/cost-patterns.md`
- [Billing & usage](https://docs.orcarouter.ai/operations/billing-and-usage) · [Per-request cost](https://docs.orcarouter.ai/operations/per-request-cost) · [Cap per-run cost](https://docs.orcarouter.ai/security/firewall/cap-cost)
