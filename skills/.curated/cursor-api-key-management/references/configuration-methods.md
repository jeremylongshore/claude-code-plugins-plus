# Configuration Methods

## Configuration Methods

### Via Settings UI

```
1. Open Settings (Cmd+,)
2. Search for "Cursor API"
3. Enter your API key
4. Save and restart if prompted
```

### Via settings.json

```json
// ~/.config/Cursor/User/settings.json

{
  "cursor.apiKeys": {
    "openai": "sk-...",
    "anthropic": "sk-ant-...",
    "azure": {
      "apiKey": "...",
      "endpoint": "https://...",
      "deployment": "..."
    }
  }
}
```

### Via Environment Variables

```bash
# Shell profile (~/.zshrc or ~/.bashrc)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Then in settings.json:
{
  "cursor.openai.apiKey": "${OPENAI_API_KEY}",
  "cursor.anthropic.apiKey": "${ANTHROPIC_API_KEY}"
}
```
