---
name: groq-core-workflow-a
description: |
  Execute Groq's primary workflow: chat completions with tool use and JSON mode.

  Use when implementing chat interfaces, function calling, structured output,
  or building AI features with Groq's fast inference.

  Trigger with phrases like "groq chat completion", "groq tool use",
  "groq function calling", "groq JSON mode".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- workflow
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Core Workflow A: Chat, Tools & Structured Output

## Overview

Primary integration patterns for Groq: chat completions, tool/function calling, JSON mode, and structured outputs. Groq's LPU delivers sub-200ms time-to-first-token, making these patterns viable for real-time user-facing features. This skill walks through five workflow steps; the lean skeleton lives here, and the full copy-paste code lives in `references/`.

## Prerequisites

- Install the SDK with `npm install groq-sdk`.
- Set `GROQ_API_KEY` in the environment (see Authentication below).
- Familiarity with the Groq model line-up and which model fits each task.

## Authentication

Groq authenticates via an API key. Create one at `console.groq.com/keys` and
export it as `GROQ_API_KEY`; the SDK reads it automatically, so `new Groq()`
needs no explicit argument. Never hardcode the key — read it from the
environment (or a secrets manager) so it stays out of source control.

## Model Selection for This Workflow

| Task | Recommended Model | Why |
|------|------------------|-----|
| Chat with tools | `llama-3.3-70b-versatile` | Best tool-calling accuracy |
| JSON extraction | `llama-3.1-8b-instant` | Fast, accurate for structured tasks |
| Structured outputs | `llama-3.3-70b-versatile` | Supports `strict: true` schema compliance |
| Vision + chat | `meta-llama/llama-4-scout-17b-16e-instruct` | Multimodal input |

## Instructions

Work through the five patterns in order. Read the target file, then Write or
Edit the integration code into your project.

1. **Chat completion** — send `system` + `user` messages to
   `groq.chat.completions.create` and return `choices[0].message.content` plus
   `usage`. Skeleton below; full example in
   [worked examples](references/examples.md).
2. **Tool use / function calling** — a three-phase loop: send the message with
   `tools` + `tool_choice: "auto"`, execute any returned `tool_calls`, then send
   the results back for the final answer. Full code in
   [implementation](references/implementation.md).
3. **JSON mode** — set `response_format: { type: "json_object" }` and describe
   the JSON shape in the system prompt. See
   [implementation](references/implementation.md).
4. **Structured outputs** — use `response_format.json_schema` with
   `strict: true` for guaranteed schema compliance (no post-validation). See
   [implementation](references/implementation.md).
5. **Multi-turn conversation** — accumulate the message history and push each
   assistant reply back onto the stack. See
   [worked examples](references/examples.md).

Minimal chat skeleton:

```typescript
import Groq from "groq-sdk";
const groq = new Groq();

const completion = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [
    { role: "system", content: "You are a concise technical assistant." },
    { role: "user", content: userMessage },
  ],
  temperature: 0.7,
  max_tokens: 1024,
});
// completion.choices[0].message.content, completion.usage
```

## Output

Each pattern returns a predictable shape:

- **Chat completion** — `{ reply: string, usage: {...} }`; `usage` carries
  `prompt_tokens` / `completion_tokens` for cost metering.
- **Tool use** — the final assistant `content` string, produced after the tool
  results are fed back; intermediate `tool_calls` carry `function.name` and a
  JSON-string `function.arguments`.
- **JSON mode** — a parsed JavaScript object matching the shape described in the
  system prompt (parse `message.content` with `JSON.parse`).
- **Structured outputs** — a parsed object *guaranteed* to satisfy the declared
  JSON schema, so no downstream validation is required.
- **Multi-turn** — the latest reply string, with conversation state retained in
  the class instance for the next turn.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `tool_calls` with malformed JSON | Model hallucinated arguments | Wrap `JSON.parse` in try/catch, retry with lower temperature |
| `json_object` returns non-JSON | System prompt missing JSON instruction | Always include "respond with JSON" in system prompt |
| `context_length_exceeded` | Conversation too long | Trim older messages, keep system prompt |
| Tool call loop | Model keeps calling tools | Set `tool_choice: "none"` on final completion |

## Examples

The chat skeleton above is the smallest complete call. Two fuller runnable
examples live in [worked examples](references/examples.md):

- **Example 1 — Chat completion with system prompt + rolling history**, returning
  `reply` and token `usage`.
- **Example 2 — Multi-turn conversation class** that retains context across turns.

For tool use, JSON mode, and strict structured outputs, see
[full implementation](references/implementation.md).

## Resources

- [Groq Tool Use Docs](https://console.groq.com/docs/tool-use)
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs)
- [Groq Text Generation](https://console.groq.com/docs/text-chat)
- [Full implementation](references/implementation.md) — tool use, JSON mode, structured outputs
- [Worked examples](references/examples.md) — chat completion, multi-turn conversation

## Next Steps

For audio, vision, and speech workflows, see the companion `groq-core-workflow-b`
skill, which covers Whisper transcription, vision inputs, and text-to-speech.
