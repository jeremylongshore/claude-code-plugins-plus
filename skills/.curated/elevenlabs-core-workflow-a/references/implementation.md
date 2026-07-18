# ElevenLabs Core Workflow A — Full Implementation Walkthrough

Deep reference for the TTS & voice cloning workflows. SKILL.md carries the
lean summary and the first Text-to-Speech example; this file holds the
remaining steps (voice cloning, WebSocket streaming, voice management) and the
tuning reference tables verbatim.

## Step 2: Instant Voice Cloning (IVC)

Clone a voice from audio samples using `POST /v1/voices/add`:

```typescript
import { createReadStream } from "fs";

async function cloneVoice(
  name: string,
  description: string,
  audioFiles: string[]  // Paths to audio samples
) {
  const voice = await client.voices.add({
    name,
    description,
    files: audioFiles.map(f => createReadStream(f)),
    // Optional: label the voice for organization
    labels: JSON.stringify({ accent: "american", age: "young" }),
  });

  console.log(`Cloned voice created: ${voice.voice_id}`);
  console.log(`Name: ${name}`);

  // Use the cloned voice immediately
  const audio = await client.textToSpeech.convert(voice.voice_id, {
    text: "This is my cloned voice speaking!",
    model_id: "eleven_multilingual_v2",
    voice_settings: {
      stability: 0.5,
      similarity_boost: 0.85,  // Higher for cloned voices to stay close to original
    },
  });

  return { voiceId: voice.voice_id, audio };
}

// Clone from 1-25 audio samples (more = better quality)
await cloneVoice(
  "My Custom Voice",
  "Professional narrator voice",
  ["sample1.mp3", "sample2.mp3"]
);
```

## Step 3: WebSocket Streaming TTS

For real-time applications (chatbots, live narration), use the WebSocket endpoint:

```typescript
import WebSocket from "ws";

async function streamTTSWebSocket(
  voiceId: string,
  textChunks: string[]
) {
  const modelId = "eleven_flash_v2_5"; // Best for real-time streaming
  const wsUrl = `wss://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream-input?model_id=${modelId}`;

  const ws = new WebSocket(wsUrl);
  const audioChunks: Buffer[] = [];

  return new Promise<Buffer>((resolve, reject) => {
    ws.on("open", () => {
      // Send initial config (BOS - Beginning of Stream)
      ws.send(JSON.stringify({
        text: " ",  // Space signals BOS
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        },
        xi_api_key: process.env.ELEVENLABS_API_KEY,
        // How many chars to buffer before generating audio
        chunk_length_schedule: [120, 160, 250, 290],
      }));

      // Stream text chunks
      for (const chunk of textChunks) {
        ws.send(JSON.stringify({ text: chunk }));
      }

      // Send EOS (End of Stream)
      ws.send(JSON.stringify({ text: "" }));
    });

    ws.on("message", (data: Buffer) => {
      const msg = JSON.parse(data.toString());
      if (msg.audio) {
        // Base64-encoded audio chunk
        audioChunks.push(Buffer.from(msg.audio, "base64"));
      }
      if (msg.isFinal) {
        ws.close();
      }
    });

    ws.on("close", () => resolve(Buffer.concat(audioChunks)));
    ws.on("error", reject);
  });
}

// Stream from an LLM response in chunks
const chunks = ["Hello, ", "this is ", "streamed ", "speech!"];
const audio = await streamTTSWebSocket("21m00Tcm4TlvDq8ikWAM", chunks);
```

## Step 4: Voice Management

```typescript
// List all available voices
async function listVoices() {
  const { voices } = await client.voices.getAll();
  for (const v of voices) {
    console.log(`${v.name} (${v.voice_id}) — ${v.category}`);
    // category: "premade" | "cloned" | "generated"
  }
}

// Get voice settings defaults
async function getVoiceSettings(voiceId: string) {
  const settings = await client.voices.getSettings(voiceId);
  console.log(`Stability: ${settings.stability}`);
  console.log(`Similarity: ${settings.similarity_boost}`);
}

// Update default voice settings
async function updateVoiceSettings(voiceId: string) {
  await client.voices.editSettings(voiceId, {
    stability: 0.6,
    similarity_boost: 0.8,
  });
}

// Delete a cloned voice
async function deleteVoice(voiceId: string) {
  await client.voices.delete(voiceId);
  console.log(`Voice ${voiceId} deleted.`);
}
```

## Voice Cloning Requirements

| Aspect | Requirement |
|--------|-------------|
| Audio length | Minimum 30 seconds total (1+ minute recommended) |
| Audio quality | Clean, no background noise, no music |
| Format | MP3, WAV, M4A, FLAC, OGG |
| Samples | 1-25 files per voice |
| Languages | Works across all supported languages |
| Plan | Available on all paid plans |

## Voice Settings Guide

| Setting | Range | Low Value Effect | High Value Effect |
|---------|-------|-----------------|-------------------|
| `stability` | 0-1 | More expressive, varied | Consistent, monotone |
| `similarity_boost` | 0-1 | More creative deviation | Strictly matches voice |
| `style` | 0-1 | Neutral delivery | Exaggerated emotion |
| `speed` | 0.7-1.2 | Slower speech | Faster speech |

**Recommended starting points:**

- Narration: stability=0.5, similarity=0.75, style=0.0
- Conversational: stability=0.4, similarity=0.6, style=0.3
- Cloned voice: stability=0.5, similarity=0.85, style=0.0
