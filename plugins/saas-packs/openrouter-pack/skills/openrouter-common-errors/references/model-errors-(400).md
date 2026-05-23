# Model Errors (400)

## Model Errors (400)

### Model Not Found

```
Error: 400 Bad Request
{
  "error": {
    "message": "Model not found: invalid/model-name",
    "type": "invalid_request_error"
  }
}
```

**Fixes:**

```python
# Check exact model ID format
# Wrong
model = "gpt-4-turbo"

# Right
model = "openai/gpt-4-turbo"

# Get valid models
response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
valid_models = [m["id"] for m in response.json()["data"]]
```

### Model Temporarily Unavailable

```
Error: 503 Service Unavailable
{
  "error": {
    "message": "Model temporarily unavailable",
    "type": "service_unavailable"
  }
}
```

**Handling:**

```python
FALLBACK_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct",
]

def chat_with_fallback(prompt, models=FALLBACK_MODELS):
    for model in models:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as e:
            if "unavailable" in str(e).lower():
                continue
            raise
    raise Exception("All models unavailable")
```
