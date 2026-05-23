# Model Compatibility

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
