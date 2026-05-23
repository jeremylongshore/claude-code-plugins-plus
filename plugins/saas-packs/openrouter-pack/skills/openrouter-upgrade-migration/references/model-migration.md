# Model Migration

## Model Migration

### Updating Model References

```python
# Old model name mapping
MODEL_MIGRATIONS = {
    "openai/gpt-4": "openai/gpt-4-turbo",
    "anthropic/claude-2": "anthropic/claude-3-haiku",
    "anthropic/claude-instant-1": "anthropic/claude-3-haiku",
}

def migrate_model_name(model: str) -> str:
    """Migrate deprecated model to current equivalent."""
    return MODEL_MIGRATIONS.get(model, model)

# Usage
old_model = "anthropic/claude-2"
new_model = migrate_model_name(old_model)
```

### Batch Model Update

```python
import re

def update_model_references(file_path: str):
    """Update model references in source file."""
    with open(file_path, 'r') as f:
        content = f.read()

    for old_model, new_model in MODEL_MIGRATIONS.items():
        # Match model in strings
        pattern = rf'["\']({re.escape(old_model)})["\']'
        content = re.sub(pattern, f'"{new_model}"', content)

    with open(file_path, 'w') as f:
        f.write(content)

# Apply to all Python files
import glob
for file in glob.glob("**/*.py", recursive=True):
    update_model_references(file)
```
