# Basic Routing Strategies

## Basic Routing Strategies

### Content-Based Routing

```python
def route_by_content(prompt: str) -> str:
    """Route to appropriate model based on content analysis."""
    prompt_lower = prompt.lower()

    # Code-related
    if any(word in prompt_lower for word in ["code", "function", "debug", "python", "javascript"]):
        return "anthropic/claude-3.5-sonnet"

    # Creative writing
    if any(word in prompt_lower for word in ["write", "story", "creative", "poem"]):
        return "anthropic/claude-3-opus"

    # Quick questions
    if len(prompt) < 100 and prompt.endswith("?"):
        return "anthropic/claude-3-haiku"

    # Default
    return "openai/gpt-4-turbo"

def chat_routed(prompt: str, **kwargs):
    model = route_by_content(prompt)
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **kwargs
    )
```

### Token-Length Routing

```python
def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars = 1 token)."""
    return len(text) // 4

def route_by_length(prompt: str, expected_output: int = 500) -> str:
    """Route based on context requirements."""
    prompt_tokens = estimate_tokens(prompt)
    total_tokens = prompt_tokens + expected_output

    # Short context
    if total_tokens < 4000:
        return "openai/gpt-3.5-turbo"

    # Medium context
    if total_tokens < 32000:
        return "openai/gpt-4-turbo"

    # Long context
    if total_tokens < 128000:
        return "anthropic/claude-3.5-sonnet"

    # Very long context
    return "anthropic/claude-3-opus"  # 200K context
```
