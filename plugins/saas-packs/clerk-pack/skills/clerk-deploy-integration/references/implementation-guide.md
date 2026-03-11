# Clerk Deploy Integration - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Platform 1: Vercel Deployment

#### Step 1: Configure Environment Variables
```bash
# Using Vercel CLI
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
vercel env add CLERK_SECRET_KEY production
vercel env add CLERK_WEBHOOK_SECRET production

# Or in vercel.json
```

```json
// vercel.json
{
  "env": {
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": "@clerk-publishable-key",
    "CLERK_SECRET_KEY": "@clerk-secret-key"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }
  ]
}
```

#### Step 2: Configure Clerk Dashboard
1. Add Vercel domain to allowed origins
2. Set production URLs in Clerk Dashboard
3. Configure webhook endpoint

#### Step 3: Deploy
```bash
# Deploy to production
vercel --prod

# Or link to Git for auto-deploy
vercel link
```

### Platform 2: Netlify Deployment

#### Step 1: Configure Environment Variables
```bash
# netlify.toml
[build]
  command = "npm run build"
  publish = ".next"

[build.environment]
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_live_..."

# Add secret in Netlify Dashboard
# Site settings > Environment variables > CLERK_SECRET_KEY
```

#### Step 2: Create Netlify Functions for API
```typescript
// netlify/functions/clerk-webhook.ts
import { Handler } from '@netlify/functions'
import { Webhook } from 'svix'

export const handler: Handler = async (event) => {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET!

  const svix_id = event.headers['svix-id']
  const svix_timestamp = event.headers['svix-timestamp']
  const svix_signature = event.headers['svix-signature']

  const wh = new Webhook(WEBHOOK_SECRET)

  try {
    const evt = wh.verify(event.body!, {
      'svix-id': svix_id!,
      'svix-timestamp': svix_timestamp!,
      'svix-signature': svix_signature!
    })

    // Process event
    return { statusCode: 200, body: JSON.stringify({ success: true }) }
  } catch (err) {
    return { statusCode: 400, body: 'Invalid signature' }
  }
}
```

### Platform 3: Railway Deployment

#### Step 1: Configure Railway
```bash
# railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "npm start",
    "healthcheckPath": "/api/health"
  }
}
```

#### Step 2: Set Environment Variables
```bash
# Using Railway CLI
railway variables set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
railway variables set CLERK_SECRET_KEY=sk_live_...
railway variables set CLERK_WEBHOOK_SECRET=whsec_...
```

### Platform 4: Docker Deployment

#### Dockerfile
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build-time args for NEXT_PUBLIC_ vars
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Runtime env vars
ENV CLERK_SECRET_KEY=""
ENV PORT=3000

EXPOSE 3000

CMD ["node", "server.js"]
```

```bash
# Build and run
docker build \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_... \
  -t myapp .

docker run -p 3000:3000 \
  -e CLERK_SECRET_KEY=sk_live_... \
  myapp
```

### Platform 5: AWS Amplify

```yaml
# amplify.yml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

## Clerk Dashboard Configuration

### Production Domain Setup
1. Go to Clerk Dashboard > Configure > Domains
2. Add your production domain
3. Configure SSL (automatic with most platforms)

### Webhook Configuration
1. Go to Clerk Dashboard > Webhooks
2. Add endpoint: `https://yourdomain.com/api/webhooks/clerk`
3. Select events to subscribe
4. Copy webhook secret to environment

### OAuth Redirect URLs
1. Update OAuth providers with production URLs
2. Add `https://yourdomain.com/sso-callback`
3. Remove development URLs for security

## Deployment Checklist

- [ ] Production Clerk keys configured
- [ ] Domain added to Clerk Dashboard
- [ ] Webhook endpoint configured
- [ ] OAuth redirect URLs updated
- [ ] SSL/HTTPS enabled
- [ ] Security headers configured
- [ ] Health check endpoint working

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 500 on sign-in | Missing secret key | Add CLERK_SECRET_KEY to platform |
| Webhook fails | Wrong endpoint URL | Update URL in Clerk Dashboard |
| CORS error | Domain not allowed | Add domain to Clerk allowed origins |
| Redirect loop | Wrong sign-in URL | Check CLERK_SIGN_IN_URL config |
