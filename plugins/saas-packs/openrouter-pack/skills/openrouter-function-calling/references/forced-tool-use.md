# Forced Tool Use

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
