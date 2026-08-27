---
name: retellai-policy-guardrails
description: "Retell AI policy guardrails \u2014 AI voice agent and phone call automation.\n\
  Use when working with Retell AI for voice agents, phone calls, or telephony.\nTrigger\
  \ with phrases like \"retell policy guardrails\", \"retellai-policy-guardrails\"\
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
# Retell AI Policy Guardrails

## Overview

Implementation patterns for Retell AI policy guardrails — voice agent and telephony platform.

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

- Retell AI integration for policy guardrails

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Restrict a booking agent to an approved action boundary

Give an appointment agent only the lookup and create-booking tools needed for
its flow, with explicit argument validation and a human handoff for refunds,
medical questions, or account changes. Test synthetic prompts that attempt
each forbidden action and verify that the agent refuses or transfers rather
than improvising. Version the policy with the agent and review deviations from
the guardrail before widening any permission.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
