---
name: guidewire-hello-world
description: |
  Execute first API calls to Guidewire PolicyCenter, ClaimCenter, and BillingCenter.
  Use when testing initial connectivity, exploring API structure,
  or making your first insurance data requests.
  Trigger with phrases like "guidewire hello world", "first guidewire call",
  "test policycenter api", "guidewire api example".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Hello World

## Overview
Execute your first API calls to Guidewire InsuranceSuite Cloud APIs - PolicyCenter, ClaimCenter, and BillingCenter.

## Prerequisites
- Completed `guidewire-install-auth` setup
- Valid OAuth2 access token
- API role permissions for target endpoints

## Instructions

### Step 1: Instructions
TOKEN=$(curl -s -X POST "${GW_HUB_URL}/oauth/token" \
### Step 2: Gosu Hello World (Server-Side)
// Gosu script to query PolicyCenter data
### Step 3: API Response Structure
All Guidewire Cloud APIs follow this structure:
### Step 4: Common Resource Patterns
// Get single resource

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Instructions
- Gosu Hello World (Server-Side)
- API Response Structure
- Common Resource Patterns

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `404 Not Found` | Invalid endpoint or resource ID | Verify endpoint path and ID format |
| `400 Bad Request` | Invalid request payload | Check required fields and data types |
| `422 Unprocessable` | Business rule violation | Review validation errors in response |
| `409 Conflict` | Concurrent modification | Retry with updated checksum |
| `415 Unsupported Media` | Wrong content type | Use `application/json` |

## Resources
- [PolicyCenter Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [ClaimCenter Cloud API Reference](https://docs.guidewire.com/cloud/cc/202503/apiref/)
- [BillingCenter Cloud API Reference](https://docs.guidewire.com/cloud/bc/202503/apiref/)
- [Cloud API Developer Guide](https://docs.guidewire.com/cloud/pc/202503/cloudapica/)

## Next Steps
For local development workflow, see `guidewire-local-dev-loop`.

## Examples

**Basic usage**: Apply guidewire hello world to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire hello world for production environments with multiple constraints and team-specific requirements.