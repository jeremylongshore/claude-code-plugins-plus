# Provider-Specific Features

## Provider-Specific Features

### OpenAI Features

```python
def openai_with_json_mode(prompt: str):
    """Use OpenAI JSON mode."""
    return client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

def openai_with_functions(prompt: str, tools: list):
    """Use OpenAI function calling."""
    return client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        tool_choice="auto"
    )
```

### Anthropic Features

```python
def anthropic_long_context(prompt: str, context: str):
    """Use Claude's long context window."""
    # Claude 3 supports 200K tokens
    messages = [
        {"role": "system", "content": f"Context:\n{context}"},
        {"role": "user", "content": prompt}
    ]

    return client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=messages,
        max_tokens=4096
    )
```

### Open Source Models

```python
def use_open_source(prompt: str, prefer_local: bool = False):
    """Use open source models through OpenRouter."""
    models = [
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mixtral-8x7b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
    ]

    model = models[0]

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```
