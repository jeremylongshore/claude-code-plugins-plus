# ElevenLabs Webhooks — Per-Event Handler Examples

Concrete handlers for each ElevenLabs event type, showing which fields each
payload carries and how to process them. Wire these into the `processEvent`
router in [implementation.md](implementation.md).

## Conversational AI post-call transcript

```typescript
// Conversational AI post-call transcript
async function handleTranscription(event: any) {
  const {
    conversation_id,
    transcript,       // Full conversation text
    analysis,         // AI analysis of the call
    metadata,         // Custom metadata from agent config
    recording_url,    // Audio recording URL (if enabled)
  } = event.data;

  console.log(`[Transcript] Conversation ${conversation_id}`);
  console.log(`Transcript: ${transcript?.substring(0, 200)}...`);

  // Store in your database
  // await db.conversations.upsert({ conversation_id, transcript, analysis });
}
```

## Post-call audio recording

```typescript
// Post-call audio recording
async function handleCallAudio(event: any) {
  const {
    conversation_id,
    audio_base64,     // Base64-encoded audio of the full conversation
  } = event.data;

  if (audio_base64) {
    const audioBuffer = Buffer.from(audio_base64, "base64");
    console.log(`[Audio] Received ${audioBuffer.length} bytes for ${conversation_id}`);
    // Save audio: await fs.writeFile(`recordings/${conversation_id}.mp3`, audioBuffer);
  }
}
```

## Failed outbound call

```typescript
// Failed outbound call
async function handleCallFailure(event: any) {
  const {
    conversation_id,
    failure_reason,
    metadata,
  } = event.data;

  console.error(`[Call Failed] ${conversation_id}: ${failure_reason}`);
  // Alert: await alerting.notify("Call initiation failed", { conversation_id, failure_reason });
}
```

## Async Speech-to-Text completion

```typescript
// Async Speech-to-Text completion
async function handleSTTCompleted(event: any) {
  const {
    transcription_id,
    text,
    words,           // Word-level timestamps
    language,
  } = event.data;

  console.log(`[STT Complete] ${transcription_id}: ${language}`);
  console.log(`Text: ${text?.substring(0, 200)}...`);
  // Process transcription results
}
```
