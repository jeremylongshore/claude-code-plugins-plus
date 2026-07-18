---
name: elevenlabs-deploy-integration
description: |
  Deploy ElevenLabs TTS applications to Vercel, Fly.io, and Cloud Run.
  Use when deploying ElevenLabs-powered apps to production, configuring
  platform-specific secrets, or setting up serverless TTS.
  Trigger with "deploy elevenlabs", "elevenlabs Vercel", "elevenlabs Cloud Run",
  "elevenlabs Fly.io", "elevenlabs serverless", "host TTS API".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- deployment
- serverless
compatibility: Designed for Claude Code
---
# ElevenLabs Deploy Integration

## Overview

Deploy ElevenLabs TTS/voice applications to Vercel (serverless), Fly.io
(containers), or Google Cloud Run with proper secrets management, timeout
configuration, and streaming support. Pick the platform that matches your
traffic shape, write the platform config + server code, store the API key as a
platform secret, then deploy and smoke-test the live endpoint.

## Prerequisites

- ElevenLabs API key for production
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)
- Application code tested locally

## Instructions

Follow these steps. The lean skeleton is below; the full config files and
server code for each platform are in
[references/implementation.md](references/implementation.md).

1. **Inspect the repo and pick a platform.** `Read` the existing app code and
   any current deploy config, then choose from the comparison table below —
   Vercel for a simple stateless TTS API, Fly.io for streaming/WebSocket, Cloud
   Run for bursty variable load.
2. **Write the platform config + server code.** Use `Write`/`Edit` to create
   the platform files in the repo — `vercel.json` + the API route for Vercel,
   `fly.toml` + Express server for Fly.io, `Dockerfile` for Cloud Run. Full
   versions are in [references/implementation.md](references/implementation.md).
3. **Set the API key as a platform secret** (never commit it):

   ```bash
   vercel env add ELEVENLABS_API_KEY production   # Vercel
   fly secrets set ELEVENLABS_API_KEY=sk_...       # Fly.io
   echo -n "sk_..." | gcloud secrets create elevenlabs-api-key --data-file=-  # Cloud Run
   ```

4. **Mind the timeout.** Vercel Hobby caps functions at 10s (30s on Pro) — use
   the `eleven_flash_v2_5` model to stay under it. Fly.io and Cloud Run have no
   such short cap.
5. **Deploy**, then smoke-test the live endpoint (see
   [references/examples.md](references/examples.md)):

   ```bash
   vercel --prod        # Vercel
   fly deploy           # Fly.io
   gcloud run deploy tts-service --source .   # Cloud Run (see full flags in implementation.md)
   ```

## Platform Comparison for ElevenLabs

| Feature | Vercel | Fly.io | Cloud Run |
|---------|--------|--------|-----------|
| Max timeout | 30s (Pro) | No limit | 60min |
| WebSocket streaming | Limited | Full support | Full support |
| Cold start | ~1-3s | ~0.5-2s | ~1-5s |
| Concurrency | Per-function | Per-VM | Per-instance |
| Best for | Simple TTS API | Streaming/WebSocket | Variable load |
| Min cost | Free tier | ~$2/mo | Free tier |

## Output

A working deployment of a validated TTS build produces:

- A live TTS endpoint returning `audio/mpeg` (Vercel/Fly.io/Cloud Run URL)
- `ELEVENLABS_API_KEY` (and any webhook secret) stored as a platform secret,
  never in the repo
- Platform config committed to the repo — `vercel.json`, `fly.toml`, or
  `Dockerfile` — matching the chosen platform's timeout/concurrency limits
- A `/health` endpoint (Fly.io/Cloud Run) reporting live quota via the SDK

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Vercel timeout | TTS > 10s on Hobby | Upgrade to Pro (30s) or use Flash model |
| Cold start slow | Container initialization | Set `min_instances=1` (Cloud Run) or `min_machines=1` (Fly) |
| Secret not found | Missing platform config | Add via platform CLI |
| Streaming broken | Proxy buffering | Disable response buffering in nginx/CDN |
| CORS errors | Missing headers | Add `Access-Control-Allow-Origin` to TTS endpoint |

## Examples

**Deploy a simple TTS API to Vercel** (Flash model, under the Pro timeout):

```bash
vercel env add ELEVENLABS_API_KEY production
vercel --prod
```

**Deploy a streaming service to Fly.io** and confirm quota via the health check:

```bash
fly secrets set ELEVENLABS_API_KEY=sk_your_prod_key
fly deploy
curl -s https://my-tts-service.fly.dev/health | jq
```

Full end-to-end flows for all three platforms — secret setup, deploy, and live
smoke-test — are in [references/examples.md](references/examples.md).

## Resources

- [references/implementation.md](references/implementation.md) — complete config files + server code per platform
- [references/examples.md](references/examples.md) — end-to-end deploy + smoke-test flows for Vercel, Fly.io, Cloud Run
- [Vercel Functions](https://vercel.com/docs/functions)
- [Fly.io Node.js](https://fly.io/docs/languages-and-frameworks/node/)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [ElevenLabs API Quickstart](https://elevenlabs.io/docs/eleven-api/quickstart)

## Next Steps

For webhook handling on a deployed service, see the `elevenlabs-webhooks-events`
skill, which covers verifying signatures and handling ElevenLabs event
callbacks against the endpoints you just shipped.
