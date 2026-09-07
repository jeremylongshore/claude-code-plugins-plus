# Groq Deploy Integration — Worked Examples

Concrete end-to-end walkthroughs that chain the recipes in
[`implementation.md`](implementation.md). Each example names the platform, the
inputs you supply, and the observable result.

## Example A: Ship a streaming chat endpoint to Vercel Edge

1. Drop the [Step 1 Vercel Edge Function](implementation.md#step-1-vercel-edge-function)
   into `app/api/chat/route.ts`.
2. Register the secret and deploy with the
   [Step 2 commands](implementation.md#step-2-vercel-deployment):

   ```bash
   set -euo pipefail
   vercel env add GROQ_API_KEY production
   vercel --prod
   ```

3. Result: a production URL exposing `POST /api/chat` that streams
   `text/event-stream` chunks when the request body sets `stream: true`, and
   returns a JSON completion otherwise. Sub-200ms first-token latency on
   `llama-3.3-70b-versatile`.

## Example B: Containerize for Cloud Run with a liveness probe

1. Build the image with the
   [Step 3 Dockerfile](implementation.md#step-3-docker-container) — its
   `HEALTHCHECK` polls `/health` every 30s.
2. Serve requests with the
   [Step 5 Express server](implementation.md#step-5-express-server-with-health-check),
   whose `/health` route pings Groq using the cheapest model
   (`llama-3.1-8b-instant`, `max_tokens: 1`) and reports round-trip latency.
3. Deploy with the [Step 4 Cloud Run command](implementation.md#step-4-cloud-run-deployment):

   ```bash
   gcloud run deploy groq-api --source . --region us-central1 \
     --set-secrets=GROQ_API_KEY=groq-api-key:latest \
     --min-instances=1 --timeout=60s
   ```

4. Result: `GET /health` returns `{ status: "healthy", groq: { connected: true,
   latencyMs: N } }` while healthy and HTTP 503 with the error message when Groq
   is unreachable — the exact signal Cloud Run's health check consumes.
   `--min-instances=1` keeps one warm instance so cold-start latency stays off
   the request path.

## Example C: Use the Vercel AI SDK instead of the raw client

When you prefer the Vercel AI SDK's `streamText` abstraction over hand-rolling
the SSE stream, swap Example A's handler for the
[Step 6 AI SDK integration](implementation.md#step-6-vercel-ai-sdk-integration):

```typescript
import { createGroq } from "@ai-sdk/groq";
import { streamText } from "ai";

const groq = createGroq({ apiKey: process.env.GROQ_API_KEY });
// ...streamText({ model: groq("llama-3.3-70b-versatile"), messages })
```

Result: identical streaming behavior, but `result.toDataStreamResponse()`
produces the AI SDK's data-stream protocol that `useChat` on the client consumes
directly — no manual `ReadableStream` plumbing.
