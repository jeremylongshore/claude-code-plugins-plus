# langchain-core-workflow — One-Pager

Compose LangChain 1.0 chains with `RunnableParallel`, `RunnableBranch`, `RunnablePassthrough.assign`, and `RunnableLambda` — correct input/output shapes, debug probes, and typed composition that catches dict-shape bugs before invocation.

## The Problem

An engineer wires a four-stage chain: classify → retrieve → format → generate. `.invoke({"question": "..."})` returns `KeyError: 'question'` from deep inside runnable internals. The stack trace names `_call_with_config` and a transformer class but **never** the stage that produced the wrong dict shape. Swapping `RunnablePassthrough()` for `RunnablePassthrough.assign(context=retriever)` changes the schema in a way that downstream `prompt.invoke(dict_in)` cannot tolerate, but LCEL gives no pre-invocation check (P06). Meanwhile, legacy `AgentExecutor` silently turns tool exceptions into empty-string observations and the agent answers "I couldn't find that" — no error surfaces (P09).

## The Solution

Add a `RunnableLambda` debug probe between every two stages (overhead <1ms per invocation) that prints or logs the dict's keys. For new code, annotate chains with `RunnableSerializable[InputT, OutputT]` plus pydantic `BaseModel` input/output types — mypy and pytest catch P06 at lint time, not at `.invoke()`. Fan-out independent retrievals with `RunnableParallel` for a 2–3× wall-clock win on 2 parallel calls. Route on input shape with `RunnableBranch` (always supply a default). Thread state through the chain with `RunnablePassthrough.assign(field=...)`. For agent loops, skip `AgentExecutor` entirely and use LangGraph's `create_react_agent` — tool errors raise, not vanish.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers wiring multi-step LCEL chains — RAG composition, classification + extraction pipelines, parallel retrieval/tool-use stages, conditional routing |
| **What** | `RunnableParallel` / `RunnableBranch` / `RunnablePassthrough.assign` / `RunnableLambda` patterns, debug-probe recipe, typed composition with `RunnableSerializable[I, O]`, 4 deep references |
| **When** | After `langchain-sdk-patterns` (composition primitives) and `langchain-model-inference` (chat models), before any multi-stage chain ships — P06's cryptic `KeyError` burns hours if the debug probes are not in from the start |

## Key Features

1. **Debug-probe pattern** — A one-line `RunnableLambda(lambda x: (print(f"[probe] keys={list(x.keys())}"), x)[1])` insertable between any two stages, <1ms overhead, surfaces the exact stage that changes the dict shape (P06 fix)
2. **Typed composition with `RunnableSerializable[InputT, OutputT]`** — Annotate chain boundaries with pydantic `BaseModel` types so mypy flags shape mismatches before invocation; pairs with `chain.input_schema.model_json_schema()` for runtime assertion
3. **RAG composition recipe** — End-to-end pattern (retriever + context formatter + prompt + llm + parser) with `RunnablePassthrough.assign(context=retriever)` that preserves the input `question` field through to the prompt, plus a parallel variant for hybrid dense + BM25 retrieval

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
