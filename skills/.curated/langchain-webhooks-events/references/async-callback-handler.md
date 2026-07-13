# Async Callback Handler — Fire-and-Forget Dispatch

A production-shaped `AsyncCallbackHandler` that dispatches LangChain 1.0 events
to an external sink without blocking the chain. Covers the sync-vs-async
decision, event filtering, task lifetime (the GC footgun), and graceful drain.

## Sync vs async handler — pick one, not both

LangChain 1.0 exposes two base classes:

| Class | When to use | Blocking behavior |
|---|---|---|
| `BaseCallbackHandler` (sync) | Only if every `on_*` method is CPU-only and fast (<1ms) | Blocks the chain step-by-step |
| `AsyncCallbackHandler` (async) | **Default for dispatch handlers** — any I/O | Awaited inline; must `asyncio.create_task` to fan out |

**Never mix** — if your handler subclasses `BaseCallbackHandler` but the
`on_*` methods are `async def`, LangChain will not await them. They become
fire-and-forget by accident, and exceptions get swallowed. Subclass
`AsyncCallbackHandler` explicitly when you need async I/O.

## The full handler

```python
import asyncio
import logging
import uuid
from collections.abc import Awaitable
from typing import Any, Protocol
from langchain_core.callbacks import AsyncCallbackHandler

logger = logging.getLogger(__name__)

class Sink(Protocol):
    async def send(
        self,
        *,
        idempotency_key: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...

class EventDispatchHandler(AsyncCallbackHandler):
    """Fire-and-forget event dispatch for LangChain 1.0.

    Usage:
        handler = EventDispatchHandler(sink=webhook_sink, run_id=req.id)
        try:
            result = await agent.ainvoke(
                {"messages": msgs},
                config={"callbacks": [handler]},  # P28 — pass via config
            )
        finally:
            await handler.drain(timeout=5.0)
    """

    def __init__(
        self,
        sink: Sink,
        *,
        run_id: str | None = None,
        dispatch_on_tool_start: bool = False,
        dispatch_on_llm_end: bool = True,
    ):
        self.sink = sink
        self.run_id = run_id or str(uuid.uuid4())
        self._step = 0
        self._tasks: set[asyncio.Task] = set()
        self._opts = {
            "tool_start": dispatch_on_tool_start,
            "llm_end": dispatch_on_llm_end,
        }

    def _next_step(self) -> int:
        self._step += 1
        return self._step

    def _dispatch(self, event_type: str, payload: dict) -> None:
        step = self._next_step()
        key = f"{self.run_id}:{event_type}:{step}"
        task = asyncio.create_task(self._safe_send(key, event_type, payload))
        # Footgun: asyncio drops weak references to orphan tasks. Hold strong
        # refs in the set so the GC doesn't cancel dispatch mid-flight.
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _safe_send(self, key: str, event_type: str, payload: dict) -> None:
        try:
            await self.sink.send(idempotency_key=key, event_type=event_type, payload=payload)
        except Exception:  # noqa: BLE001 — dispatch errors must not kill the chain
            logger.exception("event dispatch failed key=%s", key)

    # --- Callback hooks ---

    async def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        if not self._opts["tool_start"]:
            return
        self._dispatch(
            "tool_start",
            {
                "tool": (serialized or {}).get("name"),
                "input": input_str[:2000],
                "run_id": str(run_id),
            },
        )

    async def on_tool_end(self, output, *, run_id, **kwargs):
        self._dispatch(
            "tool_end",
            {
                "output": str(output)[:4000],
                "run_id": str(run_id),
            },
        )

    async def on_tool_error(self, error: BaseException, *, run_id, **kwargs):
        self._dispatch(
            "tool_error",
            {
                "error": f"{type(error).__name__}: {error}",
                "run_id": str(run_id),
            },
        )

    async def on_chain_end(self, outputs, *, run_id, **kwargs):
        # Skip unnamed / LCEL-internal nodes — P47 noise.
        name = kwargs.get("name")
        if not name or name.startswith(("RunnableLambda", "RunnableParallel", "RunnableSequence")):
            return
        self._dispatch("chain_end", {"name": name, "run_id": str(run_id)})

    async def on_llm_end(self, response, *, run_id, **kwargs):
        if not self._opts["llm_end"]:
            return
        usage = {}
        try:
            # LangChain 1.0 — AIMessage.usage_metadata
            gen = response.generations[0][0]
            msg = gen.message
            if getattr(msg, "usage_metadata", None):
                usage = dict(msg.usage_metadata)
        except (AttributeError, IndexError):
            pass
        self._dispatch("llm_end", {"usage": usage, "run_id": str(run_id)})

    # --- Graceful shutdown ---

    async def drain(self, timeout: float = 5.0) -> None:
        """Await in-flight dispatches. Call in endpoint finally block."""
        if not self._tasks:
            return
        done, pending = await asyncio.wait(self._tasks, timeout=timeout)
        if pending:
            logger.warning("drain timeout: %d dispatches still in flight", len(pending))
            for t in pending:
                t.cancel()
```

## Why the strong-reference set (`self._tasks`)

CPython's asyncio keeps only weak references to tasks created by
`asyncio.create_task`. An orphan task — no strong reference from anywhere —
can be garbage-collected mid-flight, silently cancelling the dispatch. Every
real handler keeps the task in a set and removes it on completion:

```python
task = asyncio.create_task(coro)
self._tasks.add(task)
task.add_done_callback(self._tasks.discard)
```

Missing this is the most common reason "sometimes the webhook fires, sometimes
it doesn't" in load testing.

## Step-index monotonicity

`step_index` in the idempotency key is a per-handler-instance counter. It
guarantees uniqueness within a run, which is all the receiver needs. Do NOT use
the LangChain `run_id` alone — the same `run_id` will fire multiple `on_tool_end`
events if the chain calls the same tool twice, and identical keys mean the
receiver will dedupe legitimate second calls.

## Event filter tuning

The three flags (`dispatch_on_tool_start`, `dispatch_on_llm_end`, and implicit
"dispatch on_tool_end / on_chain_end for named only") cover 90% of cases.
If you need a custom filter, override `_dispatch` to accept a predicate:

```python
def _dispatch(self, event_type, payload):
    if self.filter and not self.filter(event_type, payload):
        return
    ...
```

## When to prefer `astream_events` over a callback handler

Callbacks fire in the same task as the chain step. `astream_events(version="v2")`
decouples: the chain pushes events onto an async queue, your consumer reads in a
separate task. Prefer `astream_events` when:

- The dispatch logic needs its own concurrency limit (semaphore) across events
- You want to batch-dispatch (e.g., accumulate 10 events then POST)
- You need to replay events from a recorded stream

Stick with callbacks when:

- You want subgraph propagation automatically (callbacks pass via `config`)
- The dispatch is per-event fire-and-forget (no batching)
- You want to use the same handler in tests via `FakeListChatModel`

## Testing the handler

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_handler_dispatches_tool_end():
    sink = AsyncMock()
    handler = EventDispatchHandler(sink=sink, run_id="r1")

    await handler.on_tool_end(output="ok", run_id="tool-1")
    await handler.drain()

    sink.send.assert_awaited_once()
    call = sink.send.call_args.kwargs
    assert call["idempotency_key"] == "r1:tool_end:1"
    assert call["event_type"] == "tool_end"
    assert call["payload"]["output"] == "ok"
```

## Cross-references

- [Dispatch Targets](dispatch-targets.md) — what `sink` looks like for each transport
- [Subgraph Propagation](subgraph-propagation.md) — why `config["callbacks"]` is required (P28)
- [Idempotency and Retry](idempotency-and-retry.md) — receiver-side de-dup and replay semantics
