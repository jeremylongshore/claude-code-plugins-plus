# Intercom Deploy — Full Implementation

Complete, copy-ready code for each deployment target. Each section is self-contained:
provision secrets, deploy, then verify. Pick the platform that matches your stack; the
webhook handler and health-check code are shared across all three.

## Vercel Deployment

### Provision secrets and deploy

```bash
# Add Intercom secrets to Vercel
vercel env add INTERCOM_ACCESS_TOKEN production
vercel env add INTERCOM_WEBHOOK_SECRET production

# Deploy to production
vercel --prod
```

### API Route for Webhooks (Vercel Serverless)

Serverless functions must read the raw body to verify the signature, so `bodyParser`
is disabled. Compare signatures with `crypto.timingSafeEqual` to avoid timing leaks,
and always return within 5 seconds — queue anything slower.

```typescript
// api/webhooks/intercom.ts (Vercel serverless function)
import crypto from "crypto";

export const config = { api: { bodyParser: false } };

export default async function handler(req: any, res: any) {
  if (req.method !== "POST") return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const body = Buffer.concat(chunks);

  // Verify signature
  const signature = req.headers["x-hub-signature"] as string;
  const expected = "sha1=" + crypto
    .createHmac("sha1", process.env.INTERCOM_WEBHOOK_SECRET!)
    .update(body)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature || ""), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const event = JSON.parse(body.toString());
  console.log(`Intercom webhook: ${event.topic}`);

  // Process within 5s (Intercom timeout)
  // For long processing, queue the event and return immediately
  res.status(200).json({ received: true });
}
```

### vercel.json

```json
{
  "functions": {
    "api/webhooks/intercom.ts": {
      "maxDuration": 10
    }
  }
}
```

## Fly.io Deployment

Keep machines from auto-stopping so webhook deliveries always land, and expose a
`/health` check so Fly restarts an unhealthy instance.

```toml
# fly.toml
app = "my-intercom-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false   # Keep running for webhooks
  auto_start_machines = true

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

```bash
# Set secrets
fly secrets set INTERCOM_ACCESS_TOKEN="dG9rOi4uLg=="
fly secrets set INTERCOM_WEBHOOK_SECRET="your-secret"

# Deploy
fly deploy

# Verify health
fly status
curl https://my-intercom-app.fly.dev/health
```

## Google Cloud Run

Store both secrets in Secret Manager and mount them at deploy time. `--min-instances=1`
avoids cold-start webhook timeouts.

```bash
#!/bin/bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="intercom-service"
REGION="us-central1"

# Store secrets in Secret Manager
echo -n "$INTERCOM_ACCESS_TOKEN" | \
  gcloud secrets create intercom-token --data-file=- --replication-policy=automatic
echo -n "$INTERCOM_WEBHOOK_SECRET" | \
  gcloud secrets create intercom-webhook-secret --data-file=- --replication-policy=automatic

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="INTERCOM_ACCESS_TOKEN=intercom-token:latest,INTERCOM_WEBHOOK_SECRET=intercom-webhook-secret:latest" \
  --min-instances=1 \
  --timeout=60
```

## Health Check Endpoint (shared)

A liveness probe that actually exercises the Intercom API — it reports `degraded`
(not a hard failure) when the token is invalid, so the platform can surface the problem
without flapping the whole service.

```typescript
// src/routes/health.ts
import { IntercomClient, IntercomError } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

export async function healthCheck(): Promise<{
  status: string;
  services: { intercom: { connected: boolean; latencyMs: number; error?: string } };
}> {
  const start = Date.now();
  try {
    await client.admins.list();
    return {
      status: "healthy",
      services: {
        intercom: { connected: true, latencyMs: Date.now() - start },
      },
    };
  } catch (err) {
    const latencyMs = Date.now() - start;
    const error = err instanceof IntercomError
      ? `${err.statusCode}: ${err.message}`
      : (err as Error).message;
    return {
      status: "degraded",
      services: {
        intercom: { connected: false, latencyMs, error },
      },
    };
  }
}
```

## Register the Webhook URL

After deploying, configure the webhook URL in Intercom:

1. Go to Developer Hub > Webhooks
2. Set endpoint URL: `https://your-domain.com/api/webhooks/intercom`
3. Select topics: `conversation.user.created`, `contact.created`, etc.
4. Copy the webhook signing secret to your platform secrets
5. Send a test notification to verify
