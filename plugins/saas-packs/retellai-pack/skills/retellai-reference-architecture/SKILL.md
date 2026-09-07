---
name: retellai-reference-architecture
description: "Retell AI reference architecture \u2014 AI voice agent and phone call\
  \ automation.\nUse when working with Retell AI for voice agents, phone calls, or\
  \ telephony.\nTrigger with phrases like \"retell reference architecture\", \"retellai-reference-architecture\"\
  , \"voice agent\".\n"
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
# Retell AI Reference Architecture

## Overview

Implementation patterns for Retell AI reference architecture — voice agent and telephony platform.

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

- Retell AI integration for reference architecture

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Separate the call path from slow business-system enrichment

Route the voice agent through a stable API boundary that validates inputs and
returns a bounded response, while sending slow CRM or analytics enrichment to
an asynchronous worker. The agent receives a clear timeout and human-transfer
fallback if the business system is unavailable. Exercise this topology with a
synthetic outage before launch, then document which component owns retries,
audit events, and the rollback to the prior routing configuration.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
