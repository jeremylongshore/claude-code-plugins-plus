---
name: retellai-webhooks-events
description: |
  Retell AI webhooks events — AI voice agent and phone call automation.
  Use when working with Retell AI for voice agents, phone calls, or telephony.
  Trigger with phrases like "retell webhooks events", "retellai-webhooks-events", "voice agent".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, ai-agents]
compatible-with: claude-code, codex, openclaw
---

# Retell AI Webhooks Events

## Overview
Handle Retell AI webhook events for call lifecycle, transcripts, and function execution.

## Prerequisites
- HTTPS webhook endpoint
- Agent configured with webhook URL

## Instructions

### Step 1: Configure Webhook URL
```typescript
// Set webhook URL in agent configuration
await retell.agent.update(agentId, {
  webhook_url: 'https://your-app.com/webhooks/retell',
});
```

### Step 2: Webhook Endpoint
```typescript
import express from 'express';

const app = express();
app.post('/webhooks/retell', express.json(), async (req, res) => {
  const { event, call } = req.body;

  switch (event) {
    case 'call_started':
      console.log(`Call started: ${call.call_id} from ${call.from_number}`);
      break;

    case 'call_ended':
      console.log(`Call ended: ${call.call_id}`);
      console.log(`  Duration: ${call.duration_ms}ms`);
      console.log(`  Status: ${call.call_status}`);
      if (call.transcript) {
        await saveTranscript(call.call_id, call.transcript);
      }
      break;

    case 'call_analyzed':
      console.log(`Analysis ready: ${call.call_id}`);
      console.log(`  Summary: ${call.call_analysis?.call_summary}`);
      break;

    default:
      console.log(`Unhandled event: ${event}`);
  }

  res.status(200).json({ received: true });
});
```

### Step 3: Handle Function Calls During Conversation
```typescript
// When agent triggers a function, Retell calls your URL
app.post('/functions/book-appointment', express.json(), async (req, res) => {
  const { patient_name, phone, date, time } = req.body.args;

  // Process the booking
  const booking = await bookAppointment(patient_name, phone, date, time);

  // Return response for agent to speak
  res.json({
    result: `Appointment booked for ${patient_name} on ${date} at ${time}. Confirmation number: ${booking.id}`,
  });
});
```

## Output
- Webhook handling for call lifecycle events
- Transcript storage on call completion
- Function execution during live calls

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No webhook events | URL not configured | Set webhook_url on agent |
| Function timeout | Slow backend | Respond within 5 seconds |
| Missing transcript | Short call | Transcript only for calls > 5 seconds |

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps
Common errors: `retellai-common-errors`
