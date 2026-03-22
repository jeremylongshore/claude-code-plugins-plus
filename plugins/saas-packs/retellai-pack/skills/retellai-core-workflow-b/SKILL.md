---
name: retellai-core-workflow-b
description: |
  Retell AI core workflow b — AI voice agent and phone call automation.
  Use when working with Retell AI for voice agents, phone calls, or telephony.
  Trigger with phrases like "retell core workflow b", "retellai-core-workflow-b", "voice agent".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, ai-agents]
compatible-with: claude-code, codex, openclaw
---

# Retell AI Core Workflow B

## Overview
Manage phone calls: outbound campaigns, call transfers, recordings, and concurrent call handling.

## Prerequisites
- Completed `retellai-core-workflow-a`

## Instructions

### Step 1: Outbound Call Campaign
```typescript
const phoneNumbers = ['+14155551001', '+14155551002', '+14155551003'];

for (const number of phoneNumbers) {
  try {
    const call = await retell.call.createPhoneCall({
      from_number: process.env.RETELL_PHONE_NUMBER!,
      to_number: number,
      override_agent_id: agentId,
      metadata: { campaign: 'appointment-reminder', date: '2026-04-01' },
    });
    console.log(`Called ${number}: ${call.call_id}`);
  } catch (err) {
    console.error(`Failed to call ${number}: ${err.message}`);
  }
  // Rate limit: space calls apart
  await new Promise(r => setTimeout(r, 2000));
}
```

### Step 2: List and Filter Calls
```typescript
const calls = await retell.call.list({
  sort_order: 'descending',
  limit: 20,
});
for (const call of calls) {
  console.log(`${call.call_id}: ${call.call_status} — ${call.end_timestamp - call.start_timestamp}ms`);
}
```

### Step 3: Get Call Recording and Transcript
```typescript
const callDetail = await retell.call.retrieve(callId);
if (callDetail.recording_url) {
  console.log(`Recording: ${callDetail.recording_url}`);
}
if (callDetail.transcript) {
  console.log(`Transcript:\n${callDetail.transcript}`);
}
```

## Output
- Outbound call campaign with rate limiting
- Call listing with status and duration
- Recordings and transcripts retrieved

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Call fails immediately | Bad phone number format | Use E.164 format |
| No recording | Recording not enabled | Enable in agent settings |
| Concurrent limit | Too many active calls | Upgrade plan or queue calls |

## Resources
- [Create Phone Call](https://docs.retellai.com/api-references/create-phone-call)
- [Retell AI Documentation](https://docs.retellai.com)

## Next Steps
Handle call events: `retellai-webhooks-events`
