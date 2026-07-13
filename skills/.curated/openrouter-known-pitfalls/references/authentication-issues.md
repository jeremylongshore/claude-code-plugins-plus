# Authentication Issues

## Authentication Issues

### Wrong Key Format

```python
# ❌ Wrong: OpenAI key format
api_key = "sk-..."  # OpenAI format

# ✓ Correct: OpenRouter key format
api_key = "sk-or-v1-..."  # OpenRouter format
```

### Missing Bearer Prefix

```python
# ❌ Wrong: No Bearer prefix
headers = {"Authorization": api_key}

# ✓ Correct: With Bearer prefix
headers = {"Authorization": f"Bearer {api_key}"}
```

### Hardcoded Keys

```python
# ❌ Wrong: Hardcoded key
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-xxxxx"  # Never do this!
)

# ✓ Correct: Environment variable
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)
```
