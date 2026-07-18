---
name: groq-deploy-integration
description: 'Deploy Groq integrations to Vercel, Cloud Run, and containerized platforms.

  Use when deploying Groq-powered applications to production,

  configuring platform-specific secrets, or setting up deployment pipelines.

  Trigger with phrases like "deploy groq", "groq Vercel",

  "groq production deploy", "groq Cloud Run", "groq Docker".

  '
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- deployment
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Deploy Integration

## Overview

Deploy applications using Groq's inference API to Vercel Edge, Cloud Run, Docker, and other platforms. Groq's sub-200ms latency makes it ideal for edge deployments and real-time applications.

This SKILL.md is the high-level workflow. Every platform recipe — full source for the Vercel Edge Function, Dockerfile, Cloud Run command, Express health-check server, and Vercel AI SDK handler — lives verbatim in [`references/implementation.md`](references/implementation.md). End-to-end walkthroughs that chain those recipes are in [`references/examples.md`](references/examples.md).

## Prerequisites

- Groq API key stored in `GROQ_API_KEY`
- Application using `groq-sdk` (or `@ai-sdk/groq` for the Vercel AI SDK path)
- Platform CLI installed (`vercel`, `docker`, or `gcloud`)

## Instructions

Pick the deployment target, then follow its recipe in [`references/implementation.md`](references/implementation.md).

1. **Write the handler.** For Vercel Edge, create `app/api/chat/route.ts` with `export const runtime = "edge"` and stream Server-Sent Events when the request asks for them; otherwise return a JSON completion. See Step 1 in [`references/implementation.md`](references/implementation.md).
2. **Store the secret.** Never bake `GROQ_API_KEY` into an image. Use the platform's secret store — see the Environment Variable Config table below.
3. **Deploy.** `vercel --prod` for Vercel (Step 2); build the Dockerfile (Step 3) and `gcloud run deploy --source .` for Cloud Run (Step 4) — all in [`references/implementation.md`](references/implementation.md).
4. **Add a health check.** The Express server (Step 5) exposes `/health` that pings Groq with the cheapest model (`llama-3.1-8b-instant`, `max_tokens: 1`) and reports latency, so orchestrators can probe liveness cheaply.
5. **Keep instances warm.** On serverless platforms set `min-instances=1` to keep cold-start latency off the request path.

The essential Vercel Edge skeleton looks like this — the full streaming body is in the reference:

```typescript
// app/api/chat/route.ts
import Groq from "groq-sdk";
export const runtime = "edge";

export async function POST(req: Request) {
  const groq = new Groq({ apiKey: process.env.GROQ_API_KEY! });
  const { messages } = await req.json();
  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages,
    max_tokens: 2048,
  });
  return Response.json(completion);
}
```

## Environment Variable Config

| Platform | Command |
|----------|---------|
| Vercel | `vercel env add GROQ_API_KEY production` |
| Cloud Run | `gcloud secrets create groq-api-key --data-file=-` |
| Fly.io | `fly secrets set GROQ_API_KEY=gsk_...` |
| Railway | `railway variables set GROQ_API_KEY=gsk_...` |
| Docker | `-e GROQ_API_KEY=gsk_...` or Docker secrets |

## Output

Following this skill produces:

- A deployed Groq inference endpoint (`POST /api/chat`) on the chosen platform that streams `text/event-stream` chunks on demand and returns JSON completions otherwise.
- The secret registered in the platform's secret store — never committed to source or an image layer.
- A `/health` liveness endpoint returning `{ status: "healthy", groq: { connected: true, latencyMs: N } }` (HTTP 200) or `{ status: "unhealthy", ... }` (HTTP 503) for orchestrator probes.
- A warm serverless configuration (`min-instances=1`) keeping cold-start latency off the request path.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited (429) | Too many requests | Implement request queuing with backoff |
| Edge timeout | Response > 25s | Use streaming for long completions |
| Model unavailable | Capacity or deprecation | Fall back to `llama-3.1-8b-instant` |
| Cold start latency | Serverless function init | Set `min-instances=1` on Cloud Run |
| API key not found | Secret not configured | Check platform secret config |

## Examples

Full worked walkthroughs live in [`references/examples.md`](references/examples.md):

- **Example A — Vercel Edge streaming chat:** drop in the Step 1 handler, `vercel env add` + `vercel --prod`, get a streaming `POST /api/chat` URL.
- **Example B — Cloud Run with a liveness probe:** Dockerfile `HEALTHCHECK` + Express `/health` + `gcloud run deploy --min-instances=1`, yielding a 200/503 health signal Cloud Run consumes.
- **Example C — Vercel AI SDK path:** swap the raw client for `@ai-sdk/groq` `streamText` + `toDataStreamResponse()` for zero manual stream plumbing.

## Resources

- [Groq API Documentation](https://console.groq.com/docs)
- [Vercel AI SDK + Groq](https://console.groq.com/docs/ai-sdk)
- [Groq Client Libraries](https://console.groq.com/docs/libraries)
- [Full implementation recipes](references/implementation.md)
- [Worked examples](references/examples.md)

## Next Steps

For multi-environment setup (separate dev/staging/prod secrets and pipelines), see the `groq-multi-env-setup` skill in this pack.
