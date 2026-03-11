# Lokalise Core Workflow B - Implementation Guide

Detailed implementation reference for the lokalise-core-workflow-b skill.

## Instructions

### Step 1: Download via CLI
```bash
# Basic download
lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file download \
  --format json \
  --original-filenames=false \
  --bundle-structure "locales/%LANG_ISO%.json" \
  --unzip-to ./src

# Download with filtering
lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file download \
  --format json \
  --filter-langs "en,es,fr,de" \
  --filter-data "reviewed" \
  --export-empty-as "skip" \
  --unzip-to ./src/locales
```

### Step 2: Download via SDK
```typescript
import { LokaliseApi } from "@lokalise/node-api";
import fs from "fs";
import path from "path";
import AdmZip from "adm-zip";
import axios from "axios";

const lokaliseApi = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
});

async function downloadTranslations(projectId: string, outputDir: string) {
  // Request file export
  const response = await lokaliseApi.files().download(projectId, {
    format: "json",
    original_filenames: false,
    bundle_structure: "%LANG_ISO%.json",
    placeholder_format: "icu",
    export_empty_as: "skip",
    export_sort: "a_z",
  });

  console.log(`Bundle URL: ${response.bundle_url}`);

  // Download the ZIP file
  const zipResponse = await axios.get(response.bundle_url, {
    responseType: "arraybuffer",
  });

  // Extract to output directory
  const zip = new AdmZip(Buffer.from(zipResponse.data));
  zip.extractAllTo(outputDir, true);

  console.log(`Translations extracted to ${outputDir}`);

  // List extracted files
  return fs.readdirSync(outputDir).filter(f => f.endsWith(".json"));
}
```

### Step 3: Download Specific Languages
```typescript
async function downloadLanguages(
  projectId: string,
  languages: string[],
  outputDir: string
) {
  const response = await lokaliseApi.files().download(projectId, {
    format: "json",
    filter_langs: languages,
    original_filenames: false,
    bundle_structure: "%LANG_ISO%.json",
  });

  // Download and extract
  const zipResponse = await axios.get(response.bundle_url, {
    responseType: "arraybuffer",
  });

  const zip = new AdmZip(Buffer.from(zipResponse.data));
  zip.extractAllTo(outputDir, true);

  return languages.map(lang => path.join(outputDir, `${lang}.json`));
}
```

### Step 4: Integrate with React i18next
```typescript
// src/i18n/loadTranslations.ts
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import HttpBackend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    supportedLngs: ["en", "es", "fr", "de", "ja"],
    backend: {
      loadPath: "/locales/{{lng}}.json",
    },
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
```

### Step 5: Generate TypeScript Types
```typescript
// scripts/generateI18nTypes.ts
import fs from "fs";
import path from "path";

interface TranslationKeys {
  [key: string]: string | TranslationKeys;
}

function flattenKeys(obj: TranslationKeys, prefix = ""): string[] {
  const keys: string[] = [];

  for (const key in obj) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    const value = obj[key];

    if (typeof value === "string") {
      keys.push(fullKey);
    } else {
      keys.push(...flattenKeys(value, fullKey));
    }
  }

  return keys;
}

function generateTypes(localesDir: string, outputPath: string) {
  const enFile = path.join(localesDir, "en.json");
  const translations = JSON.parse(fs.readFileSync(enFile, "utf8"));
  const keys = flattenKeys(translations);

  const typeContent = `// Auto-generated from Lokalise translations
// Do not edit manually

export type TranslationKey =
${keys.map(k => `  | "${k}"`).join("\n")};

export interface TranslationKeys {
${keys.map(k => `  "${k}": string;`).join("\n")}
}
`;

  fs.writeFileSync(outputPath, typeContent);
  console.log(`Generated types for ${keys.length} keys`);
}

generateTypes("./src/locales", "./src/i18n/types.ts");
```


## Detailed Examples

### Download Options Reference
```typescript
const downloadOptions = {
  // Format settings
  format: "json",                    // json, xliff, po, strings, xml, etc.
  original_filenames: false,         // Use original or standardized names
  bundle_structure: "%LANG_ISO%.json", // File naming pattern

  // Content filtering
  filter_langs: ["en", "es"],        // Specific languages
  filter_data: "reviewed",           // reviewed, translated, untranslated
  export_empty_as: "skip",           // skip, empty, base

  // Placeholder handling
  placeholder_format: "icu",         // icu, printf, raw

  // Sorting
  export_sort: "a_z",                // first_added, last_added, a_z, z_a

  // Include metadata
  include_comments: true,
  include_description: false,
};
```

### CI/CD Download Script
```bash
#!/bin/bash
# scripts/download-translations.sh

set -e

OUTPUT_DIR="${1:-./src/locales}"

echo "Downloading translations..."

lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file download \
  --format json \
  --original-filenames=false \
  --bundle-structure "%LANG_ISO%.json" \
  --export-empty-as skip \
  --filter-data "translated,reviewed" \
  --unzip-to "$OUTPUT_DIR"

echo "Downloaded translations to $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
```

### Vite Plugin Integration
```typescript
// vite.config.ts
import { defineConfig } from "vite";
import { execSync } from "child_process";

export default defineConfig({
  plugins: [
    {
      name: "lokalise-sync",
      buildStart() {
        if (process.env.SYNC_TRANSLATIONS === "true") {
          console.log("Syncing translations from Lokalise...");
          execSync("npm run i18n:pull", { stdio: "inherit" });
        }
      },
    },
  ],
});
```

