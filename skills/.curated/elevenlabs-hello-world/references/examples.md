# ElevenLabs Hello World — Worked Examples

Three end-to-end scenarios that build on the code paths in
[implementation.md](implementation.md). Each shows the input, the exact command
or call, and the resulting artifact on disk.

## Example 1 — First MP3 from the SDK (batch)

Goal: prove your key and SDK install work by writing one audio file.

Input text: `"Hello! This is your first ElevenLabs text-to-speech generation."`

Run the TypeScript block from implementation.md Step 1, then:

```bash
node generate.js
# → Audio saved to output.mp3
ls -lh output.mp3
# → -rw-r--r-- 1 user user 48K output.mp3
file output.mp3
# → output.mp3: Audio file with ID3 version 2.4.0, ... MPEG ADTS, layer III
```

Play it: `afplay output.mp3` (macOS) / `mpv output.mp3` (Linux).

## Example 2 — One-shot from the shell (cURL)

Goal: generate audio with no SDK, just an API key and cURL.

```bash
export ELEVENLABS_API_KEY="sk_..."
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from the ElevenLabs API!","model_id":"eleven_multilingual_v2"}' \
  --output output.mp3
# output.mp3 (~35 KB) written; non-200 responses return JSON, not audio —
# inspect with: cat output.mp3  (it will be a readable error body)
```

## Example 3 — Low-latency streaming for playback

Goal: start hearing audio before the full clip is generated.

Use the streaming block from implementation.md Step 3 with the fast
`eleven_flash_v2_5` model (~75 ms first-chunk latency). Chunks are written to
`streamed.mp3` as they arrive:

```bash
node stream.js
# → Streamed audio saved to streamed.mp3
```

Swap `output_format` to `mp3_22050_32` for smaller streamed files, or
`pcm_16000` if you are piping raw samples into a downstream audio pipeline.
