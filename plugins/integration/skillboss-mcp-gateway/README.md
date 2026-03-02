# SkillBoss MCP Gateway

Universal AI API gateway - Access 100+ AI models and services through a single OpenAI-compatible endpoint with native MCP support.

## Overview

SkillBoss provides a unified gateway to access multiple AI providers:

- **50+ LLMs**: Claude, GPT, Gemini, Llama, DeepSeek, Mistral
- **Image Generation**: DALL-E 3, Flux, Stable Diffusion
- **Video Generation**: Veo 2, Runway, Kling
- **Business Services**: Email, payments, web scraping

## Installation

### MCP Server (Recommended)

```bash
claude mcp add skillboss -- npx -y @skillboss/mcp-server
```

### Manual Configuration

Add to your Claude Code settings:

```json
{
  "mcpServers": {
    "skillboss": {
      "command": "npx",
      "args": ["-y", "@skillboss/mcp-server"],
      "env": {
        "SKILLBOSS_API_KEY": "sk-your-key"
      }
    }
  }
}
```

## Usage

### Direct API (OpenAI Compatible)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.heybossai.com/v1",
    api_key="sk-your-skillboss-key"
)

response = client.chat.completions.create(
    model="bedrock/claude-4-5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### MCP Tools

Once installed, your agent can use:

```typescript
// List models
mcp.tools.skillboss.models.list()

// Chat
mcp.tools.skillboss.chat({
  model: "gpt-5",
  messages: [...]
})

// Generate images
mcp.tools.skillboss.images.generate({
  model: "dall-e-3",
  prompt: "A beautiful sunset"
})
```

## Features

| Feature | Description |
|---------|-------------|
| OpenAI Compatible | Drop-in replacement |
| 50+ Models | All major providers |
| Unified Billing | One credit system |
| MCP Native | First-class support |
| Cost Tracking | Per-request visibility |

## Pricing

- Pay-as-you-go
- No monthly minimum
- Free tier available

## Links

- [Website](https://skillboss.co)
- [Documentation](https://skillboss.co/docs)
- [NPM Package](https://www.npmjs.com/package/@skillboss/mcp-server)
- [Get API Key](https://skillboss.co/dashboard)
