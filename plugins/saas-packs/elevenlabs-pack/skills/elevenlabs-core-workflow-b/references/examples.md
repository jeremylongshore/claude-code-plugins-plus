# ElevenLabs Core Workflow B — Worked Examples

Concrete, copy-ready invocations for each of the four workflows. All helper
functions (`speechToSpeech`, `generateSoundEffect`, `isolateVoice`,
`transcribeAudio`) are defined in [implementation.md](implementation.md).

## Speech-to-Speech: convert a recording to the "Rachel" voice

```typescript
// Convert your voice recording to sound like "Rachel"
await speechToSpeech(
  "my_recording.mp3",
  "21m00Tcm4TlvDq8ikWAM",
  "converted.mp3"
);
```

Output: `Voice-converted audio saved to converted.mp3`

## Sound Effects: rain, laser, and a seamless forest loop

```typescript
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

Higher `promptInfluence` (0.6-0.8) keeps the output faithful to the description;
lower values (0.2-0.4) give the model creative latitude.

## Audio Isolation: clean a noisy interview

```typescript
// Remove background noise from a recording
await isolateVoice("noisy_interview.mp3", "clean_interview.mp3");
```

Output: `Clean audio saved to clean_interview.mp3`. For files approaching the
500 MB / 1-hour ceiling, use the streaming variant (`isolateVoiceStreaming`) in
[implementation.md](implementation.md).

## Speech-to-Text: transcribe a podcast episode

```typescript
await transcribeAudio("podcast_episode.mp3");
```

Prints the full transcript, then word-level timestamps:

```
Transcription: Welcome back to the show...
[0.00-0.42] Welcome
[0.42-0.71] back
[0.71-0.95] to
...
```

Uncomment `diarize: true` in the helper to attach speaker labels, or
`language_code` to force a specific language instead of auto-detection.

## cURL-only quickstart (no SDK)

Every workflow has a cURL equivalent in [implementation.md](implementation.md).
The minimal speech-to-speech call:

```bash
curl -X POST "https://api.elevenlabs.io/v1/speech-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -F "audio=@my_recording.mp3" \
  -F "model_id=eleven_english_sts_v2" \
  --output converted.mp3
```
