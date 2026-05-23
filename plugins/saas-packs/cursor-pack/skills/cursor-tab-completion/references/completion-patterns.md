# Completion Patterns

## Completion Patterns

### Function Bodies

```python
def fibonacci(n):
    # Tab completes the entire function
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### Repetitive Code

```javascript
// If you've defined similar patterns, AI continues them
const handleNameChange = (e) => setName(e.target.value);
const handleEmailChange = │ // Completes similarly
```

### Test Generation

```python
def test_calculate_total():
    # AI suggests test cases based on function signature
    items = [Item(price=10), Item(price=20)]
    result = calculate_total(items)
    assert result == 30
```

### Documentation

```python
def complex_function(data: dict, options: Options) -> Result:
    """
    │ ← AI completes docstring with params, returns, examples
    """
```
