---
name: retellai-migration-deep-dive
description: "Retell AI migration deep dive \u2014 AI voice agent and phone call automation.\n\
  Use when working with Retell AI for voice agents, phone calls, or telephony.\nTrigger\
  \ with phrases like \"retell migration deep dive\", \"retellai-migration-deep-dive\"\
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
# Retell AI Migration Deep Dive

## Overview

Implementation patterns for Retell AI migration deep dive — voice agent and telephony platform.

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

- Retell AI integration for migration deep dive

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RETELL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check API documentation |

## Examples

### Migrate one agent while preserving a rollback path

Export the current agent configuration and record its version, routing rule,
and supported handoff behavior before making schema or prompt changes. Import
the candidate into a preview environment, replay synthetic scenarios, and
compare the redacted outcomes with the old version. Move a small canary route
only after those checks pass; leave the previous configuration intact until
the canary completion and escalation rates remain within the agreed bounds.

## Resources

- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps

See related Retell AI skills for more workflows.
