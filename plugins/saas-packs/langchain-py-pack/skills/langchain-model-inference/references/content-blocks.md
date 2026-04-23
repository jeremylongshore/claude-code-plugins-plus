# AIMessage Content Blocks Reference

LangChain 1.0 unifies provider-specific response shapes into typed content blocks
on `AIMessage.content`. This reference documents the block types, the two places
Claude and OpenAI diverge from the docs, and copy-paste extractors.

## Block Types (LangChain 1.0)

| Type | Fields | Producers |
|------|--------|-----------|
| `text` | `text: str` | All providers |
| `tool_use` | `id: str`, `name: str`, `input: dict` | Claude, GPT-4o with tools, Gemini |
| `tool_result` | `tool_use_id: str`, `content: str \| list` | `ToolMessage` -> serialized here |
| `image` | `source_type: "base64"\|"url"`, `data: str`, `mime_type: str` | Claude, GPT-4o vision |
| `thinking` | `thinking: str`, `signature: str` | Claude extended thinking only |
| `document` | `source: {...}`, `title: str` | Claude citations API |

## The list-vs-str divergence (P02)

`AIMessage.content` is:

- `str` — on simple text completions with **no** tools bound and no multimodal
  input, on OpenAI and Gemini by default
- `list[dict]` — on Claude always (even for text-only), and on OpenAI/Gemini
  the moment a `tool_use` or `image` block appears in the response

Production code must handle both shapes or it crashes on its first Claude call.

## Safe Extractor

```python
from langchain_core.messages import AIMessage

def extract_text(msg: AIMessage) -> str:
    """Return concatenated text content regardless of block shape."""
    if isinstance(msg.content, str):
        return msg.content
    parts = []
    for block in msg.content:
        # Blocks may be dicts (provider-native) or typed objects (1.0 wrappers)
        t = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
        if t == "text":
            parts.append(block["text"] if isinstance(block, dict) else block.text)
    return "".join(parts)


def extract_tool_calls(msg: AIMessage) -> list[dict]:
    """Return tool_use blocks as {name, args, id} dicts."""
    # Prefer the 1.0 helper — it normalizes across providers
    return [
        {"name": tc["name"], "args": tc["args"], "id": tc["id"]}
        for tc in msg.tool_calls
    ]
```

`AIMessage.tool_calls` is canonical. Do not parse `content` for tool calls
directly — the shape differs per provider and per version.

## Streaming deltas

On `astream_events(version="v2")`, each `on_chat_model_stream` event carries a
`chunk` with `content` that is *also* list-or-str. The extractor above works on
chunks too:

```python
async for event in model.astream_events({"messages": [...]}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        print(extract_text(chunk), end="", flush=True)
```

Chunks with `tool_use` deltas have incremental `input` dicts — the final tool
call is only complete on `on_chat_model_end`.

## Universal `image` content block (1.0)

Before 1.0, images were `{"type": "image_url", "image_url": {"url": ...}}` on
OpenAI and `{"type": "image", "source": {"type": "base64", ...}}` on Claude.
1.0 standardizes on:

```python
{
    "type": "image",
    "source_type": "base64",   # or "url"
    "data": b64_string,         # or url if source_type == "url"
    "mime_type": "image/png",
}
```

Use this shape when composing messages manually. The provider adapter translates
to the per-provider wire format.

## When block iteration is wrong

If you iterate `content` to extract tool calls, you re-parse what LangChain
already did. Always use `msg.tool_calls` (list of typed `ToolCall`) instead.
If you iterate to extract plain text, use `msg.text()` (1.0+) — it calls the
extractor above internally.

Hand-roll block iteration only when you need to preserve *order* of mixed
text + tool_use + thinking blocks (e.g., for replaying a conversation in a UI).
