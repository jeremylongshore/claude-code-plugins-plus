# Branch Routing Patterns

`RunnableBranch` dispatches an input to the first branch whose condition
returns truthy. It is the LCEL equivalent of `if/elif/else` — with one
important rule: **always supply a default**. The signature is:

```python
RunnableBranch(
    (cond_1, runnable_1),
    (cond_2, runnable_2),
    ...,
    default_runnable,
)
```

Conditions are callables taking the chain input and returning bool. They run
top-to-bottom; the first match wins and evaluation short-circuits. The final
positional arg is the default branch — it runs when no condition matches.

## Classifier-gated routing

The common case: a small cheap model tags the input with a category, then
`RunnableBranch` dispatches to a specialist chain per category.

```python
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify the ticket as one of: refund, shipping, technical, other."),
    ("human", "{{ question }}"),
], template_format="jinja2")

classifier = classifier_prompt | haiku_llm | StrOutputParser()

router = RunnableBranch(
    (lambda x: x["category"] == "refund", refund_chain),
    (lambda x: x["category"] == "shipping", shipping_chain),
    (lambda x: x["category"] == "technical", technical_chain),
    general_chain,  # default — required
)

full = (
    RunnablePassthrough.assign(category=classifier)
    | router
)
```

Why two stages rather than a branch-on-raw-input: keeping classification in
its own `.assign` step means (a) the classifier result is visible in traces
and debug probes, (b) you can swap classifiers without touching the router,
and (c) tests can pin the category directly.

## Fallback route on unmatched input

The default branch is **not** an error handler — it is the "none of the above"
path. For real input, the default might be a general-purpose chain with a
disclaimer prompt:

```python
disclaimer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a general assistant. If the question needs a specialist, say so."),
    ("human", "{{ question }}"),
], template_format="jinja2")

general_chain = disclaimer_prompt | llm | StrOutputParser()
```

For explicit error handling on a missing category, raise inside the default:

```python
def raise_unmatched(x):
    raise ValueError(f"no route for category={x.get('category')!r}")

router = RunnableBranch(
    (lambda x: x["category"] == "refund", refund_chain),
    RunnableLambda(raise_unmatched),   # fail loudly instead of silent fallthrough
)
```

This is the pattern to use in CI or staging — surface unmatched inputs
instead of quietly serving them with a default chain.

## Condition patterns

Conditions can be any callable that returns a boolean-ish value. Common shapes:

| Condition | Use |
|---|---|
| `lambda x: x["category"] == "refund"` | Direct key match |
| `lambda x: len(x["question"]) > 2000` | Input-size routing (long form → bigger model) |
| `lambda x: x.get("user_tier") == "enterprise"` | Tier-gated features |
| `lambda x: any(w in x["q"].lower() for w in URGENT_WORDS)` | Keyword short-circuit |
| `predicate_chain` (a `Runnable[I, bool]`) | Async/LLM-based predicate |

A `Runnable` predicate lets the branch use the same input pipeline as the
target runnables — useful for predicates that need an LLM judgment, but slower
than a pure-Python lambda. Prefer lambdas for hot paths.

## Common mistakes

**Omitting the default.** Older LCEL code sometimes passes only `(cond, runnable)`
tuples with no trailing default arg. Without a default, unmatched inputs fall
through to the last-declared pair — a silent correctness bug.

**Condition mutating the input.** Conditions run on every branch evaluation.
If a condition has side effects (logging counters, cache writes), you will
see duplicated side effects when conditions run top-to-bottom.

**Non-exhaustive conditions on enum categories.** If your classifier can emit
`"refund"`, `"shipping"`, `"technical"`, and `"other"`, but your branch only
handles the first three, `"other"` silently hits the default. Enumerate all
categories or add a `raise_unmatched` default.

**Conditions that read missing keys.** `lambda x: x["category"]` raises
`KeyError` if classification is skipped. Use `.get()` with a default:
`lambda x: x.get("category") == "refund"`.

## Testing branches in isolation

Each branch is a `Runnable` — test it directly without going through the
router. This is the biggest win of `RunnableBranch` over inline if/elif
Python:

```python
def test_refund_chain_handles_basic_case():
    result = refund_chain.invoke({"question": "I want my money back"})
    assert "refund" in result.lower()

def test_router_dispatches_refund_to_refund_chain(monkeypatch):
    # Pin classifier output without calling the LLM
    monkeypatch.setattr("mymodule.classifier", RunnableLambda(lambda x: "refund"))
    result = full.invoke({"question": "return this"})
    # assert target chain ran
```

For the router itself, test each condition by invoking with a pinned input
that matches exactly one branch. Run a separate test for the default path —
assert it fires on a category your router does not handle.

## Resources

- [LangChain Python: dynamic routing](https://python.langchain.com/docs/how_to/routing/)
- [`RunnableBranch` API reference](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.branch.RunnableBranch.html)
- Pack pain catalog: P56 (LangGraph conditional edges — sibling footgun)
