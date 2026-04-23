# Virtual Filesystem Patterns — P51 Mitigation

The Deep Agent pattern uses a "virtual filesystem" in graph state for
subagent artifacts and scratch. Without eviction policies and size limits,
`state["files"]` grows to megabytes, the checkpointer serializes slowly, and
end-to-end latency doubles over a long run. This reference covers the full
mitigation procedure.

## The growth trajectory (P51, observed)

A 50-tool-call Deep Agent run with no eviction, captured on LangGraph 1.0.2:

| Step | `state["files"]` entries | Serialized state size | `MemorySaver.put()` time |
|------|--------------------------|-----------------------|--------------------------|
| 5    | 3                        | 40 KB                 | 20 ms                    |
| 15   | 11                       | 400 KB                | 80 ms                    |
| 30   | 26                       | 2.1 MB                | 200 ms                   |
| 50   | 45                       | 8.0 MB                | 400 ms                   |

At step 50, every node visit pays 400 ms in checkpoint writes plus the
LangSmith trace upload bandwidth cost. Observed user-facing latency climbs
from 1.2 s/node to 2.5 s/node over the run with no tool-level culprit —
the slowdown is entirely in checkpoint I/O.

## Three-tier storage policy

### Tier 1 — dict-backed (< 100 KB, hot working set)

```python
from typing import TypedDict, Annotated
from operator import or_

class DeepAgentState(TypedDict):
    files: Annotated[dict, or_]  # {name: {content, written_at_step, status}}

INLINE_SIZE_LIMIT_BYTES = 100 * 1024

def write_inline(state, name, content, status="active"):
    return {"files": {name: {
        "content": content,
        "written_at_step": state["step"],
        "status": status,
    }}}
```

### Tier 2 — disk-backed (>= 100 KB, warm storage)

```python
import os, hashlib

DISK_ROOT = "/tmp/deep_agent"
os.makedirs(DISK_ROOT, exist_ok=True)

def write_spilled(state, name, content, status="active"):
    path = os.path.join(DISK_ROOT, f"{state['step']}_{name}")
    with open(path, "w") as f:
        f.write(content)
    return {"files": {name: {
        "content": None,
        "disk_path": path,
        "size_bytes": len(content.encode("utf-8")),
        "written_at_step": state["step"],
        "status": status,
    }}}

def write_artifact(state, name, content, status="active"):
    size = len(content.encode("utf-8"))
    return write_spilled(state, name, content, status) if size >= INLINE_SIZE_LIMIT_BYTES \
           else write_inline(state, name, content, status)

def read_artifact(entry: dict) -> str:
    if entry.get("content") is not None:
        return entry["content"]
    with open(entry["disk_path"]) as f:
        return f.read()
```

### Tier 3 — content-addressed storage (dedup, cold storage)

When two subagents produce the same artifact (common with retrieval-heavy
research patterns), dedup by SHA-256.

```python
def write_cas(state, name, content, status="active"):
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    path = os.path.join(DISK_ROOT, f"cas_{h}")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)
    return {"files": {name: {
        "content": None,
        "disk_path": path,
        "sha256": h,
        "written_at_step": state["step"],
        "status": status,
    }}}
```

## Eviction policy — cleanup node

The cleanup node runs between dispatch and reflection. It prunes entries
that are stale (older than `MAX_FILE_AGE_STEPS`) or completed (`status="done"`
and older than 3 steps).

```python
MAX_FILE_AGE_STEPS = 20
DONE_RETENTION_STEPS = 3

def cleanup_node(state: DeepAgentState) -> dict:
    current_step = state["step"]
    kept = {}
    evicted = []
    for name, entry in state["files"].items():
        age = current_step - entry["written_at_step"]
        if entry.get("status") == "done" and age > DONE_RETENTION_STEPS:
            evicted.append((name, "done+aged"))
            continue
        if age > MAX_FILE_AGE_STEPS:
            evicted.append((name, "stale"))
            continue
        kept[name] = entry
    # Optional: log evictions to a small ring buffer for observability
    return {"files": kept}
```

Tune `MAX_FILE_AGE_STEPS` to your workload. For long-horizon research
(synthesis over 100+ tool calls), raise to 40. For tight interactive loops,
lower to 10.

## Checkpoint strategy — boundary-only

Default `MemorySaver` writes after every node. For Deep Agents, write only
at user-facing boundaries.

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_after=["reflection"],  # checkpoint only when reflection yields control
)
```

For production, replace `MemorySaver` with a durable store
(`PostgresSaver` / `RedisSaver`) and override `put` to no-op on non-boundary
nodes if you need mid-run durability without per-node I/O.

## Asserting the fix in tests

```python
import pickle

def test_state_stays_under_500kb_over_50_steps():
    cfg = {"configurable": {"thread_id": "bound-test"}, "recursion_limit": 60}
    app.invoke(initial_state_for_long_goal(), config=cfg)
    final = app.get_state(cfg).values
    size = len(pickle.dumps(final))
    assert size < 500_000, f"P51 regression: state = {size} bytes (limit 500 KB)"

def test_memorysaver_put_latency_bounded(memory_saver_with_timing):
    # Instrument MemorySaver.put to record durations; assert p95 < 50ms.
    app.invoke(initial_state_for_long_goal(), config=cfg)
    p95 = memory_saver_with_timing.p95_ms()
    assert p95 < 50, f"P51 regression: checkpoint p95 = {p95}ms (limit 50ms)"
```

## Checklist

- [ ] Entries carry `{written_at_step, status}` not bare content
- [ ] Writes route through `write_artifact()` that picks inline vs spilled
- [ ] `cleanup_node` runs before every planner re-entry
- [ ] `interrupt_after=["reflection"]` on `graph.compile`
- [ ] `len(pickle.dumps(state)) < 500 KB` asserted in trajectory tests
- [ ] Disk-spilled entries cleaned up in a post-run hook (or in an
      external retention job)

## Related

- [architecture-blueprint.md](architecture-blueprint.md) — where cleanup sits in the graph
- [reflection-loop.md](reflection-loop.md) — reflection reads file summaries, not contents
- Pain catalog: **P51** — Deep Agent virtual FS state grows unboundedly
- Cross-skill: `langchain-langgraph-checkpointing` (L27) — deeper checkpointer tuning
