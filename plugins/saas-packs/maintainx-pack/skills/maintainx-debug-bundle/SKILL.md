---
name: maintainx-debug-bundle
description: |
  Comprehensive debugging toolkit for MaintainX integrations.
  Use when experiencing complex issues, need detailed logging,
  or troubleshooting integration problems with MaintainX.
  Trigger with phrases like "debug maintainx", "maintainx troubleshoot",
  "maintainx detailed logs", "diagnose maintainx", "maintainx issue".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Debug Bundle

## Overview
Complete debugging toolkit for diagnosing and resolving MaintainX integration issues with detailed logging, diagnostic scripts, and troubleshooting procedures.

## Prerequisites
- MaintainX API access configured
- Node.js environment
- curl for direct API testing

## Instructions
Follow these high-level steps to implement maintainx-debug-bundle:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-debug-bundle/references/implementation-guide.md)`

## Output
- Environment diagnostic report
- Request/response logs with timing
- API health check results
- Data validation issues
- Support bundle for troubleshooting

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX Help Center](https://help.getmaintainx.com/)
- [MaintainX API Status](https://status.getmaintainx.com)
- [MaintainX Community](https://community.getmaintainx.com/)

## Next Steps
For rate limit handling, see `maintainx-rate-limits`.
