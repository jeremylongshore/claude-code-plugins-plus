# Startup Smoke Test

Run a four-integration probe before the HTTP server binds its port. Total
budget: **10 seconds**. If any probe fails, the container exits non-zero, the
orchestrator's rollout halts, and the previous version keeps taking traffic.

## The probe set

| Probe | What it verifies | Typical latency | Failure mode |
|---|---|---|---|
| Model reachable | Provider key is valid, model id exists, network route works | 200-800 ms | Auth / model-not-found / DNS |
| Checkpointer reachable | Postgres connection, schema present, migrations applied | 50-300 ms | Network / schema drift (P20) |
| Vector store reachable | Index exists, tenant / API key scope correct | 100-500 ms | Wrong index name / cold cluster |
| Observability endpoint | OTLP endpoint reachable, TLS cert valid | 50-200 ms | DNS / cert |

Sum at p50: ~500 ms. At p99 (cold network, cold DB pool): 3-5 s. Budget 10 s
leaves headroom for one degraded integration while still failing fast.

## Implementation

```python
import time
from anthropic import Anthropic, APIError

def validate_integrations(settings: "Settings") -> None:
    t0 = time.monotonic()
    errors: list[str] = []

    # 1. Model — 1-token ping, costs ~ $0.00001
    try:
        anthropic = Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
        anthropic.messages.create(
            model=settings.model_id,
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
    except APIError as e:
        errors.append(f"model ping failed: {e}")

    # 2. Checkpointer (skip in dev where MemorySaver is fine)
    if settings.env != "dev":
        try:
            cp = build_checkpointer(settings)
            cp.setup()  # SELECT 1 + schema check
        except Exception as e:
            errors.append(f"checkpointer setup failed: {e}")

    # 3. Vector store (see langchain-embeddings-search for the client)
    if settings.vector_index_name:
        try:
            validate_vector_store(settings)
        except Exception as e:
            errors.append(f"vector store probe failed: {e}")

    # 4. OTEL endpoint (HTTP health)
    try:
        import urllib.request
        urllib.request.urlopen(
            f"{settings.otel_endpoint}/health", timeout=2
        )
    except Exception as e:
        errors.append(f"otel endpoint unreachable: {e}")

    elapsed = time.monotonic() - t0

    if errors:
        raise RuntimeError(
            f"startup smoke test failed after {elapsed:.1f}s: "
            + "; ".join(errors)
        )
    if elapsed > 10.0:
        raise RuntimeError(
            f"startup smoke test took {elapsed:.1f}s (budget 10s)"
        )
```

Call at the top of the app entrypoint, before the web server binds:

```python
# main.py
settings = build_settings()
validate_integrations(settings)   # raises → exits non-zero → deploy halts
app = build_fastapi_app(settings)
uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Failure-mode matrix

| Error string | Most likely cause | First debug step |
|---|---|---|
| `model ping failed: authentication_error` | Secret Manager returned wrong key, or wrong account | Compare `settings.anthropic_api_key[:8] + "..."` against expected prefix |
| `model ping failed: model_not_found` | Pinned `model_id` not yet rolled out to this account | `curl https://api.anthropic.com/v1/models -H "x-api-key: ..."` — list what IS available |
| `model ping failed: timeout` | Network egress blocked | Check VPC firewall / NAT route to the provider |
| `checkpointer setup failed: connection refused` | Postgres not up yet, or wrong URL | `psql $CHECKPOINTER_URL -c "SELECT 1"` from the pod |
| `checkpointer setup failed: relation "checkpoints" does not exist` | Schema migration skipped (P20) | Run `PostgresSaver.create_tables(conn_str)` once during deploy |
| `vector store probe failed: index not found` | Wrong `vector_index_name` or wrong env cluster | List indexes on the cluster; compare against pinned name |
| `otel endpoint unreachable` | Collector not deployed, or DNS not resolving | `nslookup otel-collector.observability.svc.cluster.local` from the pod |
| `startup smoke test took 11.3s` | One integration is degraded (usually cold DB pool) | Look at per-probe timing logs; increase budget only if consistently slow |

## Parallelizing the probes

The four probes are independent. At p99 (3-5s per probe), serial execution
pushes past the 10s budget. Parallelize with `asyncio.gather` once you have
async clients:

```python
import asyncio

async def validate_integrations_async(settings: "Settings") -> None:
    results = await asyncio.gather(
        probe_model(settings),
        probe_checkpointer(settings),
        probe_vector_store(settings),
        probe_otel(settings),
        return_exceptions=True,
    )
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        raise RuntimeError(...)
```

Worst-case wall clock drops from 4×probe to max(probe). The budget stays 10s,
but the headroom grows. Do this once you notice p99 startup creeping toward
the budget — serial is simpler and fine at p50.

## Idempotency

Probes must be safe to call repeatedly. Kubernetes will restart the container
on any transient network blip, and a probe that mutates state (creates a row,
increments a counter) will accumulate garbage across restarts.

- Model probe: read-only ✓
- Checkpointer `setup()`: idempotent (creates tables IF NOT EXISTS) ✓
- Vector store `describe_index()`: read-only ✓
- OTEL `/health`: read-only ✓

If you add a fifth probe, enforce the read-only / idempotent rule.

## When to skip smoke tests

**Never skip in prod.** In dev, a fast inner loop matters more than the
10s probe cost, so gate the smoke test on env:

```python
if settings.env == "dev" and os.environ.get("SKIP_SMOKE") == "1":
    logger.warning("skipping smoke test (dev only)")
else:
    validate_integrations(settings)
```

Allow the env-var escape hatch only in dev. Staging and prod must run the
full probe set every start. If staging feels flaky because the OTEL endpoint
is down 5% of the time, fix the OTEL endpoint — do not disable the probe.
