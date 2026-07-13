# Basic Function Calling

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
