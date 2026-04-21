# Per-Env Pinning

Three things pin per env: the model id, the prompt commit hash, and the
vector index name. Pinning means the value is **explicit** per env, **audited**
on promotion, and **rollbackable** independently.

## What gets pinned

| Pin | Source of truth | Changes on | Rollback unit |
|---|---|---|---|
| `model_id` | provider model catalog | provider rolls new version | env var, no deploy |
| `prompt_commit_hash` | LangSmith prompt registry | author publishes new version | env var, no deploy |
| `vector_index_name` | vector DB (Pinecone / Qdrant / Weaviate) | re-embed corpus | env var, no deploy |
| `checkpointer_url` | cloud SQL / Postgres instance | infra migration | k8s config, deploy |

All four live in the `Settings` class. No conditionals on `settings.env` in
business code — the app reads `settings.model_id` and gets the right answer.

## Model id pinning

**Never use `"latest"` or the unqualified family name.** `"claude-sonnet"`
resolves to whatever the provider considers "current", which drifts. Use the
full versioned id: `claude-sonnet-4-6`, `gpt-4o-2024-08-06`.

Dev / staging / prod can run different ids:

```
LANGCHAIN_MODEL_ID=claude-haiku-4-6    # dev — cheap, fast
LANGCHAIN_MODEL_ID=claude-sonnet-4-6   # staging — prod-tier
LANGCHAIN_MODEL_ID=claude-sonnet-4-6   # prod
```

Dev on a cheap model is a real money saver — a typical dev loop burns 1000x
more tokens than a prod request. Haiku at dev, Sonnet at staging and prod
for parity.

## Prompt commit hash pinning

LangChain's prompt registry (LangSmith) assigns a commit hash to every
published prompt. Pin the hash, not the name:

```
LANGCHAIN_PROMPT_COMMIT=abc1234   # dev — WIP commit
LANGCHAIN_PROMPT_COMMIT=def5678   # staging — canary, ~1 day old
LANGCHAIN_PROMPT_COMMIT=ghi9012   # prod — stable, ~1 week old
```

The app reads the pinned commit:

```python
from langsmith import Client
ls = Client(api_key=settings.langsmith_api_key.get_secret_value())
prompt = ls.pull_prompt(f"triage-prompt:{settings.prompt_commit_hash}")
```

Cross-ref: `langchain-prompt-engineering` owns the prompt-authoring and
`pull_prompt` workflow in full. This skill just stores the pin.

## Promotion workflow — dev → staging → prod

```
┌─────┐     ┌─────────┐     ┌──────┐
│ dev │ --> │ staging │ --> │ prod │
└─────┘     └─────────┘     └──────┘
  ^             ^              ^
  │             │              │
  WIP hash      canary hash    stable hash
  any id        prod-tier id   prod-tier id
```

Promotion is a three-step CI job:

1. **Test in dev** — prompt author commits new prompt version to LangSmith,
   CI test runs with that hash in the dev env, eval harness passes.
2. **Canary in staging** — set `LANGCHAIN_PROMPT_COMMIT=<new-hash>` as the
   staging env var (Secret Manager config or k8s config map). Deploy the
   service with the new pin. Monitor for 24-48h against the eval harness
   and any live-traffic canaries.
3. **Roll to prod** — copy the hash into the prod env var. Roll out. Keep
   the previous hash noted in the rollback runbook.

**Never skip a step.** Going straight from dev to prod is how wrong-env
prompt loads become incidents. The CI promotion job should reject a prompt
hash that has not yet been observed running in staging for N hours.

## Rollback

Every pin is an env var, so rollback does not require a code deploy:

```
# Rollback prod model to previous version
kubectl set env deployment/langchain-svc LANGCHAIN_MODEL_ID=claude-sonnet-4-5

# Rollback prod prompt to previous commit
kubectl set env deployment/langchain-svc LANGCHAIN_PROMPT_COMMIT=fed0987
```

The k8s rollout strategy (default: rolling update, 25% surge) brings up pods
with the new env var, drains the old pods, and the deploy is done in minutes.
No git, no build, no image push. This is the main reason pins live in env
vars and not in application code.

## Vector index pinning

Re-embedding the corpus creates a new index name (`prod-index-v2`, etc.).
Cutover is a config change:

```
LANGCHAIN_VECTOR_INDEX=prod-index-v1   # current
LANGCHAIN_VECTOR_INDEX=prod-index-v2   # after re-embed
```

Shadow traffic strategy: run `prod-index-v2` in staging for a week, diff
retrieval quality against `prod-index-v1` (compare top-k overlap on a
canonical query set), then cut prod.

Do not delete the old index until at least one rollback window has passed.

## What NOT to pin

Values that are environmental and mechanical, not semantic, stay out of the
`Settings` class:

- **Container image tag** — this is a deploy artifact, pin it in the k8s
  manifest, not in `Settings`.
- **Log level** — `LOG_LEVEL=DEBUG` can stay in env vars, but not typed into
  `Settings`. It changes often and per-pod.
- **Feature flags** — those belong in a feature flag service
  (Unleash / LaunchDarkly / etc.), not in `Settings`. Mixing the two makes
  the `Settings` class unreviewable.

Rule of thumb: if the value is a **semantic pin** (model version, prompt
version, index version), it goes in `Settings`. If it is a **mechanical knob**
(log level, timeout, image tag), keep it out.
