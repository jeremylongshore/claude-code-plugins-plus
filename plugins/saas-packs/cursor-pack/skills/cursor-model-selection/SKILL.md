---
name: cursor-model-selection
description: |
  Configure and select AI models in Cursor. Triggers on "cursor model",
  "cursor gpt", "cursor claude", "change cursor model", "cursor ai model".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Model Selection & Configuration

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

## Model Selection by Task

### Completions (Tab)

```
Recommended: GPT-3.5 Turbo or Cursor-small
- Fast response time critical
- Context window usually sufficient
- Cost effective for high volume

Settings:
{
  "cursor.completion.model": "gpt-3.5-turbo"
}
```

### Chat

```
Task-based selection:

Quick questions → GPT-3.5 Turbo
Code review → GPT-4 Turbo
Explanations → Claude 3.5 Sonnet
Complex architecture → GPT-4 or Claude Opus
Debugging → GPT-4 Turbo (large context)
```

### Composer

```
Recommended: GPT-4 Turbo or Claude 3.5 Sonnet
- Multi-file edits need accuracy
- Large context for project understanding
- Quality over speed

Settings:
{
  "cursor.composer.model": "gpt-4-turbo"
}
```

## Switching Models

### In Chat
```
Method 1: Model dropdown in chat header
Method 2: Type model name in chat:
  "Using GPT-4: explain this code"
Method 3: Settings > Default Chat Model
```

### Per-Conversation
```
Start chat with model preference:
"[Claude] Explain this authentication flow"
"[GPT-4] Review this for security issues"
```

### Global Defaults

```json
// settings.json
{
  "cursor.chat.defaultModel": "gpt-4-turbo",
  "cursor.completion.model": "gpt-3.5-turbo",
  "cursor.composer.model": "gpt-4-turbo"
}
```

## Model Comparison

### GPT-4 vs Claude 3.5 Sonnet

```
GPT-4 Turbo:
✓ Better at code generation
✓ Stronger at following complex instructions
✓ More consistent output format
✗ Can be verbose

Claude 3.5 Sonnet:
✓ Better explanations
✓ More natural conversation
✓ Excellent at documentation
✗ Sometimes over-cautious
```

### Speed vs Quality Tradeoffs

```
Speed Priority (GPT-3.5 Turbo):
- Autocomplete while typing
- Quick lookups
- Simple refactors
- ~100-500ms response

Quality Priority (GPT-4):
- Architecture decisions
- Security reviews
- Complex debugging
- ~2-10s response
```

## Cost Optimization

### Cursor Subscription
```
Free: 2000 completions, 50 slow requests/month
Pro ($20/mo): Unlimited completions, 500 fast requests
Business ($40/user): Everything + admin features

Fast vs Slow:
- Fast: GPT-4 Turbo, Claude Opus
- Slow: Queue-based, may take 30s+
```

### Using Own API Keys

```
Cost comparison (approx per 1M tokens):
GPT-4 Turbo: $10 input, $30 output
GPT-3.5 Turbo: $0.50 input, $1.50 output
Claude Sonnet: $3 input, $15 output
Claude Opus: $15 input, $75 output

Strategy:
- Use GPT-3.5 for completions (high volume)
- Use GPT-4 for chat (lower volume, higher stakes)
```

## Model-Specific Settings

### OpenAI Models

```json
{
  "cursor.openai.temperature": 0.7,
  "cursor.openai.maxTokens": 4096,
  "cursor.openai.topP": 1.0,
  "cursor.openai.frequencyPenalty": 0,
  "cursor.openai.presencePenalty": 0
}
```

### Anthropic Models

```json
{
  "cursor.anthropic.temperature": 0.7,
  "cursor.anthropic.maxTokens": 4096
}
```

## Advanced Configuration

### Custom Endpoints

```json
// For self-hosted or proxy setups
{
  "cursor.api.baseUrl": "https://your-proxy.com/v1",
  "cursor.api.headers": {
    "X-Custom-Header": "value"
  }
}
```

### Model Fallbacks

```json
// If primary fails, use fallback
{
  "cursor.model.fallback": {
    "gpt-4": "gpt-3.5-turbo",
    "claude-3-opus": "claude-3-sonnet"
  }
}
```

## Troubleshooting Models

### "Model Not Available"
```
1. Check subscription tier
2. Verify API key if using own
3. Check model name spelling
4. Some models require waitlist
```

### "Rate Limited"
```
1. Switch to different model
2. Wait for limit reset
3. Use own API key
4. Upgrade plan
```

### "Context Too Long"
```
1. Use larger context model (GPT-4 Turbo)
2. Reduce selected code
3. Start new conversation
4. Be more concise in prompts
```
