---
name: lokalise-incident-runbook
description: |
  Execute Lokalise incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Lokalise-related outages, investigating errors,
  or running post-incident reviews for Lokalise integration failures.
  Trigger with phrases like "lokalise incident", "lokalise outage",
  "lokalise down", "lokalise on-call", "lokalise emergency", "translations broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(lokalise2:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Incident Runbook

## Overview

Rapid-response procedures for Lokalise-related incidents in production. Covers quick diagnostics (API health, token validity, rate limit status), triage for five common failure modes (missing translations, stale translations, API outage, file upload failures, OTA failures), fallback to cached translations, and communication templates for stakeholder notification. Designed to be executed under pressure — each section is self-contained.

## Prerequisites

- `curl` and `jq` available on the responder's machine
- Production Lokalise API token accessible (from secret manager or break-glass procedure)
- `LOKALISE_PROJECT_ID` known (check your deployment config or Lokalise dashboard)
- Access to application logs (Datadog, CloudWatch, GCP Logging, or equivalent)
- Incident communication channel (Slack, PagerDuty, or equivalent)

## Instructions

### Step 1: Quick Diagnostics (Run First)

Execute these three checks immediately to narrow the problem scope. Copy-paste into your terminal:

```bash
#!/bin/bash
# incident-diagnostics.sh — Run all three checks in sequence
set -uo pipefail

: "${LOKALISE_API_TOKEN:?Set LOKALISE_API_TOKEN before running diagnostics}"
: "${LOKALISE_PROJECT_ID:?Set LOKALISE_PROJECT_ID before running diagnostics}"

echo "=== 1. Lokalise API Health ==="
API_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
  "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}")

case "$API_STATUS" in
  200) echo "API: HEALTHY (200 OK)" ;;
  401) echo "API: AUTH FAILURE (401) — Token invalid or expired. Rotate immediately." ;;
  403) echo "API: FORBIDDEN (403) — Token lacks permissions for this project." ;;
  404) echo "API: NOT FOUND (404) — Check LOKALISE_PROJECT_ID value." ;;
  429) echo "API: RATE LIMITED (429) — Throttled. Wait 10 seconds and retry." ;;
  5*)  echo "API: LOKALISE OUTAGE (${API_STATUS}) — Check https://status.lokalise.com" ;;
  000) echo "API: UNREACHABLE — DNS/network issue. Check connectivity." ;;
  *)   echo "API: UNEXPECTED (${API_STATUS}) — Investigate further." ;;
esac

echo ""
echo "=== 2. Token Validity ==="
TOKEN_CHECK=$(curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" 2>/dev/null)

if [[ $? -eq 0 ]]; then
  PROJECT_NAME=$(echo "$TOKEN_CHECK" | jq -r '.project.name')
  TEAM_ID=$(echo "$TOKEN_CHECK" | jq -r '.project.team_id')
  echo "Token: VALID"
  echo "  Project: ${PROJECT_NAME}"
  echo "  Team ID: ${TEAM_ID}"
else
  echo "Token: INVALID or project inaccessible"
  echo "  Action: Get a valid token from your secret manager or Lokalise dashboard"
fi

echo ""
echo "=== 3. Rate Limit Status ==="
RATE_RESPONSE=$(curl -sI "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/keys?limit=1" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" 2>/dev/null)

RATE_LIMIT=$(echo "$RATE_RESPONSE" | grep -i "x-ratelimit-limit" | tr -d '\r' | awk '{print $2}')
RATE_REMAINING=$(echo "$RATE_RESPONSE" | grep -i "x-ratelimit-remaining" | tr -d '\r' | awk '{print $2}')

if [[ -n "$RATE_REMAINING" ]]; then
  echo "Rate limit:     ${RATE_LIMIT:-6} req/sec"
  echo "Remaining:      ${RATE_REMAINING} req/sec"
  if [[ "${RATE_REMAINING}" -eq 0 ]]; then
    echo "STATUS: EXHAUSTED — Wait 1 second for reset"
  else
    echo "STATUS: OK"
  fi
else
  echo "Could not determine rate limit status"
fi
```

### Step 2: Triage Decision Tree

Based on the diagnostics above, follow the appropriate path:

| Symptom | Diagnostics Result | Go To |
|---------|-------------------|-------|
| Users see English instead of their language | API healthy, token valid | **Triage A: Missing Translations** |
| Users see outdated translations | API healthy, token valid | **Triage B: Stale Translations** |
| All translations fail to load | API returns 5xx | **Triage C: API Outage** |
| CI upload fails | API returns 4xx on upload | **Triage D: File Upload Failures** |
| App works but new keys show raw key names | API healthy, keys exist in Lokalise | **Triage A: Missing Translations** |

### Triage A: Missing Translations in Production

**Likely causes:** New keys deployed before translations were uploaded, download step skipped in CI, locale file not included in build.

```bash
# 1. Check if the key exists in Lokalise
KEY_NAME="homepage.welcome_message"  # Replace with the missing key
curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/keys?filter_keys=${KEY_NAME}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq '.keys[] | {key_name: .key_name.web, translations: [.translations[] | {locale: .language_iso, value: .translation}]}'

# 2. Check if the locale file was included in the deployed build
# (run on the production server or check the build artifact)
ls -la /app/locales/  # Adjust path to your deployed locale directory
cat /app/locales/de.json | jq ".$KEY_NAME" 2>/dev/null || echo "Key not found in deployed file"

# 3. Quick fix: Re-download and redeploy
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=true \
  --directory-prefix="" \
  --export-empty-as=base \
  --unzip-to "src/locales/"
# Then trigger a redeploy
```

### Triage B: Stale Translations

**Likely causes:** Cache not invalidated, OTA bundle not refreshed, CI downloaded from wrong branch or old snapshot.

```bash
# 1. Compare Lokalise timestamp with deployed file
LOKALISE_UPDATED=$(curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq -r '.project.statistics.datetime')
echo "Lokalise last updated: $LOKALISE_UPDATED"

# 2. Check when your deployed translations were built
stat src/locales/en.json  # File modification time

# 3. Force cache invalidation if using OTA
# For i18next-http-backend or similar:
# Clear the browser/app cache or increment the version query parameter

# 4. Re-download fresh translations
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=true \
  --directory-prefix="" \
  --unzip-to "src/locales/"
```

### Triage C: API Outage

**When Lokalise API returns 5xx or is unreachable.**

```bash
# 1. Confirm on status page
echo "Check: https://status.lokalise.com"
curl -sf "https://status.lokalise.com/api/v2/summary.json" 2>/dev/null \
  | jq '.status.description' || echo "Status page unreachable"

# 2. Enable fallback translations
# Your app should have a fallback mechanism. If not, deploy one immediately:
```

```typescript
// Emergency fallback implementation
// Add to your translation loader

import bundledTranslations from './locales/en.json';

async function loadTranslations(locale: string): Promise<Record<string, string>> {
  try {
    // Try loading from Lokalise/CDN/API
    const response = await fetch(`/api/translations/${locale}`, {
      signal: AbortSignal.timeout(3000),  // 3-second timeout
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error(`Translation fetch failed for ${locale}, using fallback:`, error);
    // Fall back to bundled English translations
    return bundledTranslations;
  }
}
```

```bash
# 3. If your app crashes without the API, set the env var to enable static fallback:
export LOKALISE_FALLBACK_ENABLED=true
# Then restart the application

# 4. Monitor for recovery
watch -n 30 'curl -sf -o /dev/null -w "%{http_code}" \
  "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}"'
```

### Triage D: File Upload Failures

**When CI fails to upload source strings to Lokalise.**

```bash
# 1. Validate the source file locally
jq empty src/locales/en.json && echo "Valid JSON" || echo "INVALID JSON — fix syntax"

# 2. Check file size (Lokalise limit: 50MB per file)
du -h src/locales/en.json

# 3. Test upload with verbose output
lokalise2 file upload \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file "src/locales/en.json" \
  --lang-iso "en" \
  --replace-modified \
  --poll \
  --poll-timeout 120s 2>&1

# 4. Common fixes:
# - "Unsupported file format": Check file extension matches --format
# - "Key name too long": Lokalise limit is 1024 chars per key
# - "Too many keys": Split into multiple files if > 10,000 keys per upload
# - 429 error: Wait and retry, or reduce upload frequency
```

### Step 3: Fallback to Cached Translations

If the Lokalise API is down and you need the app to keep running, use bundled translations.

```typescript
// src/i18n/fallback-loader.ts
import fs from 'fs';
import path from 'path';

const CACHE_DIR = path.resolve(__dirname, '../locales');
const FALLBACK_DIR = path.resolve(__dirname, '../locales-fallback');

/**
 * Copy current translations to fallback directory.
 * Run this as a post-build step: `cp -r src/locales/ src/locales-fallback/`
 */
export function loadWithFallback(locale: string): Record<string, unknown> {
  const primaryPath = path.join(CACHE_DIR, `${locale}.json`);
  const fallbackPath = path.join(FALLBACK_DIR, `${locale}.json`);
  const defaultPath = path.join(FALLBACK_DIR, 'en.json');

  // Try primary (freshly downloaded)
  if (fs.existsSync(primaryPath)) {
    try {
      return JSON.parse(fs.readFileSync(primaryPath, 'utf-8'));
    } catch { /* fall through */ }
  }

  // Try locale-specific fallback
  if (fs.existsSync(fallbackPath)) {
    console.warn(`Using fallback translations for ${locale}`);
    return JSON.parse(fs.readFileSync(fallbackPath, 'utf-8'));
  }

  // Last resort: English fallback
  console.error(`No translations available for ${locale}, falling back to English`);
  return JSON.parse(fs.readFileSync(defaultPath, 'utf-8'));
}
```

### Step 4: Communication Templates

**Initial notification (post within 5 minutes of detection):**

```
[INCIDENT] Translation service degraded
Status: Investigating
Impact: [Users in DE/FR/ES/JA locales may see English text | All translations unavailable]
Start time: YYYY-MM-DD HH:MM UTC
Cause: [Lokalise API outage | Stale translation cache | Missing keys in deployment]
Next update: 15 minutes
```

**Mitigation applied:**

```
[UPDATE] Translation service — Mitigation in progress
Status: Mitigating
Action taken: [Enabled fallback translations | Redeployed with fresh downloads | Reverted to previous build]
ETA for full resolution: [30 minutes | Next deployment cycle | Pending Lokalise recovery]
```

**Resolved:**

```
[RESOLVED] Translation service restored
Duration: X hours Y minutes
Root cause: [Brief description]
Impact: [Number of affected users/requests]
Follow-up: Postmortem scheduled for YYYY-MM-DD
```

### Step 5: Post-Incident Checklist

After the incident is resolved:

1. Verify all locales are loading correctly in production
2. Check for any data loss (keys deleted or overwritten during incident)
3. Review rate limit consumption during the incident
4. Document the timeline in your incident tracker
5. Schedule a postmortem with findings:
   - What failed and why
   - How it was detected (monitoring alert or user report?)
   - Time to detection, time to mitigation, time to resolution
   - What changes would prevent recurrence

## Output

After executing this runbook:
- Root cause identified and documented
- Immediate mitigation applied (fallback translations, redeployment, or cache clear)
- Stakeholders notified via communication templates
- Post-incident evidence collected for postmortem

## Error Handling

| Issue During Response | Cause | Solution |
|----------------------|-------|----------|
| Can't access Lokalise dashboard | Lokalise fully down | Use CLI with API token; check status.lokalise.com on mobile |
| Token from secret manager fails | Secret manager also experiencing issues | Use break-glass procedure (documented token in secure vault) |
| Fallback translations not present | Never set up fallback mechanism | Deploy English-only as emergency, then implement fallback |
| App crashes on missing translations | No null-safe translation access | Hotfix: wrap translation calls in try-catch, return key name |
| Rate limited during recovery | Too many API calls fixing the issue | Wait 1 second between requests; max 6 req/sec |
| Git deploy blocked by CI | CI translation checks failing | Bypass with `[skip-translation-check]` in commit message (if configured) |

## Examples

### One-Line Health Check

```bash
curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq '{name: .project.name, keys: .project.statistics.keys_total, progress: .project.statistics.progress_total}' \
  || echo "UNHEALTHY — API unreachable or auth failed"
```

### Application Health Endpoint

```typescript
// GET /health/translations
export async function translationHealthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, unknown>;
}> {
  const checks = {
    api_reachable: false,
    translations_loaded: false,
    cache_fresh: false,
  };

  // Check 1: Can we reach the Lokalise API?
  try {
    const res = await fetch(`https://api.lokalise.com/api2/projects/${process.env.LOKALISE_PROJECT_ID}`, {
      headers: { 'X-Api-Token': process.env.LOKALISE_API_TOKEN! },
      signal: AbortSignal.timeout(5000),
    });
    checks.api_reachable = res.ok;
  } catch { /* timeout or network error */ }

  // Check 2: Are translations loaded in memory?
  checks.translations_loaded = Object.keys(i18next.store.data).length > 0;

  // Check 3: Is the cache fresh (less than 1 hour old)?
  const cacheAge = Date.now() - (globalThis.__translationCacheTimestamp ?? 0);
  checks.cache_fresh = cacheAge < 3600_000;

  const allHealthy = Object.values(checks).every(Boolean);
  const anyHealthy = Object.values(checks).some(Boolean);

  return {
    status: allHealthy ? 'healthy' : anyHealthy ? 'degraded' : 'unhealthy',
    details: checks,
  };
}
```

## Resources

- [Lokalise Status Page](https://status.lokalise.com) — First thing to check during an outage
- [Lokalise API Rate Limits](https://developers.lokalise.com/reference/api-rate-limits)
- [Lokalise API Error Codes](https://developers.lokalise.com/reference/errors)
- [Lokalise Support](mailto:support@lokalise.com) — For P1 issues, also try the in-app chat
- [Lokalise Community Forum](https://community.lokalise.com)

## Next Steps

- After resolving the incident, run `lokalise-prod-checklist` to verify the system is fully healthy
- Implement the health endpoint from the examples if you do not already have one
- Set up automated alerting on the health endpoint (Datadog, PagerDuty, or equivalent)
- Add the fallback translation mechanism to prevent full outage on future API issues
