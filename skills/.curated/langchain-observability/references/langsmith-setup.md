# LangSmith Setup (Canonical 1.0)

LangSmith is LangChain's hosted tracing + eval product. On 1.0 the env-var
names and project-routing behavior changed; this reference is the authoritative
checklist.

## Canonical env vars

| Variable | Purpose | Required |
|----------|---------|----------|
| `LANGSMITH_TRACING` | Master switch. `true` turns tracing on, anything else is off | Yes |
| `LANGSMITH_API_KEY` | Workspace API key (`lsv2_pt_...` for personal, `lsv2_sk_...` for service) | Yes |
| `LANGSMITH_PROJECT` | Project name — group runs by service + env | Recommended |
| `LANGSMITH_ENDPOINT` | Custom endpoint for self-hosted / EU region | Optional |
| `LANGSMITH_SAMPLING_RATE` | Float 0.0-1.0, sample runs client-side | Optional |

## Legacy fallback (P26)

The old names still work for backward compatibility but are soft-deprecated
and fail silently on some 1.0 middleware paths. Do NOT use in new code:

| Legacy (deprecated) | 1.0 canonical |
|---------------------|---------------|
| `LANGCHAIN_TRACING_V2` | `LANGSMITH_TRACING` |
| `LANGCHAIN_API_KEY` | `LANGSMITH_API_KEY` |
| `LANGCHAIN_PROJECT` | `LANGSMITH_PROJECT` |
| `LANGCHAIN_ENDPOINT` | `LANGSMITH_ENDPOINT` |

If a legacy process sets both, the `LANGSMITH_*` names win in 1.0.x. Do not
rely on this — remove the `LANGCHAIN_*` copies when you migrate.

## Project-per-env, not project-per-service

Use `{service}-{env}` convention:

```
myapp-prod        # production
myapp-staging     # staging / pre-prod
myapp-dev         # shared dev
myapp-{username}  # individual dev (optional)
```

Do NOT reuse a single project for prod + staging — the LangSmith UI cannot
filter cleanly across environments, and eval datasets get polluted with
staging noise.

## Smoke-check at startup

```python
import os
from langsmith import Client
from langsmith.utils import LangSmithAuthError, LangSmithConnectionError

def verify_langsmith() -> None:
    """Fail fast at startup if LangSmith is misconfigured."""
    if os.environ.get("LANGSMITH_TRACING", "").lower() != "true":
        print("WARN: LangSmith tracing disabled (LANGSMITH_TRACING != 'true')")
        return
    try:
        c = Client()  # reads LANGSMITH_API_KEY, LANGSMITH_ENDPOINT
        list(c.list_projects(limit=1))
    except LangSmithAuthError:
        raise SystemExit("LangSmith auth failed — check LANGSMITH_API_KEY")
    except LangSmithConnectionError:
        raise SystemExit("LangSmith unreachable — check network / LANGSMITH_ENDPOINT")
    print(f"LangSmith OK — project={os.environ.get('LANGSMITH_PROJECT', 'default')}")
```

Run `verify_langsmith()` from your FastAPI lifespan / app factory. Silent
tracing failures are the #1 observability bug in new deployments.

## Process-order checklist

`Client()` reads `LANGSMITH_API_KEY` and `LANGSMITH_ENDPOINT` at instance
construction time. `LANGSMITH_PROJECT` is read when the first run is logged.
Environment set *after* import into a module that already called `Client()`
will not take effect.

1. Load `.env` / secret manager BEFORE importing `langchain` or `langsmith`
2. Or: call `importlib.reload(langsmith)` after env is loaded (fragile — don't)
3. In containerized deployments, always pass env via Dockerfile `ENV` or
   Kubernetes env, not via entrypoint script that `source`s after the process
   has started

## Sampling

LangSmith bills per trace. For high-traffic services, sample client-side:

```bash
export LANGSMITH_SAMPLING_RATE=0.1   # 10% of runs logged
```

Sampling is random per top-level run. Subgraphs inherit the decision, so a
traced run logs the whole tree. Target sample rate at enough volume to catch
regressions (100+ runs/week of your critical paths).

Never sample below 100% on staging — low-volume environments need every trace.

## Annotation queues and datasets

Production traffic is the best eval set. Route a sampled subset into a
LangSmith annotation queue for human review; reviewed runs feed `Dataset`
objects you can replay against candidate models.

```python
from langsmith import Client
c = Client()
c.create_annotation_queue(
    name="prod-regressions",
    description="1% sample of prod runs, weekly review",
)
```

Route runs into the queue via a LangSmith UI rule, filtered by a metadata
field you control (e.g., `metadata.eval_candidate == "true"`). Do NOT try to
route programmatically — the UI rule handles volume controls and reviewer
assignment.

Keep queues < 500 runs/week. Reviewers saturate past that and the dataset
quality drops.

## Self-hosted / EU region

For EU data residency, set `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`.
For self-hosted (Enterprise tier), point at your cluster URL:

```bash
LANGSMITH_ENDPOINT=https://langsmith.corp.internal
LANGSMITH_API_KEY=<self-hosted key>
```

Self-hosted uses the same client; just the endpoint differs.

## Overhead budget

LangSmith tracing adds <5ms per-span on typical latencies. On a streaming
LLM call (1-5s wall clock), the overhead is immeasurable. On a tight
embedding-only chain (10ms total), it can be 30-50% — disable tracing for
those paths via `config={"callbacks": []}` at invoke, or gate on a feature
flag.

## References

- [LangSmith concepts](https://docs.smith.langchain.com/observability/concepts)
- [LangSmith env variable reference](https://docs.smith.langchain.com/how_to_guides/setup/configure_project)
- Pack pain catalog: P26 (env-var spelling), P28 (callback propagation)
