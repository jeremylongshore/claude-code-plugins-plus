# Lokalise Deploy Integration - Implementation Guide

Detailed implementation reference for the lokalise-deploy-integration skill.

## Vercel Deployment

### Environment Setup
```bash
# Add Lokalise secrets to Vercel
vercel env add LOKALISE_API_TOKEN production
vercel env add LOKALISE_PROJECT_ID production

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
  "build": {
    "env": {
      "LOKALISE_API_TOKEN": "@lokalise_api_token",
      "LOKALISE_PROJECT_ID": "@lokalise_project_id"
    }
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

### Pre-build Translation Sync
```json
// package.json
{
  "scripts": {
    "prebuild": "npm run i18n:pull",
    "build": "next build",
    "i18n:pull": "lokalise2 file download --token $LOKALISE_API_TOKEN --project-id $LOKALISE_PROJECT_ID --format json --unzip-to ./public/locales"
  }
}
```


## Netlify Deployment

### netlify.toml
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "20"

[[plugins]]
  package = "./plugins/lokalise-sync"

[context.production.environment]
  LOKALISE_ENV = "production"
```

### Netlify Build Plugin
```javascript
// plugins/lokalise-sync/index.js
module.exports = {
  onPreBuild: async ({ utils }) => {
    try {
      const { execSync } = require("child_process");

      console.log("Downloading translations from Lokalise...");

      execSync(`
        curl -sL https://github.com/lokalise/lokalise-cli-2-go/releases/latest/download/lokalise2_linux_x86_64.tar.gz | tar xz
        ./lokalise2 file download \
          --token "$LOKALISE_API_TOKEN" \
          --project-id "$LOKALISE_PROJECT_ID" \
          --format json \
          --unzip-to ./src/locales
      `, { stdio: "inherit" });

      console.log("Translations downloaded successfully!");
    } catch (error) {
      utils.build.failBuild("Failed to download translations", { error });
    }
  },
};
```

### Netlify Environment Variables
```bash
# Using Netlify CLI
netlify env:set LOKALISE_API_TOKEN "your-token"
netlify env:set LOKALISE_PROJECT_ID "123456.abcdef"

# Deploy
netlify deploy --prod
```


## Google Cloud Run

### Dockerfile
```dockerfile
FROM node:20-slim AS builder

WORKDIR /app

# Install Lokalise CLI
RUN apt-get update && apt-get install -y curl && \
    curl -sL https://github.com/lokalise/lokalise-cli-2-go/releases/latest/download/lokalise2_linux_x86_64.tar.gz | tar xz && \
    mv lokalise2 /usr/local/bin/

COPY package*.json ./
RUN npm ci

# Download translations at build time
ARG LOKALISE_API_TOKEN
ARG LOKALISE_PROJECT_ID
RUN lokalise2 file download \
    --token "$LOKALISE_API_TOKEN" \
    --project-id "$LOKALISE_PROJECT_ID" \
    --format json \
    --unzip-to ./src/locales

COPY . .
RUN npm run build

# Production image
FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

CMD ["node", "dist/index.js"]
```

### Cloud Run Deployment
```bash
#!/bin/bash
# deploy-cloud-run.sh

PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="my-app"
REGION="us-central1"

# Build with Lokalise token as build arg
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --build-arg LOKALISE_API_TOKEN="$LOKALISE_API_TOKEN" \
  --build-arg LOKALISE_PROJECT_ID="$LOKALISE_PROJECT_ID"

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated
```


## OTA (Over-the-Air) Updates for Mobile

### Setup OTA in Lokalise
```typescript
// Initialize OTA SDK for React Native
import { LokaliseOta } from "@lokalise/react-native-ota";

const ota = new LokaliseOta({
  projectId: process.env.LOKALISE_PROJECT_ID!,
  token: process.env.LOKALISE_OTA_TOKEN!,  // OTA-specific token
  preloadLanguages: ["en", "es", "fr"],
});

// Check for updates on app start
async function initTranslations() {
  try {
    const updated = await ota.checkForUpdates();
    if (updated) {
      console.log("Translations updated!");
    }
  } catch (error) {
    console.warn("OTA update failed, using bundled translations");
  }
}
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const health = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    services: {
      translations: await checkTranslations(),
    },
  };

  const statusCode = health.services.translations.ok ? 200 : 503;
  return Response.json(health, { status: statusCode });
}

async function checkTranslations() {
  try {
    const locales = ["en", "es", "fr"];
    for (const locale of locales) {
      const path = `./public/locales/${locale}.json`;
      if (!fs.existsSync(path)) {
        return { ok: false, error: `Missing ${locale}.json` };
      }
    }
    return { ok: true, locales };
  } catch (error) {
    return { ok: false, error: error.message };
  }
}
```


## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs.

### Step 2: Configure Secrets
Store Lokalise API token securely using the platform's secrets management.

### Step 3: Set Up Pre-build Sync
Configure translation download before build step.

### Step 4: Deploy and Verify
Deploy application and verify translations are included.


## Detailed Examples

### Quick Deploy Script
```bash
#!/bin/bash
# Platform-agnostic deploy helper

set -e

# Ensure translations are fresh
npm run i18n:pull

# Build
npm run build

# Deploy based on platform
case "${DEPLOY_PLATFORM:-vercel}" in
  vercel)
    vercel --prod
    ;;
  netlify)
    netlify deploy --prod
    ;;
  cloudrun)
    ./scripts/deploy-cloud-run.sh
    ;;
esac
```

### CDN-Cached Translations
```typescript
// Load translations from CDN with cache
const CACHE_TTL = 3600;  // 1 hour

async function loadTranslations(locale: string) {
  const cdnUrl = `https://cdn.example.com/locales/${locale}.json`;

  const response = await fetch(cdnUrl, {
    next: { revalidate: CACHE_TTL },
  });

  if (!response.ok) {
    // Fall back to bundled translations
    return import(`./locales/${locale}.json`);
  }

  return response.json();
}
```

