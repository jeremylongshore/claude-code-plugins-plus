# `tool_use` Block Iteration

The one-line rule: **use `msg.tool_calls`, not `msg.content`**. This reference
documents the exceptions — streaming deltas, multi-tool-per-turn, and ID
matching — and shows the canonical patterns for each.

## Canonical path (non-streaming)

`AIMessage.tool_calls` is `list[ToolCall]` where each `ToolCall` is:

```python
{
    "name": "get_weather",
    "args": {"city": "Vancouver"},  # parsed dict, NOT a JSON string
    "id":   "toolu_01A7f...",        # provider-shaped; see below
    "type": "tool_call",
}
```

LangChain 1.0 normalizes this across providers. You only drop back to
`msg.content` iteration when you need to see `tool_use` blocks *in
interleaved order* with `text` or `thinking` blocks (e.g., for UI replay).

## Provider-shaped IDs

| Provider | Format | Example | Length |
|----------|--------|---------|--------|
| Anthropic | `toolu_` + 24 base58 chars | `toolu_01A7fMZzxkqp2bYv9rE3wCnL` | 30 chars total |
| OpenAI | `call_` + 24 alphanumerics | `call_abc123def456ghi789jkl012` | 29 chars total |
| Gemini | no native id; LangChain synthesizes UUID4 | `d4e7a2b6-...` | 36 chars |

The `ToolMessage.tool_call_id` you return must match this string
**byte-for-byte**. Round-tripping through a lowercase/uppercase
normalizer is the most common cause of `BadRequestError: tool_use_id
not found`.

## Matching `ToolMessage` back to the right call

```python
from langchain_core.messages import AIMessage, ToolMessage

def handle_tool_calls(ai_msg: AIMessage, tools: dict) -> list[ToolMessage]:
    """Execute each tool call and return one ToolMessage per call."""
    results = []
    for tc in ai_msg.tool_calls:
        fn = tools[tc["name"]]
        try:
            output = fn(**tc["args"])
        except Exception as e:
            # On error, set status="error" — Anthropic treats this as tool_use failure
            results.append(ToolMessage(
                content=f"Error: {e}",
                tool_call_id=tc["id"],
                status="error",
            ))
            continue
        results.append(ToolMessage(
            content=str(output),
            tool_call_id=tc["id"],
        ))
    return results
```

Two invariants that production code violates:

1. **Every `tool_use` gets exactly one `ToolMessage`.** Skipping one (e.g., because you filtered "low-priority" tools) makes Claude reply `messages.N: tool_use ids were found without tool_result blocks`.
2. **Order matters on Anthropic.** `ToolMessage`s must appear in the same order as the original `tool_use` blocks, not the order they finished executing. Sort by `tool_calls` position, not by execution completion time.

## Streaming-delta accumulation

In `astream_events(version="v2")`, `tool_use.input` arrives as *partial
JSON fragments* across multiple `on_chat_model_stream` events. The
chunk-level `tool_call_chunks` field is designed for this:

```python
from collections import defaultdict
import json

async def stream_with_tool_use(model, messages):
    partial_args = defaultdict(str)   # tool_call_index -> accumulated JSON
    tool_calls = {}                    # index -> {name, id}

    async for event in model.astream_events({"messages": messages}, version="v2"):
        if event["event"] != "on_chat_model_stream":
            continue
        chunk = event["data"]["chunk"]
        for tc_chunk in getattr(chunk, "tool_call_chunks", []) or []:
            idx = tc_chunk["index"]
            if tc_chunk.get("name"):
                tool_calls[idx] = {
                    "name": tc_chunk["name"],
                    "id":   tc_chunk["id"],
                }
            if tc_chunk.get("args"):
                partial_args[idx] += tc_chunk["args"]

    # Parse only at end — mid-stream fragments are incomplete JSON
    completed = []
    for idx, meta in tool_calls.items():
        completed.append({**meta, "args": json.loads(partial_args[idx])})
    return completed
```

Three traps:

- **Do not `json.loads` inside the loop.** Partial fragments like `{"city":"Van` raise `JSONDecodeError`. Buffer, then parse once at end.
- **Multiple concurrent tool calls share the same stream.** That's why `tool_call_chunks` is keyed by `index`. Don't assume fragments for call A finish before fragments for call B start.
- **`chunk.tool_call_chunks` can be `None`.** Guard before iterating.

An alternative if you only need the *final* assembled calls: skip
`astream_events` entirely and use `.invoke()`; LangChain accumulates
internally and you read `msg.tool_calls`. Stream-delta handling is only
worth it if you are rendering partial args in real time (e.g., a tool
inspector UI).

## Forced `tool_choice` — P63 trap

`bind_tools([classify], tool_choice={"type":"tool","name":"classify"})`
forces the model to call `classify`. **Use this only for single-call
extraction.** Inside an agent loop, the forced choice prevents
`stop_reason="end_turn"` — the model *must* call a tool even when it
has nothing to do, so your agent loop never terminates.

For loops, use `tool_choice="auto"` (the default) and let the model
decide to stop.

## When to actually iterate `content`

Two real cases:

1. **Order-preserving UI replay.** Rendering a Claude response as
   `thinking (grey italic) → text (black) → tool_use (code block)`
   requires iterating blocks in list order, not semantic grouping.

2. **Claude citations extraction.** Citations attach to *text blocks*,
   not tool calls, but discovering them requires block iteration:

   ```python
   for block in msg.content:
       if block.get("type") != "text":
           continue
       for citation in block.get("citations", []):
           print(f"Cited {citation['document_title']} "
                 f"({citation['cited_text']!r})")
   ```

   `msg.text()` flattens these away — you lose the citations if you use
   it. See `multimodal-composition.md` for the input side (`document`
   blocks), and Anthropic's citations docs for the full citation shape.

## Errors you will hit

| Error | Cause | Fix |
|-------|-------|-----|
| `anthropic.BadRequestError: tool_use_id not found in corresponding tool_result` | Typo / case mismatch in `ToolMessage.tool_call_id` | Copy `tc["id"]` verbatim; never normalize |
| `anthropic.BadRequestError: tool_use ids were found without tool_result blocks` | Skipped one tool call | Emit one `ToolMessage` per `tool_call`, even on errors (use `status="error"`) |
| `json.JSONDecodeError: Expecting property name: line 1 column 2` | `json.loads` on a partial delta | Buffer fragments; parse once at `on_chat_model_end` |
| Infinite agent loop | Forced `tool_choice` inside a loop (P63) | Use `tool_choice="auto"` |
| `AttributeError: 'NoneType' object has no attribute 'append'` on `tool_call_chunks` | Not all chunks carry `tool_call_chunks` | Guard with `or []` |
