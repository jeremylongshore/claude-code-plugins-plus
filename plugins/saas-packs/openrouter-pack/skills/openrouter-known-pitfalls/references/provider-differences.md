# Provider Differences

## Provider Differences

### Assuming Identical Behavior

```python
# ❌ Problem: Same code, different providers
# Function calling syntax differs slightly

# OpenAI style (works on OpenAI models)
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    tools=[...],
    tool_choice="auto"
)

# Claude might have slight differences
# Always test with target provider
```

### Different Response Formats

```python
# Different models may format responses differently
# Always handle variations

def extract_response(response, model: str):
    content = response.choices[0].message.content

    # Some models add extra formatting
    if content.startswith("```"):
        # Strip code blocks if not expected
        content = content.strip("`")

    return content
```
