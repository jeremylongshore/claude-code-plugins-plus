---
name: "cursor-api-key-management"
description: |
  Manage API keys and authentication in Cursor. Triggers on "cursor api key",
  "cursor openai key", "cursor anthropic key", "own api key cursor". Use when working with APIs or building integrations. Trigger with phrases like "cursor api key management", "cursor management", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Api Key Management

## Overview

### Why Use Your Own API Keys?
```
Benefits:
- Bypass Cursor rate limits
- Access specific models
- Control costs directly
- Use enterprise agreements
- Comply with data policies

## Prerequisites

- Cursor IDE Pro or Business subscription (or own API keys)
- API account with OpenAI, Anthropic, Azure, or Google
- API key with appropriate permissions and credits
- Secure storage solution for credentials

## Instructions

1. Generate API key from your chosen provider
2. Open Cursor Settings (Cmd+,)
3. Search for "Cursor API"
4. Enter your API key in the appropriate field
5. Set file permissions to restrict access
6. Configure billing alerts on provider dashboard
7. Test API key by making a request in Cursor

## Output

- Custom API key configured in Cursor
- Bypass of Cursor rate limits
- Direct billing relationship with provider
- Access to specific models via your key

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Anthropic Console](https://console.anthropic.com/)
- [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- [Cursor Security Documentation](https://cursor.com/security)
