# ElevenLabs Core Workflow B — Full Implementation Walkthrough

Complete TypeScript SDK (`@elevenlabs/elevenlabs-js`) and cURL implementations for
all four secondary ElevenLabs workflows. Every snippet assumes `ELEVENLABS_API_KEY`
is set in the environment (see [Prerequisites & Auth](#prerequisites--auth)).

## Prerequisites & Auth

- Completed `elevenlabs-install-auth` setup.
- The SDK client reads the API key from the `ELEVENLABS_API_KEY` environment
  variable automatically (`new ElevenLabsClient()`). Never hardcode the key.
- cURL requests authenticate with the `xi-api-key: ${ELEVENLABS_API_KEY}` header.

## Step 1: Speech-to-Speech (Voice Changer)

Transform audio from one voice to another using `POST /v1/speech-to-speech/{voice_id}`:

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createReadStream, createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new ElevenLabsClient();

async function speechToSpeech(
  sourceAudioPath: string,
  targetVoiceId: string,
  outputPath: string
) {
  const audio = await client.speechToSpeech.convert(targetVoiceId, {
    audio: createReadStream(sourceAudioPath),
    model_id: "eleven_english_sts_v2",  // STS-specific model
    voice_settings: JSON.stringify({
      stability: 0.5,
      similarity_boost: 0.8,
      style: 0.0,
    }),
    remove_background_noise: true,  // Built-in noise removal
  });

  await pipeline(Readable.fromWeb(audio as any), createWriteStream(outputPath));
  console.log(`Voice-converted audio saved to ${outputPath}`);
}

// Convert your voice recording to sound like "Rachel"
await speechToSpeech(
  "my_recording.mp3",
  "21m00Tcm4TlvDq8ikWAM",
  "converted.mp3"
);
```

**cURL equivalent:**

```bash
curl -X POST "https://api.elevenlabs.io/v1/speech-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -F "audio=@my_recording.mp3" \
  -F "model_id=eleven_english_sts_v2" \
  -F 'voice_settings={"stability":0.5,"similarity_boost":0.8}' \
  -F "remove_background_noise=true" \
  --output converted.mp3
```

## Step 2: Sound Effects Generation

Generate cinematic sound effects from text descriptions using `POST /v1/sound-generation`:

```typescript
async function generateSoundEffect(
  description: string,
  outputPath: string,
  options?: {
    duration?: number;      // 0.5-30 seconds (null = auto)
    promptInfluence?: number; // 0-1 (default 0.3, higher = follows prompt more closely)
    loop?: boolean;          // Seamless looping (default false)
  }
) {
  const audio = await client.textToSoundEffects.convert({
    text: description,
    duration_seconds: options?.duration,
    prompt_influence: options?.promptInfluence ?? 0.3,
    // model_id: "eleven_text_to_sound_v2",  // default
  });

  await pipeline(Readable.fromWeb(audio as any), createWriteStream(outputPath));
  console.log(`Sound effect saved to ${outputPath}`);
}

// Generate various sound effects
await generateSoundEffect(
  "Heavy rain on a tin roof with distant thunder",
  "rain.mp3",
  { duration: 10, promptInfluence: 0.6 }
);

await generateSoundEffect(
  "Sci-fi laser gun firing three quick bursts",
  "laser.mp3",
  { duration: 3, promptInfluence: 0.8 }
);

await generateSoundEffect(
  "Gentle forest ambiance with birds chirping",
  "forest_loop.mp3",
  { duration: 15, loop: true }  // Seamless loop for background audio
);
```

**cURL equivalent:**

```bash
curl -X POST "https://api.elevenlabs.io/v1/sound-generation" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Heavy rain on a tin roof with distant thunder",
    "duration_seconds": 10,
    "prompt_influence": 0.6
  }' \
  --output rain.mp3
```

## Step 3: Audio Isolation (Voice Isolator)

Remove background noise from audio using `POST /v1/audio-isolation`:

```typescript
async function isolateVoice(
  noisyAudioPath: string,
  cleanOutputPath: string
) {
  const cleanAudio = await client.audioIsolation.audioIsolation({
    audio: createReadStream(noisyAudioPath),
  });

  await pipeline(
    Readable.fromWeb(cleanAudio as any),
    createWriteStream(cleanOutputPath)
  );
  console.log(`Clean audio saved to ${cleanOutputPath}`);
}

// Remove background noise from a recording
await isolateVoice("noisy_interview.mp3", "clean_interview.mp3");
```

**Streaming variant** for large files (`POST /v1/audio-isolation/stream`):

```typescript
async function isolateVoiceStreaming(
  noisyAudioPath: string,
  cleanOutputPath: string
) {
  const stream = await client.audioIsolation.audioIsolationStream({
    audio: createReadStream(noisyAudioPath),
  });

  const writer = createWriteStream(cleanOutputPath);
  for await (const chunk of stream) {
    writer.write(chunk);
  }
  writer.end();
}
```

**cURL equivalent:**

```bash
curl -X POST "https://api.elevenlabs.io/v1/audio-isolation" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -F "audio=@noisy_interview.mp3" \
  --output clean_interview.mp3
```

## Step 4: Speech-to-Text (Transcription)

Transcribe audio with speaker diarization using `POST /v1/speech-to-text`:

```typescript
async function transcribeAudio(audioPath: string) {
  const result = await client.speechToText.convert({
    audio: createReadStream(audioPath),
    model_id: "scribe_v1",  // ElevenLabs' STT model
    // language_code: "en",  // Optional: force language
    // diarize: true,        // Enable speaker detection
    // timestamps_granularity: "word",  // "word" or "character"
  });

  console.log("Transcription:", result.text);

  // Word-level timestamps
  if (result.words) {
    for (const word of result.words) {
      console.log(`[${word.start.toFixed(2)}-${word.end.toFixed(2)}] ${word.text}`);
    }
  }

  return result;
}

await transcribeAudio("podcast_episode.mp3");
```

## Sound Effect Tips

- Be specific: "wooden door creaking slowly open in a quiet room" beats "door sound"
- Specify quantity: "three quick gunshots" vs "gunshots"
- Set mood: "eerie", "cheerful", "aggressive" changes the output character
- Use `prompt_influence: 0.6-0.8` for precise results, `0.2-0.4` for creative variation
- Max duration: 30 seconds per generation

## Audio Isolation Limits

| Aspect | Limit |
|--------|-------|
| Max file size | 500 MB |
| Max duration | 1 hour |
| Supported formats | MP3, WAV, M4A, FLAC, OGG, WEBM |
| PCM optimization | Use `file_format: "pcm_s16le_16"` for lowest latency |
