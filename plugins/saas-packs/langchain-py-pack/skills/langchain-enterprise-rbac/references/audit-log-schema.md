# Audit-log Schema

The audit log is the record of truth during an incident. One JSON record per chain / agent invocation, emitted on both success and failure paths.

## Required fields

| Field | Type | Notes |
|---|---|---|
| `trace_id` | string (UUID v4) | Unique per invocation; joins to OTel spans when instrumented |
| `tenant_id` | string | From `RunnableConfig.configurable.tenant_id`; non-null |
| `user_id` | string | Application user identifier; non-null |
| `chain_name` | string | Human-readable; e.g. `"rag-qa-v3"`, `"support-agent"` |
| `outcome` | enum | One of `success`, `error`, `tool_denied`, `rate_limited`, `budget_exceeded` |
| `latency_ms` | integer | Wall-clock, including retries |
| `timestamp` | string (ISO 8601) | UTC, millisecond precision |

## Optional fields (recommended)

| Field | Type | Notes |
|---|---|---|
| `role` | string | Caller role at invocation time; useful for tool allowlist audits |
| `tools_called` | string[] | Tool names invoked during the run; empty array for pure chains |
| `tool_denied` | object | `{name, reason}` when `outcome == "tool_denied"` |
| `input_tokens` | integer | Prompt tokens |
| `output_tokens` | integer | Completion tokens |
| `cache_read_tokens` | integer | Anthropic cache read hits (P14) |
| `cost_usd` | float | Computed from usage × per-model rate card |
| `model` | string | e.g. `claude-sonnet-4-6`, `gpt-4o` |
| `error_class` | string | Python exception class when `outcome == "error"` |
| `error_message` | string | Truncated to 500 chars; never logs raw prompt content |
| `parent_trace_id` | string | For agent → sub-agent invocations |
| `retrieval_ids` | string[] | Document IDs returned by the retriever; for cross-tenant leak forensics |

## Fields that must NEVER appear

- Raw prompt content (use upstream redaction; see pain-catalog P24)
- Raw tool arguments (log the tool name + arg keys, not values)
- API keys, JWTs, session cookies (even if they appeared in the prompt)
- PII not already authorized for retention (emails, SSNs, payment data)

If the chain operates on PII, apply redaction middleware **before** the audit sink — otherwise the log becomes a new PII store to defend.

## JSON example

```json
{
  "trace_id": "0f9e5c83-7e54-4a6c-ae9a-3f2c1b1a0d11",
  "tenant_id": "initech",
  "user_id": "u_42",
  "role": "viewer",
  "chain_name": "rag-qa-v3",
  "outcome": "success",
  "latency_ms": 842,
  "timestamp": "2026-04-21T14:05:22.107Z",
  "tools_called": ["search_docs"],
  "input_tokens": 1532,
  "output_tokens": 284,
  "cache_read_tokens": 1200,
  "cost_usd": 0.0041,
  "model": "claude-sonnet-4-6",
  "retrieval_ids": ["initech-doc-34", "initech-doc-77", "initech-doc-91"]
}
```

## The `try / finally` emit contract

```python
import json, time, uuid
from contextlib import contextmanager

@contextmanager
def audit(ctx: dict):
    started = time.monotonic()
    record = {
        "trace_id": str(uuid.uuid4()),
        "timestamp": _utc_iso_now(),
        "outcome": "pending",
        **ctx,
    }
    try:
        yield record
        record.setdefault("outcome", "success")
    except PermissionError as exc:
        record["outcome"] = "tool_denied"
        record["tool_denied"] = {"reason": str(exc)[:200]}
        raise
    except RateLimitError:
        record["outcome"] = "rate_limited"
        raise
    except BudgetExceededError:
        record["outcome"] = "budget_exceeded"
        raise
    except Exception as exc:
        record["outcome"] = "error"
        record["error_class"] = type(exc).__name__
        record["error_message"] = str(exc)[:500]
        raise
    finally:
        record["latency_ms"] = int((time.monotonic() - started) * 1000)
        _sink(json.dumps(record))
```

The `finally` block guarantees emission even when the chain raises. The exception-specific handlers classify the outcome before re-raising.

## Sink choice

| Sink | Pros | Cons |
|---|---|---|
| **stdout + Cloud Logging** | Zero extra deps; works in Cloud Run / GKE; 10GB free tier | Index cost at volume; 30-day default retention |
| **BigQuery streaming insert** | SQL queries for compliance; 180-day retention tier; cheap at scale | Latency (2-10s to queryability); quota on streaming inserts |
| **Splunk HEC** | Security-team standard; mature alerting | Vendor cost per ingest GB |
| **Datadog Logs** | Correlates with APM traces via `trace_id` | Vendor cost; retention tiering |
| **Kafka → Sink of choice** | Decouples chain latency from log sink | Adds infra |

For most teams starting out: stdout JSON → log aggregator → nightly export to BigQuery for 180-day retention. Splunk / Datadog if the security team already runs one.

## BigQuery DDL

```sql
CREATE TABLE `project.audit.langchain_invocations` (
  trace_id          STRING  NOT NULL,
  tenant_id         STRING  NOT NULL,
  user_id           STRING  NOT NULL,
  role              STRING,
  chain_name        STRING  NOT NULL,
  outcome           STRING  NOT NULL,
  latency_ms        INT64   NOT NULL,
  timestamp         TIMESTAMP NOT NULL,
  tools_called      ARRAY<STRING>,
  input_tokens      INT64,
  output_tokens     INT64,
  cache_read_tokens INT64,
  cost_usd          FLOAT64,
  model             STRING,
  error_class       STRING,
  error_message     STRING,
  retrieval_ids     ARRAY<STRING>,
  parent_trace_id   STRING,
)
PARTITION BY DATE(timestamp)
CLUSTER BY tenant_id, chain_name;
```

Partition by date for retention / query cost. Cluster by `tenant_id` so tenant-scoped queries scan only their slice.

## Query recipes

### Every tool call by user X in the last 24h

```sql
SELECT timestamp, chain_name, tools_called, outcome
FROM `project.audit.langchain_invocations`
WHERE user_id = 'u_42'
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND ARRAY_LENGTH(tools_called) > 0
ORDER BY timestamp DESC;
```

### Tenants with >1% error rate in the last hour

```sql
SELECT
  tenant_id,
  COUNTIF(outcome = 'error') / COUNT(*) AS error_rate,
  COUNT(*) AS n
FROM `project.audit.langchain_invocations`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY tenant_id
HAVING error_rate > 0.01 AND n > 100
ORDER BY error_rate DESC;
```

### Highest-spend tenants this month

```sql
SELECT tenant_id, SUM(cost_usd) AS spend_usd
FROM `project.audit.langchain_invocations`
WHERE DATE(timestamp) >= DATE_TRUNC(CURRENT_DATE(), MONTH)
GROUP BY tenant_id
ORDER BY spend_usd DESC
LIMIT 20;
```

### Cross-tenant leak detection (retrieval_ids from wrong tenant)

```sql
-- Flags invocations where a retrieved doc's ID prefix disagrees with the tenant_id.
-- Assumes your document IDs encode tenant (e.g. "initech-doc-77").
SELECT trace_id, tenant_id, retrieval_ids
FROM `project.audit.langchain_invocations`,
     UNNEST(retrieval_ids) AS doc_id
WHERE NOT STARTS_WITH(doc_id, CONCAT(tenant_id, '-'))
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
```

A non-empty result on this query is a P33 incident — page on it.

## Related

- [Retriever-per-request](retriever-per-request.md) — so `retrieval_ids` are always tenant-scoped
- [Role-scoped tool allowlist](role-scoped-tool-allowlist.md) — `tool_denied` outcome source
- [Multi-tenant regression tests](multi-tenant-regression-tests.md) — tests that assert audit-log completeness
