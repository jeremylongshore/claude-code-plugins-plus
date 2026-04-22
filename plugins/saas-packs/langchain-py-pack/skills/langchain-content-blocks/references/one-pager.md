# langchain-content-blocks — One-Pager

Work correctly with LangChain 1.0's typed content blocks on `AIMessage.content` — text, tool_use, image, thinking, document — across Claude, GPT-4o, and Gemini.

## The Problem

Multi-modal and tool-use code that works on GPT-4o breaks on Claude because the image-block shape differs (P64) and `AIMessage.content` is always a `list[dict]` on Claude (P02) so `.split()`/`.lower()` crashes with `AttributeError`. Extended-thinking replay fails with `anthropic.BadRequestError: missing signature` when prior `thinking` blocks are stripped between turns. Forcing `tool_choice` to a specific tool ignores `stop_reason="end_turn"` and loops forever (P63).

## The Solution

This skill is the deep reference for LangChain 1.0's six typed block types: text, tool_use, tool_result, image, thinking, document. It covers streaming-delta accumulation of `tool_use.input` JSON, Claude `thinking` block signature preservation for multi-turn replay, the universal `image` block shape (base64 vs url, mime_type rules, per-provider size limits), Claude citations extraction from `document` blocks, and a provider-adapter checklist that keeps multi-modal composition portable across Claude, GPT-4o, and Gemini.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers composing multi-modal messages, iterating `tool_use` across stream deltas, handling Claude extended thinking, or extracting citations |
| **What** | Block-type matrix (6 types x 4 attributes), safe iteration patterns, universal `image` composition, `tool_use` delta accumulation, `thinking` replay with signature, `document`/citations extraction, per-provider adapter checklist, 4 references |
| **When** | After `langchain-model-inference` — when you need multi-modal composition, extended-thinking replay, or citation extraction; or when a tool-calling agent loop needs per-delta `tool_use.input` streaming |

## Key Features

1. **Block-type matrix** — One row per block type (text, tool_use, tool_result, image, thinking, document) with columns for producers, consumer code, streaming behavior, and common gotchas; covers all six types in LangChain 1.0
2. **`tool_use` stream-delta accumulation** — Canonical pattern for assembling fragmented `input` JSON deltas back into a dict before the `on_chat_model_end` event; covers ID matching against `ToolMessage.tool_call_id` (24-char `toolu_*` format on Anthropic)
3. **Claude `thinking` block replay** — Signature verification, redaction (`redacted_thinking`) handling, and multi-turn replay semantics where prior thinking blocks must be passed back intact or Anthropic rejects the request

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
