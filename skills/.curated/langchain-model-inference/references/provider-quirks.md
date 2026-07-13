# Provider-Specific Quirks

Quick reference for the places Claude, GPT-4o, and Gemini diverge in ways that
break LangChain code.

## Claude (langchain-anthropic 1.0.x)

| Quirk | Impact | Fix |
|---|---|---|
| `AIMessage.content` always `list[dict]`, even on text-only | Code that calls `.lower()` on content crashes | Use `msg.text()` or content extractor (P02) |
| `temperature=0` still uses nucleus sampling | Snapshot tests nondeterministic (P05) | Record with VCR or use `FakeListChatModel` |
| System message goes to `system` field, not messages array | Middleware that reorders messages silently loses system prompt (P58) | Validate first message is `SystemMessage` before send |
| Forced `tool_choice={"type":"tool", "name":"X"}` prevents `end_turn` stop (P63) | Agent loops forever | Use forced choice only for single-shot extraction |
| Tool description > 1024 chars truncated silently (P11) | Agent picks wrong arg shape | Keep descriptions short; move examples to prompt |

## OpenAI (langchain-openai 1.0.x)

| Quirk | Impact | Fix |
|---|---|---|
| `max_retries=6` default | 1 logical call can bill as 7 (P30) | Set `max_retries=2` |
| `.batch()` default `max_concurrency=1` on some older versions (P08) | Serial batching | Pass `config={"max_concurrency": 10}` |
| o1/o3 reasoning tokens invisible in content | Cost surprise | Include `output_token_details.reasoning` in math |
| Image input as `image_url`, not Claude's `source_type` (P64) | Multi-modal code breaks on swap | Use 1.0 universal `image` block |
| `response_format={"type":"json_object"}` does NOT enforce schema (P54) | Ships invalid shapes | Prefer `method="json_schema"` on GPT-4o+ |

## Gemini (langchain-google-genai 1.0.x)

| Quirk | Impact | Fix |
|---|---|---|
| Safety filters block benign medical/legal/security prompts (P65) | `finish_reason=SAFETY`, empty content | Override `safety_settings` per init |
| Streaming emits `usage_metadata` on every chunk | Different aggregation code than OpenAI | Use the union pattern in Token Accounting ref |
| Tool-call `args` sometimes arrive as JSON strings instead of dicts | `KeyError` in tool dispatch | Parse with `json.loads` defensively |
| Context caching is separate API, not transparent | Caching requires explicit management | Use provider's `CachedContent` if needed |

## Cross-provider invariants

Properties you can rely on across all three when using LangChain 1.0:

- `AIMessage.tool_calls` is a canonical list of `{name, args, id}` dicts
- `AIMessage.usage_metadata` follows the `{input_tokens, output_tokens, total_tokens}` shape
- `astream_events(version="v2")` produces the same event taxonomy
- `with_structured_output(Schema, method="json_schema")` enforces the schema on
  the capable models listed in the decision tree

Code that sticks to these invariants is provider-agnostic. Code that reads
`response_metadata` or iterates `content` by hand is provider-specific.

## Draft-then-finalize pattern

A production pattern — use a cheap model for the first pass, expensive model for
the final output:

```python
def draft_and_finalize(prompt: str, schema: type[BaseModel]) -> BaseModel:
    draft_model = chat_model("openai", model="gpt-4o-mini", timeout=20)
    final_model = chat_model("anthropic", model="claude-sonnet-4-6", timeout=30)

    draft = draft_model.invoke(f"Draft an answer, bullet points only: {prompt}")
    structured = final_model.with_structured_output(schema, method="json_schema")
    return structured.invoke(
        f"Refine this draft into the requested schema.\n\nDraft:\n{draft.text()}"
    )
```

Savings depend on workload but typically 50-70% of tokens go through the cheap
model. Keep the final model's input short — paste only the draft bullets, not
the full conversation history.

## When to abstain from switching providers

If your prompt relies on a provider-specific feature (extended thinking, specific
tool-use format, Anthropic's citations API), the switch cost is often larger
than the cost savings. Measure per-prompt cost on the target provider before
migrating.
