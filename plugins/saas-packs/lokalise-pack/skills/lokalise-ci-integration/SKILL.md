---
name: lokalise-ci-integration
description: |
  Configure Lokalise CI/CD integration with GitHub Actions and automated sync.
  Use when setting up automated translation sync, configuring CI pipelines,
  or integrating Lokalise into your build process.
  Trigger with phrases like "lokalise CI", "lokalise GitHub Actions",
  "lokalise automated sync", "CI lokalise", "lokalise pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise CI Integration

## Overview

Automate the full translation lifecycle through GitHub Actions: upload source strings when code is pushed, download translations during builds, block PRs with missing translations, and manage branch-based translation workflows that mirror your Git branching strategy. The goal is zero manual translation file management — developers write code, translators work in Lokalise, and CI keeps everything in sync.

## Prerequisites

- Lokalise project with Project ID (Settings > General > Project ID)
- Lokalise API token with read/write permissions (Profile > API Tokens), stored as `LOKALISE_API_TOKEN` GitHub secret
- `LOKALISE_PROJECT_ID` stored as GitHub secret (or variable)
- Lokalise CLI v2 (`lokalise2`) — installed in CI via `curl -sfL https://raw.githubusercontent.com/nicktomlin/lokalise-cli-2-install/master/install.sh | sh`
- Source locale files committed to the repository (e.g., `src/locales/en.json`)

## Instructions

### Step 1: Upload Source Strings on Push

Create `.github/workflows/lokalise-upload.yml` to push source strings to Lokalise whenever the default locale file changes on `main`:

```yaml
name: Upload translations to Lokalise
on:
  push:
    branches: [main]
    paths:
      - 'src/locales/en.json'  # Adjust to your source locale path

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Lokalise CLI
        run: |
          curl -sfL https://raw.githubusercontent.com/lokalise/lokalise-cli-2-go/master/install.sh | sh
          sudo mv ./bin/lokalise2 /usr/local/bin/lokalise2

      - name: Upload source strings
        run: |
          lokalise2 file upload \
            --token "${{ secrets.LOKALISE_API_TOKEN }}" \
            --project-id "${{ secrets.LOKALISE_PROJECT_ID }}" \
            --file "src/locales/en.json" \
            --lang-iso "en" \
            --replace-modified \
            --include-path \
            --distinguish-by-file \
            --poll \
            --poll-timeout 120s
        # --replace-modified updates existing keys with new values
        # --poll waits for the async upload to complete before exiting
```

### Step 2: Download Translations During Build

Create `.github/workflows/lokalise-build.yml` or add a step to your existing build workflow:

```yaml
name: Build with translations
on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Lokalise CLI
        run: |
          curl -sfL https://raw.githubusercontent.com/lokalise/lokalise-cli-2-go/master/install.sh | sh
          sudo mv ./bin/lokalise2 /usr/local/bin/lokalise2

      - name: Download translations
        run: |
          lokalise2 file download \
            --token "${{ secrets.LOKALISE_API_TOKEN }}" \
            --project-id "${{ secrets.LOKALISE_PROJECT_ID }}" \
            --format json \
            --original-filenames=true \
            --directory-prefix="" \
            --export-empty-as=base \
            --unzip-to "src/locales/"
        # --export-empty-as=base falls back to source language for untranslated keys
        # --original-filenames preserves the file structure from Lokalise

      - name: Build application
        run: npm run build
```

### Step 3: PR Check for Missing Translations

Add a workflow that comments on PRs when new translation keys lack translations in required locales:

```yaml
name: Translation coverage check
on:
  pull_request:
    paths:
      - 'src/locales/**'

jobs:
  check-translations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check translation coverage
        run: |
          #!/bin/bash
          set -euo pipefail

          REQUIRED_LOCALES=("en" "de" "fr" "es" "ja")
          SOURCE_FILE="src/locales/en.json"
          MISSING=0
          REPORT=""

          source_keys=$(jq -r '[paths(scalars)] | map(join(".")) | .[]' "$SOURCE_FILE" | sort)

          for locale in "${REQUIRED_LOCALES[@]}"; do
            locale_file="src/locales/${locale}.json"
            if [[ ! -f "$locale_file" ]]; then
              REPORT+="- **${locale}**: File missing entirely\n"
              MISSING=1
              continue
            fi

            locale_keys=$(jq -r '[paths(scalars)] | map(join(".")) | .[]' "$locale_file" | sort)
            missing_keys=$(comm -23 <(echo "$source_keys") <(echo "$locale_keys"))

            if [[ -n "$missing_keys" ]]; then
              count=$(echo "$missing_keys" | wc -l)
              REPORT+="- **${locale}**: ${count} missing keys\n"
              MISSING=1
            fi
          done

          if [[ $MISSING -eq 1 ]]; then
            echo "## Translation Coverage Report" >> "$GITHUB_STEP_SUMMARY"
            echo "" >> "$GITHUB_STEP_SUMMARY"
            echo -e "$REPORT" >> "$GITHUB_STEP_SUMMARY"
            echo "" >> "$GITHUB_STEP_SUMMARY"
            echo "Run \`lokalise2 file download\` to pull latest translations." >> "$GITHUB_STEP_SUMMARY"
            exit 1
          fi

          echo "All locales have complete translation coverage." >> "$GITHUB_STEP_SUMMARY"
```

### Step 4: Integration Tests for Key Coverage

Add a test that validates translation files have all required keys at build time:

```typescript
// tests/i18n-coverage.test.ts
import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.resolve(__dirname, '../src/locales');
const SOURCE_LOCALE = 'en';
const REQUIRED_LOCALES = ['en', 'de', 'fr', 'es', 'ja'];

function flattenKeys(obj: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([key, value]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      return flattenKeys(value as Record<string, unknown>, fullKey);
    }
    return [fullKey];
  });
}

describe('Translation coverage', () => {
  const sourceFile = JSON.parse(
    fs.readFileSync(path.join(LOCALES_DIR, `${SOURCE_LOCALE}.json`), 'utf-8')
  );
  const sourceKeys = flattenKeys(sourceFile).sort();

  for (const locale of REQUIRED_LOCALES) {
    it(`${locale}.json contains all source keys`, () => {
      const localeFile = JSON.parse(
        fs.readFileSync(path.join(LOCALES_DIR, `${locale}.json`), 'utf-8')
      );
      const localeKeys = flattenKeys(localeFile).sort();
      const missing = sourceKeys.filter(k => !localeKeys.includes(k));

      expect(missing, `Missing keys in ${locale}: ${missing.join(', ')}`).toHaveLength(0);
    });
  }

  it('no orphaned keys exist in non-source locales', () => {
    for (const locale of REQUIRED_LOCALES.filter(l => l !== SOURCE_LOCALE)) {
      const localeFile = JSON.parse(
        fs.readFileSync(path.join(LOCALES_DIR, `${locale}.json`), 'utf-8')
      );
      const localeKeys = flattenKeys(localeFile);
      const orphaned = localeKeys.filter(k => !sourceKeys.includes(k));

      expect(orphaned, `Orphaned keys in ${locale}: ${orphaned.join(', ')}`).toHaveLength(0);
    }
  });
});
```

### Step 5: Branch-Based Translation Workflow

Use Lokalise branching to isolate translation work per feature branch. This prevents in-progress translations from leaking into production:

```yaml
# .github/workflows/lokalise-branch.yml
name: Lokalise branch management
on:
  pull_request:
    types: [opened, synchronize, closed]
    paths:
      - 'src/locales/en.json'

jobs:
  manage-branch:
    runs-on: ubuntu-latest
    env:
      BRANCH_NAME: ${{ github.head_ref }}
    steps:
      - uses: actions/checkout@v4

      - name: Create Lokalise branch on PR open
        if: github.event.action == 'opened'
        run: |
          curl -X POST "https://api.lokalise.com/api2/projects/${{ secrets.LOKALISE_PROJECT_ID }}/branches" \
            -H "X-Api-Token: ${{ secrets.LOKALISE_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"${BRANCH_NAME}\"}"

      - name: Upload source to branch
        if: github.event.action == 'opened' || github.event.action == 'synchronize'
        run: |
          # Upload to the branch-specific project
          # Branch project ID format: {project_id}:{branch_name}
          lokalise2 file upload \
            --token "${{ secrets.LOKALISE_API_TOKEN }}" \
            --project-id "${{ secrets.LOKALISE_PROJECT_ID }}:${BRANCH_NAME}" \
            --file "src/locales/en.json" \
            --lang-iso "en" \
            --replace-modified \
            --poll \
            --poll-timeout 120s

      - name: Merge Lokalise branch on PR merge
        if: github.event.action == 'closed' && github.event.pull_request.merged == true
        run: |
          curl -X POST "https://api.lokalise.com/api2/projects/${{ secrets.LOKALISE_PROJECT_ID }}/branches/merge" \
            -H "X-Api-Token: ${{ secrets.LOKALISE_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d "{\"source_branch\": \"${BRANCH_NAME}\", \"target_branch\": \"main\", \"force_conflict_resolve_using\": \"source\"}"

      - name: Delete Lokalise branch on PR close (unmerged)
        if: github.event.action == 'closed' && github.event.pull_request.merged == false
        run: |
          # Get branch ID first
          BRANCH_ID=$(curl -s "https://api.lokalise.com/api2/projects/${{ secrets.LOKALISE_PROJECT_ID }}/branches" \
            -H "X-Api-Token: ${{ secrets.LOKALISE_API_TOKEN }}" \
            | jq -r ".branches[] | select(.name == \"${BRANCH_NAME}\") | .branch_id")

          if [[ -n "$BRANCH_ID" ]]; then
            curl -X DELETE "https://api.lokalise.com/api2/projects/${{ secrets.LOKALISE_PROJECT_ID }}/branches/${BRANCH_ID}" \
              -H "X-Api-Token: ${{ secrets.LOKALISE_API_TOKEN }}"
          fi
```

## Output

After applying this skill, the project will have:
- GitHub Actions workflow files for upload, download, and branch management
- PR checks that block merges when translations are incomplete
- Integration tests validating key coverage across all required locales
- Branch-based isolation so feature work does not pollute the main translation set
- A `scripts/lokalise-pull.sh` for local development use

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Upload returns 401 | Token expired or invalid | Rotate token in Lokalise dashboard, update GitHub secret |
| Upload returns 429 | Rate limit exceeded (6 req/sec) | Add retry with exponential backoff; batch file uploads |
| Download produces empty files | `export-empty-as` not set | Use `--export-empty-as=base` to fall back to source language |
| Branch merge conflicts | Same key modified in both branches | Use `force_conflict_resolve_using: source` or resolve manually in Lokalise UI |
| PR check fails on new keys | Translations not yet done | Expected — translators work in Lokalise, re-run check after translations complete |
| `--poll` times out | Large file or Lokalise queue backed up | Increase `--poll-timeout`; check Lokalise status page |
| Wrong file paths after download | `directory-prefix` mismatch | Set `--directory-prefix=""` and `--original-filenames=true` |
| CI hangs on upload | Missing `--poll` flag | Without `--poll`, upload is async — add the flag to wait for completion |

## Examples

### Local Translation Script

```bash
#!/bin/bash
# scripts/lokalise-pull.sh — Pull latest translations for local development
set -euo pipefail

: "${LOKALISE_API_TOKEN:?Set LOKALISE_API_TOKEN in your environment}"
: "${LOKALISE_PROJECT_ID:?Set LOKALISE_PROJECT_ID in your environment}"

echo "Downloading translations from Lokalise..."
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=true \
  --directory-prefix="" \
  --export-empty-as=base \
  --unzip-to "src/locales/"

echo "Translations updated at src/locales/"
ls -la src/locales/
```

### Upload Script with Retry

```bash
#!/bin/bash
# scripts/lokalise-push.sh — Upload source strings with retry logic
set -euo pipefail

MAX_RETRIES=3
RETRY_DELAY=5

for attempt in $(seq 1 $MAX_RETRIES); do
  if lokalise2 file upload \
    --token "$LOKALISE_API_TOKEN" \
    --project-id "$LOKALISE_PROJECT_ID" \
    --file "src/locales/en.json" \
    --lang-iso "en" \
    --replace-modified \
    --poll \
    --poll-timeout 120s; then
    echo "Upload successful on attempt $attempt"
    exit 0
  fi

  echo "Attempt $attempt failed, retrying in ${RETRY_DELAY}s..."
  sleep $RETRY_DELAY
  RETRY_DELAY=$((RETRY_DELAY * 2))
done

echo "Upload failed after $MAX_RETRIES attempts"
exit 1
```

## Resources

- [Lokalise CLI v2 Reference](https://docs.lokalise.com/en/articles/3659951-lokalise-cli-tool)
- [Lokalise API v2 — File Upload](https://developers.lokalise.com/reference/upload-a-file)
- [Lokalise API v2 — File Download](https://developers.lokalise.com/reference/download-files)
- [Lokalise Branching](https://docs.lokalise.com/en/articles/3181040-branching)
- [Lokalise GitHub Integration](https://docs.lokalise.com/en/articles/3632575-github)
- [Lokalise Status Page](https://status.lokalise.com)

## Next Steps

- Set up `lokalise-multi-env-setup` to manage per-environment API tokens and project IDs
- Use `lokalise-prod-checklist` before your first production deployment
- Configure webhook-based sync for real-time translation updates (Lokalise Settings > Integrations > Webhooks)
