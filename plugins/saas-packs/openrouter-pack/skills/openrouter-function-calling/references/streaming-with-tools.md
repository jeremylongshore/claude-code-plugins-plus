# Streaming With Tools

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
