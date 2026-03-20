---
name: lokalise-data-handling
description: |
  Implement Lokalise translation data handling, PII management, and compliance patterns.
  Use when handling sensitive translation data, implementing data redaction,
  or ensuring compliance with privacy regulations for Lokalise integrations.
  Trigger with phrases like "lokalise data", "lokalise PII",
  "lokalise GDPR", "lokalise data retention", "lokalise privacy", "lokalise compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Data Handling

## Overview

Lokalise manages translation data through keys, translations, snapshots, and branches. This skill covers the translation data lifecycle (create, update, export), key metadata management (tags, descriptions, screenshots), translation snapshots for versioning, branch-based translation isolation, export format handling (JSON flat/nested, XLIFF, PO), character encoding (UTF-8 BOM handling), and plural form support across locales.

## Prerequisites

- `@lokalise/node-api` SDK installed (`npm install @lokalise/node-api`)
- API token with read/write access to the target project
- Understanding of i18n key naming conventions for your project
- `lokalise2` CLI for bulk file operations (optional)

## Instructions

### 1. Understand the Translation Data Lifecycle

Translation data in Lokalise follows this flow: **Create keys** (with platforms, tags, descriptions) -> **Add base translations** (source language) -> **Translate** (manually or via integrations) -> **Review** (proofread flag) -> **Export** (download to codebase).

Create keys with metadata that helps translators:

```typescript
import { LokaliseApi } from "@lokalise/node-api";
const lokalise = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Create keys with rich metadata
await lokalise.keys().create({
  project_id: projectId,
  keys: [
    {
      key_name: {
        ios: "welcome.title",
        android: "welcome_title",
        web: "welcome.title",
        other: "welcome.title",
      },
      description: "Main heading on the welcome screen shown after signup",
      platforms: ["web", "ios", "android"],
      tags: ["onboarding", "v2.1"],
      base_translations: [
        { language_iso: "en", translation: "Welcome to {{appName}}" },
      ],
      is_plural: false,
      is_hidden: false,
    },
  ],
});
```

### 2. Manage Key Metadata

Tags, descriptions, and screenshots help translators understand context. Keep metadata current:

```typescript
// Bulk update tags for release management
await lokalise.keys().bulk_update({
  project_id: projectId,
  keys: [
    { key_id: 12345, tags: ["release-3.0", "reviewed"] },
    { key_id: 12346, tags: ["release-3.0", "needs-review"] },
  ],
});

// Add a screenshot for visual context
await lokalise.screenshots().create({
  project_id: projectId,
  screenshots: [
    {
      data: base64EncodedImage, // Base64 JPEG/PNG, max 6 MB
      title: "Welcome screen — mobile layout",
      description: "Shows welcome.title and welcome.subtitle keys",
      key_ids: [12345, 12346],
    },
  ],
});

// Retrieve key with all metadata
const key = await lokalise.keys().get(keyId, {
  project_id: projectId,
  disable_references: 0, // include reference language info
});
console.log(key.key_name, key.tags, key.description);
```

### 3. Use Snapshots for Translation Versioning

Snapshots capture the entire project state at a point in time. Create them before bulk changes:

```typescript
// Create a snapshot before a major update
const snapshot = await lokalise.snapshots().create({
  project_id: projectId,
  title: `Pre-release v3.0 — ${new Date().toISOString()}`,
});
console.log(`Snapshot created: ${snapshot.snapshot_id}`);

// List snapshots
const snapshots = await lokalise.snapshots().list({
  project_id: projectId,
  limit: 20,
});
snapshots.items.forEach((s) =>
  console.log(`${s.snapshot_id}: ${s.title} (${s.created_at})`)
);

// Restore a snapshot (creates a NEW project with the snapshot data)
const restored = await lokalise.snapshots().restore(snapshotId, {
  project_id: projectId,
});
console.log(`Restored to new project: ${restored.project_id}`);
```

Snapshots are immutable. Restoring creates a new project — it does not overwrite the current one.

### 4. Use Branches for Translation Isolation

Branches let you work on translations for a feature without affecting production strings:

```typescript
// Create a feature branch
await lokalise.branches().create({
  project_id: projectId,
  name: "feature/checkout-redesign",
});

// List branches
const branches = await lokalise.branches().list({ project_id: projectId });

// Work on the branch — use the branch name in file operations
await lokalise.files().upload({
  project_id: projectId,
  data: base64FileContent,
  filename: "en.json",
  lang_iso: "en",
  use_automations: true,
  branch: "feature/checkout-redesign", // target the branch
});

// Merge branch back to main when translations are ready
await lokalise.branches().merge(branchId, {
  project_id: projectId,
  force_current: false, // false = conflict detection enabled
});
```

### 5. Handle Export Formats

Lokalise supports multiple export formats. Choose based on your stack:

```typescript
// Download as flat JSON (React, Next.js, Vue)
const flatJson = await lokalise.files().download({
  project_id: projectId,
  format: "json",
  original_filenames: false,
  bundle_structure: "locales/%LANG_ISO%.json",
  json_unescaped_slashes: true,
  export_empty_as: "base",    // use base language for untranslated
  include_tags: ["release-3.0"],
  filter_langs: ["en", "fr", "de", "ja"],
});
// Returns { bundle_url: "https://..." } — download the ZIP
```

```typescript
// Download as nested JSON (common for namespaced i18n)
const nestedJson = await lokalise.files().download({
  project_id: projectId,
  format: "json",
  original_filenames: false,
  bundle_structure: "locales/%LANG_ISO%/%FILENAME%.json",
  json_unescaped_slashes: true,
  export_key_as: "key_name_dots_to_nested", // a.b.c → {a:{b:{c:"..."}}}
});
```

```bash
# Export as XLIFF 2.0 (for professional translation agencies)
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$PROJECT_ID" \
  --format xliff \
  --dest ./translations/ \
  --include-tags "release-3.0"

# Export as PO/POT (for gettext-based projects)
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$PROJECT_ID" \
  --format po \
  --dest ./locales/ \
  --export-empty-as base
```

### 6. Handle Character Encoding

All Lokalise exports use UTF-8. Watch for these encoding issues:

```typescript
// Remove UTF-8 BOM if present (some editors add it)
function stripBOM(content: string): string {
  return content.charCodeAt(0) === 0xfeff ? content.slice(1) : content;
}

// Validate JSON translation files after download
import { readFileSync } from "fs";

function loadTranslations(filePath: string): Record<string, string> {
  const raw = readFileSync(filePath, "utf-8");
  const clean = stripBOM(raw);
  try {
    return JSON.parse(clean);
  } catch (e) {
    throw new Error(
      `Invalid JSON in ${filePath}: ${(e as Error).message}. ` +
      `Check for encoding issues or unescaped characters.`
    );
  }
}
```

When uploading files, always specify UTF-8 encoding. Lokalise auto-detects encoding but explicit is safer:

```bash
# Upload with explicit encoding
lokalise2 file upload \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$PROJECT_ID" \
  --file ./locales/en.json \
  --lang-iso en \
  --convert-placeholders true
```

### 7. Handle Plural Forms

Lokalise uses CLDR plural rules. Different languages have different plural categories:

```typescript
// Create a plural key
await lokalise.keys().create({
  project_id: projectId,
  keys: [
    {
      key_name: "items.count",
      is_plural: true,
      platforms: ["web"],
      base_translations: [
        {
          language_iso: "en",
          translation: JSON.stringify({
            one: "{{count}} item",
            other: "{{count}} items",
          }),
        },
      ],
    },
  ],
});
```

Plural categories by language:

| Language | Categories | Example |
|----------|-----------|---------|
| English | one, other | 1 item / 2 items |
| French | one, many, other | 1 chose / 1000000 choses / 2 choses |
| Arabic | zero, one, two, few, many, other | 6 categories |
| Japanese | other | No plural distinction |
| Polish | one, few, many, other | 1 element / 2 elementy / 5 elementow |

In JSON exports, plural keys appear as objects:

```json
{
  "items.count": {
    "one": "{{count}} item",
    "other": "{{count}} items"
  }
}
```

Ensure your i18n framework handles plural objects (i18next, react-intl, vue-i18n all support this natively).

## Output

- Translation keys created with metadata (tags, descriptions, platforms)
- Snapshots capturing project state before bulk changes
- Branch-based workflow isolating feature translations from production
- Exported translation files in the target format (JSON/XLIFF/PO) with correct encoding
- Plural keys configured with CLDR-compliant category coverage

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Garbled characters in export | BOM or wrong encoding assumed | Strip BOM, ensure UTF-8 |
| Missing plural form | Language requires categories not provided | Check CLDR plural rules for target language |
| Branch merge conflict | Same key modified in both branches | Resolve via Lokalise UI or set `force_current: true` |
| Snapshot restore fails | Exceeded project limit on plan | Delete unused projects or upgrade plan |
| Empty translations in export | Key has no translation for language | Use `export_empty_as: "base"` to fall back to source |
| Upload overwrites existing | Default merge behavior is replace | Use `replace_modified: false` to preserve existing |

## Examples

### Upload a JSON Translation File

```typescript
import { readFileSync } from "fs";

const fileContent = readFileSync("./locales/en.json", "utf-8");
const base64Content = Buffer.from(fileContent).toString("base64");

await lokalise.files().upload({
  project_id: projectId,
  data: base64Content,
  filename: "en.json",
  lang_iso: "en",
  convert_placeholders: true,
  detect_icu_plurals: true,
  replace_modified: false, // preserve manual edits
  tags_inserted_keys: ["auto-import"],
});
```

### Export and Write to Disk

```bash
#!/bin/bash
# download-translations.sh
BUNDLE_URL=$(curl -s -X POST \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/files/download" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "original_filenames": false,
    "bundle_structure": "locales/%LANG_ISO%.json",
    "export_empty_as": "base",
    "json_unescaped_slashes": true
  }' | jq -r '.bundle_url')

curl -sL "$BUNDLE_URL" -o translations.zip
unzip -o translations.zip -d ./src/
rm translations.zip
echo "Translations downloaded and extracted to ./src/locales/"
```

## Resources

- [Lokalise Keys API](https://developers.lokalise.com/reference/list-all-keys)
- [Lokalise Files API](https://developers.lokalise.com/reference/download-files)
- [Lokalise Branches](https://developers.lokalise.com/docs/branching)
- [Lokalise Snapshots](https://developers.lokalise.com/reference/list-all-snapshots)
- [CLDR Plural Rules](https://cldr.unicode.org/index/cldr-spec/plural-rules)
- [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/)

## Next Steps

For deploying translations into your CI/CD pipeline, see `lokalise-deploy-integration`. For handling API errors during data operations, see `lokalise-common-errors`.
