# Debugging Completions

## Debugging Completions

### Completion Quality Checklist

```
[ ] Does the comment/docstring clearly describe intent?
[ ] Are type hints present and accurate?
[ ] Is the surrounding code consistent?
[ ] Is .cursorrules up to date?
[ ] Is the right model selected?
[ ] Has codebase been indexed recently?
```

### Improving Completion Quality

#### Add Context

```python
# Before (AI guesses):
def process(data):
    │

# After (AI understands):
def process(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform user data.
    - Remove null values
    - Normalize column names
    - Convert dates to ISO format
    """
    │
```

#### Use Explicit Comments

```javascript
// Before:
function handle(req) {
  │
}

// After:
// Handle POST /api/users - validate input, create user, return 201
function handleCreateUser(req: Request): Response {
  │
}
```
