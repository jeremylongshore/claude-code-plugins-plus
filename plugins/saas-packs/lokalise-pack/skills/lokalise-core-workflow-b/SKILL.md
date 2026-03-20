---
name: lokalise-core-workflow-b
description: |
  Manage Lokalise secondary workflow: Download translations and integrate with app.
  Use when downloading translation files, exporting translations,
  or integrating Lokalise output into your application.
  Trigger with phrases like "lokalise download", "lokalise pull translations",
  "export lokalise", "get translations from lokalise".
allowed-tools: Read, Write, Edit, Bash(lokalise2:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Core Workflow B

## Overview

Everything on the "Lokalise to app" side: download translated files, manage translations and review status, leverage translation memory, manage contributors and their language access, and handle format differences across JSON, XLIFF, and PO files.

## Prerequisites

- Lokalise API token exported as `LOKALISE_API_TOKEN`
- Lokalise project ID exported as `LOKALISE_PROJECT_ID`
- `@lokalise/node-api` installed for SDK examples
- `lokalise2` CLI installed for CLI examples
- `unzip` available for extracting download bundles

## Instructions

1. Download translated files. The download endpoint returns an S3 URL to a zip bundle — request the bundle, download the zip, then extract.

**SDK — Download and extract:**

```typescript
import { LokaliseApi } from "@lokalise/node-api";
import { execSync } from "node:child_process";
import { mkdirSync } from "node:fs";

const client = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });
const PROJECT_ID = process.env.LOKALISE_PROJECT_ID!;

// Request the download bundle
const download = await client.files().download(PROJECT_ID, {
  format: "json",
  original_filenames: false,
  bundle_structure: "%LANG_ISO%.json",     // Output: en.json, fr.json, de.json
  filter_langs: ["en", "fr", "de", "es"],  // Only these languages
  export_empty_as: "base",                 // Use base language for empty translations
  include_tags: ["release-3.0"],           // Only keys with this tag
  replace_breaks: false,
});

const bundleUrl = download.bundle_url;
console.log(`Bundle URL: ${bundleUrl}`);

// Download and extract
mkdirSync("./locales", { recursive: true });
execSync(`curl -sL "${bundleUrl}" -o /tmp/lokalise-bundle.zip`);
execSync(`unzip -o /tmp/lokalise-bundle.zip -d ./locales`);
console.log("Translations extracted to ./locales/");
```

**CLI — Download with structure:**

```bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" file download \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=false \
  --bundle-structure "locales/%LANG_ISO%.json" \
  --filter-langs "en,fr,de,es" \
  --export-empty-as base \
  --replace-breaks=false \
  --unzip-to .
```

**SDK — Download with original file structure preserved:**

```typescript
const download = await client.files().download(PROJECT_ID, {
  format: "json",
  original_filenames: true,
  directory_prefix: "",                    // No extra prefix
  export_empty_as: "skip",                 // Omit untranslated keys
  include_comments: false,
  include_description: false,
});
```

2. Manage translations — list, update, and mark as reviewed.

**SDK — List translations for a language:**

```typescript
const frTranslations = await client.translations().list({
  project_id: PROJECT_ID,
  filter_lang_id: 673,            // Language ID for French (find via languages endpoint)
  filter_is_reviewed: 0,          // Only unreviewed
  limit: 100,
});

for (const t of frTranslations.items) {
  console.log(`[${t.key_id}] ${t.translation} (reviewed: ${t.is_reviewed})`);
}
```

**SDK — Update a translation:**

```typescript
const updated = await client.translations().update(TRANSLATION_ID, {
  project_id: PROJECT_ID,
  translation: "Nouvelle traduction",
  is_reviewed: false,              // Mark as needing review after edit
});
```

**SDK — Mark translations as reviewed (batch):**

```typescript
const unreviewed = await client.translations().list({
  project_id: PROJECT_ID,
  filter_lang_id: LANG_ID,
  filter_is_reviewed: 0,
  limit: 500,
});

for (const t of unreviewed.items) {
  await client.translations().update(t.translation_id, {
    project_id: PROJECT_ID,
    is_reviewed: true,
  });
}

console.log(`Marked ${unreviewed.items.length} translations as reviewed`);
```

**SDK — List translations with cursor pagination (for large datasets):**

```typescript
async function* paginateTranslations(
  client: LokaliseApi,
  projectId: string,
  langId: number
) {
  let cursor: string | undefined;
  do {
    const params: Record<string, unknown> = {
      project_id: projectId,
      filter_lang_id: langId,
      limit: 500,
    };
    if (cursor) params.cursor = cursor;

    const page = await client.translations().list(params);
    yield* page.items;
    cursor = page.hasNextCursor() ? page.nextCursor() : undefined;
  } while (cursor);
}

// Usage
for await (const t of paginateTranslations(client, PROJECT_ID, 673)) {
  console.log(`${t.key_id}: ${t.translation}`);
}
```

3. Leverage translation memory (TM) for auto-suggestions based on previously translated segments.

**SDK — Use TM during upload:**

```typescript
const tmResults = await client.translationProviders().list({
  team_id: TEAM_ID,
});

// TM is automatically applied during file upload when `use_automations: true`
const upload = await client.files().upload(PROJECT_ID, {
  data: base64Data,
  filename: "en.json",
  lang_iso: "en",
  use_automations: true,       // Apply TM and MT suggestions automatically
  slashn_to_linebreak: true,
});
```

**SDK — Leverage TM during download (pre-translate empty keys):**

```typescript
// Pre-translate uses TM + MT before download
// First, trigger pre-translation
// Then download with filled translations
const download = await client.files().download(PROJECT_ID, {
  format: "json",
  original_filenames: false,
  bundle_structure: "%LANG_ISO%.json",
  export_empty_as: "base",    // Fallback to base language if TM has no match
});
```

4. Manage contributors — add translators and configure language access.

**SDK — Add a translator with specific language access:**

```typescript
const contributor = await client.contributors().create({
  project_id: PROJECT_ID,
  contributors: [
    {
      email: "translator@example.com",
      fullname: "Marie Dupont",
      is_admin: false,
      is_reviewer: true,
      languages: [
        {
          lang_iso: "fr",
          is_writable: true,       // Can edit French translations
        },
        {
          lang_iso: "de",
          is_writable: false,      // Read-only access to German
        },
      ],
    },
  ],
});

console.log(`Added contributor: ${contributor.items[0].email}`);
```

**SDK — List all contributors:**

```typescript
const contributors = await client.contributors().list({
  project_id: PROJECT_ID,
  limit: 100,
});

for (const c of contributors.items) {
  const langs = c.languages.map(
    (l: { lang_iso: string; is_writable: boolean }) =>
      `${l.lang_iso}${l.is_writable ? "(rw)" : "(r)"}`
  ).join(", ");
  console.log(`${c.fullname} <${c.email}> — ${langs}`);
}
```

**SDK — Update contributor permissions:**

```typescript
await client.contributors().update(CONTRIBUTOR_ID, {
  project_id: PROJECT_ID,
  is_reviewer: true,
  languages: [
    { lang_iso: "fr", is_writable: true },
    { lang_iso: "es", is_writable: true },   // Grant Spanish write access
  ],
});
```

5. Handle file format differences across JSON flat, JSON nested, XLIFF, and PO.

**JSON flat (react-i18next default):**

```json
{
  "greeting.hello": "Hello",
  "greeting.goodbye": "Goodbye",
  "errors.network": "Network error"
}
```

Download config:

```typescript
const download = await client.files().download(PROJECT_ID, {
  format: "json",
  json_unescaped_slashes: true,
  original_filenames: false,
  bundle_structure: "%LANG_ISO%.json",
  placeholder_format: "icu",          // {name} style
  export_sort: "a_z",
});
```

**JSON nested (next-intl, vue-i18n):**

```json
{
  "greeting": {
    "hello": "Hello",
    "goodbye": "Goodbye"
  },
  "errors": {
    "network": "Network error"
  }
}
```

Download config — use `_` as key separator so Lokalise nests on `.`:

```bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" file download \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=false \
  --bundle-structure "%LANG_ISO%.json" \
  --export-key-name-as "key_name_dot_separated" \
  --unzip-to ./locales
```

**XLIFF 1.2 (iOS, Angular):**

```typescript
const download = await client.files().download(PROJECT_ID, {
  format: "xliff",
  original_filenames: false,
  bundle_structure: "%LANG_ISO%.xliff",
  export_empty_as: "empty",
});
```

**PO / GNU gettext:**

```bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" file download \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format po \
  --original-filenames=false \
  --bundle-structure "%LANG_ISO%/LC_MESSAGES/messages.po" \
  --unzip-to ./locales
```

**Upload format auto-detection:**

```typescript
// Lokalise detects format from filename extension
// Just make sure the filename matches the content format
await client.files().upload(PROJECT_ID, {
  data: base64Data,
  filename: "messages.xliff",   // Triggers XLIFF parser
  lang_iso: "en",
});
```

## Output

- Downloaded translation files extracted to project directory
- Translations updated and review status managed
- Contributors added with appropriate language permissions
- Files exported in the correct format for your i18n framework

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `404 Project not found` | Wrong `project_id` | Run `client.projects().list()` to verify |
| `Empty bundle (0 files)` | No translations match filters | Remove `include_tags` / `filter_langs` to broaden |
| `400 Invalid format` | Unsupported export format string | Use: `json`, `xliff`, `po`, `strings`, `xml`, `yaml` |
| `Download timeout` | Large project with many languages | Filter to specific languages with `filter_langs` |
| `403 Forbidden` | Contributor lacks write access | Check contributor language permissions |
| `curl: (28) Operation timed out` | S3 bundle URL expired (valid ~30 min) | Request a fresh download URL |

## Examples

### Build-Time Translation Fetch

```typescript
// scripts/fetch-translations.ts — run in CI before build
import { LokaliseApi } from "@lokalise/node-api";
import { execSync } from "node:child_process";
import { mkdirSync, readdirSync } from "node:fs";

const client = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });
const PROJECT_ID = process.env.LOKALISE_PROJECT_ID!;

const download = await client.files().download(PROJECT_ID, {
  format: "json",
  original_filenames: false,
  bundle_structure: "%LANG_ISO%.json",
  export_empty_as: "base",
  export_sort: "a_z",
  replace_breaks: false,
});

mkdirSync("./src/locales", { recursive: true });
execSync(`curl -sL "${download.bundle_url}" -o /tmp/i18n.zip`);
execSync("unzip -o /tmp/i18n.zip -d ./src/locales");

const files = readdirSync("./src/locales").filter((f) => f.endsWith(".json"));
console.log(`Downloaded ${files.length} locale files: ${files.join(", ")}`);
```

### Contributor Onboarding Script

```typescript
const translators = [
  { email: "hans@example.com", name: "Hans Mueller", langs: ["de"] },
  { email: "yuki@example.com", name: "Yuki Tanaka", langs: ["ja"] },
  { email: "ana@example.com",  name: "Ana Garcia",  langs: ["es", "pt"] },
];

for (const t of translators) {
  await client.contributors().create({
    project_id: PROJECT_ID,
    contributors: [{
      email: t.email,
      fullname: t.name,
      is_admin: false,
      is_reviewer: false,
      languages: t.langs.map((l) => ({ lang_iso: l, is_writable: true })),
    }],
  });
  console.log(`Invited ${t.name} for ${t.langs.join(", ")}`);
}
```

## Resources

- [File Download API](https://developers.lokalise.com/reference/download-files)
- [Translations API](https://developers.lokalise.com/reference/list-all-translations)
- [Contributors API](https://developers.lokalise.com/reference/list-all-contributors)
- [Export Options Reference](https://docs.lokalise.com/en/articles/1400465-exporting-translation-files)
- [Bundle Structure Placeholders](https://docs.lokalise.com/en/articles/2281317-filenames)
- [Supported File Formats](https://docs.lokalise.com/en/articles/1400492-uploading-translation-files)

## Next Steps

For common errors and troubleshooting, see `lokalise-common-errors`. For production SDK patterns, see `lokalise-sdk-patterns`.
