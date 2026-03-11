# Speak Deploy Integration - Implementation Guide

Detailed implementation reference for the speak-deploy-integration skill.

## Vercel Deployment

### Environment Setup
```bash
# Add Speak secrets to Vercel
vercel secrets add speak_api_key sk_live_***
vercel secrets add speak_app_id app_***
vercel secrets add speak_webhook_secret whsec_***

# Link to project
vercel link

# Deploy preview
vercel

# Deploy production
vercel --prod
```

### vercel.json Configuration
```json
{
  "env": {
    "SPEAK_API_KEY": "@speak_api_key",
    "SPEAK_APP_ID": "@speak_app_id"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 60
    },
    "api/speech/**/*.ts": {
      "maxDuration": 120,
      "memory": 1024
    }
  },
  "headers": [
    {
      "source": "/api/speech/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "POST, OPTIONS" }
      ]
    }
  ]
}
```

### Next.js API Routes for Speak
```typescript
// pages/api/speak/session.ts
import { SpeakClient } from '@speak/language-sdk';
import type { NextApiRequest, NextApiResponse } from 'next';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { language, topic, difficulty } = req.body;

    const session = await client.tutor.startSession({
      language,
      topic,
      difficulty,
    });

    res.json({ sessionId: session.id });
  } catch (error) {
    console.error('Speak session error:', error);
    res.status(500).json({ error: 'Failed to start session' });
  }
}
```


## Fly.io Deployment

### fly.toml
```toml
app = "my-speak-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  SPEAK_TARGET_LANGUAGE = "es"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false  # Keep warm for low latency
  auto_start_machines = true
  min_machines_running = 1

[[services.http_checks]]
  interval = 10000
  grace_period = "10s"
  method = "get"
  path = "/health"
  protocol = "http"
  timeout = 2000

# Larger instance for audio processing
[[vm]]
  cpu_kind = "performance"
  cpus = 2
  memory_mb = 2048
```

### Secrets Configuration
```bash
# Set Speak secrets
fly secrets set SPEAK_API_KEY=sk_live_***
fly secrets set SPEAK_APP_ID=app_***
fly secrets set SPEAK_WEBHOOK_SECRET=whsec_***

# Set audio storage (if using external)
fly secrets set AUDIO_STORAGE_URL=https://storage.example.com
fly secrets set AUDIO_ENCRYPTION_KEY=base64_key_here

# Deploy
fly deploy
```

### Volume for Audio Caching
```bash
# Create volume for audio cache
fly volumes create speak_cache --size 10 --region iad

# Update fly.toml
[mounts]
  source = "speak_cache"
  destination = "/app/cache"
```


## Google Cloud Run

### Dockerfile
```dockerfile
FROM node:20-slim

WORKDIR /app

# Install audio dependencies for speech processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsox-fmt-all \
    && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Non-root user for security
USER node

CMD ["npm", "start"]
```

### Deploy Script
```bash
#!/bin/bash
# deploy-cloud-run.sh

PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="speak-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 120 \
  --concurrency 80 \
  --min-instances 1 \
  --set-secrets=SPEAK_API_KEY=speak-api-key:latest,SPEAK_APP_ID=speak-app-id:latest

# Set up Cloud Storage for audio (optional)
gsutil mb -l $REGION gs://$PROJECT_ID-speak-audio
gcloud run services update $SERVICE_NAME \
  --set-env-vars=AUDIO_BUCKET=gs://$PROJECT_ID-speak-audio
```

### Cloud Run with WebSocket Support
```yaml
# cloudrun.yaml (for WebSocket connections needed for real-time speech)
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: speak-service
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/session-affinity: "true"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: gcr.io/PROJECT_ID/speak-service
          ports:
            - name: http1
              containerPort: 3000
          resources:
            limits:
              cpu: "2"
              memory: 2Gi
```


## Environment Configuration Pattern

```typescript
// config/speak.ts
interface SpeakConfig {
  apiKey: string;
  appId: string;
  environment: 'development' | 'staging' | 'production';
  webhookSecret?: string;
  audioStorage?: {
    type: 'local' | 's3' | 'gcs';
    bucket?: string;
  };
}

export function getSpeakConfig(): SpeakConfig {
  const env = process.env.NODE_ENV || 'development';

  return {
    apiKey: process.env.SPEAK_API_KEY!,
    appId: process.env.SPEAK_APP_ID!,
    environment: env as SpeakConfig['environment'],
    webhookSecret: process.env.SPEAK_WEBHOOK_SECRET,
    audioStorage: {
      type: process.env.AUDIO_STORAGE_TYPE as any || 'local',
      bucket: process.env.AUDIO_BUCKET,
    },
  };
}
```


## Health Check Endpoint

```typescript
// api/health.ts
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
});

export async function GET() {
  const start = Date.now();

  try {
    const speakHealth = await client.health.check();

    return Response.json({
      status: speakHealth.healthy ? 'healthy' : 'degraded',
      services: {
        speak: {
          connected: speakHealth.healthy,
          latencyMs: Date.now() - start,
        },
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return Response.json({
      status: 'unhealthy',
      services: {
        speak: {
          connected: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        },
      },
      timestamp: new Date().toISOString(),
    }, { status: 503 });
  }
}
```


## Detailed Examples

### Quick Deploy Script
```bash
#!/bin/bash
# Platform-agnostic deploy helper
case "$1" in
  vercel)
    vercel secrets add speak_api_key "$SPEAK_API_KEY"
    vercel secrets add speak_app_id "$SPEAK_APP_ID"
    vercel --prod
    ;;
  fly)
    fly secrets set SPEAK_API_KEY="$SPEAK_API_KEY"
    fly secrets set SPEAK_APP_ID="$SPEAK_APP_ID"
    fly deploy
    ;;
  cloudrun)
    gcloud run deploy speak-service \
      --set-secrets=SPEAK_API_KEY=speak-api-key:latest
    ;;
esac
```

