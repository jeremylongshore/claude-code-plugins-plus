# Phased Rollout Playbook

A reversible rollout plan for a LangChain 0.3 → 1.0 migration that touches production traffic. Designed so that any failure mode can be rolled back in under five minutes.

## Phase 0 — Pre-flight (no production change)

1. Run the pre-flight audit (see SKILL.md Step 1). Inventory every 0.3 usage and pick the owning team for each hit.
2. Snapshot `pip freeze > requirements.lock.pre-1.0.txt` — this is your rollback pin.
3. Snapshot the persistent chat-history store (if you have one) — RDS snapshot, Redis RDB dump, or S3 copy. The 1.0 LangGraph checkpointer uses a new schema; a rollback without this snapshot is data-lossy for in-flight conversations.
4. Branch: `feat/langchain-1.0-migration`. Merge nothing to main yet.

## Phase 1 — Upgrade packages in a sandbox

On the migration branch only:

```
pip install --upgrade \
  "langchain>=1.0,<2" \
  "langchain-core>=0.3,<0.4" \
  "langchain-openai>=1.0" \
  "langchain-anthropic>=1.0" \
  "langgraph>=1.0,<2" \
  "anthropic>=0.40,<1"
```

Run `pytest -W error::DeprecationWarning` — every `DeprecationWarning` is now a test failure, so any surviving 0.3 pattern surfaces immediately. Do not proceed to Phase 2 while the test suite is red.

## Phase 2 — Codemod, one module at a time

Per-module order, lowest blast radius first:

1. **Pure-function chains** (LLMChain → LCEL). Easiest. No state, no persistence.
2. **Embedding + vectorstore imports** (P38). Import path changes only; no behaviour change.
3. **Stateless agents** (initialize_agent → create_react_agent without memory).
4. **Streaming callers** (astream_log → astream_events v2). Watch for payload-shape bugs — the event dict is typed.
5. **Stateful agents + memory** (ConversationBufferMemory → LangGraph checkpointer). Highest risk — needs the dual-write below.

After each module: run its unit tests, commit with a pain-code reference (e.g. `refactor: migrate P39 LLMChain in billing-summariser to LCEL`).

## Phase 3 — Dual-write for persistent chat histories

If conversations are persisted (Redis, Postgres, Dynamo) and you cannot drop existing threads, dual-write for the cutover window:

1. Keep the 0.3 history writer running. Every turn, also write to the 1.0 LangGraph checkpointer table/keyspace under the same `thread_id`.
2. Reads in 1.0 code path always go to the checkpointer. Reads in any surviving 0.3 code path keep their old source.
3. Run dual-write for at least one full retention window (24h for most chat products).
4. After promotion (Phase 5), stop the 0.3 writer and delete the old store on a delay (not immediately — keeps the rollback viable).

## Phase 4 — Shadow traffic in staging

1. Deploy the 1.0 branch to a staging environment that mirrors production traffic shape. A mirror proxy (e.g. `goreplay`, `tcpcopy`, or a logged-request replayer) is ideal.
2. Compare outputs on a sample (100–1000 requests) against the 0.3 production behaviour. Diff on:
   - Response content (fuzzy — LLM outputs vary; look for catastrophic drift, not token-level diffs).
   - Tool-call counts per turn (should be within +/- 1 on average; a big delta means the ReAct prompt changed behaviour).
   - Latency p50/p95 (LangGraph adds a small state-serialisation cost; watch for regressions > 20%).
   - Error rate (target: zero new `ImportError`, `AttributeError`, or `KeyError` on `intermediate_steps`).
3. Exit criteria for Phase 4: 24h of shadow traffic with no new error classes and no regression on the four metrics above.

## Phase 5 — Feature-flagged production cutover

1. Put the 1.0 entrypoint behind a feature flag (`LANGCHAIN_1_0_ENABLED`). Default off.
2. Canary: flip on for 1% of traffic. Watch dashboards for 30 minutes.
3. Ramp: 10% → 25% → 50% → 100% over 2–4 hours, with a 15-minute soak at each step.
4. At each step, the on-call engineer owns the rollback call. Rollback is always "flip the flag off" — not a redeploy.

## Phase 6 — Pin and clean up

1. After 100% for at least one full day, remove the feature flag and the 0.3 code path.
2. Pin `langchain`, `langchain-core`, `langgraph`, `langchain-openai`, `langchain-anthropic`, and `anthropic` to exact versions in `requirements.txt`. This prevents a drive-by dependency update from re-introducing a 0.3 compatibility shim or a breaking 1.1 change.
3. Delete the 0.3 dual-write path and, after the retention window, the 0.3 chat history store.
4. Archive `requirements.lock.pre-1.0.txt` in the repo for one release cycle; delete after that.

## Rollback Plan

If Phase 5 reveals a regression:

1. **Flip the flag off.** This is always step one. Traffic returns to the 0.3 code path within seconds.
2. If the 0.3 code path has already been deleted (you are past Phase 6): `pip install -r requirements.lock.pre-1.0.txt` on the rollback branch, redeploy. This is a hard rollback and takes one deploy cycle.
3. If persistent chat histories are involved, restore from the Phase 0 snapshot if the schema drift corrupted any 0.3-readable data. In practice, dual-write (Phase 3) prevents this — do not skip dual-write if you have persisted histories.

## Exit Criteria (Migration is Done)

- Zero hits on the verification greps in [breaking-changes-matrix.md](breaking-changes-matrix.md).
- `pytest -W error::DeprecationWarning` is green.
- `LANGCHAIN_1_0_ENABLED` flag is removed and all callers go through the 1.0 path.
- `requirements.txt` pins all six packages to exact 1.0.x versions.
- Post-mortem note in the repo: what broke, what the grep audit missed, so the next major bump is cheaper.
