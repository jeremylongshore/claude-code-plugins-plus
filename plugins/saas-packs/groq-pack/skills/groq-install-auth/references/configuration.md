# Groq SDK Configuration Reference

## SDK Defaults

The Groq SDK auto-reads `GROQ_API_KEY` from environment if no `apiKey` is passed to the constructor. Additional constructor options:

```typescript
const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,  // Optional if env var set
  baseURL: "https://api.groq.com/openai/v1",  // Default
  maxRetries: 2,      // Default retry count
  timeout: 60_000,    // 60 second timeout (ms)
});
```

Because the base URL is OpenAI-compatible (`api.groq.com/openai/v1/`), you can
also point the official OpenAI SDK at Groq by overriding its `baseURL` and
passing your `gsk_` key — useful when migrating an existing OpenAI codebase.

## API Key Formats

| Prefix | Type | Usage |
|--------|------|-------|
| `gsk_` | Standard API key | All API endpoints |

Groq uses a single key type. There are no separate read/write scopes -- all keys have full API access. Restrict access through organizational controls in the console.

## .gitignore Template

Add these before you ever write a `.env` file, so a key can never be committed:

```
# Groq secrets
.env
.env.local
.env.*.local
```
