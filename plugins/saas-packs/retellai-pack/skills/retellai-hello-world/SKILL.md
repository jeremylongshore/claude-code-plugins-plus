---
name: retellai-hello-world
description: |
  Retell AI hello world — AI voice agent and phone call automation.
  Use when working with Retell AI for voice agents, phone calls, or telephony.
  Trigger with phrases like "retell hello world", "retellai-hello-world", "voice agent".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, ai-agents]
compatible-with: claude-code, codex, openclaw
---

# Retell AI Hello World

## Overview
Create your first Retell AI voice agent and make a test phone call.

## Prerequisites
- Completed `retellai-install-auth`
- A phone number registered in Retell AI Dashboard (or use web call for testing)

## Instructions

### Step 1: Create an LLM Configuration
```typescript
import Retell from 'retell-sdk';
const retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });

// Create LLM configuration (what the agent says)
const llm = await retell.llm.create({
  model: 'gpt-4o',
  general_prompt: `You are a friendly receptionist for Acme Corp.
    - Greet callers warmly
    - Ask how you can help
    - Take messages if needed
    - Be concise and professional`,
});
console.log(`LLM created: ${llm.llm_id}`);
```

### Step 2: Create a Voice Agent
```typescript
const agent = await retell.agent.create({
  response_engine: {
    type: 'retell-llm',
    llm_id: llm.llm_id,
  },
  voice_id: '11labs-Adrian',  // Choose from available voices
  agent_name: 'Acme Receptionist',
});
console.log(`Agent created: ${agent.agent_id}`);
```

### Step 3: Make a Test Phone Call
```typescript
// Outbound call (requires a registered phone number)
const call = await retell.call.createPhoneCall({
  from_number: '+14155551234',  // Your Retell number
  to_number: '+14155555678',    // Destination
  override_agent_id: agent.agent_id,
});
console.log(`Call initiated: ${call.call_id}`);
```

### Step 4: Or Test with Web Call
```typescript
// Web call (no phone number needed — great for testing)
const webCall = await retell.call.createWebCall({
  agent_id: agent.agent_id,
});
console.log(`Web call URL: ${webCall.call_id}`);
// Use retell-client-js-sdk to connect from browser
```

### Step 5: Check Call Status
```typescript
const callDetail = await retell.call.retrieve(call.call_id);
console.log(`Status: ${callDetail.call_status}`);
console.log(`Duration: ${callDetail.end_timestamp - callDetail.start_timestamp}ms`);
if (callDetail.transcript) {
  console.log(`Transcript: ${callDetail.transcript}`);
}
```

## Output
- LLM configuration with custom prompt
- Voice agent with selected voice
- Test call initiated (phone or web)
- Call status and transcript retrieved

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Invalid voice_id` | Unknown voice | List available voices in Dashboard |
| `400 No phone number` | Number not registered | Register number in Dashboard first |
| Call not connecting | Destination unreachable | Try web call for testing |

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [Create Phone Call](https://docs.retellai.com/api-references/create-phone-call)

## Next Steps
Configure agent behavior: `retellai-core-workflow-a`
