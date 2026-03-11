---
name: openrouter-install-auth
description: |
  Execute set up OpenRouter API authentication and configure API keys. Use when starting a new OpenRouter integration or troubleshooting auth issues. Trigger with phrases like 'openrouter setup', 'openrouter api key', 'openrouter authentication', 'configure openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Openrouter Install Auth

## Overview

This skill guides you through obtaining and configuring OpenRouter API credentials, setting up environment variables, and verifying your authentication is working correctly.

## Prerequisites

- OpenRouter account (free at openrouter.ai)
- Python 3.8+ or Node.js 18+
- OpenAI SDK installed (`pip install openai` or `npm install openai`)

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)