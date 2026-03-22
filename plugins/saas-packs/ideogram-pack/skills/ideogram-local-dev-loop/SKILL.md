---
name: ideogram-local-dev-loop
description: |
  Configure Ideogram local development with mock responses and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Ideogram.
  Trigger with phrases like "ideogram dev setup", "ideogram local development",
  "ideogram dev environment", "develop with ideogram", "ideogram testing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, testing, workflow, development]

---
# Ideogram Local Dev Loop

## Overview
Set up a fast local development workflow for Ideogram integrations. Includes a typed client wrapper, mock server for offline development (avoids burning credits), and vitest integration for automated testing.

## Prerequisites
- Completed `ideogram-install-auth` setup
- Node.js 18+ with npm/pnpm
- `IDEOGRAM_API_KEY` environment variable set

## Instructions

### Step 1: Create Project Structure
```
my-ideogram-project/
├── src/
│   ├── ideogram/
│   │   ├── client.ts       # Typed Ideogram client wrapper
│   │   ├── types.ts         # Request/response type definitions
│   │   └── mock-server.ts   # Local mock for offline dev
│   └── index.ts
├── tests/
│   └── ideogram.test.ts
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
├── tsconfig.json
└── package.json
```

### Step 2: Install Dependencies
```bash
set -euo pipefail
npm install dotenv
npm install -D typescript tsx vitest @types/node
```

### Step 3: Type Definitions
```typescript
// src/ideogram/types.ts
export type StyleType = "AUTO" | "GENERAL" | "REALISTIC" | "DESIGN" | "RENDER_3D" | "ANIME";
export type AspectRatio = "ASPECT_1_1" | "ASPECT_16_9" | "ASPECT_9_16" | "ASPECT_3_2" | "ASPECT_2_3"
  | "ASPECT_4_3" | "ASPECT_3_4" | "ASPECT_10_16" | "ASPECT_16_10" | "ASPECT_1_3" | "ASPECT_3_1";
export type Model = "V_1" | "V_1_TURBO" | "V_2" | "V_2_TURBO" | "V_2A" | "V_2A_TURBO";
export type MagicPrompt = "AUTO" | "ON" | "OFF";

export interface GenerateRequest {
  prompt: string;
  model?: Model;
  style_type?: StyleType;
  aspect_ratio?: AspectRatio;
  magic_prompt_option?: MagicPrompt;
  negative_prompt?: string;
  num_images?: number;
  seed?: number;
}

export interface ImageResult {
  url: string;
  prompt: string;
  resolution: string;
  is_image_safe: boolean;
  seed: number;
  style_type: StyleType;
}

export interface GenerateResponse {
  created: string;
  data: ImageResult[];
}
```

### Step 4: Client Wrapper
```typescript
// src/ideogram/client.ts
import type { GenerateRequest, GenerateResponse } from "./types";

const IDEOGRAM_API = "https://api.ideogram.ai";

export class IdeogramClient {
  constructor(private apiKey: string) {
    if (!apiKey) throw new Error("IDEOGRAM_API_KEY is required");
  }

  async generate(request: GenerateRequest): Promise<GenerateResponse> {
    const response = await fetch(`${IDEOGRAM_API}/generate`, {
      method: "POST",
      headers: {
        "Api-Key": this.apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ image_request: request }),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new IdeogramError(response.status, body);
    }
    return response.json();
  }
}

export class IdeogramError extends Error {
  constructor(public status: number, public body: string) {
    super(`Ideogram API error ${status}: ${body}`);
    this.name = "IdeogramError";
  }
}
```

### Step 5: Mock Server for Offline Development
```typescript
// src/ideogram/mock-server.ts
import type { GenerateResponse } from "./types";

// Use this in development to avoid burning real credits
export function mockGenerate(prompt: string): GenerateResponse {
  return {
    created: new Date().toISOString(),
    data: [{
      url: `https://placehold.co/1024x1024/333/fff?text=${encodeURIComponent(prompt.slice(0, 30))}`,
      prompt,
      resolution: "1024x1024",
      is_image_safe: true,
      seed: Math.floor(Math.random() * 100000),
      style_type: "GENERAL",
    }],
  };
}
```

### Step 6: Vitest Tests
```typescript
// tests/ideogram.test.ts
import { describe, it, expect, vi } from "vitest";
import { IdeogramClient, IdeogramError } from "../src/ideogram/client";
import { mockGenerate } from "../src/ideogram/mock-server";

describe("IdeogramClient", () => {
  it("should reject missing API key", () => {
    expect(() => new IdeogramClient("")).toThrow("IDEOGRAM_API_KEY is required");
  });

  it("should construct generate request correctly", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(mockGenerate("test")), { status: 200 })
    );

    const client = new IdeogramClient("test-key");
    const result = await client.generate({ prompt: "test", model: "V_2" });

    expect(fetchSpy).toHaveBeenCalledWith(
      "https://api.ideogram.ai/generate",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Api-Key": "test-key" }),
      })
    );
    expect(result.data[0].prompt).toBe("test");
    fetchSpy.mockRestore();
  });

  it("should throw IdeogramError on 401", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("Unauthorized", { status: 401 })
    );

    const client = new IdeogramClient("bad-key");
    await expect(client.generate({ prompt: "test" })).rejects.toThrow(IdeogramError);
  });
});

describe("mockGenerate", () => {
  it("should return valid response shape", () => {
    const result = mockGenerate("hello world");
    expect(result.data).toHaveLength(1);
    expect(result.data[0].is_image_safe).toBe(true);
    expect(result.data[0].seed).toBeGreaterThan(0);
  });
});
```

### Step 7: Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "generate": "tsx src/index.ts"
  }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Env not loaded | Missing `.env.local` | Copy from `.env.example` |
| Test timeout | Mocking not set up | Use `mockGenerate` in tests |
| Credits burned in tests | Using real API in CI | Mock `fetch` in test files |

## Output
- Typed client wrapper for Ideogram API
- Mock server for offline development
- Vitest test suite with fetch mocking
- Fast iteration cycle without spending credits

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Runner](https://github.com/privatenumber/tsx)

## Next Steps
See `ideogram-sdk-patterns` for production-ready code patterns.
