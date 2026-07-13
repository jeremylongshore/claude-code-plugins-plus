# Architecture Implementation Examples

## Agent and LLM Configuration

```typescript
import Retell from 'retell-sdk';

const retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });

// Create LLM with personality and tools
async function createAgentLLM() {
  const llm = await retell.llm.create({
    model: 'gpt-4o-mini',
    general_prompt: `You are Sarah, a friendly appointment scheduling assistant.

Instructions:
- Greet callers warmly and ask how to assist
- Collect: name, preferred date/time, reason for appointment
- Confirm all details before booking
- Keep responses under 2 sentences
- Be conversational, not robotic`,
    begin_message: "Hi there! This is Sarah from scheduling. How may we assist today?",
    general_tools: [
      {
        type: 'end_call',
        name: 'end_call',
        description: 'End call when conversation is complete',
      },
      {
        type: 'custom',
        name: 'book_appointment',
        description: 'Book an appointment after collecting all details',
        url: `${process.env.BASE_URL}/api/retell/book`,
        parameters: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Caller name' },
            date: { type: 'string', description: 'Preferred date' },
            time: { type: 'string', description: 'Preferred time' },
            reason: { type: 'string', description: 'Appointment reason' },
          },
          required: ['name', 'date', 'time'],
        },
      },
    ],
  });

  return llm;
}
```

## Voice Agent Setup

```typescript
async function createVoiceAgent(llmId: string) {
  return retell.agent.create({
    agent_name: 'Appointment Scheduler',
    response_engine: { type: 'retell-llm', llm_id: llmId },
    voice_id: 'eleven_labs_rachel',
    language: 'en-US',
    responsiveness: 0.8,
    interruption_sensitivity: 0.7,
    enable_backchannel: true,
    voice_speed: 1.0,
    voice_temperature: 0.5,
  });
}
```

## Tool Function Endpoints

```typescript
import express from 'express';
const app = express();

// Tool function: book appointment
app.post('/api/retell/book', express.json(), async (req, res) => {
  const { name, date, time, reason } = req.body.args;

  const booking = await bookAppointment({ name, date, time, reason });

  res.json({
    result: `Appointment booked for ${name} on ${date} at ${time}. Confirmation number: ${booking.id}`,
  });
});

// Webhook: call events
app.post('/api/retell/webhook', express.json(), async (req, res) => {
  const { event, call } = req.body;

  if (event === 'call_ended') {
    await saveCallRecord({
      callId: call.call_id,
      duration: call.end_timestamp - call.start_timestamp,
      transcript: call.transcript,
      sentiment: call.call_analysis?.sentiment,
    });
  }

  res.json({ received: true });
});
```

## Outbound Calls

```typescript
async function makeOutboundCall(
  toNumber: string,
  agentId: string,
  metadata?: Record<string, string>
) {
  return retell.call.createPhoneCall({
    from_number: process.env.RETELL_PHONE_NUMBER!,
    to_number: toNumber,
    override_agent_id: agentId,
    metadata,
  });
}
```

## Quick Agent Test

```typescript
// Create a web call for testing (no phone needed)
const webCall = await retell.call.createWebCall({
  agent_id: agentId,
  metadata: { test: 'true' },
});
console.log(`Test call URL: ${webCall.call_id}`);
```
