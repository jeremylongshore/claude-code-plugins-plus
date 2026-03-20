---
name: lokalise-local-dev-loop
description: |
  Configure Lokalise local development with file sync and hot reload.
  Use when setting up a development environment, configuring translation sync,
  or establishing a fast iteration cycle with Lokalise.
  Trigger with phrases like "lokalise dev setup", "lokalise local development",
  "lokalise dev environment", "develop with lokalise", "lokalise sync".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(lokalise2:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Local Dev Loop

## Overview

Set up a complete local development workflow with Lokalise: project structure for i18n files, CLI push/pull commands, file watching for auto-upload, mock translations for offline development, framework integration (React i18next, Vue i18n), and a pre-commit hook to keep translations synced.

## Prerequisites

- Lokalise API token exported as `LOKALISE_API_TOKEN`
- Lokalise project ID exported as `LOKALISE_PROJECT_ID`
- Node.js 18+ with npm or pnpm
- `lokalise2` CLI installed
- Git (for pre-commit hook)

## Instructions

1. Set up the project directory structure for i18n files, compatible with Lokalise's `bundle_structure` and most i18n frameworks.

```
project-root/
├── src/
│   └── locales/
│       ├── en.json          # Base language (source of truth)
│       ├── fr.json          # Downloaded from Lokalise
│       ├── de.json
│       ├── es.json
│       └── index.ts         # Barrel export + type definitions
├── scripts/
│   ├── i18n-push.sh         # Upload source to Lokalise
│   ├── i18n-pull.sh         # Download translations from Lokalise
│   └── i18n-mock.ts         # Generate mock translations
├── .env.local               # LOKALISE_API_TOKEN, LOKALISE_PROJECT_ID
└── package.json             # i18n:push, i18n:pull, i18n:sync scripts
```

**Barrel export with type safety (`src/locales/index.ts`):**

```typescript
import en from "./en.json";

// Type derived from base language — all other locales must match this shape
export type TranslationKeys = typeof en;

export const defaultLocale = "en" as const;
export const supportedLocales = ["en", "fr", "de", "es"] as const;
export type Locale = (typeof supportedLocales)[number];

export async function loadLocale(locale: Locale): Promise<TranslationKeys> {
  const mod = await import(`./${locale}.json`);
  return mod.default;
}
```

2. Create CLI push/pull scripts for the upload-translate-download cycle.

**Push script (`scripts/i18n-push.sh`):**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Upload source language file to Lokalise
lokalise2 --token "$LOKALISE_API_TOKEN" file upload \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file ./src/locales/en.json \
  --lang-iso en \
  --replace-modified \
  --include-path \
  --detect-icu-plurals \
  --poll \
  --tag-inserted-keys \
  --tag-updated-keys

echo "Source strings pushed to Lokalise"
```

**Pull script (`scripts/i18n-pull.sh`):**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Download all translations from Lokalise
lokalise2 --token "$LOKALISE_API_TOKEN" file download \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=false \
  --bundle-structure "%LANG_ISO%.json" \
  --export-empty-as base \
  --export-sort a_z \
  --replace-breaks=false \
  --placeholder-format icu \
  --unzip-to ./src/locales

echo "Translations pulled to ./src/locales/"

# Show what changed
git diff --stat src/locales/ || true
```

**Package.json scripts:**

```json
{
  "scripts": {
    "i18n:push": "bash scripts/i18n-push.sh",
    "i18n:pull": "bash scripts/i18n-pull.sh",
    "i18n:sync": "npm run i18n:push && npm run i18n:pull"
  }
}
```

**Typical workflow:**

```bash
# Edit source strings locally
vim src/locales/en.json

# Push changes to Lokalise
npm run i18n:push

# ... translators work in Lokalise UI ...

# Pull completed translations
npm run i18n:pull

# Full round-trip
npm run i18n:sync
```

3. Set up watch mode to auto-upload source strings when `en.json` changes during development.

```typescript
// scripts/i18n-watch.ts — run with: npx tsx scripts/i18n-watch.ts
import { watch } from "node:fs";
import { execSync } from "node:child_process";

const SOURCE_FILE = "./src/locales/en.json";
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function pushToLokalise() {
  console.log(`[${new Date().toISOString()}] Uploading ${SOURCE_FILE}...`);
  try {
    execSync("npm run i18n:push", { stdio: "inherit" });
    console.log("Upload complete\n");
  } catch (err) {
    console.error("Upload failed:", (err as Error).message);
  }
}

watch(SOURCE_FILE, (eventType) => {
  if (eventType !== "change") return;
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(pushToLokalise, 2000); // 2s debounce
});

console.log(`Watching ${SOURCE_FILE} for changes... (Ctrl+C to stop)`);
```

Add to package.json:

```json
{
  "scripts": {
    "i18n:watch": "npx tsx scripts/i18n-watch.ts"
  }
}
```

4. Generate mock translations for offline development and layout testing.

```typescript
// scripts/i18n-mock.ts
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const source: Record<string, string> = JSON.parse(
  readFileSync("./src/locales/en.json", "utf-8")
);

// Pseudo-localization: wraps text in brackets and adds length
function pseudoLocalize(text: string): string {
  // Preserve ICU placeholders like {name}, {count, plural, ...}
  return text.replace(/([^{}]+)/g, (match) => {
    const padded = match.replace(/[a-zA-Z]/g, (c) => {
      const base = c === c.toUpperCase() ? 65 : 97;
      return String.fromCharCode(((c.charCodeAt(0) - base + 13) % 26) + base);
    });
    return `[${padded}]`;
  });
}

// Generate longer text to test layout overflow
function stretchLocalize(text: string): string {
  return `[${text}${"~".repeat(Math.ceil(text.length * 0.3))}]`;
}

const pseudo: Record<string, string> = {};
const stretch: Record<string, string> = {};
for (const [key, value] of Object.entries(source)) {
  pseudo[key] = pseudoLocalize(value);
  stretch[key] = stretchLocalize(value);
}

mkdirSync("./src/locales", { recursive: true });
writeFileSync("./src/locales/pseudo.json", JSON.stringify(pseudo, null, 2));
writeFileSync("./src/locales/xx-long.json", JSON.stringify(stretch, null, 2));

console.log("Generated pseudo.json and xx-long.json for testing");
```

Use in development:

```typescript
// In your app's locale config, add mock locales for dev only
const devLocales = process.env.NODE_ENV === "development"
  ? { pseudo: () => import("./locales/pseudo.json"), "xx-long": () => import("./locales/xx-long.json") }
  : {};
```

5. Integrate with React i18next (or skip to step 6 for Vue i18n).

```typescript
// src/i18n.ts
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

// Lazy-load other languages
export async function changeLanguage(lng: string) {
  if (!i18n.hasResourceBundle(lng, "translation")) {
    const mod = await import(`./locales/${lng}.json`);
    i18n.addResourceBundle(lng, "translation", mod.default);
  }
  await i18n.changeLanguage(lng);
}

export default i18n;
```

6. Integrate with Vue i18n (alternative to step 5).

```typescript
// src/i18n.ts
import { createI18n } from "vue-i18n";
import en from "./locales/en.json";

const i18n = createI18n({
  legacy: false,
  locale: "en",
  fallbackLocale: "en",
  messages: { en },
});

// Lazy-load translations
export async function loadLocaleMessages(locale: string) {
  if (i18n.global.availableLocales.includes(locale)) {
    i18n.global.locale.value = locale;
    return;
  }
  const messages = await import(`./locales/${locale}.json`);
  i18n.global.setLocaleMessage(locale, messages.default);
  i18n.global.locale.value = locale;
}

export default i18n;
```

7. Add a pre-commit hook to prevent committing stale translations.

```bash
#!/usr/bin/env bash
# .husky/pre-commit (or .git/hooks/pre-commit)
set -euo pipefail

# Only run if locale files are staged
STAGED_LOCALES=$(git diff --cached --name-only -- 'src/locales/*.json' || true)
if [ -z "$STAGED_LOCALES" ]; then
  exit 0
fi

echo "Locale files staged — pulling latest translations from Lokalise..."

# Pull latest translations
npm run i18n:pull

# Check if pull changed any staged files
CHANGED=$(git diff --name-only -- 'src/locales/*.json' || true)
if [ -n "$CHANGED" ]; then
  echo ""
  echo "WARNING: Lokalise has newer translations for:"
  echo "$CHANGED"
  echo ""
  echo "Review the changes, then: git add src/locales/ && git commit"
  exit 1
fi

echo "Translations are up to date"
```

Install with Husky:

```bash
set -euo pipefail
npx husky add .husky/pre-commit "bash .husky/pre-commit"
chmod +x .husky/pre-commit
```

## Output

- Project directory structured for i18n with typed locale imports
- Push/pull/sync npm scripts for CLI workflow
- File watcher for automatic source string uploads
- Mock translation files for offline UI testing
- Framework integration (React i18next or Vue i18n) with lazy loading
- Pre-commit hook preventing stale translations

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `LOKALISE_API_TOKEN not set` | Missing env variable | Add to `.env.local` and source it |
| `LOKALISE_PROJECT_ID not set` | Missing env variable | Get from Lokalise dashboard > Project Settings |
| `File not found` for push | Wrong path in script | Verify `--file` path matches your project structure |
| `Rate limit 429` | Watch mode uploading too fast | Increase debounce timeout to 5+ seconds |
| `Polling timeout` | Large file taking too long | Add `--poll-timeout 120` to CLI commands |
| `git diff` shows unexpected changes | Lokalise reformatted JSON | Use `export_sort: "a_z"` and consistent formatting |

## Examples

### Complete Setup Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# One-time setup for a new project
mkdir -p src/locales scripts

# Create base language file if it doesn't exist
if [ ! -f src/locales/en.json ]; then
  echo '{}' > src/locales/en.json
  echo "Created empty src/locales/en.json"
fi

# Create push/pull scripts
cat > scripts/i18n-push.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" file upload \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file ./src/locales/en.json \
  --lang-iso en \
  --replace-modified \
  --detect-icu-plurals \
  --poll
echo "Pushed source strings"
SCRIPT

cat > scripts/i18n-pull.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" file download \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=false \
  --bundle-structure "%LANG_ISO%.json" \
  --export-empty-as base \
  --export-sort a_z \
  --unzip-to ./src/locales
echo "Pulled translations"
SCRIPT

chmod +x scripts/i18n-push.sh scripts/i18n-pull.sh

# Add npm scripts (requires jq)
jq '.scripts += {"i18n:push":"bash scripts/i18n-push.sh","i18n:pull":"bash scripts/i18n-pull.sh","i18n:sync":"npm run i18n:push && npm run i18n:pull"}' \
  package.json > package.json.tmp && mv package.json.tmp package.json

echo "Setup complete. Add LOKALISE_API_TOKEN and LOKALISE_PROJECT_ID to .env.local"
```

## Resources

- [Lokalise CLI Documentation](https://docs.lokalise.com/en/articles/3401683-lokalise-cli-v2)
- [File Upload API](https://developers.lokalise.com/reference/upload-a-file)
- [File Download API](https://developers.lokalise.com/reference/download-files)
- [react-i18next Setup](https://react.i18next.com/getting-started)
- [Vue i18n Guide](https://vue-i18n.intlify.dev/guide/)
- [Bundle Structure Placeholders](https://docs.lokalise.com/en/articles/2281317-filenames)

## Next Steps

See `lokalise-sdk-patterns` for production-ready code patterns and advanced SDK usage.
