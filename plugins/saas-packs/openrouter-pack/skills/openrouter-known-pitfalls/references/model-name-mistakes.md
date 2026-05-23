# Model Name Mistakes

## Model Name Mistakes

### Missing Provider Prefix

```python
# ❌ Wrong: No provider prefix
model = "gpt-4-turbo"

# ✓ Correct: With provider prefix
model = "openai/gpt-4-turbo"
```

### Typos in Model Names

```python
# Common typos:
# ❌ "anthropic/claude-3-sonnet"   -> ✓ "anthropic/claude-3.5-sonnet"
# ❌ "openai/gpt4-turbo"           -> ✓ "openai/gpt-4-turbo"
# ❌ "meta/llama-3.1-70b"          -> ✓ "meta-llama/llama-3.1-70b-instruct"

# Verify model exists
def verify_model(model: str) -> bool:
    models = get_available_models(api_key)
    return any(m["id"] == model for m in models)
```

### Deprecated Model Names

```python
# Models get deprecated - check current list
# ❌ "anthropic/claude-2"          -> ✓ "anthropic/claude-3-haiku" (or newer)
# ❌ "openai/gpt-4-0314"           -> ✓ "openai/gpt-4-turbo"

# Always use canonical names from the API
response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
valid_models = [m["id"] for m in response.json()["data"]]
```
