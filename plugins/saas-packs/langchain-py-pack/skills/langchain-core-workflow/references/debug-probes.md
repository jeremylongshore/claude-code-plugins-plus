# Debug Probes

P06's cryptic `KeyError` costs hours when probes are not installed. This
reference covers three tools for making LCEL chains observable: inline
`RunnableLambda` probes, `langchain.debug` global flag, and a shape-assertion
decorator for CI.

## The inline probe

A `RunnableLambda` that logs input and returns it unchanged. <1ms overhead
per invocation. Drop it between any two stages.

```python
from langchain_core.runnables import RunnableLambda

def probe(stage: str, *, logger=print):
    """Observability probe. Logs shape, returns input unchanged."""
    def _probe(x):
        if isinstance(x, dict):
            logger(f"[probe:{stage}] keys={list(x.keys())}")
        else:
            logger(f"[probe:{stage}] type={type(x).__name__}")
        return x
    return RunnableLambda(_probe)
```

Wire it into a chain:

```python
chain = (
    probe("input")
    | RunnablePassthrough.assign(category=classifier)
    | probe("after-classify")
    | RunnablePassthrough.assign(docs=retriever)
    | probe("after-retrieve")
    | prompt
    | probe("after-prompt")
    | llm
    | StrOutputParser()
)

chain.invoke({"question": "What's our refund policy?"})
# [probe:input] keys=['question']
# [probe:after-classify] keys=['question', 'category']
# [probe:after-retrieve] keys=['question', 'category', 'docs']
# [probe:after-prompt] type=ChatPromptValue
```

When P06 strikes, the **last probe that printed** names the stage before the
crash. That stage is where the dict shape changed unexpectedly.

## Gating probes on an env var

You do not want probes printing in production. Gate them:

```python
import os, logging

log = logging.getLogger(__name__)

def probe(stage: str):
    if os.environ.get("LCEL_DEBUG") != "1":
        return RunnableLambda(lambda x: x)  # no-op passthrough
    def _probe(x):
        if isinstance(x, dict):
            log.debug("probe=%s keys=%s", stage, list(x.keys()))
        else:
            log.debug("probe=%s type=%s", stage, type(x).__name__)
        return x
    return RunnableLambda(_probe)
```

Set `LCEL_DEBUG=1` during development, leave it unset in prod. The no-op
probe adds a negligible frame but preserves the chain shape for consistent
behavior.

## Shape-assertion decorator

In CI, probes should **raise** instead of print — turning P06 into a test
failure with a clear message instead of a production mystery:

```python
from langchain_core.runnables import RunnableLambda

def assert_shape(stage: str, required_keys: set[str]):
    """Probe that raises if required keys are missing. For CI."""
    def _assert(x):
        if not isinstance(x, dict):
            raise TypeError(f"[{stage}] expected dict, got {type(x).__name__}")
        missing = required_keys - set(x.keys())
        if missing:
            raise KeyError(f"[{stage}] missing keys: {missing}; have {set(x.keys())}")
        return x
    return RunnableLambda(_assert)

# Usage in tests
test_chain = (
    assert_shape("input", {"question"})
    | RunnablePassthrough.assign(category=classifier)
    | assert_shape("after-classify", {"question", "category"})
    | rest_of_chain
)
```

Name the expected shape at each boundary. A missing key surfaces at that
boundary, not 200 lines into `_call_with_config`.

## `langchain.debug` — the global flag

LangChain ships a global debug mode that logs every runnable's input and
output:

```python
import langchain
langchain.debug = True

chain.invoke({"question": "..."})
# Logs each step with full input/output
```

Useful for **one-off** debugging but verbose — it will dump the full prompt
string, the LLM response, and every intermediate object. Turn it off after
you find the bug.

Alternatively, `langchain.verbose = True` is a lighter logger that shows
chain entry/exit without full payloads.

## Structured logging — replace `print` with `structlog`

For long-running services, prefer structured logging to `print`:

```python
import structlog
logger = structlog.get_logger()

def probe(stage: str):
    def _probe(x):
        keys = list(x.keys()) if isinstance(x, dict) else None
        logger.debug("lcel.probe", stage=stage, keys=keys, type=type(x).__name__)
        return x
    return RunnableLambda(_probe)
```

This writes JSON lines that LangSmith, Datadog, or your log aggregator can
filter by stage.

## LangSmith — the production answer

Once you are past "debug with prints", use [LangSmith](https://smith.langchain.com):

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "ls__..."
```

Every runnable's input, output, latency, and token count show up in the
LangSmith UI. The tradeoff: `RunnableLambda` calls render as opaque blobs
(they do not expose internal structure the way `RunnableSequence` does), so
for observability-first code, prefer composition primitives over lambdas —
see `runnable-composition-matrix.md` in `langchain-sdk-patterns`.

## Probe decision table

| Situation | Use |
|---|---|
| Active development, fast iteration | Inline `print` probes |
| CI test runs | `assert_shape` probes that raise |
| Staging / production (persistent) | `structlog` probes + LangSmith |
| One-off "where did this break?" debug | `langchain.debug = True` |
| Chain works but answers are wrong | LangSmith trace replay |

## Minimal probe — the one-liner

If you want a single-line copy-paste:

```python
probe = RunnableLambda(lambda x: (print(f"[probe] {list(x.keys()) if isinstance(x, dict) else type(x).__name__}"), x)[1])

chain = probe | step_1 | probe | step_2 | probe | step_3
```

Ugly, fast, effective — a one-time debug tool. Replace with the named probe
factory once you know which stage is broken.

## Resources

- [LangChain Python: debugging](https://python.langchain.com/docs/how_to/debugging/)
- [LangSmith tracing setup](https://docs.smith.langchain.com/tracing)
- Pack pain catalog: P06 (the reason this reference exists)
