---
name: apollo-common-errors
description: |
  Diagnose and fix common Apollo.io API errors.
  Use when encountering Apollo API errors, debugging integration issues,
  or troubleshooting failed requests.
  Trigger with phrases like "apollo error", "apollo api error",
  "debug apollo", "apollo 401", "apollo 429", "apollo troubleshoot".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Common Errors

## Overview
Comprehensive guide to diagnosing and fixing common Apollo.io API errors with specific solutions and prevention strategies.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-common-errors:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-common-errors/references/implementation-guide.md)`

## Output


- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [debugging implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check Apollo status page |

## Resources
- [Apollo API Error Codes](https://apolloio.github.io/apollo-api-docs/#errors)
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)

## Next Steps
Proceed to `apollo-debug-bundle` for collecting debug evidence.

## Examples

**Basic usage**: Apply apollo common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo common errors for production environments with multiple constraints and team-specific requirements.