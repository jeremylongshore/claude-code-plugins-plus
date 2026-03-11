---
name: retellai-known-pitfalls
description: |
  Identify and avoid Retell AI anti-patterns and common integration mistakes.
  Use when reviewing Retell AI code for issues, onboarding new developers,
  or auditing existing Retell AI integrations for best practices violations.
  Trigger with phrases like "retellai mistakes", "retellai anti-patterns",
  "retellai pitfalls", "retellai what not to do", "retellai code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Known Pitfalls

## Overview
Real gotchas when building voice AI agents with Retell AI. Retell handles telephony, speech-to-text, and text-to-speech in a WebSocket pipeline -- latency sensitivity and audio-specific failure modes require different thinking than typical REST APIs.

## Prerequisites
- Retell AI API key and agent configured
- Understanding of WebSocket-based communication
- Awareness of telephony concepts (PSTN, SIP)

## Instructions

### Step 1: Manage Voice Latency Budget

Retell pipelines must respond in under 1 second for natural conversation. Your webhook response time is part of that budget.

```typescript
// BAD: slow webhook handler kills conversation flow
app.post('/retell-webhook', async (req, res) => {
  const dbResult = await complexDatabaseQuery(req.body);  // 800ms
  const aiResult = await callExternalLLM(dbResult);        // 2000ms
  res.json({ response: aiResult });  // Total: 2.8s = awkward silence
});

// GOOD: pre-compute, cache, and keep responses fast
app.post('/retell-webhook', async (req, res) => {
  const cached = await redis.get(`context:${req.body.call_id}`);
  const response = generateQuickResponse(req.body, cached);
  res.json({ response });  // < 200ms

  // Do heavy processing async for next turn
  processInBackground(req.body).catch(console.error);
});
```

### Step 2: Handle Call State Transitions

Calls can disconnect at any point. Not handling state transitions causes zombie sessions.

```typescript
// BAD: assuming linear call flow
retell.on('call_started', async (event) => {
  await startExpensiveProcess(event.call_id);
  // If call drops immediately, process runs forever
});

// GOOD: track and clean up call state
const activeCalls = new Map();

retell.on('call_started', async (event) => {
  activeCalls.set(event.call_id, { started: Date.now() });
});

retell.on('call_ended', async (event) => {
  const call = activeCalls.get(event.call_id);
  if (call) {
    await cleanupResources(event.call_id);
    activeCalls.delete(event.call_id);
  }
});

// Periodic cleanup for missed end events
setInterval(() => {
  for (const [id, call] of activeCalls) {
    if (Date.now() - call.started > 3600000) {  // 1 hour max  # 3600000 = configured value
      cleanupResources(id);
      activeCalls.delete(id);
    }
  }
}, 60000);  # 60000: 1 minute in ms
```

### Step 3: Don't Ignore Audio Quality Issues

Poor audio input causes misrecognition. Always configure noise handling.

```typescript
// BAD: no audio configuration
const agent = await retell.agent.create({
  voice_id: "some-voice",
  llm_websocket_url: webhookUrl,
  // Missing: ambient_sound, responsiveness settings
});

// GOOD: configure for real-world audio conditions
const agent = await retell.agent.create({
  voice_id: "some-voice",
  llm_websocket_url: webhookUrl,
  ambient_sound: "office",
  responsiveness: 0.5,  // balance between speed and accuracy
  interruption_sensitivity: 0.6,
  enable_backchannel: true,  // "uh-huh", "I see"
});
```

### Step 4: Handle Concurrent Call Limits

Retell enforces concurrent call limits per plan. Exceeding them silently fails new calls.

```typescript
// BAD: no concurrency tracking
app.post('/initiate-call', async (req, res) => {
  const call = await retell.call.createPhoneCall({/*...*/});
  res.json(call);  // Fails at limit with cryptic error
});

// GOOD: track and enforce concurrency
let activeConcurrent = 0;
const MAX_CONCURRENT = 10;  // check your plan limit

app.post('/initiate-call', async (req, res) => {
  if (activeConcurrent >= MAX_CONCURRENT) {
    return res.status(429).json({ error: "Call capacity reached" });  # HTTP 429 Too Many Requests
  }
  activeConcurrent++;
  try {
    const call = await retell.call.createPhoneCall({/*...*/});
    res.json(call);
  } catch (e) {
    activeConcurrent--;
    throw e;
  }
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Awkward silences | Webhook response > 1s | Cache context, respond fast |
| Misrecognition | Background noise | Set `ambient_sound` config |
| Zombie sessions | Missed `call_ended` events | Periodic cleanup timer |
| Calls rejected | Hit concurrent limit | Track active calls, queue overflow |
| One-sided audio | WebSocket connection drop | Implement reconnection logic |

## Examples

### Webhook Latency Monitoring
```typescript
app.post('/retell-webhook', async (req, res) => {
  const start = Date.now();
  const response = await handleTurn(req.body);
  const latency = Date.now() - start;
  if (latency > 500) console.warn(`Slow response: ${latency}ms`);  # HTTP 500 Internal Server Error
  res.json(response);
});
```

## Resources
- [Retell AI Docs](https://docs.retellai.com)
- [Voice Agent Best Practices](https://docs.retellai.com/guide/best-practices)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale