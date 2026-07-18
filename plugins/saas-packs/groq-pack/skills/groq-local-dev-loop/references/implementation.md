# Groq Local Dev Loop — Full Implementation

Complete code for the project scaffold, singleton client, model constants, and
environment template. The SKILL.md shows the lean skeleton; this file is the
full walkthrough.

## Project Structure

```
my-groq-project/
├── src/
│   ├── groq/
│   │   ├── client.ts       # Singleton Groq client
│   │   ├── models.ts       # Model constants and selection
│   │   └── completions.ts  # Completion wrappers
│   └── index.ts
├── tests/
│   ├── groq.test.ts         # Unit tests with mocks
│   └── groq.integration.ts  # Live API tests (CI-only)
├── .env.local               # Local secrets (git-ignored)
├── .env.example              # Template for team
└── package.json
```

## Package Setup

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "GROQ_INTEGRATION=1 vitest tests/groq.integration.ts"
  },
  "dependencies": {
    "groq-sdk": "^0.12.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0"
  }
}
```

## Singleton Client

The client is lazily instantiated and memoized so a single configured instance
is shared across the app. It fails fast with an actionable message when
`GROQ_API_KEY` is missing, and exposes `resetClient()` so tests can clear the
memoized instance between runs.

```typescript
// src/groq/client.ts
import Groq from "groq-sdk";

let _client: Groq | null = null;

export function getGroqClient(): Groq {
  if (!_client) {
    if (!process.env.GROQ_API_KEY) {
      throw new Error("GROQ_API_KEY not set. Copy .env.example to .env.local");
    }
    _client = new Groq({
      apiKey: process.env.GROQ_API_KEY,
      maxRetries: 2,
      timeout: 30_000,
    });
  }
  return _client;
}

// Reset for testing
export function resetClient(): void {
  _client = null;
}
```

## Model Constants

Centralize model IDs so switching dev vs production quality is a one-line
change. `DEV_MODEL` defaults to the 8B instant model to conserve free-tier
quota during tight iteration.

```typescript
// src/groq/models.ts
export const MODELS = {
  FAST: "llama-3.1-8b-instant",         // Dev default: cheapest, fastest
  VERSATILE: "llama-3.3-70b-versatile",  // Production quality
  SPECDEC: "llama-3.3-70b-specdec",      // Speculative decoding variant
  SCOUT: "meta-llama/llama-4-scout-17b-16e-instruct",  // Vision
} as const;

export const DEV_MODEL = MODELS.FAST;  // Use 8B for dev to save quota
```

## Environment Template

Commit `.env.example` (never `.env.local`). The `GROQ_API_KEY` is read
automatically by `new Groq()` / `getGroqClient()`.

```bash
# .env.example
# Get your key at https://console.groq.com/keys
GROQ_API_KEY=gsk_your_key_here

# Optional: override default dev model
GROQ_MODEL=llama-3.1-8b-instant
```
