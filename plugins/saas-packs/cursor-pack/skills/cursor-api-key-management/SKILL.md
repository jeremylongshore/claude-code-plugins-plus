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

Manage API keys and authentication for Cursor IDE, including configuring OpenAI, Anthropic, and custom model provider keys.

## Prerequisites

- Access to the authentication environment or API
- Required CLI tools installed and authenticated
- Familiarity with authentication concepts and terminology

## Instructions

1. Assess the current state of the authentication configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [authentication implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with authentication |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply cursor api key management to a standard project setup with default configuration options.

**Advanced scenario**: Customize cursor api key management for production environments with multiple constraints and team-specific requirements.

## Resources

- Official authentication documentation
- Community best practices and patterns
- Related skills in this plugin pack
