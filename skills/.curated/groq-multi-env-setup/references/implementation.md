# Groq Multi-Environment Implementation

Full walkthrough of the environment-aware configuration module, the service
wrapper that consumes it, and the verification script. Copy these into your
project and adjust the model names / token budgets to match your workload.

## Step 1: Configuration Module

A single module resolves the correct config for the active `NODE_ENV`, validates
that a key is present (with an environment-specific error message), and
memoizes one Groq client per process.

```typescript
// config/groq.ts
import Groq from "groq-sdk";

interface GroqEnvConfig {
  apiKey: string;
  model: string;
  maxTokens: number;
  temperature: number;
  maxRetries: number;
  timeout: number;
  logRequests: boolean;
}

const configs: Record<string, GroqEnvConfig> = {
  development: {
    apiKey: process.env.GROQ_API_KEY || "",
    model: "llama-3.1-8b-instant",       // Cheapest, fastest for iteration
    maxTokens: 512,
    temperature: 0.7,
    maxRetries: 1,
    timeout: 15_000,
    logRequests: true,                     // Verbose in dev
  },
  staging: {
    apiKey: process.env.GROQ_API_KEY_STAGING || process.env.GROQ_API_KEY || "",
    model: "llama-3.3-70b-versatile",    // Match production model
    maxTokens: 2048,
    temperature: 0.3,
    maxRetries: 3,
    timeout: 30_000,
    logRequests: false,
  },
  production: {
    apiKey: process.env.GROQ_API_KEY_PROD || process.env.GROQ_API_KEY || "",
    model: "llama-3.3-70b-versatile",    // Quality model
    maxTokens: 2048,
    temperature: 0.3,
    maxRetries: 5,                        // More retries in prod
    timeout: 30_000,
    logRequests: false,
  },
};

function getEnv(): string {
  return process.env.NODE_ENV || "development";
}

export function getGroqConfig(): GroqEnvConfig {
  const env = getEnv();
  const config = configs[env] || configs.development;

  if (!config.apiKey) {
    throw new Error(
      `GROQ_API_KEY not set for ${env}. ` +
      (env === "development"
        ? "Copy .env.example to .env.local and add your key from console.groq.com/keys"
        : `Set GROQ_API_KEY_${env.toUpperCase()} in your secret manager`)
    );
  }

  return config;
}

let _client: Groq | null = null;

export function getGroqClient(): Groq {
  if (!_client) {
    const config = getGroqConfig();
    _client = new Groq({
      apiKey: config.apiKey,
      maxRetries: config.maxRetries,
      timeout: config.timeout,
    });
  }
  return _client;
}
```

## Step 2: Environment-Aware Service

The service reads the resolved config once, applies per-environment logging, and
surfaces rate-limit headers on `429` so the caller can back off intelligently.

```typescript
// services/groq-service.ts
import { getGroqClient, getGroqConfig } from "../config/groq";

export async function complete(
  messages: any[],
  options?: { model?: string; maxTokens?: number }
): Promise<string> {
  const groq = getGroqClient();
  const config = getGroqConfig();

  const model = options?.model || config.model;
  const maxTokens = options?.maxTokens || config.maxTokens;

  if (config.logRequests) {
    console.log(`[groq:${model}] ${messages.length} messages, max_tokens=${maxTokens}`);
  }

  try {
    const completion = await groq.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
      temperature: config.temperature,
    });

    if (config.logRequests) {
      const u = completion.usage!;
      console.log(`[groq:${model}] ${u.prompt_tokens}+${u.completion_tokens} tokens, ${((u as any).total_time * 1000).toFixed(0)}ms`);
    }

    return completion.choices[0].message.content || "";
  } catch (err: any) {
    if (err.status === 429) {
      const retryAfter = err.headers?.["retry-after"] || "?";
      console.error(`[groq:${model}] Rate limited. Retry after ${retryAfter}s`);
    }
    throw err;
  }
}
```

## Step 5: Verify Environment Config

Run this against each environment (with the matching `NODE_ENV`) to confirm the
key resolves, the expected model is selected, and a live round-trip succeeds.

```typescript
// scripts/verify-groq-env.ts
import { getGroqConfig, getGroqClient } from "../config/groq";

async function verify() {
  const config = getGroqConfig();
  console.log(`Environment: ${process.env.NODE_ENV || "development"}`);
  console.log(`Model: ${config.model}`);
  console.log(`Max retries: ${config.maxRetries}`);
  console.log(`API key prefix: ${config.apiKey.slice(0, 8)}...`);

  const groq = getGroqClient();
  const start = performance.now();
  const result = await groq.chat.completions.create({
    model: config.model,
    messages: [{ role: "user", content: "Reply: OK" }],
    max_tokens: 5,
    temperature: 0,
  });

  console.log(`Connection: OK (${Math.round(performance.now() - start)}ms)`);
  console.log(`Model response: ${result.choices[0].message.content}`);
}

verify().catch((err) => {
  console.error(`FAILED: ${err.message}`);
  process.exit(1);
});
```
