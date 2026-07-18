# Klaviyo Platform Deployment Walkthroughs

Full, copy-pasteable deployment recipes for each supported platform. The
`SKILL.md` carries the lean skeleton; this file carries every command,
config file, and code block verbatim.

## Vercel Deployment

```bash
# 1. Add secrets to Vercel project
vercel env add KLAVIYO_PRIVATE_KEY production
# Paste your pk_*** key when prompted

vercel env add KLAVIYO_WEBHOOK_SIGNING_SECRET production
# Paste your whsec_*** secret

# 2. Configure vercel.json
```

```json
{
  "env": {
    "KLAVIYO_PRIVATE_KEY": "@klaviyo_private_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  },
  "rewrites": [
    { "source": "/webhooks/klaviyo", "destination": "/api/webhooks/klaviyo" }
  ]
}
```

```bash
# 3. Deploy
vercel --prod

# 4. Verify health
curl -s https://your-app.vercel.app/api/health | jq '.services.klaviyo'
```

### Vercel Webhook Handler (Edge-compatible)

```typescript
// api/webhooks/klaviyo.ts (Vercel serverless function)
import crypto from 'crypto';

export const config = { api: { bodyParser: false } };

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const body = Buffer.concat(chunks);

  // Verify HMAC-SHA256 signature
  const signature = req.headers['klaviyo-webhook-signature'];
  const expected = crypto
    .createHmac('sha256', process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET!)
    .update(body)
    .digest('base64');

  if (!crypto.timingSafeEqual(Buffer.from(signature || ''), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(body.toString());
  // Process event...
  console.log('Klaviyo webhook:', event.type);

  res.status(200).json({ received: true });
}
```

## Fly.io Deployment

```toml
# fly.toml
app = "my-klaviyo-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[[services.http_checks]]
  interval = 30000
  timeout = 5000
  path = "/health"
  method = "GET"
```

```bash
# 1. Set secrets
fly secrets set KLAVIYO_PRIVATE_KEY=pk_***
fly secrets set KLAVIYO_WEBHOOK_SIGNING_SECRET=whsec_***

# 2. Deploy
fly deploy

# 3. Verify
fly status
curl -s https://my-klaviyo-app.fly.dev/health | jq
```

## Google Cloud Run Deployment

```dockerfile
# Dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json .
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
# 1. Store secret in GCP Secret Manager
echo -n "pk_***" | gcloud secrets create klaviyo-private-key --data-file=-
echo -n "whsec_***" | gcloud secrets create klaviyo-webhook-secret --data-file=-

# 2. Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding klaviyo-private-key \
  --member="serviceAccount:YOUR_SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Deploy to Cloud Run
gcloud run deploy klaviyo-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=KLAVIYO_PRIVATE_KEY=klaviyo-private-key:latest,KLAVIYO_WEBHOOK_SIGNING_SECRET=klaviyo-webhook-secret:latest \
  --min-instances=1 \
  --max-instances=10

# 4. Verify
gcloud run services describe klaviyo-service --region=us-central1 --format="value(status.url)"
```

## Universal Health Check

Works identically on all three platforms — expose it at the path each
platform's health check probes (`/api/health` on Vercel, `/health` on
Fly.io and Cloud Run).

```typescript
// src/health.ts -- works on all platforms
import { ApiKeySession, AccountsApi } from 'klaviyo-api';

export async function healthCheck(): Promise<{
  status: string;
  services: { klaviyo: { connected: boolean; latencyMs: number } };
}> {
  const start = Date.now();
  try {
    const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
    const api = new AccountsApi(session);
    await api.getAccounts();
    return {
      status: 'healthy',
      services: { klaviyo: { connected: true, latencyMs: Date.now() - start } },
    };
  } catch {
    return {
      status: 'degraded',
      services: { klaviyo: { connected: false, latencyMs: Date.now() - start } },
    };
  }
}
```
