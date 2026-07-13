# Per-Tenant Budgets

A single runaway tenant can consume the pack's budget in hours. This reference
covers the middleware pattern, Redis-backed counter schema, soft-vs-hard cap
semantics, grace period handling, and alert wiring.

## Why per-tenant, per-day

Most cost incidents we have seen come from:

- A prompt template bug that grows context unboundedly per turn (one such
  incident: 400x cost spike in 6 hours for one tenant)
- An agent loop that hits `recursion_limit=25` on a new class of user query
  (P10) and burns the full budget on every request
- A new feature shipped without a gold-set evaluation, where Haiku silently
  underperforms and the retry middleware keeps re-invoking

Per-tenant, per-day budgets contain all three. Per-day gives you a clean
reset; per-tenant isolates the blast radius.

## Middleware interface (LangChain 1.0)

```python
from datetime import date
from typing import Any
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import ConfigurableField

class BudgetExceeded(Exception):
    def __init__(self, tenant_id: str, used: int, cap: int):
        self.tenant_id = tenant_id
        self.used = used
        self.cap = cap
        super().__init__(f"Tenant {tenant_id} used {used}/{cap} tokens")


class BudgetMiddleware:
    def __init__(self, redis, soft_caps: dict[str, int], hard_caps: dict[str, int],
                 alert_fn):
        self.redis = redis
        self.soft_caps = soft_caps
        self.hard_caps = hard_caps
        self.alert_fn = alert_fn

    def _day_key(self, tenant_id: str) -> str:
        return f"budget:{tenant_id}:{date.today().isoformat()}"

    async def check(self, tenant_id: str, estimated_input: int) -> None:
        used = int(await self.redis.get(self._day_key(tenant_id)) or 0)
        hard = self.hard_caps[tenant_id]
        soft = self.soft_caps[tenant_id]
        projected = used + estimated_input
        if projected > hard:
            raise BudgetExceeded(tenant_id, used, hard)
        if projected > soft:
            await self.alert_fn(tenant_id, used, soft, hard)

    async def commit(self, tenant_id: str, actual_tokens: int) -> None:
        # Post-call: increment by ACTUAL (input + output), not estimate.
        await self.redis.incrby(self._day_key(tenant_id), actual_tokens)
        # TTL 48h so the day boundary is covered even on timezone edge cases.
        await self.redis.expire(self._day_key(tenant_id), 172800)
```

Wire it into a chain:

```python
async def bounded_invoke(chain, tenant_id: str, inputs: dict, budget: BudgetMiddleware):
    estimate = rough_token_estimate(inputs)    # tiktoken on the prompt
    await budget.check(tenant_id, estimate)
    result = await chain.ainvoke(inputs, config={
        "metadata": {"tenant_id": tenant_id}
    })
    actual = result.usage_metadata["input_tokens"] + result.usage_metadata["output_tokens"]
    await budget.commit(tenant_id, actual)
    return result
```

## Soft vs hard cap semantics

| Cap | Behavior | Example cap | Notification |
|---|---|---|---|
| **Soft** | Allow request; emit alert | 80% of hard | First hit per day → Slack `#ai-ops` |
| **Hard** | Refuse request with `BudgetExceeded` | Full daily budget | Page on-call if > 3 tenants hit hard in 1h |

The soft cap exists so operations hears about the problem before it becomes
an outage. The hard cap exists so a single bug does not exhaust the pack.

## Grace period on hard-cap hit

When hard cap is hit mid-request:

1. **Allow in-flight calls to complete** — they already billed. Refusing
   mid-stream wastes the tokens already spent without canceling the provider
   charge.
2. **Refuse new calls** — return `429 Too Many Requests` with a
   `Retry-After: <seconds-until-midnight-UTC>` header.
3. **Emit a "hard cap hit" alert** — page on-call; the tenant is either
   malicious, compromised, or has a runaway prompt bug.
4. **Log enough detail to reconstruct** — tenant_id, day_key, used, cap,
   user_id (if available), chain_name, timestamp. A post-mortem will need
   these.

The day boundary is UTC, not tenant-local. Mixed-timezone tenants all get the
same reset at 00:00 UTC. If you need tenant-local day boundaries, use the
tenant's configured timezone in `date.today()` — but document clearly, as
this changes cron semantics for alerts.

## Estimating input before the call

A rough pre-call estimate is better than none; exact input tokens are only
known after the call. `tiktoken` for OpenAI models gives input within ±2%.
Anthropic's `client.messages.count_tokens()` gives exact counts but is itself
a billable API call (free at low volume, verify current policy).

A cheap estimator:

```python
import tiktoken
_enc = tiktoken.get_encoding("cl100k_base")  # GPT-4, close enough for estimation

def rough_token_estimate(inputs: dict) -> int:
    text = str(inputs)  # or serialize the prompt + context
    return len(_enc.encode(text)) + 500  # 500 buffer for output
```

Estimate is for the budget check only; `commit()` uses actual tokens from
`usage_metadata`. If the estimate is high and the call is cheap, the budget
rebalances on commit.

## Redis schema

```
KEY:  budget:{tenant_id}:{YYYY-MM-DD}
TYPE: string (counter, tokens)
TTL:  172800 (48h, survives day boundary)
OPS:  INCRBY, GET, EXPIRE

KEY:  budget:{tenant_id}:alerted:{YYYY-MM-DD}
TYPE: string (single byte, existence check)
TTL:  86400 (24h)
OPS:  SET NX, EXISTS
```

The `alerted` key dedupes soft-cap alerts so you page once per day per tenant,
not on every request after breach.

## Alert wiring

```python
async def alert(tenant_id: str, used: int, soft: int, hard: int):
    alert_key = f"budget:{tenant_id}:alerted:{date.today().isoformat()}"
    if not await redis.set(alert_key, "1", nx=True, ex=86400):
        return  # already alerted today
    pct_of_hard = (used / hard) * 100
    await slack.post(
        channel="#ai-ops",
        text=f":warning: tenant `{tenant_id}` at {pct_of_hard:.0f}% of daily cap "
             f"({used:,} / {hard:,} tokens). Soft cap {soft:,} crossed.",
    )
```

For hard-cap hits, route to an on-call pager instead (PagerDuty, OpsGenie).
Do not rely on Slack alone for hard-cap pages — Slack outages are too
frequent to be your only signal.

## Testing budget semantics

Three unit tests worth writing:

```python
async def test_soft_cap_alerts_once_per_day():
    ...

async def test_hard_cap_refuses():
    ...

async def test_grace_period_allows_in_flight():
    # Start a long-running call, hit hard cap mid-call, verify it completes.
    ...
```

Integration test with a fake Redis and fake chain for CI; production Redis
for staging validation.

## Cross-references

- `langchain-middleware-patterns` — middleware order (redact → cache →
  budget → model), retry telemetry
- `langchain-rate-limits` — RPM/ITPM budgeting at the client level (P31) is
  orthogonal to tenant cost budgets; you need both
- `langchain-observability` — LangSmith traces tagged with `tenant_id` from
  `config.metadata` so you can reconstruct a budget breach from the trace
