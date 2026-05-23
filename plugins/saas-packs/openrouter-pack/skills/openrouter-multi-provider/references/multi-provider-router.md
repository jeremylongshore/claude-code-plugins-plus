# Multi-Provider Router

## Multi-Provider Router

### Best Provider for Task

```python
PROVIDER_STRENGTHS = {
    "anthropic": {
        "strengths": ["code", "analysis", "long_context", "safety"],
        "models": {
            "premium": "anthropic/claude-3-opus",
            "standard": "anthropic/claude-3.5-sonnet",
            "fast": "anthropic/claude-3-haiku"
        }
    },
    "openai": {
        "strengths": ["general", "function_calling", "json", "creative"],
        "models": {
            "premium": "openai/gpt-4",
            "standard": "openai/gpt-4-turbo",
            "fast": "openai/gpt-3.5-turbo"
        }
    },
    "meta-llama": {
        "strengths": ["cost", "open_source", "general"],
        "models": {
            "premium": "meta-llama/llama-3.1-405b-instruct",
            "standard": "meta-llama/llama-3.1-70b-instruct",
            "fast": "meta-llama/llama-3.1-8b-instruct"
        }
    },
    "mistralai": {
        "strengths": ["speed", "european", "efficient"],
        "models": {
            "premium": "mistralai/mistral-large",
            "standard": "mistralai/mixtral-8x7b-instruct",
            "fast": "mistralai/mistral-7b-instruct"
        }
    }
}

def select_provider_for_task(
    task: str,
    quality: str = "standard"
) -> str:
    """Select best provider for task."""
    task_providers = {
        "code": ["anthropic", "openai"],
        "analysis": ["anthropic", "openai"],
        "function_calling": ["openai"],
        "json": ["openai"],
        "creative": ["openai", "anthropic"],
        "long_context": ["anthropic"],
        "cost": ["meta-llama", "mistralai"],
        "general": ["anthropic", "openai", "meta-llama"]
    }

    providers = task_providers.get(task, task_providers["general"])
    best_provider = providers[0]

    return PROVIDER_STRENGTHS[best_provider]["models"][quality]

# Usage
model = select_provider_for_task("code", "standard")
# Returns: "anthropic/claude-3.5-sonnet"
```
