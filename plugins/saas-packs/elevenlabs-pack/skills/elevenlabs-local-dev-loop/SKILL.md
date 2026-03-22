---
name: elevenlabs-local-dev-loop
description: |
  Configure local ElevenLabs development with mocking, hot reload, and audio testing.
  Use when setting up a dev environment for TTS/voice projects, configuring test
  workflows, or building a fast iteration cycle with ElevenLabs audio.
  Trigger: "elevenlabs dev setup", "elevenlabs local development",
  "elevenlabs dev environment", "develop with elevenlabs", "test elevenlabs locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, tts, testing]
compatible-with: claude-code
---

# ElevenLabs Local Dev Loop

## Overview

Set up a fast, cost-effective local development workflow for ElevenLabs audio projects. Includes SDK mocking to avoid burning character quota during development, audio output testing, and hot-reload patterns.

## Prerequisites

- Completed `elevenlabs-install-auth` setup
- Node.js 18+ with npm/pnpm
- `vitest` for testing (recommended)

## Instructions

### Step 1: Project Structure

```
my-elevenlabs-project/
├── src/
│   ├── elevenlabs/
│   │   ├── client.ts       # Singleton client wrapper
│   │   ├── config.ts       # Environment-aware config
│   │   └── tts.ts          # TTS service layer
│   └── index.ts
├── tests/
│   ├── __mocks__/
│   │   └── elevenlabs.ts   # SDK mock for free testing
│   ├── tts.test.ts
│   └── fixtures/
│       └── sample.mp3      # Known-good audio for comparison
├── output/                  # Generated audio (git-ignored)
├── .env.local               # Local API key (git-ignored)
├── .env.example             # Template for team
└── package.json
```

### Step 2: Environment Configuration

```typescript
// src/elevenlabs/config.ts
export interface ElevenLabsConfig {
  apiKey: string;
  modelId: string;
  defaultVoiceId: string;
  outputFormat: string;
}

export function loadConfig(): ElevenLabsConfig {
  const env = process.env.NODE_ENV || "development";

  return {
    apiKey: process.env.ELEVENLABS_API_KEY || "",
    // Use cheaper/faster model in dev, high-quality in prod
    modelId: env === "production"
      ? "eleven_multilingual_v2"    // 1.0 credits/char, best quality
      : "eleven_flash_v2_5",       // 0.5 credits/char, ~75ms latency
    defaultVoiceId: process.env.ELEVENLABS_VOICE_ID || "21m00Tcm4TlvDq8ikWAM",
    outputFormat: "mp3_22050_32",  // Smaller files for dev
  };
}
```

### Step 3: Mock the SDK for Unit Tests

```typescript
// tests/__mocks__/elevenlabs.ts
// Avoids API calls (and character charges) during testing
import { vi } from "vitest";
import { readFileSync } from "fs";

const sampleAudio = readFileSync("tests/fixtures/sample.mp3");

export const mockElevenLabsClient = {
  textToSpeech: {
    convert: vi.fn().mockResolvedValue(
      new ReadableStream({
        start(controller) {
          controller.enqueue(sampleAudio);
          controller.close();
        },
      })
    ),
    stream: vi.fn().mockImplementation(async function* () {
      yield sampleAudio.subarray(0, 1024);
      yield sampleAudio.subarray(1024);
    }),
  },
  voices: {
    getAll: vi.fn().mockResolvedValue({
      voices: [
        { voice_id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel" },
        { voice_id: "ErXwobaYiN019PkySvjV", name: "Antoni" },
      ],
    }),
  },
  user: {
    get: vi.fn().mockResolvedValue({
      subscription: {
        tier: "free",
        character_count: 500,
        character_limit: 10000,
      },
    }),
  },
};
```

### Step 4: Development Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "ELEVENLABS_INTEGRATION=1 vitest run tests/integration/",
    "generate": "tsx src/generate.ts",
    "quota": "tsx src/check-quota.ts"
  }
}
```

### Step 5: Quota-Aware Development

```typescript
// src/check-quota.ts — run before integration tests
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient();

async function checkQuota() {
  const user = await client.user.get();
  const { character_count, character_limit } = user.subscription;
  const remaining = character_limit - character_count;
  const pct = ((character_count / character_limit) * 100).toFixed(1);

  console.log(`Characters: ${character_count.toLocaleString()} / ${character_limit.toLocaleString()} (${pct}% used)`);
  console.log(`Remaining: ${remaining.toLocaleString()} characters`);

  if (remaining < 1000) {
    console.warn("WARNING: Low character quota. Use mocks for development.");
    process.exit(1);
  }
}

checkQuota().catch(console.error);
```

### Step 6: Integration Test Guard

```typescript
// tests/tts.test.ts
import { describe, it, expect, vi, beforeAll } from "vitest";
import { mockElevenLabsClient } from "./__mocks__/elevenlabs";

// Only hit real API when explicitly enabled
const useRealApi = process.env.ELEVENLABS_INTEGRATION === "1";

describe("TTS Service", () => {
  it("should generate audio from text (mocked)", async () => {
    const audio = await mockElevenLabsClient.textToSpeech.convert(
      "21m00Tcm4TlvDq8ikWAM",
      { text: "Test speech", model_id: "eleven_flash_v2_5" }
    );
    expect(audio).toBeDefined();
  });

  it.skipIf(!useRealApi)("should generate real audio (integration)", async () => {
    const { ElevenLabsClient } = await import("@elevenlabs/elevenlabs-js");
    const client = new ElevenLabsClient();
    const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
      text: "Integration test.",
      model_id: "eleven_flash_v2_5",
    });
    expect(audio).toBeDefined();
  });
});
```

## Output

- Working development environment with hot reload via `tsx watch`
- Mock layer that avoids API calls and character charges during dev
- Quota checker to prevent surprise billing
- Integration test guard pattern (`ELEVENLABS_INTEGRATION=1`)
- Environment-aware model selection (cheap in dev, quality in prod)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `MODULE_NOT_FOUND` | SDK not installed | `npm install @elevenlabs/elevenlabs-js` |
| Mock returns undefined | Mock not wired | Check vi.mock path matches import |
| Integration test fails | No API key | Set `ELEVENLABS_API_KEY` in `.env.local` |
| Quota exceeded in dev | Running real API calls | Use mock layer; run `npm run quota` first |

## Resources

- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js)
- [Vitest Mocking](https://vitest.dev/guide/mocking.html)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)

## Next Steps

See `elevenlabs-sdk-patterns` for production-ready code patterns.
