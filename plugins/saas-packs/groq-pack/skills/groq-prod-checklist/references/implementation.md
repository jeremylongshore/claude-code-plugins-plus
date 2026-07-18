# Groq Production Implementation Patterns

Copy-paste-ready TypeScript patterns for the fallback and health-check items
on the pre-deployment checklist. Each is referenced from the lean workflow in
`SKILL.md`.

## Fallback & Graceful Degradation

Primary model with automatic fallback to a faster model on 429/5xx, then a
graceful static response if Groq is fully unavailable. Wire this into any
completion path that must never hard-fail for the user.

```typescript
async function completionWithFallback(messages: any[]) {
  try {
    return await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages,
      timeout: 15_000,
    });
  } catch (err: any) {
    if (err.status === 429 || err.status >= 500) {
      console.warn("Groq primary failed, trying fallback model");
      try {
        return await groq.chat.completions.create({
          model: "llama-3.1-8b-instant",
          messages,
          timeout: 10_000,
        });
      } catch {
        console.error("Groq fully unavailable, degrading gracefully");
        return { choices: [{ message: { content: "Service temporarily unavailable. Please try again." } }] };
      }
    }
    throw err;
  }
}
```

## Health Check Endpoint

Exposes a `/api/health` (or `/healthz`) route that probes Groq with a 1-token
request and reports connection status plus latency. Returns `503` when
degraded so load balancers and uptime monitors can react.

```typescript
// /api/health or /healthz
export async function GET() {
  const checks: Record<string, any> = { status: "healthy" };
  const start = performance.now();

  try {
    await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "OK" }],
      max_tokens: 1,
      temperature: 0,
    });
    checks.groq = { status: "connected", latencyMs: Math.round(performance.now() - start) };
  } catch (err: any) {
    checks.status = "degraded";
    checks.groq = { status: "error", error: err.status || err.message };
  }

  return Response.json(checks, { status: checks.status === "healthy" ? 200 : 503 });
}
```
