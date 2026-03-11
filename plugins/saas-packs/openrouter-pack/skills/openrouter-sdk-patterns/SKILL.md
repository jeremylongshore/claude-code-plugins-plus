---
name: openrouter-sdk-patterns
description: |
  Implement common SDK patterns for OpenRouter integration. Use when building production applications. Trigger with phrases like 'openrouter sdk', 'openrouter client pattern', 'openrouter best practices', 'openrouter code patterns'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenRouter SDK Patterns

## Overview

This skill covers proven SDK patterns including client initialization, error handling, retry logic, and configuration management for robust OpenRouter integrations.

## Prerequisites

- OpenRouter API key configured
- Python 3.8+ or Node.js 18+
- OpenAI SDK installed

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill covers proven SDK patterns including client initialization, error handling, retry logic, and configuration management for robust OpenRouter integrations.

## Prerequisites

- OpenRouter API key configured
- Python 3.8+ or Node.js 18+
- OpenAI SDK installed

## Python with OpenAI SDK

### Basic Setup
```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",

## Detailed Reference

See `${CLAUDE_SKILL_DIR}/references/implementation.md` for complete implementation guide.
