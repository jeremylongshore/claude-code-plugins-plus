# Model Information Api

## Model Information API

### Get Model Details

```python
def get_model_info(model_id):
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    models = response.json()["data"]
    return next((m for m in models if m["id"] == model_id), None)

model = get_model_info("anthropic/claude-3.5-sonnet")
print(f"Context: {model['context_length']}")
print(f"Prompt cost: ${model['pricing']['prompt']}/token")
print(f"Completion cost: ${model['pricing']['completion']}/token")
```

### Model Schema

```json
{
  "id": "anthropic/claude-3.5-sonnet",
  "name": "Claude 3.5 Sonnet",
  "description": "...",
  "context_length": 200000,
  "pricing": {
    "prompt": "0.000003",
    "completion": "0.000015"
  },
  "top_provider": {
    "context_length": 200000,
    "max_completion_tokens": 8192
  },
  "per_request_limits": null
}
```
