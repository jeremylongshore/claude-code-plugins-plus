---
name: retellai-core-workflow-a
description: |
  Retell AI core workflow a — AI voice agent and phone call automation.
  Use when working with Retell AI for voice agents, phone calls, or telephony.
  Trigger with phrases like "retell core workflow a", "retellai-core-workflow-a", "voice agent".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, ai-agents]
compatible-with: claude-code, codex, openclaw
---

# Retell AI Core Workflow A

## Overview
Build and configure voice agents with custom prompts, function calling, and call flow logic.

## Prerequisites
- Completed `retellai-hello-world`

## Instructions

### Step 1: Agent with Function Calling
```typescript
const llm = await retell.llm.create({
  model: 'gpt-4o',
  general_prompt: `You are a booking assistant for Dr. Smith's office.
    - Help callers book, reschedule, or cancel appointments
    - Collect: name, phone, preferred date/time
    - Confirm all details before booking`,
  functions: [
    {
      name: 'book_appointment',
      description: 'Book a new appointment',
      parameters: {
        type: 'object',
        properties: {
          patient_name: { type: 'string' },
          phone: { type: 'string' },
          date: { type: 'string', description: 'YYYY-MM-DD format' },
          time: { type: 'string', description: 'HH:MM format' },
        },
        required: ['patient_name', 'phone', 'date', 'time'],
      },
      url: 'https://your-api.com/appointments',
      speak_during_execution: true,
      speak_after_execution: true,
    },
  ],
});
```

### Step 2: Configure Voice and Behavior
```typescript
const agent = await retell.agent.create({
  response_engine: { type: 'retell-llm', llm_id: llm.llm_id },
  voice_id: '11labs-Rachel',
  agent_name: 'Dr. Smith Booking Agent',
  language: 'en-US',
  opt_out_sensitive_data_storage: false,
  end_call_after_silence_ms: 10000,  // End call after 10s silence
  max_call_duration_ms: 300000,       // 5-minute max
  enable_backchannel: true,           // "mhm", "yeah" responses
  boosted_keywords: ['appointment', 'schedule', 'Dr. Smith'],
});
```

### Step 3: Update Agent Configuration
```typescript
await retell.agent.update(agent.agent_id, {
  voice_id: '11labs-Dorothy',  // Change voice
  end_call_after_silence_ms: 15000,
});
```

## Output
- Agent with custom LLM prompt and function calling
- Voice and behavior configuration
- Real-time function execution during calls

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Function not triggering | Prompt doesn't guide to function | Include function use in prompt |
| Voice quality issues | Wrong voice selection | Test different voices |
| Call ending too early | Short silence timeout | Increase `end_call_after_silence_ms` |

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps
Phone call management: `retellai-core-workflow-b`
