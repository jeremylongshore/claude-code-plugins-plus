# Lokalise Prod Checklist - Implementation Guide

Detailed implementation reference for the lokalise-prod-checklist skill.

## Instructions

### Step 1: Pre-Deployment Configuration
- [ ] Production API token stored in secure vault
- [ ] Token has appropriate permissions (read-only if possible for downloads)
- [ ] Environment variables set in deployment platform
- [ ] Webhook endpoints configured with HTTPS
- [ ] Webhook secrets stored securely

### Step 2: Code Quality Verification
- [ ] All tests passing (`npm test`)
- [ ] No hardcoded API tokens or secrets
- [ ] Error handling covers all Lokalise error types (401, 403, 404, 429, 5xx)
- [ ] Rate limiting implemented (6 req/sec)
- [ ] Logging is production-appropriate (no PII, no tokens)
- [ ] TypeScript types are up to date

### Step 3: Translation Quality
- [ ] All base language strings present
- [ ] Critical languages fully translated
- [ ] No missing translations for essential UI
- [ ] Placeholder syntax validated (ICU format)
- [ ] No HTML/script injection in translations

### Step 4: Infrastructure Setup
- [ ] Health check endpoint includes Lokalise connectivity
- [ ] Monitoring/alerting configured for API errors
- [ ] Circuit breaker pattern implemented
- [ ] Graceful degradation for translation failures
- [ ] CDN caching for downloaded translations (if applicable)

### Step 5: Documentation Requirements
- [ ] Incident runbook created
- [ ] Token rotation procedure documented
- [ ] Rollback procedure documented
- [ ] On-call escalation path defined

### Step 6: Deploy with Verification
```bash
#!/bin/bash
# deploy-with-verification.sh

set -e

echo "=== Lokalise Production Deployment ==="

# Pre-flight checks
echo "1. Checking Lokalise API status..."
STATUS=$(curl -s https://api.lokalise.com/api2/system/health | jq -r '.status // "unknown"')
if [ "$STATUS" != "ok" ]; then
  echo "ERROR: Lokalise API not healthy. Aborting."
  exit 1
fi

echo "2. Verifying API token..."
TOKEN_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=1")
if [ "$TOKEN_CHECK" != "200" ]; then
  echo "ERROR: API token invalid (HTTP $TOKEN_CHECK). Aborting."
  exit 1
fi

echo "3. Downloading fresh translations..."
npm run i18n:pull

echo "4. Building application..."
npm run build

echo "5. Running post-build tests..."
npm run test:e2e

echo "6. Deploying..."
# Your deployment command here
# vercel --prod / fly deploy / gcloud run deploy

echo "7. Verifying deployment..."
HEALTH=$(curl -s https://your-app.com/api/health | jq -r '.services.translations')
if [ "$HEALTH" != "healthy" ]; then
  echo "WARNING: Translation service health check failed"
fi

echo "=== Deployment Complete ==="
```


## Detailed Examples

### Health Check Implementation
```typescript
interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  translations: {
    connected: boolean;
    latencyMs: number;
    lastSync?: string;
  };
}

async function checkTranslationHealth(): Promise<HealthStatus> {
  const start = Date.now();

  try {
    const client = new LokaliseApi({
      apiKey: process.env.LOKALISE_API_TOKEN!,
    });

    // Quick connectivity check
    await client.projects().list({ limit: 1 });

    return {
      status: "healthy",
      translations: {
        connected: true,
        latencyMs: Date.now() - start,
        lastSync: process.env.TRANSLATIONS_LAST_SYNC,
      },
    };
  } catch (error) {
    return {
      status: "degraded",
      translations: {
        connected: false,
        latencyMs: Date.now() - start,
      },
    };
  }
}

// Express health endpoint
app.get("/health", async (req, res) => {
  const health = await checkTranslationHealth();
  const statusCode = health.status === "healthy" ? 200 : 503;
  res.status(statusCode).json(health);
});
```

### Graceful Degradation
```typescript
import en from "./locales/en.json";  // Bundled fallback

async function getTranslations(locale: string): Promise<Record<string, string>> {
  try {
    // Try to load from Lokalise/CDN
    const response = await fetch(`/locales/${locale}.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  } catch (error) {
    console.warn(`Failed to load ${locale}, falling back to English`);
    return en;
  }
}
```

### Rollback Procedure
```bash
#!/bin/bash
# rollback-translations.sh

# Option 1: Revert to previous Git commit translations
git checkout HEAD~1 -- src/locales/

# Option 2: Download specific snapshot from Lokalise
lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file download \
  --format json \
  --filter-data reviewed \
  --unzip-to ./src/locales

# Rebuild and redeploy
npm run build
npm run deploy
```

### Pre-Production Validation Script
```typescript
async function validateProductionReadiness(): Promise<{
  ready: boolean;
  issues: string[];
}> {
  const issues: string[] = [];

  // Check environment
  if (!process.env.LOKALISE_API_TOKEN) {
    issues.push("LOKALISE_API_TOKEN not set");
  }
  if (!process.env.LOKALISE_PROJECT_ID) {
    issues.push("LOKALISE_PROJECT_ID not set");
  }

  // Check translations exist
  const localeDir = "./src/locales";
  const requiredLocales = ["en", "es", "fr", "de"];
  for (const locale of requiredLocales) {
    const path = `${localeDir}/${locale}.json`;
    if (!fs.existsSync(path)) {
      issues.push(`Missing locale file: ${locale}.json`);
    }
  }

  // Check for missing translations in non-base languages
  const baseTranslations = JSON.parse(
    fs.readFileSync(`${localeDir}/en.json`, "utf8")
  );
  const baseKeys = Object.keys(flattenObject(baseTranslations));

  for (const locale of requiredLocales.filter(l => l !== "en")) {
    const translations = JSON.parse(
      fs.readFileSync(`${localeDir}/${locale}.json`, "utf8")
    );
    const localeKeys = Object.keys(flattenObject(translations));
    const missingKeys = baseKeys.filter(k => !localeKeys.includes(k));

    if (missingKeys.length > 0) {
      issues.push(`${locale}: ${missingKeys.length} missing translations`);
    }
  }

  return {
    ready: issues.length === 0,
    issues,
  };
}
```

