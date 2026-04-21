# Block-Type Matrix (LangChain 1.0)

Full reference for the six typed content blocks that can appear on
`AIMessage.content` (and on streaming chunks). This extends — does not
duplicate — `langchain-model-inference/references/content-blocks.md`,
which covers the two-shape (`str` vs `list[dict]`) divergence and the
safe extractor. Here we go deeper on each block type.

## The matrix

| Block type | Producers | Consumer handling | Streaming behavior | Common gotcha |
|------------|-----------|-------------------|--------------------|---------------|
| `text` | All providers | `msg.text()` (1.0+) concatenates; or filter `block["type"] == "text"` | Arrives as multiple chunks; `text` field grows per delta | On Claude, pure text still comes back as `[{"type":"text","text":"..."}]` — never as `str`. `msg.content.lower()` raises `AttributeError`. |
| `tool_use` | Claude, GPT-4o with tools bound, Gemini 2.5 | **Never hand-parse.** Use `msg.tool_calls` (normalized `list[ToolCall]`). | Partial; `input` arrives as JSON fragments across deltas and is only complete on `on_chat_model_end` | IDs are provider-shaped (`toolu_01ABC...` on Anthropic, `call_abc123` on OpenAI, 24+ chars). Match `ToolMessage.tool_call_id` exactly — case-sensitive. |
| `tool_result` | You (via `ToolMessage`) | Constructed with `ToolMessage(content=..., tool_call_id=tc["id"])`; serialized into `content` when the message list is sent back | N/A (input side) | `content` accepts `str` or `list[dict]` of blocks. Returning an image requires a `list[dict]` with an `image` block — a bare base64 string is interpreted as text and the model "sees" garbled characters. |
| `image` | Claude, GPT-4o vision, Gemini 2.5 | In 1.0, use the universal shape `{"type":"image","source_type":"base64"\|"url","data":"...","mime_type":"image/..."}`; the adapter translates to per-provider wire format | Images do not stream; they are part of the initial `HumanMessage` on input | Pre-1.0 code used `{"type":"image_url","image_url":{"url":...}}` (OpenAI) or `{"type":"image","source":{"type":"base64",...}}` (Anthropic). Mixing both in one `messages` list breaks the adapter. |
| `thinking` | Claude (extended thinking only; Opus 4+, Sonnet 4+) | Filter with `block["type"] == "thinking"`; preserve `signature` verbatim for replay | Streams as `thinking_delta` then `signature_delta` events; full block only assembled at end | **Must be passed back intact on next turn** or Anthropic returns `BadRequestError: messages.N.content.M: missing signature`. Redacted variants (`redacted_thinking`) carry no plaintext but still require signature. |
| `document` | Claude (citations API, Sonnet 4+) | Iterate `block["type"] == "document"` for source metadata; citation blocks appear *inline* in the following `text` blocks with `citations: [...]` arrays | Document blocks are input-side; citations attached to output `text` blocks stream with the text | `document` is input-only. On the response, citations attach as metadata on `text` blocks (`block["citations"]`). Parsing the top-level `content` list for a `citation` type finds nothing. |

## Cross-cutting invariants

1. **Order is load-bearing.** `content` is a *list*, not a set. For a Claude response the order is typically `thinking → text → tool_use` (or `thinking → tool_use`). Re-ordering when you round-trip breaks replay (see `thinking-blocks.md`).

2. **Blocks can be dicts *or* typed objects.** In LangChain 1.0 some providers hand back `dict` blocks while others hand back typed wrappers (`TextBlock`, etc.). Your extractor must handle both — see `langchain-model-inference/references/content-blocks.md#safe-extractor` for the canonical pattern.

3. **`msg.tool_calls` is canonical.** Do not derive tool calls from `content`. The 1.0 `AIMessage.tool_calls: list[ToolCall]` is normalized across providers and strips the format drift.

## Producer compatibility

| Block type | Claude (Sonnet 4.6) | GPT-4o | Gemini 2.5 Pro |
|------------|---------------------|--------|----------------|
| `text` | yes | yes | yes |
| `tool_use` | yes (IDs: `toolu_*`) | yes (IDs: `call_*`) | yes (no id, LangChain synthesizes) |
| `image` input | yes (5MB/image, up to 20) | yes (20MB/image, no hard count) | yes (20MB per request, combined) |
| `thinking` | yes (extended thinking only) | no | no |
| `document` | yes (citations API) | no | no |

## When to iterate blocks manually vs. use helpers

Use the helper when:
- You only want text. Use `msg.text()`.
- You want tool calls. Use `msg.tool_calls`.
- You want usage. Use `msg.usage_metadata`.

Iterate blocks manually when:
- You need to preserve order (e.g., rendering `thinking → text → tool_use` in a transcript UI).
- You are round-tripping a Claude assistant message back into the next turn and must keep `thinking` blocks intact (see `thinking-blocks.md`).
- You are extracting Claude citations (see `tool-use-iteration.md#citations` and below).

## Minimal iteration pattern (order-preserving)

```python
from langchain_core.messages import AIMessage

def iter_blocks(msg: AIMessage):
    """Yield (type, block) pairs in order. Works on both shapes."""
    if isinstance(msg.content, str):
        yield "text", {"type": "text", "text": msg.content}
        return
    for block in msg.content:
        if isinstance(block, dict):
            yield block.get("type", "unknown"), block
        else:
            yield getattr(block, "type", "unknown"), block
```

Use this when the *sequence* of blocks matters. For the common case of
"just get me the text," stick with `msg.text()`.
