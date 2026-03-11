---
name: openrouter-model-routing
description: |
  Implement advanced model routing with A/B testing. Use when optimizing model selection or running experiments. Trigger with phrases like 'openrouter a/b test', 'model experiment', 'openrouter routing', 'model comparison'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenRouter Model Routing

## Overview

This skill covers advanced routing patterns including A/B testing, gradual rollouts, and performance-based model selection.

## Prerequisites

- OpenRouter integration
- Metrics collection capability

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Intelligent Model Selection

Use multi-criteria routing to select models based on cost, latency, and quality requirements per request.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [testing implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with testing |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply openrouter model routing to a standard project setup with default configuration options.

**Advanced scenario**: Customize openrouter model routing for production environments with multiple constraints and team-specific requirements.

## Resources

- Official testing documentation
- Community best practices and patterns
- Related skills in this plugin pack
