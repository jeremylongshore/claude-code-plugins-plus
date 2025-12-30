---
name: openrouter-function-calling
description: |
  Implement function/tool calling with OpenRouter models. Use when building agents or structured outputs. Trigger with phrases like 'openrouter functions', 'openrouter tools', 'openrouter agent', 'function calling'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Function Calling

## Overview

This skill demonstrates implementing function calling and tool use patterns with OpenRouter-supported models.

## Prerequisites

- OpenRouter integration
- Model that supports function calling (GPT-4, Claude, etc.)

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill demonstrates implementing function calling and tool use patterns with OpenRouter-supported models.

## Prerequisites

- OpenRouter integration
- Model that supports function calling (GPT-4, Claude, etc.)

## Basic Function Calling

### Define Tools
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g., 'San Francisco, CA'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="openai/gpt-4-turbo",  # Supports function calling
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto"
)
```

### Handle Tool Calls
```python
import json

def handle_tool_calls(response) -> list:
    """Process tool calls from response."""
    tool_calls = response.choices[0].message.tool_calls

    if not tool_calls:
        return []

    results = []
    for call in tool_calls:
        function_name = call.function.name
        arguments = json.loads(call.function.arguments)

        # Execute function
        if function_name == "get_weather":
            result = get_weather(**arguments)
        else:
            result = {"error": f"Unknown function: {function_name}"}

        results.append({
            "tool_call_id": call.id,
            "role": "tool",
            "content": json.dumps(result)
        })

    return results

def get_weather(location: str, unit: str = "celsius") -> dict:
    """Mock weather function."""
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "conditions": "sunny"
    }
```

### Complete Conversation Loop
```python
def chat_with_tools(prompt: str, tools: list) -> str:
    """Complete conversation with tool execution."""
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # No tool calls - return final response
        if not message.tool_calls:
            return message.content

        # Add assistant message with tool calls
        messages.append(message)

        # Execute tools and add results
        tool_results = handle_tool_calls(response)
        messages.extend(tool_results)

# Usage
result = chat_with_tools(
    "What's the weather in Paris and London?",
    tools
)
print(result)
```

## Advanced Tool Definitions

### Complex Parameters
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search for products in the catalog",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "filters": {
                        "type": "object",
                        "properties": {
                            "min_price": {"type": "number"},
                            "max_price": {"type": "number"},
                            "category": {
                                "type": "string",
                                "enum": ["electronics", "clothing", "home"]
                            },
                            "in_stock": {"type": "boolean"}
                        }
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "price_low", "price_high", "rating"]
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

### Multiple Tools
```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_user",
            "description": "Get user information by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user",
            "description": "Update user information",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List orders for a user",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "shipped", "delivered"]
                    },
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["user_id"]
            }
        }
    }
]
```

## Tool Router

### Dispatch Tool Calls
```python
class ToolRouter:
    """Route and execute tool calls."""

    def __init__(self):
        self.handlers = {}

    def register(self, name: str, handler: callable):
        """Register a function handler."""
        self.handlers[name] = handler

    def execute(self, tool_call) -> dict:
        """Execute a tool call."""
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        handler = self.handlers.get(function_name)
        if not handler:
            return {"error": f"Unknown function: {function_name}"}

        try:
            result = handler(**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}

    def process_response(self, response) -> list:
        """Process all tool calls in response."""
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return []

        return [
            {
                "tool_call_id": call.id,
                "role": "tool",
                "content": json.dumps(self.execute(call))
            }
            for call in tool_calls
        ]

# Setup router
router = ToolRouter()
router.register("get_weather", get_weather)
router.register("get_user", lambda user_id: {"id": user_id, "name": "John"})
router.register("list_orders", lambda user_id, **kwargs: [{"id": "1"}])
```

## Forced Tool Use

### Require Specific Tool
```python
# Force use of specific function
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Get weather data"}],
    tools=tools,
    tool_choice={
        "type": "function",
        "function": {"name": "get_weather"}
    }
)

# Force any tool (model must call a tool)
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Help me check the weather"}],
    tools=tools,
    tool_choice="required"
)

# Disable tools for this request
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Just answer directly"}],
    tools=tools,
    tool_choice="none"
)
```

## Parallel Tool Calls

### Handle Multiple Calls
```python
async def execute_tools_parallel(tool_calls: list) -> list:
    """Execute multiple tool calls in parallel."""
    import asyncio

    async def execute_one(call):
        result = router.execute(call)
        return {
            "tool_call_id": call.id,
            "role": "tool",
            "content": json.dumps(result)
        }

    return await asyncio.gather(*[
        execute_one(call) for call in tool_calls
    ])

# Usage in conversation loop
async def chat_with_parallel_tools(prompt: str, tools: list) -> str:
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=messages,
            tools=tools,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append(message)

        # Execute in parallel
        tool_results = await execute_tools_parallel(message.tool_calls)
        messages.extend(tool_results)
```

## Model Compatibility

### Check Tool Support
```python
TOOL_SUPPORTING_MODELS = {
    "openai/gpt-4-turbo": True,
    "openai/gpt-4": True,
    "openai/gpt-4o": True,
    "openai/gpt-3.5-turbo": True,
    "anthropic/claude-3.5-sonnet": True,  # Via tool_use
    "anthropic/claude-3-opus": True,
    "anthropic/claude-3-haiku": True,
}

def supports_tools(model: str) -> bool:
    """Check if model supports function calling."""
    return TOOL_SUPPORTING_MODELS.get(model, False)

def chat_with_tool_fallback(
    prompt: str,
    tools: list,
    preferred_model: str = "openai/gpt-4-turbo"
):
    """Use tools if supported, otherwise regular chat."""
    if not supports_tools(preferred_model):
        # Fall back to model that supports tools
        preferred_model = "openai/gpt-4-turbo"

    return client.chat.completions.create(
        model=preferred_model,
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
    )
```

## Streaming with Tools

### Stream Tool Responses
```python
def stream_with_tools(prompt: str, tools: list):
    """Stream response that may include tool calls."""
    messages = [{"role": "user", "content": prompt}]

    while True:
        stream = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=messages,
            tools=tools,
            stream=True
        )

        collected_tool_calls = []
        current_content = ""

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Collect content
            if delta.content:
                current_content += delta.content
                yield {"type": "content", "data": delta.content}

            # Collect tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.index >= len(collected_tool_calls):
                        collected_tool_calls.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })
                    if tc.function.name:
                        collected_tool_calls[tc.index]["function"]["name"] = tc.function.name
                    if tc.function.arguments:
                        collected_tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

        # If no tool calls, we're done
        if not collected_tool_calls:
            break

        # Execute tools
        messages.append({
            "role": "assistant",
            "tool_calls": collected_tool_calls
        })

        for tc in collected_tool_calls:
            result = router.execute_dict(tc)
            yield {"type": "tool_result", "data": result}
            messages.append({
                "tool_call_id": tc["id"],
                "role": "tool",
                "content": json.dumps(result)
            })
```

## Error Handling

### Robust Tool Execution
```python
def safe_execute_tool(tool_call, timeout: float = 10.0) -> dict:
    """Execute tool with timeout and error handling."""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Tool execution timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout))

    try:
        result = router.execute(tool_call)
        signal.alarm(0)
        return result
    except TimeoutError:
        return {"error": "Tool execution timed out"}
    except json.JSONDecodeError:
        return {"error": "Invalid tool arguments"}
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
    finally:
        signal.alarm(0)
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
