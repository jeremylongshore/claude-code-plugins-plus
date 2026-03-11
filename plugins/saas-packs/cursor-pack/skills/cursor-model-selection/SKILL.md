---
name: "cursor-model-selection"
description: |
  Configure and select AI models in Cursor. Triggers on "cursor model",
  "cursor gpt", "cursor claude", "change cursor model", "cursor ai model". Use when working with cursor model selection functionality. Trigger with phrases like "cursor model selection", "cursor selection", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Model Selection

## Overview

This skill helps you configure and select AI models in Cursor. It covers available models, task-based model selection, cost optimization strategies, and advanced configuration options to get the best results from different AI providers.

## Prerequisites

- Cursor IDE with subscription or API keys
- Understanding of model capabilities
- Knowledge of task requirements
- API account (if using own keys)

## Instructions

1. Understand model strengths and context limits
2. Choose model based on task type (speed vs quality)
3. Configure default models in settings
4. Use per-conversation model selection
5. Set up API keys for additional models
6. Monitor usage and costs

## Output

- Optimal model selection per task
- Configured default models
- Cost-effective model usage
- Fallback model configuration

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Model Documentation](https://cursor.com/docs/models)
- [OpenAI Model Guide](https://platform.openai.com/docs/models)
- [Anthropic Claude Models](https://docs.anthropic.com/claude/docs/models-overview)