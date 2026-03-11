---
name: apollo-debug-bundle
description: |
  Collect Apollo.io debug evidence for support.
  Use when preparing support tickets, documenting issues,
  or gathering diagnostic information for Apollo problems.
  Trigger with phrases like "apollo debug", "apollo support bundle",
  "collect apollo diagnostics", "apollo troubleshooting info".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Debug Bundle

## Overview
Collect comprehensive debug information for Apollo.io API issues to expedite support resolution.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-debug-bundle:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-debug-bundle/references/implementation-guide.md)`

## Output
- Comprehensive debug JSON bundle
- Environment verification results
- API connectivity status
- Recent request/response samples
- Ready-to-submit support ticket

## Error Handling
| Issue | Debug Step |
|-------|------------|
| Connection timeout | Check network/firewall |
| 401 errors | Verify API key |
| 429 errors | Check rate limit status |
| 500 errors | Check Apollo status page |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support Portal](https://support.apollo.io)
- [Apollo API Documentation](https://apolloio.github.io/apollo-api-docs/)

## Next Steps
Proceed to `apollo-rate-limits` for rate limiting implementation.

## Examples

**Basic usage**: Apply apollo debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo debug bundle for production environments with multiple constraints and team-specific requirements.