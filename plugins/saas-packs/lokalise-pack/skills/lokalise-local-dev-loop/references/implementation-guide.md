# Lokalise Local Dev Loop - Implementation Guide

Detailed implementation reference for the lokalise-local-dev-loop skill.

## Instructions

### Step 1: Create Project Structure
```
my-lokalise-project/
├── src/
│   ├── i18n/
│   │   ├── index.ts          # i18n setup and exports
│   │   └── config.ts         # Lokalise configuration
│   └── locales/
│       ├── en.json           # English (base)
│       ├── es.json           # Spanish
│       └── fr.json           # French
├── scripts/
│   ├── lokalise-pull.sh      # Download translations
│   └── lokalise-push.sh      # Upload source strings
├── .env.local                # Local secrets (git-ignored)
├── .env.example              # Template for team
├── lokalise.json             # Lokalise CLI config
└── package.json
```

### Step 2: Create Lokalise CLI Config
```json
// lokalise.json
{
  "$schema": "https://json.schemastore.org/lokalise.json",
  "project_id": "YOUR_PROJECT_ID.abcdef",
  "export": {
    "format": "json",
    "original_filenames": false,
    "bundle_structure": "locales/%LANG_ISO%.json",
    "placeholder_format": "icu",
    "export_empty_as": "skip"
  },
  "import": {
    "file_path": "./src/locales/en.json",
    "lang_iso": "en",
    "replace_modified": true,
    "convert_placeholders": true,
    "detect_icu_plurals": true
  }
}
```

### Step 3: Create Sync Scripts
```bash
#!/bin/bash
# scripts/lokalise-pull.sh - Download translations from Lokalise

set -e

PROJECT_ID="${LOKALISE_PROJECT_ID:-$(jq -r '.project_id' lokalise.json)}"

echo "Pulling translations from Lokalise..."

lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$PROJECT_ID" \
  file download \
  --format json \
  --original-filenames=false \
  --bundle-structure "src/locales/%LANG_ISO%.json" \
  --placeholder-format icu \
  --export-empty-as skip \
  --unzip-to .

echo "Translations downloaded to src/locales/"
```

```bash
#!/bin/bash
# scripts/lokalise-push.sh - Upload source strings to Lokalise

set -e

PROJECT_ID="${LOKALISE_PROJECT_ID:-$(jq -r '.project_id' lokalise.json)}"

echo "Pushing source strings to Lokalise..."

lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$PROJECT_ID" \
  file upload \
  --file "./src/locales/en.json" \
  --lang-iso en \
  --replace-modified \
  --convert-placeholders \
  --detect-icu-plurals \
  --poll \
  --poll-timeout 120s

echo "Source strings uploaded successfully!"
```

### Step 4: Configure package.json Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "i18n:pull": "bash scripts/lokalise-pull.sh",
    "i18n:push": "bash scripts/lokalise-push.sh",
    "i18n:sync": "npm run i18n:push && npm run i18n:pull",
    "predev": "npm run i18n:pull",
    "prebuild": "npm run i18n:pull"
  }
}
```

### Step 5: Set Up File Watcher (Optional)
```typescript
// scripts/watch-translations.ts
import chokidar from "chokidar";
import { exec } from "child_process";

const watcher = chokidar.watch("./src/locales/en.json", {
  persistent: true,
  ignoreInitial: true,
});

watcher.on("change", (path) => {
  console.log(`Source file changed: ${path}`);
  console.log("Pushing to Lokalise...");
  exec("npm run i18n:push", (error, stdout, stderr) => {
    if (error) {
      console.error(`Push failed: ${error.message}`);
      return;
    }
    console.log(stdout);
  });
});

console.log("Watching for translation changes...");
```


## Detailed Examples

### Quick Pull/Push Commands
```bash
# Pull all translations
npm run i18n:pull

# Push source strings only
npm run i18n:push

# Full sync (push then pull)
npm run i18n:sync
```

### Environment Setup
```bash
# .env.local
LOKALISE_API_TOKEN=your-api-token
LOKALISE_PROJECT_ID=123456789.abcdef
```

### React i18n Integration
```typescript
// src/i18n/index.ts
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "../locales/en.json";
import es from "../locales/es.json";
import fr from "../locales/fr.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    es: { translation: es },
    fr: { translation: fr },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
```

### Git Hooks with Husky
```bash
# .husky/pre-commit
#!/bin/sh
npm run i18n:push
```

