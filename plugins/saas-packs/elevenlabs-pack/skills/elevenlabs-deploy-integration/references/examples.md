# ElevenLabs Deploy — Worked Examples

Each example is an end-to-end flow: set the secret, ship the code, verify. The
full server/config code these commands deploy lives in
[implementation.md](implementation.md).

## Example 1 — Simple TTS API on Vercel (Flash model)

Best when you have a stateless request/response TTS endpoint and want the
free tier or a quick Pro deploy. Stay under the 30s Pro timeout with the Flash
model.

```bash
# 1. Store the production + preview secret
vercel env add ELEVENLABS_API_KEY production
vercel env add ELEVENLABS_API_KEY preview

# 2. Ship (app/api/tts/route.ts + vercel.json already in the repo)
vercel --prod

# 3. Verify the live endpoint returns audio/mpeg
curl -s -o /tmp/out.mp3 -w '%{content_type}\n' \
  -X POST https://your-app.vercel.app/api/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"Deployment smoke test"}'
# → audio/mpeg
```

## Example 2 — Streaming service on Fly.io (WebSocket / long-running)

Best when you need chunked/streaming audio or persistent connections that a
serverless function can't hold open.

```bash
# 1. Store the prod key and webhook secret
fly secrets set ELEVENLABS_API_KEY=sk_your_prod_key
fly secrets set ELEVENLABS_WEBHOOK_SECRET=whsec_your_secret

# 2. Deploy the container (fly.toml + server.ts)
fly deploy

# 3. Confirm the health check reports quota
curl -s https://my-tts-service.fly.dev/health | jq
# → { "status": "healthy", "quota": { "used": ..., "limit": ... } }

# 4. Tail logs if the stream misbehaves
fly logs
```

## Example 3 — Variable-load service on Cloud Run (scale to zero)

Best for bursty traffic — scales to zero when idle, up to a capped max under
load.

```bash
# 1. Create the secret in Secret Manager
echo -n "sk_your_prod_key" | gcloud secrets create elevenlabs-api-key --data-file=-

# 2. Deploy from source (Dockerfile builds the container)
gcloud run deploy tts-service \
  --source . \
  --region us-central1 \
  --set-secrets=ELEVENLABS_API_KEY=elevenlabs-api-key:latest \
  --timeout=60 --concurrency=10 --min-instances=0 --max-instances=5 \
  --allow-unauthenticated

# 3. Hit the deployed URL printed by the deploy command
curl -s -o /tmp/out.mp3 -w '%{http_code}\n' \
  -X POST "$(gcloud run services describe tts-service --region us-central1 --format='value(status.url)')/api/tts" \
  -H 'Content-Type: application/json' -d '{"text":"hello"}'
# → 200
```

## Choosing between them

| You need... | Deploy to |
|-------------|-----------|
| A simple stateless TTS endpoint, minimal ops | Vercel |
| Streaming / WebSocket / persistent connections | Fly.io |
| Bursty load that should scale to zero when idle | Cloud Run |
