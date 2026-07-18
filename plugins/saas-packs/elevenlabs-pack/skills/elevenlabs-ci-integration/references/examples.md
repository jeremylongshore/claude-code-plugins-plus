# ElevenLabs CI Integration — Test Examples Reference

Complete test code for both tiers plus the package scripts that wire them
together. SKILL.md shows a minimal mock skeleton; this file is the full,
copy-paste source.

## Step 3: Unit Test with SDK Mock

```typescript
// tests/unit/tts-service.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the entire SDK — no API calls, no quota usage
vi.mock("@elevenlabs/elevenlabs-js", () => ({
  ElevenLabsClient: vi.fn().mockImplementation(() => ({
    textToSpeech: {
      convert: vi.fn().mockResolvedValue(
        new ReadableStream({
          start(controller) {
            controller.enqueue(new Uint8Array([0xFF, 0xFB, 0x90, 0x00])); // MP3 header
            controller.close();
          },
        })
      ),
      stream: vi.fn().mockImplementation(async function* () {
        yield new Uint8Array([0xFF, 0xFB, 0x90, 0x00]);
      }),
    },
    voices: {
      getAll: vi.fn().mockResolvedValue({
        voices: [
          { voice_id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel", category: "premade" },
        ],
      }),
    },
    user: {
      get: vi.fn().mockResolvedValue({
        subscription: { tier: "pro", character_count: 1000, character_limit: 500000 },
      }),
    },
  })),
}));

import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

describe("TTS Service", () => {
  let client: InstanceType<typeof ElevenLabsClient>;

  beforeEach(() => {
    client = new ElevenLabsClient();
  });

  it("should call TTS with correct parameters", async () => {
    await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
      text: "Test speech",
      model_id: "eleven_multilingual_v2",
      voice_settings: { stability: 0.5, similarity_boost: 0.75 },
    });

    expect(client.textToSpeech.convert).toHaveBeenCalledWith(
      "21m00Tcm4TlvDq8ikWAM",
      expect.objectContaining({
        text: "Test speech",
        model_id: "eleven_multilingual_v2",
      })
    );
  });

  it("should handle voice listing", async () => {
    const result = await client.voices.getAll();
    expect(result.voices).toHaveLength(1);
    expect(result.voices[0].name).toBe("Rachel");
  });
});
```

## Step 4: Integration Test (Gated)

```typescript
// tests/integration/tts-smoke.test.ts
import { describe, it, expect } from "vitest";

const SKIP = !process.env.ELEVENLABS_INTEGRATION;

describe.skipIf(SKIP)("ElevenLabs Integration", () => {
  it("should generate audio from text", async () => {
    const { ElevenLabsClient } = await import("@elevenlabs/elevenlabs-js");
    const client = new ElevenLabsClient();

    // Use Flash model + short text to minimize quota usage
    const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
      text: "CI test.",  // 8 characters = 4 credits (Flash)
      model_id: "eleven_flash_v2_5",
      output_format: "mp3_22050_32",
    });

    expect(audio).toBeDefined();
  }, 30_000);

  it("should list voices", async () => {
    const { ElevenLabsClient } = await import("@elevenlabs/elevenlabs-js");
    const client = new ElevenLabsClient();
    const { voices } = await client.voices.getAll();
    expect(voices.length).toBeGreaterThan(0);
  });
});
```

## Step 5: Package Scripts

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "test:integration": "ELEVENLABS_INTEGRATION=1 vitest run tests/integration/",
    "test:ci": "vitest run --coverage --reporter=junit --outputFile=test-results.xml"
  }
}
```
