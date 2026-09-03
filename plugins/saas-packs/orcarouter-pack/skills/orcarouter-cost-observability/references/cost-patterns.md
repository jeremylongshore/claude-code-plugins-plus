# OrcaRouter Cost & Observability — References

## SQL aggregation

If you log completions to a SQL table, store the cost field you actually observed (`cost_usd` when the opt-in header was sent; the settled amount from `GET /v1/generation` is the authority):

```sql
SELECT model,
       COUNT(*)                                  AS requests,
       ROUND(SUM(usage_cost_usd), 6)             AS total_cost_usd,
       SUM(total_tokens)                         AS total_tokens
FROM orca_completions
GROUP BY model
ORDER BY total_cost_usd DESC;
```

Per agent:

```sql
SELECT metadata_agent,
       COUNT(*)                                  AS requests,
       ROUND(SUM(usage_cost_usd), 6)             AS total_cost_usd
FROM orca_completions
GROUP BY metadata_agent
ORDER BY total_cost_usd DESC;
```

## Logging hook

Record the inline cost only when the opt-in header was sent. A logged `cost_usd: None` means the header was absent — do not interpret it as a zero-cost request.

```python
import json, time

def log_completion(r, agent="default"):
    entry = {
        "ts": int(time.time()),
        "request_id": r.id,
        "model": r.model,
        "agent": agent,
        "total_tokens": r.usage.total_tokens,
        "prompt_tokens": r.usage.prompt_tokens,
        "completion_tokens": r.usage.completion_tokens,
        "cost_usd": getattr(r.usage, "cost_usd", None),
        "finish_reason": r.choices[0].finish_reason,
    }
    print(json.dumps(entry))  # ship to your log sink
```

## Tier-based budgeting

| Tier | Use for | Cost posture |
| ---- | ------- | ------------ |
| `orcarouter/fusion` | Production assistant | Frontier panel + judge |
| `orcarouter/fusion-flash` | High-volume / latency-sensitive | Cheaper budget panel |
| `orcarouter/fusion-mini` | Simple tasks | Lean two-model panel |
| `orcarouter/free` | CI, smoke tests, dev loop | No-credit tier (rate-limited) |

## Settled-cost reconciliation

Every response carries an `X-Orca-Request-Id`. The settled amount for a request is authoritative over the inline figure:

```bash
curl -s "https://api.orcarouter.ai/v1/generation?id=$REQUEST_ID" \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" | jq '.data | {total_cost, cost_currency}'
```

## Alert wiring

Trigger an alert when a per-agent daily cost crosses a threshold:

```python
def alert_if_over(agg, agent, threshold=1.0):
    if agg[agent]["cost"] > threshold:
        print(f"ALERT: {agent} spend ${agg[agent]['cost']:.4f} > ${threshold}")
```

## Next skills

- `orcarouter-agent-security` — govern who spends, not just how much
