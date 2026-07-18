# Intercom Deploy — Worked Examples

Three end-to-end walkthroughs, one per platform. Each assumes an app with an Intercom
integration ready to ship and the corresponding platform CLI authenticated.

## Example 1: Ship a Next.js app to Vercel

```bash
# 1. Add production secrets
vercel env add INTERCOM_ACCESS_TOKEN production   # paste token when prompted
vercel env add INTERCOM_WEBHOOK_SECRET production  # paste signing secret

# 2. Deploy
vercel --prod
# → https://my-intercom-app.vercel.app

# 3. Register the webhook in Developer Hub > Webhooks
#    Endpoint: https://my-intercom-app.vercel.app/api/webhooks/intercom
#    Topics:   conversation.user.created, contact.created

# 4. Send a test notification from Developer Hub, then confirm the log line:
#    "Intercom webhook: conversation.user.created"
```

Expected result: the test notification returns `200 { "received": true }` and the
serverless log shows the topic. A `401 Invalid signature` means `INTERCOM_WEBHOOK_SECRET`
does not match the Developer Hub value.

## Example 2: Ship a long-running Node service to Fly.io

```bash
# 1. Set secrets (survives redeploys, injected as env at boot)
fly secrets set INTERCOM_ACCESS_TOKEN="dG9rOi4uLg=="
fly secrets set INTERCOM_WEBHOOK_SECRET="whsec_..."

# 2. Deploy (uses fly.toml with auto_stop_machines = false)
fly deploy

# 3. Verify the health probe wired to /health
fly status
curl https://my-intercom-app.fly.dev/health
# → {"status":"healthy","services":{"intercom":{"connected":true,"latencyMs":142}}}
```

Expected result: `fly status` shows the machine `passing` its health check. A
`"status":"degraded"` body with a `401` error string means the production token is
invalid — re-run `fly secrets set INTERCOM_ACCESS_TOKEN`.

## Example 3: Ship a container to Google Cloud Run

```bash
export GOOGLE_CLOUD_PROJECT="my-project"
export INTERCOM_ACCESS_TOKEN="dG9rOi4uLg=="
export INTERCOM_WEBHOOK_SECRET="whsec_..."

# Run the deploy script from references/implementation.md § Google Cloud Run
./deploy-cloudrun.sh
# → Service [intercom-service] revision deployed
#   Service URL: https://intercom-service-xxxx.a.run.app

# Register that URL + /api/webhooks/intercom in Developer Hub, then test.
```

Expected result: `gcloud run deploy` prints the service URL and the revision serves the
health check. `Secret not found` on redeploy means the secret already exists — use
`gcloud secrets versions add intercom-token --data-file=-` instead of `create`.
