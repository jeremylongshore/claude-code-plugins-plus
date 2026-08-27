---
name: retellai-security-basics
description: "Retell AI security basics \u2014 AI voice agent and phone call automation.\n\
  Use when working with Retell AI for voice agents, phone calls, or telephony.\nTrigger\
  \ with phrases like \"retell security basics\", \"retellai-security-basics\", \"\
  voice agent\".\n"
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.9.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- retellai
- voice
- telephony
- ai-agents
compatibility: Designed for Claude Code
---
# Retell AI Security Basics

## Overview

Implementation patterns for Retell AI security basics — voice agent and telephony platform.

## Prerequisites

- Completed `retellai-install-auth` setup

## Instructions

### Step 1: SDK Pattern

```typescript
import Retell from 'retell-sdk';
const retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });

const agents = await retell.agent.list();
console.log(`Agents: ${agents.length}`);
```

## Output

- Retell AI integration for security basics

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Rotate an exposed development credential safely

Disable the exposed development key in the provider console, create a scoped
replacement, and update only the development secret reference. Verify the new
key with a harmless agent-list request while ensuring command output does not
print its value. Review access logs and affected preview configurations, then
document the incident with the credential identifier and rotation time rather
than copying key material into the ticket or source repository.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
