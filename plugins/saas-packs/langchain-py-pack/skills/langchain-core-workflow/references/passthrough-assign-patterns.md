# Passthrough Assign Patterns

`RunnablePassthrough.assign(field=ch)` merges a computed field into the input
dict without losing any existing keys. It is the primary pattern for
**threading state** through a chain — the input dict grows as it flows,
every earlier key stays reachable by later stages.

This reference covers staged context assembly for RAG, the `itemgetter`
variant for typed sub-chains, and anti-patterns around key shadowing.

## The core shape

```python
RunnablePassthrough.assign(key=runnable)
# Input:  {"a": 1, "b": 2}
# Output: {"a": 1, "b": 2, "key": runnable.invoke({"a": 1, "b": 2})}
```

The `runnable` receives the **full input dict** and its output is assigned
to the new key. This is different from `RunnableParallel`, which replaces
the dict with one keyed only by the parallel branches.

## Staged context assembly for RAG

The canonical RAG pipeline stages context in three assigns:

```python
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs: list) -> str:
    return "\n\n".join(f"[{i+1}] {d.page_content}" for i, d in enumerate(docs))

def extract_citations(docs: list) -> list[str]:
    return [d.metadata.get("url", "") for d in docs]

rag_context = (
    RunnablePassthrough.assign(docs=retriever)
    | RunnablePassthrough.assign(
        context=lambda x: format_docs(x["docs"]),
        citations=lambda x: extract_citations(x["docs"]),
    )
)

rag_context.invoke({"question": "..."})
# {"question": "...", "docs": [...], "context": "...", "citations": [...]}
```

Note that `.assign` accepts **multiple kwargs at once** — both computed fields
run after the previous stage and both see the full input including `docs`.
Use this when two computed fields derive from the same upstream value.

## `itemgetter` for pulling a field into a typed sub-chain

When a sub-chain expects a concrete input type (string, list), not the whole
dict, use `itemgetter` to extract the field. This is the pattern to pass a
dict's `question` to a retriever that takes a string:

```python
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough

question_only = itemgetter("question") | retriever  # Runnable[dict, list[Document]]

chain = RunnablePassthrough.assign(docs=question_only)
```

Without `itemgetter`, you would pass the full dict to `retriever.invoke`,
which would try to embed the dict and crash (P06 exactly — `retriever` expects
`str`, sees `dict`). This is the cleanest shape-matching primitive in LCEL
for pulling typed fields into typed sub-chains.

## Preserving input alongside transforms in `RunnableParallel`

`RunnablePassthrough()` (the bare call, no `.assign`) is the identity
runnable — input passes through unchanged. Inside a `RunnableParallel`, this
keeps the original value alongside computed values:

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

enriched = RunnableParallel(
    summary=summary_chain,
    entities=entity_chain,
    original=RunnablePassthrough(),  # keep the input around
)
# Output: {"summary": "...", "entities": [...], "original": "<input>"}
```

Use this when a downstream stage needs both a transform and the raw input.
The common case is a prompt that quotes the user's original question
alongside an LLM-generated classification.

## Lambda assigns — short, readable, no-LLM

`.assign(field=lambda x: ...)` wraps the lambda in a `RunnableLambda`
automatically. This is the clean way to add computed fields from pure-Python
logic:

```python
from datetime import datetime

annotated = RunnablePassthrough.assign(
    timestamp=lambda x: datetime.utcnow().isoformat(),
    word_count=lambda x: len(x["question"].split()),
    is_urgent=lambda x: "urgent" in x["question"].lower(),
)
```

Keep the lambdas short (1 line). If the logic is >3 lines, extract to a
named function and pass the function — it traces better and tests are easier.

## Anti-pattern: shadowing input keys

```python
# BAD — overwrites the original "question" with a paraphrase
bad = RunnablePassthrough.assign(
    question=paraphrase_chain,   # shadowed!
)
```

Downstream stages that expected the original `question` now see the
paraphrased version. This is a silent correctness bug — the chain runs fine,
but your citations no longer match what the user asked.

**Rule:** name computed fields distinctly from input keys. If you genuinely
need to replace a field, do it via a full `RunnableLambda` that signals
intent, not via a sneaky `.assign` that looks like augmentation.

## Anti-pattern: chained `.assign` with circular dependencies

```python
# BAD — "context" is computed from "docs", but "docs" is computed from "context"
broken = (
    RunnablePassthrough.assign(docs=lambda x: retrieve(x["context"]))
    | RunnablePassthrough.assign(context=lambda x: format_docs(x["docs"]))
)
```

At the first `.assign`, `x["context"]` does not exist — `KeyError`. Order
matters. Make the dependency graph explicit: compute upstream first, merge
into dict, then compute downstream.

## Combining with `RunnableBranch` for computed routes

A clean pattern: use `.assign` to compute a category, then `RunnableBranch`
to route on it:

```python
routed = (
    RunnablePassthrough.assign(category=classifier)
    | RunnableBranch(
        (lambda x: x["category"] == "refund", refund_chain),
        (lambda x: x["category"] == "shipping", shipping_chain),
        general_chain,
    )
)
```

The branch runnables all receive the dict with `category` included — they
can use it for further conditional logic, or ignore it.

## Shape cheat sheet

| Before | After `.assign(k=ch)` |
|---|---|
| `{"a": 1}` | `{"a": 1, "k": ch.invoke({"a": 1})}` |
| `{"a": 1, "k": "old"}` | `{"a": 1, "k": ch.invoke({"a": 1, "k": "old"})}` (shadowed!) |
| `"not a dict"` | `TypeError` — `.assign` requires dict input |

## Resources

- [LangChain Python: passthrough](https://python.langchain.com/docs/how_to/passthrough/)
- [`RunnablePassthrough` API reference](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.passthrough.RunnablePassthrough.html)
- Pack pain catalog: P06 (dict-shape divergence — shadowing is a common cause)
