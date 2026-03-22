---
name: anth-migration-deep-dive
description: |
  Migrate to Claude API from OpenAI, Gemini, or other LLM providers.
  Use when switching from GPT-4 to Claude, migrating from Text Completions,
  or building a multi-provider abstraction layer.
  Trigger with phrases like "migrate to claude", "openai to anthropic",
  "switch from gpt to claude", "multi-provider llm".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Migration Deep Dive

## Overview

Migration strategies for switching to Claude from OpenAI, Google, or other LLM providers, including API mapping, prompt translation, and multi-provider abstraction.

## OpenAI to Anthropic API Mapping

| OpenAI | Anthropic | Notes |
|--------|-----------|-------|
| `openai.ChatCompletion.create()` | `anthropic.messages.create()` | Different response shape |
| `model: "gpt-4"` | `model: "claude-sonnet-4-20250514"` | Different model IDs |
| `messages: [{role, content}]` | `messages: [{role, content}]` | Same format |
| `functions` / `tools` | `tools` | Similar but different schema key names |
| `function_call` | `tool_choice` | Different naming |
| `response.choices[0].message.content` | `response.content[0].text` | Different access path |
| `stream: true` → yields chunks | `stream: true` → SSE events | Different event format |
| System message in `messages[]` | `system` parameter (separate) | Claude separates system prompt |
| `n` (multiple completions) | Not supported | Use multiple requests |
| `logprobs` | Not supported | N/A |

## Side-by-Side Code Comparison

```python
# === OpenAI ===
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"}
    ],
    max_tokens=1024,
    temperature=0.7
)
text = response.choices[0].message.content

# === Anthropic ===
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system="You are helpful.",           # System prompt is separate
    messages=[
        {"role": "user", "content": "Hello"}
    ],
    max_tokens=1024,                     # Required (not optional)
    temperature=0.7
)
text = response.content[0].text
```

## Tool Use Migration

```python
# OpenAI tools format
openai_tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
    }
}]

# Anthropic tools format — flatter structure
anthropic_tools = [{
    "name": "get_weather",
    "description": "Get weather for a city",  # Required in Anthropic
    "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}}
}]
```

## Multi-Provider Abstraction

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str = "", **kwargs) -> str: ...

class AnthropicProvider(LLMProvider):
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic()

    def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        msg = self.client.messages.create(
            model=kwargs.get("model", "claude-sonnet-4-20250514"),
            max_tokens=kwargs.get("max_tokens", 1024),
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()

    def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self.client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 1024)
        )
        return resp.choices[0].message.content
```

## Migration Checklist

- [ ] Map model names (GPT-4 → Claude Sonnet, GPT-3.5 → Claude Haiku)
- [ ] Move system prompts from `messages[]` to `system` parameter
- [ ] Update response access path (`.choices[0].message.content` → `.content[0].text`)
- [ ] Make `max_tokens` explicit (required in Anthropic, optional in OpenAI)
- [ ] Update tool definitions to Anthropic format
- [ ] Test prompt behavior (Claude may respond differently to same prompts)
- [ ] Update error handling for Anthropic error types

## Resources

- [Anthropic vs OpenAI Migration](https://docs.anthropic.com/en/docs/about-claude/models)
- [Messages API Reference](https://docs.anthropic.com/en/api/messages)

## Next Steps

For advanced debugging, see `anth-advanced-troubleshooting`.
