# Parallel vs Sequential — RunnableParallel Deep Dive

`RunnableParallel({"a": chain_a, "b": chain_b})` runs sub-chains concurrently
and merges their outputs into a dict. In practice, it is the single biggest
latency win in an LCEL pipeline after correct `.batch(max_concurrency=...)`.
This reference covers when parallel wins, async semantics, shared-state
gotchas, and a benchmarking template.

## When parallel wins

| Scenario | Speedup | Why |
|---|---|---|
| 2 independent retrievers (dense + BM25) | 2–3× | Both hit the network; wall-clock = slower one |
| Tool-use call + analysis summary | ~2× | Tool and LLM are both I/O-bound and independent |
| 3 sub-chains (summary + entities + sentiment) | 2.5–3× | Same input fans out, unrelated downstream |
| Local CPU transform + remote LLM call | ~1.0× | CPU work is cheap; LLM dominates anyway |
| Two chained retrievers (A then B needs A's output) | N/A | Not parallel — this is sequential by contract |

Parallel wins when branches are **I/O-bound, independent, and of comparable
latency**. Two 500ms network calls in parallel take ~500ms. If one branch is
2s and the other is 50ms, parallel gives 2s — no worse than sequential's 2.05s,
but not the dramatic win of balanced branches.

## Sync vs async

`RunnableParallel` uses `asyncio.gather` under the hood when called via
`.ainvoke` / `.abatch`. The sync `.invoke` uses a thread pool, which:

- Works correctly for network-bound branches (they release the GIL)
- Does **not** parallelize CPU-bound Python work (GIL contention)
- Has ~5–15ms thread-pool overhead per branch

For production async services (FastAPI, LangGraph nodes), use `.ainvoke` /
`.abatch`. The thread-pool path is acceptable for scripts and eval harnesses.

```python
# Sync — thread pool, fine for scripts
result = hybrid.invoke("query")

# Async — asyncio.gather, use in async services
result = await hybrid.ainvoke("query")
```

## Shared state gotchas

Branches in a `RunnableParallel` run concurrently. If they close over shared
mutable state, you will get races. Symptoms include intermittent `KeyError`,
corrupted lists, and "flaky" unit tests.

```python
# BAD — shared mutable list
results_log = []
def logged_retrieve(q):
    docs = retriever.invoke(q)
    results_log.append(docs)   # race with other branch
    return docs

parallel = RunnableParallel(
    a=RunnableLambda(logged_retrieve),
    b=RunnableLambda(logged_retrieve),
)
```

Rules:

1. **Branches are side-effect-free.** Do logging/metrics after the parallel block.
2. **Materialize shared inputs before the parallel.** Pass a frozen snapshot.
3. **Use `contextvars` for per-request state**, not module-level globals.
4. **No generators**. Parallel branches that yield are hostile to `asyncio.gather`.

## Benchmarking template

Measuring a real speedup matters — parallel is not automatic. Use this
template to compare serial vs parallel for a given pair of sub-chains:

```python
import asyncio, time
from langchain_core.runnables import RunnableParallel

async def bench(inputs: list[str], n: int = 20):
    # Serial baseline
    t0 = time.perf_counter()
    for x in inputs[:n]:
        await chain_a.ainvoke(x)
        await chain_b.ainvoke(x)
    serial = time.perf_counter() - t0

    # Parallel
    parallel = RunnableParallel(a=chain_a, b=chain_b)
    t0 = time.perf_counter()
    for x in inputs[:n]:
        await parallel.ainvoke(x)
    par = time.perf_counter() - t0

    print(f"serial: {serial:.2f}s  parallel: {par:.2f}s  speedup: {serial/par:.2f}x")

asyncio.run(bench(queries))
```

Report the ratio, not the absolute — absolute times vary with provider load.
Speedup below 1.3× means one branch dominates; below 1.1× means you added
overhead without winning anything.

## Fan-out + batch — the two-dimensional pattern

`RunnableParallel` runs N branches for a single input. `.batch(inputs,
max_concurrency=K)` runs K inputs at once through the whole chain. Combined,
you get `N × K` in-flight calls:

```python
parallel = RunnableParallel(a=chain_a, b=chain_b)  # N=2 branches
results = await parallel.abatch(
    big_input_list,
    config={"max_concurrency": 10},                # K=10 inputs
)
# 2 × 10 = up to 20 provider calls in flight
```

Watch provider rate limits — the effective concurrency is the product. Tune
`max_concurrency` downward when `N` is large; see
`langchain-sdk-patterns/references/batch-concurrency-tuning.md` for
per-provider ceilings.

## When to use sequential

Not every pair should be parallel. Use sequential (`|`) when:

- Branch B's input depends on branch A's output
- Branches write to the same downstream state (avoid races)
- One branch is ~10× slower (parallel wins nothing, but adds overhead)
- You need early-exit semantics (`RunnableBranch` is a better fit)

The rule of thumb from `runnable-composition-matrix.md` stands: linear flow
goes through `|`, independent sub-tasks go through `RunnableParallel`.

## Resources

- [LangChain Python: parallel execution](https://python.langchain.com/docs/how_to/parallel/)
- [asyncio.gather semantics](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather)
- Pack pain catalog: P08 (batch concurrency), P06 (dict-shape divergence)
