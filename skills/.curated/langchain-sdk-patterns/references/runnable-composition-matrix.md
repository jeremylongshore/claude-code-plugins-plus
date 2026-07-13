# Runnable Composition Matrix

LangChain 1.0 exposes five composition primitives. Picking the wrong one is
rarely a crash — it is usually a quiet performance or maintainability loss.
This is the decision table.

## The five primitives

| Primitive | Input | Output | Runs | When to use |
|---|---|---|---|---|
| `RunnableSequence` (`a \| b`) | Same as `a.input` | Same as `b.output` | Sequentially | Linear pipeline: prompt → llm → parser |
| `RunnableParallel({"x": a, "y": b})` | Forwarded to both | `{"x": a.output, "y": b.output}` | Concurrently | Fan-out enrichment: summary + entities + sentiment from one doc |
| `RunnableBranch((cond, chain), ..., default)` | Any | First matching branch's output | Sequential dispatch | Per-input routing: route to a cheap or expensive model based on input size |
| `RunnablePassthrough()` | Any | Same as input | Identity | Keep the original value alongside a transform in a `RunnableParallel` |
| `RunnableLambda(fn)` | `fn`'s arg | `fn`'s return | Wraps arbitrary Python | Escape hatch for ad-hoc transforms — avoid for anything you want traced well |

## Shape conventions

Every chain declares an input schema and an output schema. Keep them explicit:

```python
from typing import TypedDict

class TriageIn(TypedDict):
    ticket_text: str
    customer_tier: str

class TriageOut(TypedDict):
    priority: str
    suggested_reply: str
```

`RunnableSequence` propagates these types through `|`. When you drop a
`RunnableLambda` in the middle, annotate its signature — otherwise the
chain's inferred schema collapses to `Any`.

## Fan-out with `RunnableParallel`

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

enrich = RunnableParallel(
    summary=summary_chain,         # Runnable[str, str]
    entities=entity_chain,          # Runnable[str, list[str]]
    original=RunnablePassthrough(), # keep the input
)

# Output: {"summary": "...", "entities": [...], "original": "..."}
```

All three sub-chains run concurrently. If one is 5x slower than the others,
your wall-clock is the slow one — not the sum. This is the single biggest
latency win in an LCEL pipeline after correct `.batch(max_concurrency=...)`.

## Per-input routing with `RunnableBranch`

```python
from langchain_core.runnables import RunnableBranch

router = RunnableBranch(
    (lambda x: len(x["text"]) < 500, fast_chain),  # cheap model
    (lambda x: x["tier"] == "enterprise", premium_chain),
    default_chain,  # mandatory — unmatched inputs go here
)
```

The default branch is required. Without it you get a silent fallthrough —
exactly the kind of error P56 covers for LangGraph conditional edges, and the
runnable version has the same footgun.

## When `RunnableLambda` is the wrong answer

`RunnableLambda(fn)` wraps any Python callable but loses LangSmith tracing
fidelity — the input/output show up as opaque blobs. For data shaping that
must be observable, prefer:

- `RunnablePassthrough.assign(key=chain)` — merges a computed field into the dict
- `itemgetter("key") | runnable` — pulls a field and runs a typed chain on it
- A concrete `BaseRunnable` subclass when the lambda has >3 lines of logic

## Input/output shape conventions table

| Pattern | Typical input | Typical output |
|---|---|---|
| `prompt \| llm \| StrOutputParser()` | `dict[str, Any]` | `str` |
| `prompt \| llm.with_structured_output(T)` | `dict[str, Any]` | `T` (Pydantic) |
| `RunnableParallel(a=ch1, b=ch2)` | `dict[str, Any]` | `{"a": ..., "b": ...}` |
| `RunnablePassthrough.assign(x=chain)` | `dict[str, Any]` | input dict with `"x"` added |
| `RunnableBranch((cond, ch), default)` | anything cond accepts | `ch.output` or `default.output` |

## Composition rule of thumb

1. Linear flow → `|` (builds a `RunnableSequence`)
2. Independent sub-tasks on the same input → `RunnableParallel`
3. Input-dependent dispatch → `RunnableBranch`
4. Merge computed fields → `RunnablePassthrough.assign`
5. One-off Python glue → `RunnableLambda` (but consider a subclass)

When in doubt, prefer composition primitives over lambdas: they trace better,
they serialize for inspection, and their schemas propagate.
