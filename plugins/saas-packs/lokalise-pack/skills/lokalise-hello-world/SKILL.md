---
name: lokalise-hello-world
description: |
  Create a minimal working Lokalise example.
  Use when starting a new Lokalise integration, testing your setup,
  or learning basic Lokalise API patterns.
  Trigger with phrases like "lokalise hello world", "lokalise example",
  "lokalise quick start", "simple lokalise code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Hello World

## Overview

End-to-end walkthrough: list projects, create a test project, add keys, set translations across languages, and retrieve them. Covers both the Node SDK (`@lokalise/node-api`) and the CLI (`lokalise2`).

## Prerequisites

- Lokalise API token exported as `LOKALISE_API_TOKEN`
- Node.js 18+ with `@lokalise/node-api` installed (`npm i @lokalise/node-api`)
- Lokalise CLI v2 installed (`brew install lokalise2` or [binary releases](https://github.com/lokalise/lokalise-cli-2-go/releases))

## Instructions

1. List all projects using the SDK and CLI.

```typescript
import { LokaliseApi } from "@lokalise/node-api";

const client = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

const projects = await client.projects().list({ page: 1, limit: 20 });
for (const p of projects.items) {
  console.log(`${p.project_id}  ${p.name}  (${p.statistics.languages} languages)`);
}
```

```bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" project list
```

2. Create a test project with three languages.

```typescript
const project = await client.projects().create({
  name: "hello-world-test",
  description: "Quick start demo",
  languages: [
    { lang_iso: "en", custom_name: "English" },
    { lang_iso: "fr", custom_name: "French" },
    { lang_iso: "de", custom_name: "German" },
  ],
  base_language_iso: "en",
});

const PROJECT_ID = project.project_id;
console.log(`Created project: ${PROJECT_ID}`);
```

3. Add translation keys with their English (base language) translations in a single call.

```typescript
const keys = await client.keys().create({
  project_id: PROJECT_ID,
  keys: [
    {
      key_name: { web: "greeting.hello" },
      platforms: ["web"],
      translations: [{ language_iso: "en", translation: "Hello" }],
    },
    {
      key_name: { web: "greeting.goodbye" },
      platforms: ["web"],
      translations: [{ language_iso: "en", translation: "Goodbye" }],
    },
    {
      key_name: { web: "app.title" },
      platforms: ["web"],
      translations: [{ language_iso: "en", translation: "My Application" }],
    },
  ],
});

console.log(`Created ${keys.items.length} keys`);
```

4. Set translations for French and German by retrieving key IDs and updating each translation.

```typescript
const allKeys = await client.keys().list({
  project_id: PROJECT_ID,
  limit: 100,
});

const translations: Record<string, Record<string, string>> = {
  "greeting.hello":   { fr: "Bonjour",         de: "Hallo" },
  "greeting.goodbye": { fr: "Au revoir",       de: "Auf Wiedersehen" },
  "app.title":        { fr: "Mon Application",  de: "Meine Anwendung" },
};

for (const key of allKeys.items) {
  const keyName = key.key_name.web;
  const langs = translations[keyName];
  if (!langs) continue;

  for (const [langIso, value] of Object.entries(langs)) {
    const existing = key.translations.find(
      (t: { language_iso: string }) => t.language_iso === langIso
    );
    if (existing) {
      await client.translations().update(existing.translation_id, {
        project_id: PROJECT_ID,
        translation: value,
      });
    }
  }
}

console.log("Translations set for fr and de");
```

5. Retrieve and display all translations grouped by key.

```typescript
const result = await client.translations().list({
  project_id: PROJECT_ID,
  page: 1,
  limit: 100,
});

const grouped = new Map<number, { key: string; langs: Record<string, string> }>();
for (const t of result.items) {
  if (!grouped.has(t.key_id)) {
    grouped.set(t.key_id, { key: `key:${t.key_id}`, langs: {} });
  }
  grouped.get(t.key_id)!.langs[t.language_iso] = t.translation;
}

for (const [, entry] of grouped) {
  console.log(`\n${entry.key}`);
  for (const [lang, text] of Object.entries(entry.langs)) {
    console.log(`  ${lang}: ${text}`);
  }
}
```

6. Verify via CLI by listing keys and exporting translations.

```bash
set -euo pipefail
PROJECT_ID="YOUR_PROJECT_ID"

# List keys
lokalise2 --token "$LOKALISE_API_TOKEN" key list \
  --project-id "$PROJECT_ID" \
  --limit 100

# Export all translations as JSON
lokalise2 --token "$LOKALISE_API_TOKEN" file download \
  --project-id "$PROJECT_ID" \
  --format json \
  --original-filenames=false \
  --bundle-structure "%LANG_ISO%.json" \
  --unzip-to ./locales
```

## Output

- A new Lokalise project with 3 keys and translations in 3 languages
- Console output showing all key/translation pairs
- Exported JSON files in `./locales/` (if CLI step run)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API token | Verify `LOKALISE_API_TOKEN` is set and valid |
| `400 Bad Request` | Missing required fields (e.g., `key_name`) | Check payload matches API schema |
| `404 Not Found` | Project ID does not exist | Run project list to get correct ID |
| `429 Too Many Requests` | Exceeded 6 req/sec rate limit | Add 170ms delay between calls or batch operations |
| `Cannot find module` | SDK not installed | Run `npm i @lokalise/node-api` |

## Examples

### Minimal One-File Script

```typescript
// hello-lokalise.ts — run with: npx tsx hello-lokalise.ts
import { LokaliseApi } from "@lokalise/node-api";

const api = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Create project
const proj = await api.projects().create({
  name: `demo-${Date.now()}`,
  languages: [{ lang_iso: "en" }, { lang_iso: "es" }],
  base_language_iso: "en",
});

// Add a key with translations
await api.keys().create({
  project_id: proj.project_id,
  keys: [{
    key_name: { web: "welcome" },
    platforms: ["web"],
    translations: [
      { language_iso: "en", translation: "Welcome" },
      { language_iso: "es", translation: "Bienvenido" },
    ],
  }],
});

// Read it back
const translations = await api.translations().list({
  project_id: proj.project_id,
  limit: 10,
});

for (const t of translations.items) {
  console.log(`[${t.language_iso}] ${t.translation}`);
}

// Cleanup
await api.projects().delete(proj.project_id);
console.log("Project deleted");
```

### CLI-Only Quick Test

```bash
set -euo pipefail

# Create project
PROJECT=$(lokalise2 --token "$LOKALISE_API_TOKEN" project create \
  --name "cli-test-$(date +%s)" \
  --base-language-iso en \
  --languages '[{"lang_iso":"en"},{"lang_iso":"ja"}]' 2>&1)

PROJECT_ID=$(echo "$PROJECT" | grep -oP 'Project ID: \K[^\s]+')

# Upload a source file
echo '{"hello":"Hello","bye":"Bye"}' > /tmp/en.json
lokalise2 --token "$LOKALISE_API_TOKEN" file upload \
  --project-id "$PROJECT_ID" \
  --file /tmp/en.json \
  --lang-iso en \
  --poll

echo "Project $PROJECT_ID created and source uploaded"
```

## Resources

- [Lokalise API Reference](https://developers.lokalise.com/reference/lokalise-rest-api)
- [Projects API](https://developers.lokalise.com/reference/list-all-projects)
- [Keys API](https://developers.lokalise.com/reference/create-keys)
- [Translations API](https://developers.lokalise.com/reference/list-all-translations)
- [Node SDK Docs](https://lokalise.github.io/node-lokalise-api/)

## Next Steps

Proceed to `lokalise-local-dev-loop` for development workflow setup, or `lokalise-core-workflow-a` for file upload and key management.
