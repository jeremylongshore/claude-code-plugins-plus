---
name: maintainx-common-errors
description: |
  Debug and resolve common MaintainX API errors.
  Use when encountering API errors, authentication issues,
  or unexpected responses from the MaintainX API.
  Trigger with phrases like "maintainx error", "maintainx 401",
  "maintainx api problem", "maintainx not working", "debug maintainx".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Common Errors

## Overview
Quick reference guide for diagnosing and resolving common MaintainX API errors.

## Prerequisites
- MaintainX API credentials configured
- Basic understanding of HTTP status codes
- Access to API logs

## Instructions
Follow these high-level steps to implement maintainx-common-errors:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-common-errors/references/implementation-guide.md)`

## Output
- Identified error cause
- Applied appropriate fix
- Verified resolution

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Status](https://status.getmaintainx.com)
- [MaintainX Help Center](https://help.getmaintainx.com)
- [API Documentation](https://maintainx.dev/)

## Next Steps
For comprehensive debugging, see `maintainx-debug-bundle`.

## Examples

**Basic usage**: Apply maintainx common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx common errors for production environments with multiple constraints and team-specific requirements.