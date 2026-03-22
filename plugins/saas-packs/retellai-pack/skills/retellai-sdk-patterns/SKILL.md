---
name: retellai-sdk-patterns
description: |
  Production-ready Retell AI SDK patterns for voice agent applications.
  Use when building production voice agents, implementing retry logic, or establishing patterns.
  Trigger with phrases like "retell patterns", "voice agent patterns", "retell best practices".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, patterns]
compatible-with: claude-code, codex, openclaw
---

# Retell AI SDK Patterns

## Overview
Production-ready patterns for Retell AI: client singletons, typed agent configurations, call management, and error handling.

## Prerequisites
- Completed `retellai-install-auth`
- `retell-sdk` installed

## Instructions

### Step 1: Singleton Client
```typescript
import Retell from 'retell-sdk';

let _retell: Retell | null = null;

export function getRetellClient(): Retell {
  if (!_retell) {
    _retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });
  }
  return _retell;
}
```

### Step 2: Typed Agent Configuration
```typescript
interface AgentConfig {
  name: string;
  voiceId: string;
  prompt: string;
  functions?: FunctionConfig[];
  maxCallDurationMs?: number;
  endCallAfterSilenceMs?: number;
}

async function createAgent(config: AgentConfig) {
  const retell = getRetellClient();

  const llm = await retell.llm.create({
    model: 'gpt-4o',
    general_prompt: config.prompt,
    functions: config.functions,
  });

  const agent = await retell.agent.create({
    response_engine: { type: 'retell-llm', llm_id: llm.llm_id },
    voice_id: config.voiceId,
    agent_name: config.name,
    max_call_duration_ms: config.maxCallDurationMs || 300000,
    end_call_after_silence_ms: config.endCallAfterSilenceMs || 10000,
  });

  return { agentId: agent.agent_id, llmId: llm.llm_id };
}
```

### Step 3: Call Manager with Retry
```typescript
async function makeCallWithRetry(
  fromNumber: string, toNumber: string, agentId: string, maxRetries = 2
) {
  const retell = getRetellClient();
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const call = await retell.call.createPhoneCall({
        from_number: fromNumber,
        to_number: toNumber,
        override_agent_id: agentId,
      });
      return call;
    } catch (err: any) {
      if (attempt === maxRetries || err.status < 500) throw err;
      await new Promise(r => setTimeout(r, 2000 * (attempt + 1)));
    }
  }
}
```

### Step 4: Batch Call Campaign
```typescript
async function runCallCampaign(
  numbers: string[], agentId: string, concurrency = 3, delayMs = 2000
) {
  const results: Array<{ number: string; callId?: string; error?: string }> = [];
  const queue = [...numbers];
  const active = new Set<Promise<void>>();

  while (queue.length > 0 || active.size > 0) {
    while (active.size < concurrency && queue.length > 0) {
      const number = queue.shift()!;
      const p = (async () => {
        try {
          const call = await makeCallWithRetry(process.env.RETELL_PHONE_NUMBER!, number, agentId);
          results.push({ number, callId: call.call_id });
        } catch (err: any) {
          results.push({ number, error: err.message });
        }
        await new Promise(r => setTimeout(r, delayMs));
      })();
      active.add(p);
      p.finally(() => active.delete(p));
    }
    if (active.size > 0) await Promise.race(active);
  }
  return results;
}
```

## Output
- Singleton Retell client
- Typed agent creation with LLM configuration
- Retry logic for call creation
- Concurrent call campaign manager

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | All SDK calls | One client instance |
| Typed config | Agent creation | Type safety, defaults |
| Retry wrapper | Call failures | Automatic recovery |
| Campaign manager | Outbound calls | Rate-limited concurrency |

## Resources
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)
- [Retell AI Documentation](https://docs.retellai.com)

## Next Steps
Apply in `retellai-core-workflow-a` for agent building.
