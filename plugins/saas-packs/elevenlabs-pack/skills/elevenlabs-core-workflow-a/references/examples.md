# ElevenLabs Core Workflow A — Worked Examples

End-to-end scenarios that combine the steps from SKILL.md and
`implementation.md`. Each example is a complete, copy-pasteable path from
input to generated audio.

## Example 1: Generate narration from a script

Batch a marketing script into a single MP3 using a premade voice and the
narration-tuned settings (stability=0.5, similarity=0.75, style=0.0).

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new ElevenLabsClient();

const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
  text: "Welcome to our platform. Let's get you set up in three quick steps.",
  model_id: "eleven_multilingual_v2",
  voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.0 },
});

await pipeline(Readable.fromWeb(audio as any), createWriteStream("narration.mp3"));
```

**Expected result:** `narration.mp3` written to disk; console prints
`Generated: narration.mp3`.

## Example 2: Clone a narrator voice and speak with it

Clone from two clean samples, then immediately synthesize with the returned
`voice_id` using the cloned-voice settings (similarity_boost=0.85).

```typescript
const { voiceId, audio } = await cloneVoice(
  "My Custom Voice",
  "Professional narrator voice",
  ["sample1.mp3", "sample2.mp3"]
);
// voiceId now usable in any textToSpeech.convert call
```

**Expected result:** console prints `Cloned voice created: <voice_id>`; the
returned `audio` stream speaks "This is my cloned voice speaking!" in the
cloned timbre. See `implementation.md` Step 2 for the full `cloneVoice` body
and the [Voice Cloning Requirements](implementation.md#voice-cloning-requirements)
table (30s+ clean audio, 1-25 samples, paid plan).

## Example 3: Stream an LLM response as speech in real time

Pipe chatbot output through the WebSocket endpoint with the low-latency
`eleven_flash_v2_5` model so audio starts before the full text is ready.

```typescript
const chunks = ["Hello, ", "this is ", "streamed ", "speech!"];
const audio = await streamTTSWebSocket("21m00Tcm4TlvDq8ikWAM", chunks);
```

**Expected result:** a concatenated `Buffer` of base64-decoded audio chunks,
assembled as they arrive. Full `streamTTSWebSocket` body (BOS/EOS framing,
`chunk_length_schedule`, `isFinal` handling) is in `implementation.md` Step 3.

## Example 4: Audit and prune your voice library

List every voice with its category, then delete a stale cloned voice.

```typescript
await listVoices();               // prints name, voice_id, category per voice
await deleteVoice("<old_voice_id>");
```

**Expected result:** each voice printed as `name (voice_id) — category`
(`premade` | `cloned` | `generated`); the target voice removed and
`Voice <voice_id> deleted.` logged. See `implementation.md` Step 4 for
`listVoices`, `getVoiceSettings`, `updateVoiceSettings`, and `deleteVoice`.
