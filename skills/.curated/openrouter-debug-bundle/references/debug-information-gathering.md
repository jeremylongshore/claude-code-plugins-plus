# Debug Information Gathering

## Debug Information Gathering

### System Debug Function

```python
def gather_debug_info():
    """Collect all relevant debug information."""
    import platform
    import sys

    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "openai_sdk_version": None,
        "api_key_set": bool(os.environ.get("OPENROUTER_API_KEY")),
        "api_key_prefix": os.environ.get("OPENROUTER_API_KEY", "")[:10] + "...",
    }

    try:
        import openai
        info["openai_sdk_version"] = openai.__version__
    except:
        pass

    # Test connectivity
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
            timeout=10
        )
        info["api_connectivity"] = response.status_code == 200
        info["models_count"] = len(response.json().get("data", []))
    except Exception as e:
        info["api_connectivity"] = False
        info["connectivity_error"] = str(e)

    return info

# Print debug info
import json
print(json.dumps(gather_debug_info(), indent=2))
```

### Request Debug Template

```python
def debug_request(model, messages, **kwargs):
    """Create a debug-friendly request."""
    print("=" * 50)
    print("DEBUG REQUEST")
    print("=" * 50)
    print(f"Model: {model}")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    print(f"Options: {json.dumps(kwargs, indent=2)}")
    print("=" * 50)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        print("SUCCESS")
        print(f"Response model: {response.model}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Finish reason: {response.choices[0].finish_reason}")
        print(f"Content: {response.choices[0].message.content[:500]}...")

        return response

    except Exception as e:
        print("ERROR")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        raise
```
