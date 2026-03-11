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

## Python with OpenAI SDK

Initialize the OpenAI SDK client with OpenRouter base URL and configure retry logic for production use.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [Openrouter Sdk Patterns implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Openrouter Sdk Patterns |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply openrouter sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize openrouter sdk patterns for production environments with multiple constraints and team-specific requirements.

## Resources

- Official Openrouter Sdk Patterns documentation
- Community best practices and patterns
- Related skills in this plugin pack
