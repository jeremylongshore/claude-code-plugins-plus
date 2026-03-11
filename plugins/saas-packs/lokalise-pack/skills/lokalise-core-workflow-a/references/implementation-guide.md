# Lokalise Core Workflow A - Implementation Guide

Detailed implementation reference for the lokalise-core-workflow-a skill.

## Instructions

### Step 1: Upload Source File via CLI
```bash
# Basic file upload
lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file upload \
  --file "./locales/en.json" \
  --lang-iso en \
  --replace-modified \
  --distinguish-by-file \
  --poll \
  --poll-timeout 120s

# Upload with key tagging
lokalise2 \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file upload \
  --file "./locales/en.json" \
  --lang-iso en \
  --tags "web,v2.0" \
  --tag-inserted-keys \
  --tag-updated-keys \
  --poll
```

### Step 2: Upload via SDK (Async Process)
```typescript
import { LokaliseApi } from "@lokalise/node-api";
import fs from "fs";
import path from "path";

const lokaliseApi = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
});

async function uploadFile(projectId: string, filePath: string, langIso: string) {
  // Read and base64 encode the file
  const fileContent = fs.readFileSync(filePath);
  const base64Content = fileContent.toString("base64");
  const fileName = path.basename(filePath);

  // Start async upload process
  const process = await lokaliseApi.files().upload(projectId, {
    data: base64Content,
    filename: fileName,
    lang_iso: langIso,
    replace_modified: true,
    convert_placeholders: true,
    detect_icu_plurals: true,
    tags: ["uploaded-via-sdk"],
  });

  console.log(`Upload started: Process ID ${process.process_id}`);

  // Poll for completion
  return pollUploadProcess(projectId, process.process_id);
}

async function pollUploadProcess(projectId: string, processId: string) {
  const maxAttempts = 60;
  const delayMs = 2000;

  for (let i = 0; i < maxAttempts; i++) {
    const status = await lokaliseApi.queuedProcesses().get(processId, {
      project_id: projectId,
    });

    console.log(`Status: ${status.status} (${status.progress}%)`);

    if (status.status === "finished") {
      console.log("Upload completed successfully!");
      return status;
    }

    if (status.status === "failed" || status.status === "cancelled") {
      throw new Error(`Upload failed: ${status.status}`);
    }

    await new Promise(r => setTimeout(r, delayMs));
  }

  throw new Error("Upload timed out");
}
```

### Step 3: Create Keys Programmatically
```typescript
async function createKeys(projectId: string) {
  const keys = await lokaliseApi.keys().create({
    project_id: projectId,
    keys: [
      {
        key_name: "common.buttons.submit",
        description: "Submit button text",
        platforms: ["web", "ios", "android"],
        tags: ["buttons", "common"],
        translations: [
          { language_iso: "en", translation: "Submit" },
          { language_iso: "es", translation: "Enviar" },
        ],
      },
      {
        key_name: "common.buttons.cancel",
        description: "Cancel button text",
        platforms: ["web", "ios", "android"],
        tags: ["buttons", "common"],
        translations: [
          { language_iso: "en", translation: "Cancel" },
        ],
      },
      {
        key_name: "errors.network",
        description: "Network error message",
        platforms: ["web"],
        is_plural: false,
        tags: ["errors"],
        translations: [
          { language_iso: "en", translation: "Network error. Please try again." },
        ],
      },
    ],
  });

  console.log(`Created ${keys.items.length} keys`);
  return keys;
}
```

### Step 4: Update Existing Keys
```typescript
async function updateKey(projectId: string, keyId: number) {
  const updated = await lokaliseApi.keys().update(keyId, {
    project_id: projectId,
    description: "Updated description",
    tags: ["updated", "v2"],
    is_archived: false,
  });

  console.log(`Updated key: ${updated.key_name.web}`);
  return updated;
}

async function bulkUpdateKeys(projectId: string, keyIds: number[], updates: object) {
  const result = await lokaliseApi.keys().bulk_update({
    project_id: projectId,
    keys: keyIds.map(id => ({
      key_id: id,
      ...updates,
    })),
  });

  console.log(`Updated ${result.items.length} keys`);
  return result;
}
```

### Step 5: Manage Key Tags
```typescript
async function tagKeys(projectId: string, keyIds: number[], tags: string[]) {
  // Add tags to keys
  const result = await lokaliseApi.keys().bulk_update({
    project_id: projectId,
    keys: keyIds.map(id => ({
      key_id: id,
      tags,
    })),
  });

  return result;
}

async function getKeysByTag(projectId: string, tag: string) {
  const keys = await lokaliseApi.keys().list({
    project_id: projectId,
    filter_tags: tag,
    limit: 500,
  });

  return keys.items;
}
```


## Detailed Examples

### Supported File Formats
```typescript
// Lokalise supports many formats
const supportedFormats = [
  "json",           // JSON (nested or flat)
  "xliff",          // XLIFF 1.2 and 2.0
  "po",             // Gettext PO/POT
  "strings",        // iOS .strings
  "xml",            // Android XML
  "properties",     // Java properties
  "yaml",           // YAML
  "csv",            // CSV
  "xlsx",           // Excel
  "resx",           // .NET RESX
  "arb",            // Flutter ARB
];
```

### Upload with Cleanup Options
```bash
lokalise2 file upload \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file "./locales/en.json" \
  --lang-iso en \
  --cleanup-mode                  # Remove keys not in file
  --replace-modified              # Update existing translations
  --fill-empty                    # Copy base to empty translations
  --poll
```

### Batch File Upload
```typescript
async function uploadAllLocales(projectId: string, localesDir: string) {
  const files = fs.readdirSync(localesDir)
    .filter(f => f.endsWith(".json"));

  for (const file of files) {
    const langIso = path.basename(file, ".json");
    const filePath = path.join(localesDir, file);

    console.log(`Uploading ${file}...`);
    await uploadFile(projectId, filePath, langIso);

    // Respect rate limits
    await new Promise(r => setTimeout(r, 200));
  }
}
```

