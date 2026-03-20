---
name: lokalise-core-workflow-a
description: |
  Execute Lokalise primary workflow: Upload source files and manage translation keys.
  Use when uploading translation files, creating/updating keys,
  or managing source strings in Lokalise projects.
  Trigger with phrases like "lokalise upload", "lokalise push keys",
  "lokalise source strings", "add translations to lokalise".
allowed-tools: Read, Write, Edit, Bash(lokalise2:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Core Workflow A

## Overview

Primary workflow covering the "source to Lokalise" direction: upload translation files, create and update keys programmatically, tag keys for organization, and perform bulk operations. Both SDK and CLI approaches shown for every operation.

## Prerequisites

- Lokalise API token exported as `LOKALISE_API_TOKEN`
- Lokalise project ID exported as `LOKALISE_PROJECT_ID`
- `@lokalise/node-api` installed for SDK examples
- `lokalise2` CLI installed for CLI examples
- Source translation file(s) in a supported format (JSON, XLIFF, PO, YAML, etc.)

## Instructions

1. Upload source translation files. File upload is async: the API returns a process object that must be polled until completion.

**SDK — Base64 encode and upload:**

```typescript
import { LokaliseApi } from "@lokalise/node-api";
import { readFileSync } from "node:fs";

const client = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });
const PROJECT_ID = process.env.LOKALISE_PROJECT_ID!;

// Read and base64-encode the source file
const fileContent = readFileSync("./locales/en.json");
const base64Data = fileContent.toString("base64");

const uploadProcess = await client.files().upload(PROJECT_ID, {
  data: base64Data,
  filename: "en.json",
  lang_iso: "en",
  replace_modified: true,   // Overwrite changed translations
  distinguish_by_file: true, // Same key names in different files stay separate
  tags: ["source", "v2.1"],  // Auto-tag uploaded keys
});

console.log(`Upload queued: process ${uploadProcess.process_id}, status: ${uploadProcess.status}`);
```

**SDK — Poll upload process until complete:**

```typescript
async function waitForUpload(
  client: LokaliseApi,
  projectId: string,
  processId: string,
  maxWaitMs = 60_000
): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const proc = await client.queuedProcesses().get(processId, { project_id: projectId });
    console.log(`  Process ${processId}: ${proc.status}`);

    if (proc.status === "finished") return;
    if (proc.status === "cancelled" || proc.status === "failed") {
      throw new Error(`Upload ${proc.status}: ${JSON.stringify(proc.details)}`);
    }

    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`Upload timed out after ${maxWaitMs}ms`);
}

await waitForUpload(client, PROJECT_ID, uploadProcess.process_id);
console.log("Upload complete");
```

**CLI — Upload with polling:**

```bash
set -euo pipefail
lokalise2 --token "$LOKALISE_API_TOKEN" file upload \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file ./locales/en.json \
  --lang-iso en \
  --replace-modified \
  --distinguish-by-file \
  --tag-inserted-keys \
  --tag-updated-keys \
  --tags "source,v2.1" \
  --poll                     # Waits for process to finish
```

2. Create keys programmatically when keys come from code scanning, CMS exports, or CI pipelines rather than file uploads.

**SDK — Create keys with initial translations:**

```typescript
const newKeys = await client.keys().create({
  project_id: PROJECT_ID,
  keys: [
    {
      key_name: { web: "onboarding.step1.title" },
      platforms: ["web"],
      description: "First step of onboarding wizard",
      tags: ["onboarding", "v2.1"],
      translations: [
        { language_iso: "en", translation: "Welcome aboard!" },
      ],
    },
    {
      key_name: { web: "onboarding.step1.body" },
      platforms: ["web"],
      description: "Body text for onboarding step 1",
      tags: ["onboarding", "v2.1"],
      translations: [
        { language_iso: "en", translation: "Let's get you set up in just a few steps." },
      ],
    },
    {
      key_name: { web: "errors.network_timeout" },
      platforms: ["web"],
      description: "Shown when API call times out",
      is_hidden: false,
      tags: ["errors"],
      translations: [
        { language_iso: "en", translation: "Connection timed out. Please try again." },
      ],
    },
  ],
});

console.log(`Created ${newKeys.items.length} keys`);
for (const k of newKeys.items) {
  console.log(`  ${k.key_id}: ${k.key_name.web}`);
}
```

**SDK — Update existing keys:**

```typescript
const updatedKey = await client.keys().update(KEY_ID, {
  project_id: PROJECT_ID,
  description: "Updated description",
  tags: ["onboarding", "v2.2", "reviewed"],
  is_hidden: false,
});
```

3. Tag keys for organization. Tags let you filter keys in the Lokalise UI and API — useful for release tracking, feature flags, and workflow status.

**SDK — Add tags to existing keys (bulk):**

```typescript
// List keys by an existing tag
const v21Keys = await client.keys().list({
  project_id: PROJECT_ID,
  filter_tags: "v2.1",
  limit: 500,
});

// Bulk-update: add a new tag to all of them
const keyIds = v21Keys.items.map((k) => k.key_id);

const updated = await client.keys().bulk_update({
  project_id: PROJECT_ID,
  keys: keyIds.map((id) => ({
    key_id: id,
    tags: ["v2.1", "ready-for-review"],  // Full tag list (replaces existing)
  })),
});

console.log(`Tagged ${updated.items.length} keys with 'ready-for-review'`);
```

**SDK — Filter keys by tag:**

```typescript
const errorKeys = await client.keys().list({
  project_id: PROJECT_ID,
  filter_tags: "errors",
  include_translations: 1,
  limit: 100,
});

for (const k of errorKeys.items) {
  const en = k.translations.find(
    (t: { language_iso: string }) => t.language_iso === "en"
  );
  console.log(`${k.key_name.web}: ${en?.translation ?? "(empty)"}`);
}
```

4. Perform bulk key operations for large-scale changes.

**SDK — Bulk delete keys:**

```typescript
// Delete keys that are no longer in the codebase
const obsoleteKeys = await client.keys().list({
  project_id: PROJECT_ID,
  filter_tags: "deprecated",
  limit: 500,
});

if (obsoleteKeys.items.length > 0) {
  const deleteIds = obsoleteKeys.items.map((k) => k.key_id);
  const result = await client.keys().bulk_delete(deleteIds, {
    project_id: PROJECT_ID,
  });
  console.log(`Deleted ${result.keys_removed} keys`);
}
```

**SDK — Bulk update translations:**

```typescript
// Mark all translations for a tag as "needs review" by clearing is_reviewed
const keysToReview = await client.keys().list({
  project_id: PROJECT_ID,
  filter_tags: "v2.2",
  include_translations: 1,
  limit: 500,
});

for (const key of keysToReview.items) {
  for (const t of key.translations) {
    if (t.is_reviewed) {
      await client.translations().update(t.translation_id, {
        project_id: PROJECT_ID,
        is_reviewed: false,
      });
    }
  }
}
```

**CLI — Bulk operations:**

```bash
set -euo pipefail

# Upload multiple files in sequence (respect rate limits)
for lang in en fr de es ja; do
  lokalise2 --token "$LOKALISE_API_TOKEN" file upload \
    --project-id "$LOKALISE_PROJECT_ID" \
    --file "./locales/${lang}.json" \
    --lang-iso "$lang" \
    --replace-modified \
    --poll
  echo "Uploaded ${lang}.json"
  sleep 1  # Rate limit buffer
done

# Upload with cleanup mode (removes keys not present in file)
lokalise2 --token "$LOKALISE_API_TOKEN" file upload \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file ./locales/en.json \
  --lang-iso en \
  --cleanup-mode \
  --poll
```

## Output

- Source file uploaded to Lokalise with process confirmation
- Keys created with descriptions, tags, and base translations
- Keys organized by tags for filtering and workflow tracking
- Bulk operations completed with count summaries

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Invalid file format` | File extension or content not recognized | Verify format is in the supported formats list (see Resources) |
| `400 Key already exists` | Duplicate `key_name` + platform combo | Set `replace_modified: true` or use unique key names |
| `413 Payload Too Large` | Base64 payload exceeds 50MB | Split file or remove unused keys |
| `429 Too Many Requests` | Exceeded 6 req/sec | Add 170ms minimum delay between calls |
| `Process status: failed` | Invalid file content or encoding | Check file is valid JSON/XLIFF/PO and base64 encoding is correct |
| `400 keys must be an array` | Wrong payload shape for bulk ops | Wrap keys in an array even for single-key operations |

## Examples

### CI Pipeline: Extract and Upload

```typescript
// ci-upload.ts — extract keys from code and push to Lokalise
import { LokaliseApi } from "@lokalise/node-api";
import { readFileSync } from "node:fs";

const client = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });
const PROJECT_ID = process.env.LOKALISE_PROJECT_ID!;

// Upload the extracted source file
const data = readFileSync("./locales/en.json").toString("base64");
const proc = await client.files().upload(PROJECT_ID, {
  data,
  filename: "en.json",
  lang_iso: "en",
  replace_modified: true,
  cleanup_mode: true,       // Remove keys not in this file
  tags: [`build-${process.env.CI_BUILD_NUMBER ?? "local"}`],
});

// Wait for completion
let status = proc.status;
while (status === "queued" || status === "running") {
  await new Promise((r) => setTimeout(r, 2000));
  const check = await client.queuedProcesses().get(proc.process_id, {
    project_id: PROJECT_ID,
  });
  status = check.status;
}

if (status !== "finished") {
  console.error(`Upload failed with status: ${status}`);
  process.exit(1);
}

console.log("Source strings synced to Lokalise");
```

### Tag-Based Release Workflow

```bash
set -euo pipefail
# Tag all untagged keys with the current release
lokalise2 --token "$LOKALISE_API_TOKEN" key list \
  --project-id "$LOKALISE_PROJECT_ID" \
  --filter-tags "" \
  --limit 500 | jq -r '.[].key_id' | while read -r key_id; do
    lokalise2 --token "$LOKALISE_API_TOKEN" key update \
      --project-id "$LOKALISE_PROJECT_ID" \
      --key-id "$key_id" \
      --tags "release-3.0"
    sleep 0.2
done
```

## Resources

- [File Upload API](https://developers.lokalise.com/reference/upload-a-file)
- [Queued Processes](https://developers.lokalise.com/reference/list-all-processes)
- [Keys API — Create](https://developers.lokalise.com/reference/create-keys)
- [Keys API — Bulk Update](https://developers.lokalise.com/reference/bulk-update)
- [Keys API — Bulk Delete](https://developers.lokalise.com/reference/delete-multiple-keys)
- [Supported File Formats](https://docs.lokalise.com/en/articles/1400492-uploading-translation-files)

## Next Steps

For downloading translations and managing contributors, see `lokalise-core-workflow-b`.
