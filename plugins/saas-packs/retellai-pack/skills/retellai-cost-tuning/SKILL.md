---
name: retellai-cost-tuning
description: |
  Retell AI cost tuning — AI voice agent and phone call automation.
  Use when working with Retell AI for voice agents, phone calls, or telephony.
  Trigger with phrases like "retell cost tuning", "retellai-cost-tuning", "voice agent".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, ai-agents]
compatible-with: claude-code, codex, openclaw
---

# Retell AI Cost Tuning

## Overview
Implementation patterns for Retell AI cost tuning — voice agent and telephony platform.

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
- Retell AI integration for cost tuning

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps
See related Retell AI skills for more workflows.
