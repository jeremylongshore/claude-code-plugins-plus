# LangSmith Prompt Hub — Push, Pull, Pin, A/B

Reference for `langchain-prompt-engineering`. Covers the prompt-hub lifecycle:
push on merge, pull by immutable commit hash in production, promote across
environments, run A/B tests, and roll back in one config change.

Pin: `langsmith >= 0.1.99`. Env vars: `LANGSMITH_API_KEY`, `LANGSMITH_TRACING=true`,
optional `LANGSMITH_WORKSPACE_ID` for multi-workspace accounts.

## Concepts

- **Prompt** — a named artifact in the LangSmith hub (e.g., `extract-invoice`)
- **Commit** — an immutable snapshot, identified by an 8-char short SHA
  (e.g., `abc12345`). Pulling by commit hash is the production-safe pattern.
- **Tag** — a mutable label that points at a commit (`production`, `staging`,
  `dev`). Convenient for humans, unsafe for prod pins because tags move.
- **Workspace** — an account-level scope. Prompts are scoped to a workspace.
  Multi-tenant setups need `LANGSMITH_WORKSPACE_ID`.

## Push: one line, called from CI

```python
from langsmith import Client
from prompts.extract_invoice import EXTRACT_INVOICE

client = Client()
url = client.push_prompt(
    "extract-invoice",
    object=EXTRACT_INVOICE,
    tags=["production", "v2.3.0"],  # tags can be moved; commit is immutable
)
print(url)
# https://smith.langchain.com/prompts/extract-invoice/abc12345
```

Run this in a GitHub Actions step that fires on merge to `main`. Stage it behind
a manual-approval gate for regulated environments.

## Pull: always by commit hash in prod

```python
# BAD — tag is mutable. Someone can re-push "production" and your service
# silently serves a different prompt on the next restart.
prod = client.pull_prompt("extract-invoice:production")

# GOOD — commit hash is immutable. Your service pins until you ship a config change.
prod = client.pull_prompt("extract-invoice:abc12345")

# Acceptable for dev/CI
dev = client.pull_prompt("extract-invoice:dev")
latest = client.pull_prompt("extract-invoice")  # defaults to latest commit
```

Store the pinned commit hash in your app config (env var, config file, feature
flag payload). Treat it exactly like a Docker image tag.

## Per-environment promotion pipeline

| Environment | Pull strategy | Who advances |
|---|---|---|
| Local dev | `extract-invoice` (latest) | N/A — devs iterate freely |
| CI | `extract-invoice:dev` tag | Auto — moves on merge to `develop` |
| Staging | `extract-invoice:staging` tag | Auto — moves after staging tests pass |
| Production | `extract-invoice:<8-char-hash>` pin | Manual — release engineer updates config |

The `production` tag is aspirational. Operators pin to the specific commit
hash the release was cut from. Rollback = change the pinned hash.

## Rollback in one config change

```bash
# Something broke after promoting commit b6f2e190
# Roll back by changing the pinned hash — no code deploy needed
kubectl set env deployment/extractor PROMPT_EXTRACT_INVOICE=extract-invoice:abc12345
```

The previous commit stays in the hub forever. Every version is recoverable.

## A/B test harness

Two commits, one feature flag, metrics in LangSmith traces:

```python
def resolve_variant(tenant_id: str) -> tuple[str, str]:
    """Return (commit_hash, variant_tag)."""
    if feature_flag("extract_invoice_v2", tenant_id):
        return ("b6f2e190", "candidate")
    return ("abc12345", "baseline")

def extract(doc: str, tenant_id: str) -> dict:
    commit, variant = resolve_variant(tenant_id)
    prompt = client.pull_prompt(f"extract-invoice:{commit}")
    chain = prompt | llm | parser
    return chain.invoke(
        {"document": doc},
        config={
            "tags": [f"prompt_variant:{variant}", f"prompt_commit:{commit}"],
            "metadata": {"tenant_id": tenant_id},
        },
    )
```

**Cache pulled prompts** — don't hit the hub on every request:

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def pull_cached(name_and_commit: str):
    return client.pull_prompt(name_and_commit)
```

The pulled object is immutable once resolved by commit, so an unbounded cache
is safe. Size the LRU to the number of prompts in the service.

## Eval-set integration

LangSmith eval sets run against a callable — route through `resolve_variant`
so the eval harness tests both variants on the same inputs:

```python
from langsmith.evaluation import evaluate

def target(inputs):
    return extract(inputs["document"], inputs["tenant_id"])

evaluate(
    target,
    data="extract-invoice-eval-v1",
    evaluators=[correctness_evaluator, cost_evaluator],
    experiment_prefix="ab-test-b6f2e190-vs-abc12345",
)
```

Group results by the `prompt_variant` trace tag. Winner is promoted; loser
stays in hub history as a regression fixture.

## Listing and auditing

```python
# List all prompts in the workspace
for p in client.list_prompts():
    print(p.repo_handle, p.updated_at)

# List commits for a single prompt
for c in client.list_commits("extract-invoice"):
    print(c.commit_hash[:8], c.created_at, c.parent_commit_hash[:8] if c.parent_commit_hash else "(root)")
```

Use this in a compliance dashboard — every production commit hash should be
traceable to the CI run and PR that pushed it.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `LangSmithNotFoundError: prompt not found` | Wrong name, or key lacks workspace access | `client.list_prompts()` to confirm; check `LANGSMITH_WORKSPACE_ID` |
| 403 on pull | API key scoped to different workspace | Set `LANGSMITH_WORKSPACE_ID` or use correct key |
| Prompt pulled is outdated after push | LRU cache hit on stale key | Key cache on `name:commit_hash`, not `name` alone |
| Prompt structure differs across envs | Staging/prod pinned to different commits | Expected — that is the mechanism. Audit via `list_commits()` |
| A/B variants converge in metrics | Feature flag not splitting cleanly | Log `prompt_variant` tag on every call; verify distribution |

## Sources

- LangSmith prompt engineering concepts: https://docs.smith.langchain.com/prompt_engineering/concepts
- LangSmith: Manage prompts programmatically: https://docs.smith.langchain.com/prompt_engineering/how_to_guides/manage_prompts_programatically
- LangSmith SDK `Client.push_prompt`, `pull_prompt`, `list_prompts`, `list_commits`
