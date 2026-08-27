---
name: retellai-local-dev-loop
description: "Retell AI local dev loop \u2014 AI voice agent and phone call automation.\n\
  Use when working with Retell AI for voice agents, phone calls, or telephony.\nTrigger\
  \ with phrases like \"retell local dev loop\", \"retellai-local-dev-loop\", \"voice\
  \ agent\".\n"
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
# Retell AI Local Dev Loop

## Overview

Implementation patterns for Retell AI local dev loop — voice agent and telephony platform.

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

- Retell AI integration for local dev loop

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Iterate on a prompt with a deterministic local test set

Keep a small suite of synthetic caller intents, including a successful request,
an unclear request, and a required human handoff. Run that suite against a
development agent after each prompt or tool-schema change and compare only
redacted outcomes such as route, tool arguments, and completion state. Do not
point local development at a production phone number; publish a versioned
preview only after the suite continues to meet its expected behavior.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
