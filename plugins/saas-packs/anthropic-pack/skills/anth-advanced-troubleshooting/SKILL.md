---
name: anth-advanced-troubleshooting
description: |
  Debug complex Claude API issues including context window overflow,
  tool use failures, streaming corruption, and response quality problems.
  Trigger with phrases like "anthropic advanced debug", "claude complex issue",
  "claude tool use failing", "claude context overflow".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Advanced Troubleshooting

## Issue: Context Window Overflow

```python
# Symptom: invalid_request_error about token count
# Diagnosis: pre-check with Token Counting API
import anthropic

client = anthropic.Anthropic()

count = client.messages.count_tokens(
    model="claude-sonnet-4-20250514",
    messages=conversation_history,
    system=system_prompt
)
print(f"Input tokens: {count.input_tokens}")
# Claude Sonnet: 200K context, Claude Opus: 200K context

# Fix: truncate oldest messages or summarize
def trim_conversation(messages: list, max_tokens: int = 180_000) -> list:
    """Keep recent messages within token budget."""
    # Always keep first (system context) and last 5 messages
    if len(messages) <= 5:
        return messages
    return messages[:1] + messages[-5:]  # Crude but effective
```

## Issue: Tool Use Not Triggering

```python
# Symptom: Claude responds with text instead of calling tools
# Diagnosis checklist:
# 1. Tool description must clearly state WHEN to use the tool
# 2. User message must match the tool's trigger condition

# BAD description (too vague):
{"name": "search", "description": "Search for things"}

# GOOD description (clear trigger):
{"name": "search_products", "description": "Search the product catalog by name, category, or price range. Use whenever the user asks about products, pricing, or availability."}

# Force tool use if needed:
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "any"},  # Must call at least one tool
    messages=[{"role": "user", "content": "Find products under $50"}]
)
```

## Issue: Streaming Drops or Corruption

```python
# Symptom: stream ends prematurely or text is garbled
# Cause: network interruption, proxy timeout, or large response

# Fix: implement reconnection with content tracking
def resilient_stream(client, **kwargs):
    """Stream with reconnection on failure."""
    collected_text = ""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            with client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    collected_text += text
                    yield text
                return  # Success
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            # Note: Claude streams are NOT resumable
            # Must restart from beginning
            collected_text = ""
            print(f"Stream interrupted, retrying ({attempt + 1}/{max_retries})")
```

## Issue: Unexpected Stop Reason

| Stop Reason | Meaning | Action |
|-------------|---------|--------|
| `end_turn` | Normal completion | Expected |
| `max_tokens` | Hit token limit | Increase `max_tokens` |
| `stop_sequence` | Hit stop sequence | Check `stop_sequences` array |
| `tool_use` | Wants to call a tool | Process tool call and continue |

```python
# Debug unexpected truncation
msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,  # Was it too low?
    messages=[{"role": "user", "content": long_prompt}]
)
print(f"Stop reason: {msg.stop_reason}")
print(f"Output tokens: {msg.usage.output_tokens}")
print(f"Max tokens: 4096")
# If output_tokens == max_tokens, response was truncated
```

## Issue: Response Quality Degradation

```python
# Checklist for quality issues:
# 1. System prompt too long or contradictory?
# 2. Conversation history too noisy (too many turns)?
# 3. Wrong model for task complexity?
# 4. Temperature too high for deterministic tasks?

# Debug: log the full request for review
import json
request_params = {
    "model": model,
    "max_tokens": max_tokens,
    "system": system[:200] + "...",  # Truncated for logging
    "message_count": len(messages),
    "temperature": temperature,
}
print(f"Request config: {json.dumps(request_params, indent=2)}")
```

## Diagnostic Curl Commands

```bash
# Test specific model availability
for model in claude-haiku-4-20250514 claude-sonnet-4-20250514 claude-opus-4-20250514; do
  echo -n "$model: "
  curl -s -o /dev/null -w "%{http_code}" https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "{\"model\":\"$model\",\"max_tokens\":8,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}"
  echo
done
```

## Resources

- [Error Reference](https://docs.anthropic.com/en/api/errors)
- [Token Counting](https://docs.anthropic.com/en/docs/build-with-claude/token-counting)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)

## Next Steps

For load testing, see `anth-load-scale`.
