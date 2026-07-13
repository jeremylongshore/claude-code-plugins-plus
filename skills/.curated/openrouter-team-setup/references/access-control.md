# Access Control

## Access Control

### Model Access by Role

```python
ROLE_MODEL_ACCESS = {
    "admin": [
        "anthropic/claude-3-opus",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4-turbo",
        "openai/gpt-4",
        "openai/gpt-3.5-turbo",
    ],
    "developer": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
    ],
    "intern": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct",
    ]
}

def get_allowed_models(role: str) -> list:
    return ROLE_MODEL_ACCESS.get(role, ROLE_MODEL_ACCESS["intern"])

def role_checked_chat(user_role: str, model: str, prompt: str):
    allowed = get_allowed_models(user_role)

    if model not in allowed:
        raise PermissionError(
            f"Model {model} not available for role {user_role}. "
            f"Allowed: {allowed}"
        )

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```
