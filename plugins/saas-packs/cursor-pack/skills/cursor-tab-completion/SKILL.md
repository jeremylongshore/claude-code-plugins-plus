---
name: cursor-tab-completion
description: |
  Master Cursor tab completion and AI code suggestions. Triggers on "cursor completion",
  "cursor tab", "cursor suggestions", "cursor autocomplete", "cursor ghost text".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Tab Completion Mastery

## How Tab Completion Works

### The Completion Flow
```
1. You type code
2. Cursor analyzes context (open files, imports, patterns)
3. AI generates suggestion (ghost text)
4. Ghost text appears in gray
5. Press Tab to accept, Esc to reject
```

### Visual Indicators
```python
def calculate_total(items):
    │                          ← Cursor here
    return sum(item.price for item in items)  ← Ghost text (gray)
```

## Accepting Completions

### Full Acceptance
- **Tab**: Accept entire suggestion
- Cursor moves to end of inserted text

### Partial Acceptance
- **Ctrl+Right**: Accept next word
- **Cmd+Right** (Mac): Accept to end of line
- **Hold Tab**: Accept character by character

### Rejecting Completions
- **Esc**: Dismiss current suggestion
- Continue typing: Suggestion updates
- Move cursor: Suggestion dismissed

## Cycling Through Suggestions

### Multiple Suggestions
- **Alt+]**: Next suggestion
- **Alt+[**: Previous suggestion
- Cycle through alternatives

### Triggering Suggestions
- **Ctrl+Space**: Force suggestion
- Useful when suggestion doesn't appear automatically

## Context Awareness

### What Influences Completions
```
1. Current file content
2. Open tabs
3. Import statements
4. Recent edits
5. Project structure
6. .cursorrules file
7. Comments and docstrings
```

### Writing Better Triggering Code
```python
# Good - descriptive comment triggers better completion
# Calculate total price including tax and discounts
def calculate_final_price(items, tax_rate, discount):
    │ ← AI understands intent from comment

# Good - type hints guide completion
def process_users(users: list[User]) -> dict[str, int]:
    │ ← AI knows input/output types
```

## Completion Settings

### Adjusting Completion Behavior
```json
// settings.json
{
  // Delay before showing suggestions (ms)
  "cursor.completion.delay": 100,

  // Enable/disable completions
  "cursor.completion.enabled": true,

  // Completion length preference
  "cursor.completion.preferLonger": true,

  // Inline suggestions
  "editor.inlineSuggest.enabled": true
}
```

### Model for Completions
```
Settings > Cursor > Completion Model

Options:
- GPT-4 (higher quality, slower)
- GPT-3.5-turbo (faster, lighter)
- Cursor-small (optimized for speed)
```

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

## Troubleshooting Completions

### Completions Not Appearing
```
1. Check if enabled: Settings > Cursor > Completion
2. Check rate limits: Status bar shows remaining
3. Check network: AI needs connectivity
4. Restart Cursor if stuck
```

### Poor Quality Suggestions
```
1. Add more context (comments, types)
2. Check .cursorrules configuration
3. Try different completion model
4. Let codebase indexing complete
```

### Completions Too Aggressive
```json
// Reduce completion frequency
{
  "cursor.completion.delay": 500,
  "editor.quickSuggestions": {
    "other": false,
    "comments": false,
    "strings": false
  }
}
```

## Best Practices

### Guide the AI
```python
# Be explicit about what you want
# TODO: implement binary search on sorted array
def binary_search(arr, target):
    │ ← Better completion with clear intent
```

### Use Type Hints
```python
def process(data: pd.DataFrame) -> pd.DataFrame:
    │ ← AI knows pandas methods to suggest
```

### Maintain Code Style
```javascript
// If your codebase uses certain patterns,
// AI learns and continues them
const Component = ({ props }) => {
  │ ← Matches your existing component patterns
};
```

### Review Before Accepting
```
Always review ghost text:
- Check logic correctness
- Verify variable names
- Ensure style consistency
- Watch for security issues
```
