# Parallel Tool Calls

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
