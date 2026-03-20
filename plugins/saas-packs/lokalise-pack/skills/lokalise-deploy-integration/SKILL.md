---
name: lokalise-deploy-integration
description: |
  Deploy Lokalise integrations to Vercel, Netlify, and Cloud Run platforms.
  Use when deploying apps with Lokalise translations to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy lokalise", "lokalise Vercel",
  "lokalise production deploy", "lokalise Netlify", "lokalise Cloud Run".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(netlify:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Deploy Integration

## Overview

Translations must be downloaded fresh during CI/CD builds to ensure production always ships the latest reviewed content. This skill covers downloading translations as a build step, GitHub Actions workflows for translation sync, Vercel and Netlify build plugin integration, OTA (over-the-air) updates for mobile apps via Lokalise's iOS and Android SDKs, and environment-specific translation bundles.

## Prerequisites

- Lokalise API token with download permissions (read-only token recommended for CI)
- `LOKALISE_API_TOKEN` and `LOKALISE_PROJECT_ID` stored as CI secrets
- `curl` and `unzip` available in CI environment (standard on GitHub Actions runners)
- For OTA: Lokalise OTA SDK token (separate from API token, generated in Lokalise dashboard)

## Instructions

### 1. Download Translations in the Build Step

Add a pre-build script that pulls translations from Lokalise before your framework compiles:

```bash
#!/bin/bash
# scripts/download-translations.sh
set -euo pipefail

PROJECT_ID="${LOKALISE_PROJECT_ID:?Missing LOKALISE_PROJECT_ID}"
API_TOKEN="${LOKALISE_API_TOKEN:?Missing LOKALISE_API_TOKEN}"
DEST_DIR="${1:-./src/locales}"

echo "Downloading translations for project $PROJECT_ID..."

BUNDLE_URL=$(curl -sf -X POST \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/files/download" \
  -H "X-Api-Token: ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"format\": \"json\",
    \"original_filenames\": false,
    \"bundle_structure\": \"%LANG_ISO%.json\",
    \"export_empty_as\": \"base\",
    \"json_unescaped_slashes\": true,
    \"include_tags\": [\"production\"],
    \"filter_data\": [\"translated\", \"reviewed\"]
  }" | jq -r '.bundle_url')

if [ -z "$BUNDLE_URL" ] || [ "$BUNDLE_URL" = "null" ]; then
  echo "ERROR: Failed to get bundle URL from Lokalise"
  exit 1
fi

mkdir -p "$DEST_DIR"
curl -sfL "$BUNDLE_URL" -o /tmp/translations.zip
unzip -o /tmp/translations.zip -d "$DEST_DIR"
rm /tmp/translations.zip

FILE_COUNT=$(ls -1 "$DEST_DIR"/*.json 2>/dev/null | wc -l)
echo "Downloaded $FILE_COUNT translation files to $DEST_DIR"
```

Wire it into `package.json`:

```json
{
  "scripts": {
    "prebuild": "./scripts/download-translations.sh ./src/locales",
    "build": "next build"
  }
}
```

### 2. GitHub Actions Workflow

Full workflow that downloads translations, builds, and deploys:

```yaml
# .github/workflows/deploy.yml
name: Build & Deploy

on:
  push:
    branches: [main]
  # Trigger from Lokalise webhook (via repository_dispatch)
  repository_dispatch:
    types: [translations_updated]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Download translations from Lokalise
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          chmod +x ./scripts/download-translations.sh
          ./scripts/download-translations.sh ./src/locales

      - name: Verify translation integrity
        run: |
          # Ensure all expected languages are present
          EXPECTED_LANGS="en fr de ja es"
          for lang in $EXPECTED_LANGS; do
            if [ ! -f "./src/locales/${lang}.json" ]; then
              echo "ERROR: Missing translation file for ${lang}"
              exit 1
            fi
            # Validate JSON
            jq empty "./src/locales/${lang}.json" || {
              echo "ERROR: Invalid JSON in ${lang}.json"
              exit 1
            }
          done
          echo "All translation files present and valid"

      - name: Build
        run: npm run build

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: --prod
```

To trigger builds when translations change, set up a Lokalise webhook that fires a GitHub `repository_dispatch`:

```bash
# In your webhook handler (see lokalise-webhooks-events)
curl -X POST \
  "https://api.github.com/repos/OWNER/REPO/dispatches" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "translations_updated"}'
```

### 3. Vercel Build Integration

For Vercel, translations download during the build phase. Configure the token as an environment variable:

```bash
# Set Lokalise secrets in Vercel
vercel env add LOKALISE_API_TOKEN production preview
vercel env add LOKALISE_PROJECT_ID production preview
```

In `vercel.json`, ensure the build command runs the translation download:

```json
{
  "buildCommand": "./scripts/download-translations.sh ./src/locales && next build",
  "outputDirectory": ".next"
}
```

For ISR/SSR apps that need translations at runtime (not just build time), cache translations in a KV store or download on cold start:

```typescript
// lib/translations.ts (Next.js example)
import { unstable_cache } from "next/cache";

export const getTranslations = unstable_cache(
  async (locale: string) => {
    const res = await fetch(
      `https://api.lokalise.com/api2/projects/${process.env.LOKALISE_PROJECT_ID}/translations`,
      {
        headers: { "X-Api-Token": process.env.LOKALISE_API_TOKEN! },
      }
    );
    const data = await res.json();
    return data.translations
      .filter((t: any) => t.language_iso === locale)
      .reduce(
        (acc: Record<string, string>, t: any) => ({
          ...acc,
          [t.key_name]: t.translation,
        }),
        {}
      );
  },
  ["translations"],
  { revalidate: 3600, tags: ["translations"] }
);
```

### 4. Netlify Build Integration

Netlify uses build plugins or the `prebuild` command. The simplest approach uses `netlify.toml`:

```toml
# netlify.toml
[build]
  command = "./scripts/download-translations.sh ./src/locales && npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "20"
```

Set secrets via Netlify CLI:

```bash
netlify env:set LOKALISE_API_TOKEN "your-token" --scope builds
netlify env:set LOKALISE_PROJECT_ID "123456789.abcdefgh" --scope builds
```

For a custom Netlify Build Plugin that integrates more deeply:

```javascript
// plugins/netlify-plugin-lokalise/index.js
module.exports = {
  async onPreBuild({ utils, constants }) {
    const { execSync } = require("child_process");
    try {
      console.log("Downloading translations from Lokalise...");
      execSync("./scripts/download-translations.sh ./src/locales", {
        stdio: "inherit",
        env: process.env,
      });
    } catch (error) {
      utils.build.failBuild("Failed to download translations from Lokalise");
    }
  },
};
```

### 5. OTA Updates for Mobile (iOS/Android)

Over-the-air updates let you push translation changes without an app store release. Lokalise provides native SDKs for this.

**iOS (Swift):**

```swift
// AppDelegate.swift
import Lokalise

func application(_ application: UIApplication,
                 didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    // Initialize with OTA SDK token and project ID
    Lokalise.shared.setProjectID(
        "123456789.abcdefgh",
        token: "ota-sdk-token-from-lokalise-dashboard"
    )

    // Preemptively check for updates
    Lokalise.shared.checkForUpdates { updated, error in
        if let error = error {
            print("OTA update check failed: \(error.localizedDescription)")
            return
        }
        if updated {
            print("Translations updated OTA")
        }
    }

    return true
}

// Usage — works with NSLocalizedString automatically
let welcome = NSLocalizedString("welcome.title", comment: "Welcome screen title")
```

**Android (Kotlin):**

```kotlin
// Application.kt
import com.lokalise.sdk.Lokalise
import com.lokalise.sdk.LokaliseCallback

class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()

        Lokalise.init(this)
        Lokalise.updateTranslations()

        // Optional: listen for update completion
        Lokalise.setUpdateCallback(object : LokaliseCallback {
            override fun onUpdated(oldBundleId: Long, newBundleId: Long) {
                Log.d("Lokalise", "Translations updated: $oldBundleId -> $newBundleId")
            }

            override fun onErrorOccurred(e: LokaliseException) {
                Log.e("Lokalise", "OTA update failed", e)
            }
        })
    }
}

// Usage — strings.xml values are overridden by OTA bundles
val welcome = getString(R.string.welcome_title)
```

Both SDKs fall back to the bundled translations if OTA download fails, so the app always has working strings.

### 6. Environment-Specific Translation Bundles

Use tags in Lokalise to manage environment-specific content:

```bash
# Download only production-tagged translations
./scripts/download-translations.sh ./src/locales  # uses "production" tag filter

# For staging: modify the script or use an env var
LOKALISE_TAGS="staging,beta" ./scripts/download-translations.sh ./src/locales
```

Update `download-translations.sh` to support dynamic tags:

```bash
# Add near the top of download-translations.sh
TAGS="${LOKALISE_TAGS:-production}"
TAG_JSON=$(echo "$TAGS" | jq -R 'split(",")' )

# Use in the curl payload:
# "include_tags": $TAG_JSON
```

This lets you maintain separate translation sets:
- **production** — fully reviewed, stable translations
- **staging** — includes new translations under review
- **beta** — experimental copy for A/B testing

## Output

- CI/CD pipeline downloading fresh translations before every build
- GitHub Actions workflow with translation validation and deployment
- Vercel/Netlify configured with Lokalise secrets and build commands
- Mobile apps receiving OTA translation updates without app store releases
- Environment-specific bundles controlled by Lokalise tags

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing translations in build | `download-translations.sh` failed silently | Use `set -euo pipefail` and check bundle URL |
| Secret not found in CI | Env var not configured | Add via `vercel env add` / `netlify env:set` / GitHub Secrets |
| Build timeout | Large project with many languages | Filter with `filter_langs` and `include_tags` |
| OTA fails on device | Network blocked or token invalid | SDKs fall back to bundled translations automatically |
| Stale translations in production | Cache not invalidated | Use `repository_dispatch` webhook to trigger rebuild |
| Empty JSON files | No translations match tag filter | Verify tag names match between Lokalise and script |

## Examples

### Minimal GitHub Action (Translation Sync Only)

```yaml
# .github/workflows/sync-translations.yml
name: Sync Translations
on:
  schedule:
    - cron: "0 */6 * * *"  # Every 6 hours
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download translations
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          chmod +x ./scripts/download-translations.sh
          ./scripts/download-translations.sh ./src/locales

      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add ./src/locales/
          git diff --cached --quiet || git commit -m "chore: sync translations from Lokalise"
          git push
```

### Docker Build with Translations

```dockerfile
# Dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci

ARG LOKALISE_API_TOKEN
ARG LOKALISE_PROJECT_ID
COPY . .
RUN chmod +x ./scripts/download-translations.sh \
    && ./scripts/download-translations.sh ./src/locales \
    && npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --production
EXPOSE 3000
CMD ["npm", "start"]
```

Build with: `docker build --build-arg LOKALISE_API_TOKEN=$TOKEN --build-arg LOKALISE_PROJECT_ID=$PID .`

## Resources

- [Lokalise Files API — Download](https://developers.lokalise.com/reference/download-files)
- [Lokalise OTA — iOS SDK](https://docs.lokalise.com/en/articles/1400660-over-the-air-sdk-for-ios-and-android)
- [Lokalise OTA — Android SDK](https://docs.lokalise.com/en/articles/1400660-over-the-air-sdk-for-ios-and-android)
- [Lokalise CI/CD Guide](https://docs.lokalise.com/en/articles/1400581-ci-cd-integration)
- [GitHub Actions — Repository Dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch)

## Next Steps

For handling errors during API calls in your pipeline, see `lokalise-common-errors`. For managing translation data formats and encoding, see `lokalise-data-handling`.
