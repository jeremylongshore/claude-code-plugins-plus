---
name: lokalise-migration-deep-dive
description: |
  Execute major migration to Lokalise from other TMS platforms with data migration strategies.
  Use when migrating to Lokalise from competitors, performing data imports,
  or re-platforming existing translation management to Lokalise.
  Trigger with phrases like "migrate to lokalise", "lokalise migration",
  "switch to lokalise", "lokalise import", "lokalise replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(lokalise2:*), Bash(curl:*), Bash(jq:*), Bash(node:*), Bash(python3:*), Bash(mkdir:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Migration Deep Dive

## Current State
!`lokalise2 --version 2>/dev/null || echo 'CLI not installed'`
!`npm list @lokalise/node-api 2>/dev/null | grep lokalise || echo 'SDK not installed'`
!`node --version 2>/dev/null || echo 'Node.js not available'`

## Overview

Migrate translations from another TMS (Crowdin, Phrase, POEditor) into Lokalise — export from the source platform, transform key names and variable syntax to match Lokalise conventions, bulk upload via API, validate translation coverage, and handle key conflicts with format-aware tooling.

## Prerequisites

- Admin or export access to the source TMS platform
- Lokalise account with a plan that supports the target key count (Free: 500 keys, Pro: unlimited)
- `LOKALISE_API_TOKEN` environment variable set (read-write token)
- `lokalise2` CLI or `@lokalise/node-api` SDK installed
- `jq` for JSON manipulation during transformation

## Instructions

### Step 1: Export from Source Platform

Each TMS has its own export format. Export to a Lokalise-compatible format when possible (JSON, XLIFF, or the platform's native format).

**From Crowdin:**
```bash
set -euo pipefail
# Export all translations as JSON (flat key-value structure)
# Use Crowdin CLI or API to download
curl -X POST "https://api.crowdin.com/api/v2/projects/${CROWDIN_PROJECT_ID}/translations/builds" \
  -H "Authorization: Bearer ${CROWDIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"targetLanguageIds": [], "exportApprovedOnly": false}'

# Download the build when ready (poll build status first)
curl -X GET "https://api.crowdin.com/api/v2/projects/${CROWDIN_PROJECT_ID}/translations/builds/${BUILD_ID}/download" \
  -H "Authorization: Bearer ${CROWDIN_TOKEN}" -o crowdin-export.zip

unzip crowdin-export.zip -d crowdin-export/
echo "Exported $(find crowdin-export/ -name '*.json' | wc -l) translation files"
```

**From Phrase (formerly PhraseApp):**
```bash
set -euo pipefail
# Export all locales as JSON
for LOCALE in en fr de es ja; do
  curl -X GET "https://api.phrase.com/v2/projects/${PHRASE_PROJECT_ID}/locales/${LOCALE}/download?file_format=simple_json" \
    -H "Authorization: token ${PHRASE_TOKEN}" \
    -o "phrase-export/${LOCALE}.json"
  sleep 0.5
done
echo "Exported locales: $(ls phrase-export/)"
```

**From POEditor:**
```bash
set -euo pipefail
# Export via POEditor API (returns a download URL)
EXPORT_URL=$(curl -s -X POST "https://api.poeditor.com/v2/projects/export" \
  -d "api_token=${POEDITOR_TOKEN}&id=${POEDITOR_PROJECT_ID}&language=en&type=json" \
  | jq -r '.result.url')

curl -s "$EXPORT_URL" -o poeditor-export/en.json
echo "Downloaded $(wc -c < poeditor-export/en.json) bytes"
```

### Step 2: Transform Keys and Variable Syntax

Different TMS platforms use different interpolation syntax. Lokalise supports multiple formats, but consistency matters.

```javascript
// transform-keys.mjs — Convert source format to Lokalise-compatible JSON
import { readFileSync, writeFileSync, readdirSync } from 'fs';

const VARIABLE_TRANSFORMS = {
  // Crowdin ICU: {count} -> %{count} (for Ruby) or keep as {count} (for JS)
  crowdin: (value) => value, // Crowdin uses ICU by default, Lokalise supports it
  // Phrase: %{variable} -> {{variable}} (if targeting i18next)
  phrase: (value) => value.replace(/%\{(\w+)\}/g, '{{$1}}'),
  // POEditor: {{variable}} -> {variable} (if targeting ICU)
  poeditor: (value) => value.replace(/\{\{(\w+)\}\}/g, '{$1}'),
};

const SOURCE = process.argv[2] || 'crowdin'; // crowdin | phrase | poeditor
const INPUT_DIR = process.argv[3] || 'source-export';
const OUTPUT_DIR = process.argv[4] || 'lokalise-import';

const transform = VARIABLE_TRANSFORMS[SOURCE] || ((v) => v);

for (const file of readdirSync(INPUT_DIR).filter(f => f.endsWith('.json'))) {
  const data = JSON.parse(readFileSync(`${INPUT_DIR}/${file}`, 'utf8'));
  const transformed = {};

  // Flatten nested keys with dot notation (Lokalise convention)
  function flatten(obj, prefix = '') {
    for (const [key, value] of Object.entries(obj)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        flatten(value, fullKey);
      } else {
        transformed[fullKey] = transform(String(value));
      }
    }
  }
  flatten(data);
  writeFileSync(`${OUTPUT_DIR}/${file}`, JSON.stringify(transformed, null, 2));
  console.log(`Transformed ${file}: ${Object.keys(transformed).length} keys`);
}
```

```bash
set -euo pipefail
mkdir -p lokalise-import
node transform-keys.mjs crowdin crowdin-export lokalise-import
```

### Step 3: Create Lokalise Project and Upload

```bash
set -euo pipefail
# Create a new project for the migration
PROJECT=$(curl -s -X POST "https://api.lokalise.com/api2/projects" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Migration from Crowdin",
    "description": "Migrated translations",
    "base_lang_iso": "en",
    "languages": [
      {"lang_iso": "en"}, {"lang_iso": "fr"}, {"lang_iso": "de"},
      {"lang_iso": "es"}, {"lang_iso": "ja"}
    ]
  }')

PROJECT_ID=$(echo "$PROJECT" | jq -r '.project_id')
echo "Created project: ${PROJECT_ID}"
```

### Step 4: Bulk Upload Translation Files

```bash
set -euo pipefail
# Upload each language file — Lokalise processes uploads asynchronously
for FILE in lokalise-import/*.json; do
  LANG=$(basename "$FILE" .json)  # Filename must match lang_iso (e.g., en.json, fr.json)

  # Upload via CLI (handles base64 encoding automatically)
  lokalise2 --token "${LOKALISE_API_TOKEN}" \
    file upload \
    --project-id "${PROJECT_ID}" \
    --file "$FILE" \
    --lang-iso "${LANG}" \
    --replace-modified \
    --distinguish-by-file \
    --poll \
    --poll-timeout 120s

  echo "Uploaded ${LANG}: $(jq 'length' "$FILE") keys"
  sleep 0.5  # Rate limit buffer
done
```

**Alternative: Upload via API (when CLI is unavailable):**

```bash
set -euo pipefail
FILE_CONTENT=$(base64 -w 0 lokalise-import/en.json)

curl -X POST "https://api.lokalise.com/api2/projects/${PROJECT_ID}/files/upload" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": \"${FILE_CONTENT}\",
    \"filename\": \"en.json\",
    \"lang_iso\": \"en\",
    \"replace_modified\": true,
    \"distinguish_by_file\": false
  }"

# Upload is async — poll the returned process ID
```

### Step 5: Validate Coverage

```typescript
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

async function validateMigration(projectId: string, expectedKeys: number) {
  // Get project statistics
  const project = await lok.projects().get(projectId);
  const stats = project.statistics;

  console.log('=== Migration Validation ===');
  console.log(`Keys imported: ${stats.keys_total} (expected: ${expectedKeys})`);
  console.log(`Languages: ${stats.languages?.length}`);
  console.log(`Overall progress: ${stats.progress_total}%`);

  // Check per-language coverage
  const languages = await lok.languages().list({ project_id: projectId, limit: 100 });
  for (const lang of languages.items) {
    const pct = lang.words_reviewed !== undefined
      ? Math.round((lang.words_reviewed / (lang.words || 1)) * 100)
      : 'N/A';
    console.log(`  ${lang.lang_iso}: ${lang.words} words, ${pct}% reviewed`);
  }

  // Flag gaps
  if (stats.keys_total < expectedKeys) {
    console.warn(`WARNING: ${expectedKeys - stats.keys_total} keys missing after import`);
  }
}

await validateMigration(process.env.PROJECT_ID!, 5000);
```

### Step 6: Handle Key Conflicts

When importing into an existing project, keys may already exist. Lokalise offers conflict resolution via upload parameters:

```bash
set -euo pipefail
# Upload with explicit conflict handling
lokalise2 --token "${LOKALISE_API_TOKEN}" \
  file upload \
  --project-id "${PROJECT_ID}" \
  --file lokalise-import/en.json \
  --lang-iso en \
  --replace-modified \
  --tag-inserted-keys "migration-$(date +%Y%m%d)" \
  --tag-updated-keys "migration-updated-$(date +%Y%m%d)" \
  --poll

# After upload, review conflicts by tag
TAG="migration-updated-$(date +%Y%m%d)"  # Tag matches the upload batch date
curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/keys?filter_tags=${TAG}&limit=500" \
  | jq '.keys | length' | xargs -I{} echo "Keys with conflicts (updated): {}"
```

## Output

- Source TMS translations exported and archived locally
- Keys transformed to Lokalise naming convention (dot-notation, matching interpolation syntax)
- Lokalise project created with all target languages configured
- All translation files uploaded with per-language coverage validated
- Conflict report for any keys that were updated vs. inserted
- Tags applied for audit trail (date-stamped: `migration-YYYYMMDD`, `migration-updated-YYYYMMDD`)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Key name conflicts | Different naming conventions across platforms | Flatten nested keys to dot notation in Step 2 before import |
| Missing translations | Source export was incomplete or language-filtered | Re-export from source with all languages selected |
| Encoding errors | Non-UTF-8 files from legacy systems | Convert with `iconv -f LATIN1 -t UTF-8 input.json > output.json` |
| `429` during bulk upload | Uploading too fast (6 req/s limit) | Use `--poll` flag with CLI which handles waiting, or add `sleep 0.5` between API calls |
| Variable syntax mismatch | Source uses `%{user_name}`, target expects `{{user_name}}` | Use the transform script in Step 2 to normalize interpolation tokens before upload |
| Upload process stuck | Large file processing on Lokalise side | Poll process status; files over 50MB should be split by namespace |
| Plural forms missing | Source platform uses different plural rules | Manually map CLDR plural categories after import |

## Examples

### Quick Migration Inventory

Before starting a migration, assess the scope:

```bash
set -euo pipefail
echo "=== Source Platform Inventory ==="
echo "Translation files:"
find source-export/ -name "*.json" -o -name "*.xliff" -o -name "*.po" | head -20
echo ""
echo "Languages found:"
ls source-export/ | head -20
echo ""
echo "Sample key count (first file):"
FIRST_FILE=$(find source-export/ -name "*.json" -type f | head -1)
jq 'keys | length' "$FIRST_FILE" 2>/dev/null || echo "Not a flat JSON file"
```

### Dry Run — Validate Without Importing

```bash
set -euo pipefail
# Upload with --cleanup-mode to see what would happen without committing
lokalise2 --token "${LOKALISE_API_TOKEN}" \
  file upload \
  --project-id "${PROJECT_ID}" \
  --file lokalise-import/en.json \
  --lang-iso en \
  --poll \
  --detect-icu-plurals
# Review the process result before uploading remaining languages
```

## Resources

- [Lokalise File Upload API](https://developers.lokalise.com/reference/upload-a-file)
- [Supported File Formats](https://docs.lokalise.com/en/articles/1400452-file-formats)
- [Crowdin Export API](https://developer.crowdin.com/api/v2/#operation/api.projects.translations.builds.post)
- [Phrase Export API](https://developers.phrase.com/api/#tag/Locales/operation/locale/download)
- [POEditor Export API](https://poeditor.com/docs/api#projects_export)
- [CLDR Plural Rules](https://cldr.unicode.org/index/cldr-spec/plural-rules)

## Next Steps

- After migration, configure webhooks and CI integration with `lokalise-ci-integration`.
- Set up team permissions on the new project with `lokalise-enterprise-rbac`.
- If key counts are large (10K+), optimize API access with `lokalise-performance-tuning`.
