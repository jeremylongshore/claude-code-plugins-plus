# Groq SDK — Differences from OpenAI & Error-Handling Matrix

The Groq SDK mirrors the OpenAI SDK interface, but a handful of details differ. Account for them when porting OpenAI code or setting team standards.

## Key SDK Differences from OpenAI

| Feature | OpenAI SDK | Groq SDK |
|---------|-----------|----------|
| Package name | `openai` | `groq-sdk` |
| Import | `import OpenAI from "openai"` | `import Groq from "groq-sdk"` |
| Base URL | `api.openai.com/v1` | `api.groq.com/openai/v1` |
| Response `usage` | Standard fields | Adds `queue_time`, `prompt_time`, `completion_time`, `total_time` |
| Error types | `OpenAI.APIError` | `Groq.APIError`, `Groq.APIConnectionError` |

## Error-Handling Pattern Matrix

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeComplete` wrapper | All API calls | Prevents uncaught exceptions |
| `withRetry` | Rate-limited calls | Respects `retry-after` header |
| Typed error checking | `instanceof Groq.APIError` | Handles each status code specifically |
| Client singleton | App-wide usage | Single connection pool, consistent config |
