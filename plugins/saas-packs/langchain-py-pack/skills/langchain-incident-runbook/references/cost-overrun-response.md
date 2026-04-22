# Cost Overrun Response — Agent Recursion Cap, Retry Throttle, Per-Tenant Budget

Cost spikes are acute incidents. Unlike latency, they have no natural
self-recovery — if an agent is looping at $400/10min, it will still be looping
at $4,000/hour unless someone stops it. First-response actions here are about
**bleed containment**, not root cause.

## Decision tree

```
Cost-per-req spike alert
  ├── LangSmith: avg trace depth > 15? → Agent runaway (P10)
  │     → Flip recursion_limit=5 via config reload
  │     → Add session to middleware blocklist
  │     → See Step A below
  │
  ├── Callback log: attempts/logical_call > 2? → Retry amplification (P30)
  │     → Lower max_retries to 2
  │     → Check what error is triggering retries (probably 429 — see P31)
  │     → See Step B below
  │
  └── Token-use-per-req spike? → Prompt or output regression
        → Find the changed prompt via git log since last deploy
        → Check if a user pasted a giant document (move to file upload)
        → See Step C below
```

## Step A — Agent recursion containment (P10)

### Immediate stop

Flip the `recursion_limit` via whatever config-reload path you have — feature
flag, env var hot-reload, or restart:

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    llm, tools,
    recursion_limit=5,  # emergency cap — was 8 or 25
)
```

If you do not have config reload, a deploy is required. In that case, apply
Step A2 first and deploy in parallel.

### Step A2 — Middleware token-budget cap

A callback handler that tracks cumulative input + output tokens per session
and raises a custom `BudgetExceeded` exception when the cap is hit. This stops
any agent, not just the specific one you are debugging.

```python
from langchain_core.callbacks import AsyncCallbackHandler
from contextvars import ContextVar

SESSION_TOKENS: ContextVar[int] = ContextVar("SESSION_TOKENS", default=0)

class BudgetExceeded(Exception):
    pass

class TokenBudgetHandler(AsyncCallbackHandler):
    def __init__(self, cap: int = 50_000):
        self.cap = cap

    async def on_llm_end(self, response, **kwargs):
        usage = response.llm_output.get("token_usage", {})
        total = usage.get("total_tokens", 0)
        running = SESSION_TOKENS.get() + total
        SESSION_TOKENS.set(running)
        if running > self.cap:
            raise BudgetExceeded(f"Session exceeded {self.cap} tokens (used {running})")
```

Attach to the chain via `with_config({"callbacks": [TokenBudgetHandler(50_000)]})`.
Wire `BudgetExceeded` to return a graceful user-facing message, not a 500.

### Step A3 — Repeat-tool circuit (LangGraph edge)

A cheap heuristic for "agent is stuck in a loop":

```python
from langgraph.graph import StateGraph, END

def should_continue(state):
    history = state.get("messages", [])
    tool_calls = [m for m in history[-6:] if m.type == "tool"]
    if len(tool_calls) >= 2:
        # Same tool with same args twice in a row?
        if tool_calls[-1].name == tool_calls[-2].name and \
           tool_calls[-1].args == tool_calls[-2].args:
            return END
    return "continue"

graph.add_conditional_edges("agent", should_continue)
```

This catches loops long before `recursion_limit` does, typically within 2–3
steps.

## Step B — Retry amplification (P30)

`max_retries=6` on `ChatOpenAI` means **7** requests per logical call (initial
+ 6 retries). Under a rate-limit regime, each 429 triggers retries, which each
hit 429, which each retry — cost multiplies 7x for no successful output.

### Fix

```python
# BAD — default cost amplification
llm = ChatOpenAI(model="gpt-4o", max_retries=6)

# GOOD — bounded retry + circuit breaker
llm = ChatOpenAI(model="gpt-4o", max_retries=2)
```

Pair with a circuit breaker (see `provider-outage-playbook.md`) so sustained
429s short-circuit instead of every request paying 3x.

### Observability for retries

The provider SDK does not log each retry by default. Add a callback:

```python
class RetryLogger(AsyncCallbackHandler):
    async def on_retry(self, retry_state, **kwargs):
        logger.warning(
            "retry",
            attempt=retry_state.attempt_number,
            wait=retry_state.next_action.sleep,
        )
```

Emit a Prometheus counter `langchain_retries_total{provider, reason}` so you
can alert on retry-rate elevation before it becomes a cost alert.

## Step C — Token-use regression

If cost-per-req is up but trace depth and retry rate are normal, check the
token usage directly:

```
LangSmith filter:
  - service = "my-service"
  - window = last_1h
  - baseline = 24h_ago_1h
  - compare: avg(input_tokens), avg(output_tokens)
```

If input tokens are up: a user is pasting a giant document, or a retriever
is returning more chunks (k increased accidentally), or a prompt template was
modified to include more few-shot examples.

If output tokens are up: `max_tokens` was removed or raised, or the prompt
changed to encourage longer responses, or the model was swapped (e.g. Sonnet
→ Opus has different verbosity).

### Mitigations

- **`max_tokens` cap:** set explicitly on every model factory; do not leave
  unset. 1024 is a sane default for chat; 4096 for structured generation.
- **Retriever `k`:** audit every retriever for hardcoded `k` vs config-driven;
  a change from `k=4` to `k=10` doubles input cost for RAG chains.
- **Paste detection:** if users paste >10k-char bodies, route to a file-upload
  path that does chunking + retrieval, not a direct prompt inclusion.

## Per-tenant budget enforcement

For multi-tenant SaaS, per-tenant caps prevent one customer from burning the
monthly budget. Track in a fast store (Redis) keyed by tenant:

```python
import redis.asyncio as redis

class TenantBudgetHandler(AsyncCallbackHandler):
    def __init__(self, r: redis.Redis, daily_cap_usd: float = 5.0):
        self.r = r
        self.daily_cap = daily_cap_usd

    async def on_llm_end(self, response, *, tags, **kwargs):
        tenant_id = next((t[7:] for t in tags if t.startswith("tenant:")), None)
        if not tenant_id:
            return
        cost = compute_cost(response)  # dollars
        key = f"budget:{tenant_id}:{today()}"
        total = await self.r.incrbyfloat(key, cost)
        await self.r.expire(key, 86_400)
        if total > self.daily_cap:
            raise BudgetExceeded(f"Tenant {tenant_id} exceeded daily cap")
```

Tag runs with the tenant id: `chain.with_config({"tags": [f"tenant:{tid}"]})`.

## Alert thresholds

- **Page:** cost-per-req p95 > 4x baseline for 15min
- **Page:** absolute spend/hour > 2x forecast for 1h
- **Ticket:** token-use-per-req up 20% over 7-day baseline (gradual regression)
- **Ticket:** retry rate > 5% of total requests (P30 warning signal)

## Post-mitigation check

After the spike stops:

1. Confirm LangSmith shows trace depth back at baseline.
2. Confirm cost-per-req SLO back under threshold for a full window.
3. File the permanent fix ticket (e.g. "move `recursion_limit=5` from hotfix
   config to code default").
4. Add a regression test: an agent invocation with a known vague prompt must
   terminate within `recursion_limit` steps.
