# Supported Providers

## Supported Providers

### OpenAI

```json
// Settings > Cursor > API Keys

{
  "cursor.openai.apiKey": "sk-...",
  "cursor.openai.organization": "org-..." // optional
}

Available models with your key:
- gpt-4-turbo
- gpt-4
- gpt-4-32k
- gpt-3.5-turbo
- gpt-3.5-turbo-16k
```

### Anthropic

```json
{
  "cursor.anthropic.apiKey": "sk-ant-..."
}

Available models:
- claude-3-opus
- claude-3-sonnet
- claude-3-haiku
- claude-2.1
```

### Azure OpenAI

```json
{
  "cursor.azure.apiKey": "...",
  "cursor.azure.endpoint": "https://YOUR-RESOURCE.openai.azure.com",
  "cursor.azure.deployment": "gpt-4"
}

Benefits:
- Enterprise security
- Regional data residency
- Private network support
- Azure AD authentication
```

### Google AI (Gemini)

```json
{
  "cursor.google.apiKey": "...",
  "cursor.google.model": "gemini-pro"
}
```
