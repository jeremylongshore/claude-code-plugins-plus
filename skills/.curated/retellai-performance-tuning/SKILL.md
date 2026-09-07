---
name: retellai-performance-tuning
description: "Retell AI performance tuning \u2014 AI voice agent and phone call automation.\n\
  Use when working with Retell AI for voice agents, phone calls, or telephony.\nTrigger\
  \ with phrases like \"retell performance tuning\", \"retellai-performance-tuning\"\
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
# Retell AI Performance Tuning

## Overview

Implementation patterns for Retell AI performance tuning — voice agent and telephony platform.

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

- Retell AI integration for performance tuning

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Improve response latency with a measured canary

Capture baseline end-to-end latency, model latency, transfer outcome, and
completion rate for a synthetic test suite before changing an agent setting.
Apply one prompt, model, or integration change to a preview version and repeat
the same suite. Promote to a small canary only if latency improves without a
drop in completion or an increase in handoffs; otherwise restore the prior
version and retain the comparison as the performance decision record.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
