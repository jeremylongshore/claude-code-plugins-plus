# langchain-model-inference — One-Pager

Invoke Claude, GPT-4o, and Gemini through LangChain 1.0 without tripping on content blocks, token-accounting, or structured-output quirks.

## The Problem

`AIMessage.content` is a `str` on simple OpenAI calls and a `list[dict]` the instant a `tool_use`, `thinking`, or `image` block enters the response — so `message.content.lower()` crashes with `AttributeError` on your first production Claude call. Token counts via `on_llm_end` lag stream duration (5-30s on long completions). `with_structured_output(method="function_calling")` silently drops `Optional[list[X]]` fields on ~40% of real schemas. Default `max_retries=6` on `ChatOpenAI` bills a single logical call as up to seven requests.

## The Solution

This skill walks through `ChatAnthropic`, `ChatOpenAI`, and `ChatGoogleGenerativeAI` initialization with version-safe defaults (explicit timeout, bounded retries); a content-block extractor that handles both `str` and `list[dict]` shapes and streaming deltas; a factory-pattern router that centralizes provider defaults; correct token counting via `astream_events(version="v2")`; and a `with_structured_output` method decision tree tied to each provider's native schema support. Pinned to LangChain 1.0.x with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers initializing chat models, routing across providers, or extracting structured data with LangChain 1.0 |
| **What** | Version-safe model init, content-block-safe extractor, factory routing, streaming token meter, structured-output method decision tree, 4 references (content-blocks, token-accounting, structured-output-methods, provider-quirks) |
| **When** | After `langchain-install-auth`, before any real chain work — this is where content-shape and token-accounting bugs will surface first |

## Key Features

1. **Content-block safe extractor** — Single function handles both `str` (OpenAI simple) and `list[dict]` (Claude always, OpenAI with tools) shapes of `AIMessage.content`; also works on `astream_events` chunks
2. **Streaming token meter via `astream_events(version="v2")`** — Reports input/output/cache tokens incrementally from `on_chat_model_stream` events, not at stream end; dashboards stay live
3. **`with_structured_output` method decision tree** — Per-provider / per-model recommendation matrix (`json_schema` for Claude 3.5+/GPT-4o+/Gemini 2.5; `function_calling` for legacy; `json_mode` + Pydantic retry for unknown), with fallbacks for `Optional[list[X]]` and extra-field issues

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
