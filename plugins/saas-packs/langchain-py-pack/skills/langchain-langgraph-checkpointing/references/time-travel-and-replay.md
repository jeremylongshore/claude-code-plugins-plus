# Time-Travel And Replay

> When a production agent misbehaves, the usual engineering move — attach a
> debugger, add log lines, redeploy — is useless: the agent's decision depended
> on the full state at the moment of the bad call, which is already overwritten.
> LangGraph checkpointers solve this by keeping the full history of every state
> transition keyed by `thread_id`. You can enumerate past states, pick one, and
> resume from it.

## The Primitives

### `graph.get_state(config) -> StateSnapshot`

Returns the *latest* checkpoint for the given `thread_id`. The snapshot includes:

- `.values` — the full state dict at that checkpoint
- `.next` — a tuple of nodes that would run next (useful for "where did it stop?")
- `.config` — a config pinned to this exact checkpoint (includes `checkpoint_id`)
- `.metadata` — `source`, `step`, `writes`, plus any metadata you attached

```python
config = {"configurable": {"thread_id": "user-123"}}
snap = graph.get_state(config)
print(snap.values)
print("next nodes:", snap.next)
print("step:", snap.metadata.get("step"))
```

### `graph.get_state_history(config) -> Iterator[StateSnapshot]`

Enumerates checkpoints from newest to oldest. Each yielded `StateSnapshot` is pinned to a specific `checkpoint_id`:

```python
for snap in graph.get_state_history(config):
    print(snap.metadata["step"], snap.next, list(snap.values.keys()))
```

In production incidents, this is your first move. Walk backwards until you find the step *before* the bad transition, inspect its state, and confirm what the agent saw.

### Resuming From A Specific Checkpoint

Every `StateSnapshot.config` carries a `checkpoint_id`. To replay from there, pass that config back into `invoke`/`stream`:

```python
past = next(s for s in graph.get_state_history(config) if s.metadata["step"] == 3)
# past.config is like:
# {"configurable": {"thread_id": "user-123", "checkpoint_id": "1ef..."}}
result = graph.invoke(None, config=past.config)   # None = "continue from snapshot"
```

Passing `None` as the input means "use the state at this checkpoint." The graph resumes as if the remainder of history never happened — but crucially, it **does not delete** the old history; the new execution creates a new branch.

### `graph.update_state(config, values, as_node=None)`

Edit state directly. Useful for "fix the bad field, resume from here":

```python
graph.update_state(
    past.config,
    {"retry_count": 0, "error_reason": None},
    as_node="validator",   # Pretend this update came from the 'validator' node
)
result = graph.invoke(None, config=past.config)
```

The `as_node` argument controls which node's output reducer handles the update. Without `as_node`, the update merges into state as if applied from outside the graph (usable but less faithful to production execution).

## Incident Playbook — "The Agent Gave A Wrong Answer At 14:03"

1. **Find the thread_id from logs.** Your structured logger should include `thread_id` on every log line (if not, see `langchain-observability`).
2. **Get the history:**
   ```python
   config = {"configurable": {"thread_id": bad_thread_id}}
   history = list(graph.get_state_history(config))
   for i, snap in enumerate(history):
       print(i, snap.metadata.get("step"), snap.next, snap.metadata.get("writes"))
   ```
3. **Identify the bad step.** Look for the transition where the output diverged from expected. The `writes` metadata tells you which node wrote what.
4. **Inspect state at the prior checkpoint.** The node's *input* is the state of the step *before* its write:
   ```python
   bad_step = history[i]
   prior = history[i + 1]   # history is newest-first
   print("input to bad node:", prior.values)
   ```
5. **Decide the fix.** Two paths:
   - **Reproduce locally.** Use `prior.config` to resume in a dev copy of the graph with breakpoints or added logging.
   - **Patch in place.** `update_state` to correct the state, then `invoke(None, config=prior.config)` to regenerate the response. The user gets a correct answer, the original branch is still there for forensics.

## Forking For A/B Comparison

Time-travel makes branching free. From a known-good checkpoint, resume with a different prompt, different model, or different tool binding:

```python
# Branch 1: current production agent
result_prod = graph.invoke(None, config=known_good.config)

# Branch 2: same state, upgraded model
alt_graph = builder_with_new_model.compile(checkpointer=cp)
result_alt = alt_graph.invoke(None, config=known_good.config)
```

Both results are now in the checkpoint history. `get_state_history` returns them as separate branches (distinguished by `parent_checkpoint_id`). Useful for regression evaluation and for "would the new model have fixed this incident?"

## Checkpoint Pruning — Keeping The DB Bounded

Checkpoint storage grows linearly with turn count. For a user with 10,000 turns across 5 years, you are storing ~50 MB of per-thread state. Most of it is never read again. Strategies:

| Strategy | Pros | Cons |
|---|---|---|
| Keep everything | Perfect time-travel forever. | DB grows forever. |
| Keep last N checkpoints per thread | Bounded size per user. | Time-travel limited to last N steps. |
| Keep checkpoints at "important" nodes only | Small DB, meaningful history. | Requires tagging; simple resume-from-step less precise. |
| Archive to cold storage after 30 days | Balanced. | Adds restore step for old incidents. |

Implementation — N=100 per thread:

```sql
-- Run as a nightly maintenance job.
WITH ranked AS (
  SELECT checkpoint_id, thread_id,
         ROW_NUMBER() OVER (PARTITION BY thread_id ORDER BY checkpoint_id DESC) AS rn
  FROM checkpoints
)
DELETE FROM checkpoints
WHERE checkpoint_id IN (SELECT checkpoint_id FROM ranked WHERE rn > 100);
```

Cascade the same delete to `checkpoint_writes` and `checkpoint_blobs` (join by `thread_id` + `checkpoint_id`). Wrap in a transaction.

For Deep Agent workloads specifically (P51), the virtual-FS state in `state["files"]` can bloat a single checkpoint. Consider a node-level cleanup that prunes `state["files"]` entries older than N steps *inside* the graph — checkpoint size stays bounded even without DB-level pruning.

## Replay For Reproducible Evaluations

Research-flavored use: checkpoint at the end of every test case, run the agent, store the thread_id alongside test metadata. Later, replay any test by its thread_id to reproduce bit-for-bit (up to model non-determinism — see P05 for why `temperature=0` is not a guarantee on Claude).

```python
def run_eval(test_id: str, prompt: str) -> str:
    config = {"configurable": {"thread_id": f"eval:{test_id}"}}
    result = graph.invoke({"messages": [HumanMessage(prompt)]}, config=config)
    return result["messages"][-1].content

def replay_eval(test_id: str) -> list:
    config = {"configurable": {"thread_id": f"eval:{test_id}"}}
    return [snap.values for snap in graph.get_state_history(config)]
```

Pair with `langchain-evaluation-harness` for full pipelines.

## Caveats

- **Time-travel does not undo side effects.** If a node hit an external API (sent an email, charged a card), resuming from before that node re-does the side effect. Wrap external calls in idempotency keys.
- **Branching multiplies storage.** Every `invoke(None, config=past.config)` creates new checkpoints alongside the originals. Do not branch in a hot loop without pruning.
- **`update_state` is a write.** It creates a new checkpoint. The prior state is preserved (that is the point), but be mindful of the index cost on extremely busy threads.
- **`get_state_history` reads can be expensive** on threads with thousands of checkpoints. Paginate by `limit` and `before=checkpoint_id` for UI-facing history browsers.
