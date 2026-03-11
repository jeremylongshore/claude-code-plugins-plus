# Lokalise Upgrade Migration - Implementation Guide

Detailed implementation reference for the lokalise-upgrade-migration skill.

## Instructions

### Step 1: Check Current Version
```bash
# Check installed version
npm list @lokalise/node-api

# Check latest available version
npm view @lokalise/node-api version

# View all available versions
npm view @lokalise/node-api versions --json | jq '.[-10:]'

# Check CLI version
lokalise2 --version
```

### Step 2: Review Changelog
```bash
# View changelog
open https://github.com/lokalise/node-lokalise-api/releases

# Or check npm
npm view @lokalise/node-api repository.url
```

### Major Breaking Changes by Version

| SDK Version | Breaking Changes |
|-------------|-----------------|
| v9.x (2024+) | ESM only - no CommonJS require() |
| v8.x | Last CommonJS support |
| v7.x | New pagination API |
| v6.x | TypeScript strict mode |

### Step 3: Create Upgrade Branch
```bash
# Create branch for upgrade
git checkout -b upgrade/lokalise-sdk-v9

# Update SDK
npm install @lokalise/node-api@latest

# Run tests
npm test
```

### Step 4: Handle v8 to v9 Migration (ESM)
```typescript
// BEFORE (v8 - CommonJS)
const { LokaliseApi } = require("@lokalise/node-api");

// AFTER (v9 - ESM)
import { LokaliseApi } from "@lokalise/node-api";

// If you must use CommonJS, use dynamic import:
async function getClient() {
  const { LokaliseApi } = await import("@lokalise/node-api");
  return new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN });
}
```

### Step 5: Update package.json for ESM
```json
{
  "type": "module",
  "scripts": {
    "start": "node --experimental-specifier-resolution=node dist/index.js"
  }
}
```

### Step 6: Update TypeScript Configuration
```json
// tsconfig.json for ESM
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "NodeNext",
    "target": "ES2022",
    "esModuleInterop": true
  }
}
```


## Detailed Examples

### Deprecation Detection
```typescript
// Monitor for deprecation warnings during development
if (process.env.NODE_ENV === "development") {
  process.on("warning", (warning) => {
    if (warning.name === "DeprecationWarning") {
      console.warn("[Lokalise Deprecation]", warning.message);

      // Log to tracking for proactive updates
      trackDeprecation({
        message: warning.message,
        stack: warning.stack,
        timestamp: new Date(),
      });
    }
  });
}
```

### Version-Safe Import
```typescript
// utils/lokalise.ts - Works with both v8 and v9
let LokaliseApiClass: any;

async function getLokaliseApi() {
  if (!LokaliseApiClass) {
    try {
      // Try ESM import first (v9+)
      const module = await import("@lokalise/node-api");
      LokaliseApiClass = module.LokaliseApi;
    } catch {
      // Fall back to CommonJS (v8)
      LokaliseApiClass = require("@lokalise/node-api").LokaliseApi;
    }
  }

  return new LokaliseApiClass({
    apiKey: process.env.LOKALISE_API_TOKEN!,
  });
}
```

### Pagination Migration (v6 to v7+)
```typescript
// BEFORE (v6 - offset pagination only)
const keys = await client.keys().list({
  project_id: projectId,
  page: 1,
  limit: 100,
});

// AFTER (v7+ - cursor pagination available)
const keys = await client.keys().list({
  project_id: projectId,
  pagination: "cursor",  // New option
  limit: 500,
});

// Iterate with cursor
let cursor: string | undefined;
do {
  const result = await client.keys().list({
    project_id: projectId,
    pagination: "cursor",
    cursor,
    limit: 500,
  });

  processKeys(result.items);
  cursor = result.hasNextCursor() ? result.nextCursor : undefined;
} while (cursor);
```

### Rollback Procedure
```bash
# If upgrade causes issues, rollback immediately
npm install @lokalise/node-api@8.x.x --save-exact

# Revert ESM changes if needed
git checkout HEAD~1 -- tsconfig.json package.json

# Verify rollback
npm test
```

### Upgrade Validation Script
```typescript
async function validateUpgrade(): Promise<{
  success: boolean;
  issues: string[];
}> {
  const issues: string[] = [];

  try {
    const { LokaliseApi } = await import("@lokalise/node-api");
    const client = new LokaliseApi({
      apiKey: process.env.LOKALISE_API_TOKEN!,
    });

    // Test basic operations
    await client.projects().list({ limit: 1 });
    console.log("Project list: OK");

    // Test cursor pagination (v7+)
    const keys = await client.keys().list({
      project_id: process.env.LOKALISE_PROJECT_ID!,
      pagination: "cursor",
      limit: 10,
    });

    if (typeof keys.hasNextCursor !== "function") {
      issues.push("Cursor pagination not available - SDK may be outdated");
    }

    console.log("Cursor pagination: OK");

  } catch (error: any) {
    issues.push(`SDK validation failed: ${error.message}`);
  }

  return {
    success: issues.length === 0,
    issues,
  };
}
```

### CLI Upgrade
```bash
# macOS
brew upgrade lokalise2

# Linux - download latest release
curl -sL https://github.com/lokalise/lokalise-cli-2-go/releases/latest/download/lokalise2_linux_x86_64.tar.gz | tar xz

# Verify
lokalise2 --version
```

