# Available Models

## Available Models

### Built-in Models (Cursor Subscription)

| Model | Speed | Quality | Context | Best For |
|-------|-------|---------|---------|----------|
| GPT-4 Turbo | Medium | High | 128K | Complex tasks, large context |
| GPT-4 | Slow | Highest | 8K | Precision tasks |
| GPT-3.5 Turbo | Fast | Good | 16K | Quick completions |
| Claude 3.5 Sonnet | Medium | High | 100K | Explanations, docs |
| Claude 3 Opus | Slow | Highest | 100K | Complex reasoning |
| Cursor-small | Fastest | Basic | 4K | Simple completions |

### Using Your Own API Keys

```json
// Settings > Models > API Keys
{
  "openai": {
    "apiKey": "sk-...",
    "organization": "org-..." // optional
  },
  "anthropic": {
    "apiKey": "sk-ant-..."
  },
  "azure": {
    "apiKey": "...",
    "endpoint": "https://your-resource.openai.azure.com",
    "deployment": "gpt-4"
  },
  "google": {
    "apiKey": "...",
    "model": "gemini-pro"
  }
}
```
