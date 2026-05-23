# Testing During Migration

## Testing During Migration

### Parallel Testing

```python
def test_migration(prompt: str, model: str):
    """Test both old and new implementations."""
    # Old implementation
    old_result = old_chat_function(prompt, model)

    # New implementation
    new_result = new_chat_function(prompt, model)

    # Compare
    assert old_result is not None
    assert new_result is not None
    print(f"Old: {old_result[:100]}...")
    print(f"New: {new_result[:100]}...")

    return {
        "old_success": True,
        "new_success": True,
        "responses_match": old_result[:50] == new_result[:50]
    }
```

### Gradual Rollout

```python
import random

def chat_with_rollout(prompt: str, new_implementation_percentage: int = 10):
    """Gradually roll out new implementation."""
    use_new = random.randint(1, 100) <= new_implementation_percentage

    if use_new:
        try:
            return new_chat_function(prompt)
        except Exception as e:
            # Fallback to old on error
            log_error(f"New implementation failed: {e}")
            return old_chat_function(prompt)
    else:
        return old_chat_function(prompt)
```
