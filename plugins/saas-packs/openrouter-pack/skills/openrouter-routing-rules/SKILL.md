---
name: openrouter-routing-rules
description: |
  Implement intelligent model routing based on request characteristics. Use when optimizing for cost, speed, or quality per request. Trigger with phrases like 'openrouter routing', 'model selection', 'smart routing', 'dynamic model'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenRouter Routing Rules

## Overview

This skill covers implementing request-based routing logic to select optimal models based on content, urgency, or cost constraints.

## Prerequisites

- OpenRouter integration
- Understanding of model capabilities and pricing

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Basic Routing Strategies

Use content-based, cost-based, or latency-based routing to direct requests to the optimal model.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [optimization implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with optimization |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply openrouter routing rules to a standard project setup with default configuration options.

**Advanced scenario**: Customize openrouter routing rules for production environments with multiple constraints and team-specific requirements.

## Resources

- Official optimization documentation
- Community best practices and patterns
- Related skills in this plugin pack
