---
name: openrouter-function-calling
description: |
  Implement function/tool calling with OpenRouter models. Use when building agents, structured output, or tool-augmented LLM workflows. Triggers: 'openrouter function calling', 'openrouter tools', 'openrouter agent tools', 'tool use openrouter'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, function-calling, agents, tools]

---
# OpenRouter Function Calling

## Overview

OpenRouter supports OpenAI-compatible tool/function calling across multiple providers. Define tools as JSON Schema, send them with your request, and the model returns structured `tool_calls` instead of free text. This works with GPT-4o, Claude 3.5, Gemini, and other tool-capable models via the same API. The key difference from direct provider APIs: OpenRouter normalizes the tool calling interface, so the same code works across providers.

## Basic Tool Calling

```python
import os, json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# Define tools with JSON Schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "Search the product database",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        },
    },
]

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # Also works with openai/gpt-4o, etc.
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto",  # "auto" | "required" | "none" | {"type":"function","function":{"name":"..."}}
    max_tokens=1024,
)

message = response.choices[0].message
if message.tool_calls:
    for tc in message.tool_calls:
        print(f"Function: {tc.function.name}")
        print(f"Args: {json.loads(tc.function.arguments)}")
        # → Function: get_weather
        # → Args: {"location": "Tokyo", "unit": "celsius"}
```

## Multi-Turn Tool Loop

```python
def tool_loop(user_prompt: str, tools: list, model: str = "openai/gpt-4o", max_rounds: int = 5):
    """Execute tool calls in a loop until the model returns a text response."""
    messages = [{"role": "user", "content": user_prompt}]

    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=tools, max_tokens=1024,
        )
        msg = response.choices[0].message
        messages.append(msg)  # Add assistant message (with tool_calls)

        if not msg.tool_calls:
            return msg.content  # Final text response

        # Execute each tool call and feed results back
        for tc in msg.tool_calls:
            result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    return "Max tool rounds exceeded"

def execute_tool(name: str, args: dict) -> dict:
    """Dispatch to actual function implementations."""
    TOOLS = {
        "get_weather": lambda **kw: {"temp": 22, "condition": "sunny", "location": kw["location"]},
        "search_database": lambda **kw: {"results": [f"Product matching '{kw['query']}'"], "count": 1},
    }
    fn = TOOLS.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": str(e)}

# Usage
result = tool_loop("What's the weather in Tokyo and find me umbrella products?", tools)
print(result)
```

## TypeScript Tool Calling

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: { "HTTP-Referer": "https://my-app.com", "X-Title": "my-app" },
});

const tools: OpenAI.ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "calculate",
      description: "Evaluate a math expression",
      parameters: {
        type: "object",
        properties: { expression: { type: "string" } },
        required: ["expression"],
      },
    },
  },
];

const response = await client.chat.completions.create({
  model: "openai/gpt-4o",
  messages: [{ role: "user", content: "What is 42 * 17 + 3?" }],
  tools,
  tool_choice: "auto",
  max_tokens: 512,
});

const toolCalls = response.choices[0].message.tool_calls;
if (toolCalls) {
  for (const tc of toolCalls) {
    const args = JSON.parse(tc.function.arguments);
    console.log(`${tc.function.name}(${JSON.stringify(args)})`);
  }
}
```

## Structured Output (JSON Mode)

```python
# Force JSON output without tool calling (simpler for extraction tasks)
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[
        {"role": "system", "content": "Extract data as JSON with fields: name, email, company"},
        {"role": "user", "content": "Contact Jane Smith at jane@acme.co, she works at Acme Corp"},
    ],
    response_format={"type": "json_object"},
    max_tokens=200,
)
data = json.loads(response.choices[0].message.content)
# → {"name": "Jane Smith", "email": "jane@acme.co", "company": "Acme Corp"}
```

## Model Compatibility

| Model | Tool Calling | JSON Mode | Parallel Tools |
|-------|-------------|-----------|----------------|
| `openai/gpt-4o` | Yes | Yes | Yes |
| `openai/gpt-4o-mini` | Yes | Yes | Yes |
| `anthropic/claude-3.5-sonnet` | Yes | Via system prompt | Sequential |
| `google/gemini-2.0-flash-001` | Yes | Yes | Yes |
| `meta-llama/llama-3.1-70b-instruct` | Yes (varies) | Via prompt | No |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `tool_calls` is null | Model chose not to call tools | Use `tool_choice: "required"` to force tool use |
| JSON parse error on arguments | Model generated malformed JSON | Wrap in try/catch; retry or use more capable model |
| 400 invalid tool schema | Unsupported JSON Schema types | Stick to basic types (string, number, boolean, object, array) |
| Tool called with wrong args | Schema description unclear | Improve parameter descriptions; add examples in description |

## Enterprise Considerations

- Not all models support tool calling -- check model capabilities via `/api/v1/models` before sending tools
- Use `tool_choice: "required"` when you must get a tool call (e.g., extraction pipelines)
- Validate tool arguments server-side before executing -- models can hallucinate argument values
- Set `max_tokens` to prevent expensive completion when model decides not to use tools
- Use fallback chain with tool-capable models only (see openrouter-fallback-config)
- Log tool call names and arguments for audit trails (redact sensitive args)

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Tool/Function Calling](https://openrouter.ai/docs/features/tool-calling) | [API Reference](https://openrouter.ai/docs/api/reference/overview)
