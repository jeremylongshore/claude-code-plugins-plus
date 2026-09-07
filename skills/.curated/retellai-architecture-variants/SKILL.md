---
name: retellai-architecture-variants
description: "Retell AI architecture variants \u2014 AI voice agent and phone call\
  \ automation.\nUse when working with Retell AI for voice agents, phone calls, or\
  \ telephony.\nTrigger with phrases like \"retell architecture variants\", \"retellai-architecture-variants\"\
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
# Retell AI Architecture Variants

## Overview

Implementation patterns for Retell AI architecture variants — voice agent and telephony platform.

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

- Retell AI integration for architecture variants

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Choose a queue-backed architecture for bursty inbound calls

For a campaign that creates short spikes, keep the public number attached to a
stable routing layer and place CRM enrichment behind an asynchronous queue.
Start with a preview agent that records only synthetic test calls, set a clear
timeout for the enrichment request, and configure a human-transfer fallback.
Measure latency and transfer rate during the canary before selecting the
variant for production traffic.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
