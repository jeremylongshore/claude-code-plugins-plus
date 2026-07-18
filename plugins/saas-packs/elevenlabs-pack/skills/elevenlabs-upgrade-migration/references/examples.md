# ElevenLabs Upgrade & Migration — Worked Examples

Three end-to-end scenarios that chain the individual steps from
[migration-guide.md](migration-guide.md) into complete, copy-pasteable runs.

## Example 1: Migrate a Node.js app off the legacy `elevenlabs` community package

Goal: move an existing app from the deprecated community `elevenlabs` package to the
official `@elevenlabs/elevenlabs-js` SDK on an isolated branch, then validate.

```bash
# 1. Snapshot current state and branch
npm list elevenlabs
git checkout -b upgrade/elevenlabs-sdk

# 2. Swap the package
npm uninstall elevenlabs
npm install @elevenlabs/elevenlabs-js
```

```typescript
// 3. Update the client construction
// BEFORE (legacy community package)
import ElevenLabs from "elevenlabs";
const client = new ElevenLabs({ apiKey: "..." });

// AFTER (official SDK)
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
  maxRetries: 3,
  timeoutInSeconds: 60,
});
```

```bash
# 4. Validate before merging the branch
npm test
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Upgrade test.","model_id":"eleven_flash_v2_5"}'
```

A `200` from the smoke test plus a green `npm test` means the branch is safe to merge.

## Example 2: Migrate a deprecated model with a WebSocket-safe fallback

Goal: move a real-time app from `eleven_multilingual_v2` toward the more expressive
`eleven_v3` **without** breaking streaming — `eleven_v3` has no WebSocket support, so the
selector falls back automatically when a socket is required.

```typescript
// config/models.ts
type ModelPreference = "quality" | "balanced" | "speed";

const MODEL_MAP: Record<ModelPreference, string> = {
  quality: "eleven_v3",               // Best expressiveness, 70+ languages
  balanced: "eleven_multilingual_v2", // Good quality, WebSocket support
  speed: "eleven_flash_v2_5",         // ~75ms latency, 0.5x cost
};

function selectModel(preference: ModelPreference, needsWebSocket = false): string {
  if (needsWebSocket && preference === "quality") {
    // eleven_v3 doesn't support WebSocket — fall back
    console.warn("eleven_v3 does not support WebSocket streaming; using multilingual_v2");
    return "eleven_multilingual_v2";
  }
  return MODEL_MAP[preference];
}

// Batch (non-streaming) request → gets eleven_v3
selectModel("quality");                 // → "eleven_v3"
// Streaming request → safely downgraded
selectModel("quality", true);           // → "eleven_multilingual_v2"
```

Before relying on a target model, confirm your account can reach it:

```bash
curl -s https://api.elevenlabs.io/v1/models \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
  jq '[.[] | {model_id, name}]'
```

## Example 3: Upgrade the Python SDK from a pre-client generation

Goal: move Python code off the old module-level `generate` / `set_api_key` API to the
current client object, and pin the version for reproducible builds.

```bash
pip show elevenlabs
pip install --upgrade elevenlabs
pip install elevenlabs==1.x.x
echo "elevenlabs==1.x.x" >> requirements.txt
```

```python
# Old:
from elevenlabs import generate, set_api_key
set_api_key("sk_...")
audio = generate(text="Hello", voice="Rachel")

# New:
from elevenlabs.client import ElevenLabsClient
client = ElevenLabsClient(api_key="sk_...")
audio = client.text_to_speech.convert(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    text="Hello",
    model_id="eleven_multilingual_v2",
)
```

If anything regresses, roll back to the previously pinned version:

```bash
pip install elevenlabs==previous.version.here
```
