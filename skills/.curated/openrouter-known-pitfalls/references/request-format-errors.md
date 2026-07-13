# Request Format Errors

## Request Format Errors

### Invalid Message Structure

```python
# ❌ Wrong: Missing role
messages = [{"content": "Hello"}]

# ❌ Wrong: Invalid role
messages = [{"role": "assistant", "content": "Hello"}]  # Can't start with assistant

# ✓ Correct
messages = [{"role": "user", "content": "Hello"}]

# ✓ Correct with system
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello"}
]
```

### Alternating Roles Violation

```python
# ❌ Wrong: Two user messages in a row
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "user", "content": "How are you?"}  # Must alternate
]

# ✓ Correct
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
    {"role": "user", "content": "How are you?"}
]
```
