# Anti-Pattern Examples

## Voice Latency Budget Violations

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

## Call State Transition Mishandling

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
    if (Date.now() - call.started > 3600000) {  // 1 hour max
      cleanupResources(id);
      activeCalls.delete(id);
    }
  }
}, 60000);
```

## Audio Quality Neglect

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

## Concurrent Call Limit Violations

```typescript
// BAD: no concurrency tracking
app.post('/initiate-call', async (req, res) => {
  const call = await retell.call.createPhoneCall({/*...*/});
  res.json(call);  // Fails at limit with cryptic error
});

// GOOD: track and enforce concurrency
let activeConcurrent = 0;
const MAX_CONCURRENT = 10;  // check plan limit

app.post('/initiate-call', async (req, res) => {
  if (activeConcurrent >= MAX_CONCURRENT) {
    return res.status(429).json({ error: "Call capacity reached" });
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

## Webhook Latency Monitoring

```typescript
app.post('/retell-webhook', async (req, res) => {
  const start = Date.now();
  const response = await handleTurn(req.body);
  const latency = Date.now() - start;
  if (latency > 500) console.warn(`Slow response: ${latency}ms`);
  res.json(response);
});
```
