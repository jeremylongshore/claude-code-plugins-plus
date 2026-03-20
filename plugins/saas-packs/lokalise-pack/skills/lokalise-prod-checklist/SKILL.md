---
name: lokalise-prod-checklist
description: |
  Execute Lokalise production deployment checklist and rollback procedures.
  Use when deploying Lokalise integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "lokalise production", "deploy lokalise",
  "lokalise go-live", "lokalise launch checklist".
allowed-tools: Read, Bash(lokalise2:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Production Checklist

## Overview

A structured pre-deployment checklist for Lokalise integrations covering nine verification areas: translation coverage, missing key detection, format validation, API token security, rate limit preparedness, fallback language configuration, download verification, OTA configuration, and contributor access review. Run through each section before any production deployment.

## Prerequisites

- Lokalise project with production API token
- `lokalise2` CLI installed and authenticated
- `curl` and `jq` available in your environment
- Access to the Lokalise dashboard (Team Owner or Admin role)
- Application codebase with i18n integration ready for deployment

## Instructions

### Step 1: Translation Coverage Audit

Verify that every supported locale meets the coverage threshold before deploying.

```bash
#!/bin/bash
# scripts/audit-translation-coverage.sh
set -euo pipefail

: "${LOKALISE_API_TOKEN:?Required}"
: "${LOKALISE_PROJECT_ID:?Required}"

REQUIRED_COVERAGE=100  # Percentage required for production
REQUIRED_LOCALES=("en" "de" "fr" "es" "ja")

echo "=== Translation Coverage Audit ==="

# Get project statistics from Lokalise API
STATS=$(curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/statistics" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}")

TOTAL_KEYS=$(echo "$STATS" | jq '.project_statistics.keys_total')
echo "Total keys in project: $TOTAL_KEYS"

# Get per-language statistics
LANGUAGES=$(curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/languages" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}")

FAILED=0
echo ""
echo "Locale   | Progress | Words     | Status"
echo "---------|----------|-----------|-------"

for locale in "${REQUIRED_LOCALES[@]}"; do
  progress=$(echo "$LANGUAGES" | jq -r ".languages[] | select(.lang_iso == \"${locale}\") | .statistics.progress")
  words=$(echo "$LANGUAGES" | jq -r ".languages[] | select(.lang_iso == \"${locale}\") | .statistics.words_to_do")

  if [[ -z "$progress" || "$progress" == "null" ]]; then
    echo "${locale}      | MISSING  | -         | FAIL"
    FAILED=1
    continue
  fi

  if (( $(echo "$progress < $REQUIRED_COVERAGE" | bc -l) )); then
    echo "${locale}      | ${progress}%   | ${words} remaining | FAIL"
    FAILED=1
  else
    echo "${locale}      | ${progress}%   | 0         | PASS"
  fi
done

echo ""
if [[ $FAILED -eq 1 ]]; then
  echo "RESULT: FAILED — Resolve incomplete translations before deploying."
  exit 1
fi
echo "RESULT: PASSED — All locales meet ${REQUIRED_COVERAGE}% coverage."
```

### Step 2: Missing Key Detection

Detect keys present in source code but absent from Lokalise, and vice versa.

```bash
#!/bin/bash
# scripts/detect-missing-keys.sh
set -euo pipefail

: "${LOKALISE_API_TOKEN:?Required}"
: "${LOKALISE_PROJECT_ID:?Required}"

echo "=== Missing Key Detection ==="

# Download current translation keys from Lokalise
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=true \
  --directory-prefix="" \
  --unzip-to "$TEMP_DIR/" 2>/dev/null

# Extract keys from Lokalise download
LOKALISE_KEYS=$(jq -r '[paths(scalars)] | map(join(".")) | .[]' "$TEMP_DIR/en.json" | sort)

# Extract keys referenced in source code (adjust pattern for your framework)
# React/i18next: t('key'), t("key"), <Trans i18nKey="key">
SOURCE_KEYS=$(grep -roh "t(['\"][^'\"]*['\"])" src/ 2>/dev/null \
  | sed "s/t(['\"]//;s/['\"])//" \
  | sort -u || true)

echo ""
echo "Keys in Lokalise:    $(echo "$LOKALISE_KEYS" | wc -l)"
echo "Keys in source code: $(echo "$SOURCE_KEYS" | wc -l)"

# Keys in code but not in Lokalise
MISSING_IN_LOKALISE=$(comm -23 <(echo "$SOURCE_KEYS") <(echo "$LOKALISE_KEYS") || true)
if [[ -n "$MISSING_IN_LOKALISE" ]]; then
  echo ""
  echo "MISSING IN LOKALISE (used in code but not uploaded):"
  echo "$MISSING_IN_LOKALISE" | head -20
  COUNT=$(echo "$MISSING_IN_LOKALISE" | wc -l)
  [[ $COUNT -gt 20 ]] && echo "  ... and $((COUNT - 20)) more"
fi

# Keys in Lokalise but not in code (potential dead keys)
ORPHANED=$(comm -13 <(echo "$SOURCE_KEYS") <(echo "$LOKALISE_KEYS") || true)
if [[ -n "$ORPHANED" ]]; then
  echo ""
  echo "ORPHANED IN LOKALISE (not referenced in code):"
  echo "$ORPHANED" | head -20
  COUNT=$(echo "$ORPHANED" | wc -l)
  [[ $COUNT -gt 20 ]] && echo "  ... and $((COUNT - 20)) more"
fi

if [[ -z "$MISSING_IN_LOKALISE" && -z "$ORPHANED" ]]; then
  echo ""
  echo "RESULT: PASSED — Keys are in sync."
fi
```

### Step 3: Format Validation

Validate that downloaded translation files are well-formed JSON and contain no placeholder mismatches.

```typescript
// scripts/validate-translation-format.ts
import fs from 'fs';
import path from 'path';

const LOCALES_DIR = 'src/locales';
const SOURCE_LOCALE = 'en';
const PLACEHOLDER_REGEX = /\{\{?\w+\}?\}|%[sd@]|\$\{[\w.]+\}/g;

interface ValidationResult {
  locale: string;
  valid: boolean;
  errors: string[];
}

function validate(): ValidationResult[] {
  const results: ValidationResult[] = [];
  const sourceFile = path.join(LOCALES_DIR, `${SOURCE_LOCALE}.json`);
  const sourceContent = JSON.parse(fs.readFileSync(sourceFile, 'utf-8'));
  const sourcePlaceholders = extractPlaceholders(sourceContent);

  for (const file of fs.readdirSync(LOCALES_DIR)) {
    if (!file.endsWith('.json')) continue;
    const locale = file.replace('.json', '');
    const errors: string[] = [];

    // Check 1: Valid JSON
    let content: Record<string, unknown>;
    try {
      content = JSON.parse(fs.readFileSync(path.join(LOCALES_DIR, file), 'utf-8'));
    } catch (e) {
      errors.push(`Invalid JSON: ${(e as Error).message}`);
      results.push({ locale, valid: false, errors });
      continue;
    }

    // Check 2: No empty string values (should be null or absent)
    const emptyKeys = findEmptyValues(content);
    if (emptyKeys.length > 0) {
      errors.push(`Empty string values: ${emptyKeys.slice(0, 5).join(', ')}${emptyKeys.length > 5 ? ` (+${emptyKeys.length - 5} more)` : ''}`);
    }

    // Check 3: Placeholder consistency
    const localePlaceholders = extractPlaceholders(content);
    for (const [key, expected] of Object.entries(sourcePlaceholders)) {
      const actual = localePlaceholders[key];
      if (actual && actual.sort().join(',') !== expected.sort().join(',')) {
        errors.push(`Placeholder mismatch in "${key}": expected [${expected}], got [${actual}]`);
      }
    }

    results.push({ locale, valid: errors.length === 0, errors });
  }

  return results;
}

function extractPlaceholders(obj: Record<string, unknown>, prefix = ''): Record<string, string[]> {
  const result: Record<string, string[]> = {};
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') {
      const matches = value.match(PLACEHOLDER_REGEX);
      if (matches) result[fullKey] = matches;
    } else if (typeof value === 'object' && value !== null) {
      Object.assign(result, extractPlaceholders(value as Record<string, unknown>, fullKey));
    }
  }
  return result;
}

function findEmptyValues(obj: Record<string, unknown>, prefix = ''): string[] {
  const result: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value === '') result.push(fullKey);
    else if (typeof value === 'object' && value !== null) {
      result.push(...findEmptyValues(value as Record<string, unknown>, fullKey));
    }
  }
  return result;
}

// Run validation
const results = validate();
let failed = false;
for (const r of results) {
  const status = r.valid ? 'PASS' : 'FAIL';
  console.log(`[${status}] ${r.locale}`);
  r.errors.forEach(e => console.log(`       ${e}`));
  if (!r.valid) failed = true;
}
process.exit(failed ? 1 : 0);
```

### Step 4: API Token Security

```bash
echo "=== API Token Security Audit ==="

# Verify token is not hardcoded in source
HARDCODED=$(grep -r "X-Api-Token" --include="*.ts" --include="*.js" --include="*.json" \
  -l src/ 2>/dev/null | grep -v node_modules || true)

if [[ -n "$HARDCODED" ]]; then
  echo "FAIL: API token may be hardcoded in: $HARDCODED"
  exit 1
fi

# Verify token is not in version control
GIT_SECRETS=$(git log --all -p --diff-filter=A -- '*.env' '*.env.*' 2>/dev/null \
  | grep -i "LOKALISE_API_TOKEN=" | head -5 || true)

if [[ -n "$GIT_SECRETS" ]]; then
  echo "FAIL: Token found in git history. Rotate immediately."
  exit 1
fi

# Verify .env files are gitignored
if ! grep -q "\.env" .gitignore 2>/dev/null; then
  echo "WARN: .env not in .gitignore"
fi

# Verify token permissions are minimal
TOKEN_RESPONSE=$(curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" -o /dev/null -w "%{http_code}")

if [[ "$TOKEN_RESPONSE" == "200" ]]; then
  echo "PASS: Token is valid and has project access"
else
  echo "FAIL: Token returned HTTP $TOKEN_RESPONSE"
  exit 1
fi

echo "PASS: No hardcoded tokens detected"
```

### Step 5: Rate Limit Preparedness

```bash
echo "=== Rate Limit Readiness ==="

# Lokalise enforces 6 requests/second per token
# Check if your code handles 429 responses

RATE_LIMIT_HANDLING=$(grep -r "429\|rate.limit\|retry-after\|rateLimitRetry" \
  --include="*.ts" --include="*.js" src/ 2>/dev/null | head -5 || true)

if [[ -z "$RATE_LIMIT_HANDLING" ]]; then
  echo "WARN: No rate limit handling detected in source code."
  echo "      Add retry logic with exponential backoff for 429 responses."
  echo "      Lokalise limit: 6 requests/second per API token."
else
  echo "PASS: Rate limit handling detected"
  echo "$RATE_LIMIT_HANDLING"
fi
```

### Step 6: Fallback Language Configuration

Verify the application gracefully falls back when a translation is missing.

```typescript
// Verify in your i18n configuration:
// i18next example
import i18next from 'i18next';

// Correct fallback configuration
i18next.init({
  fallbackLng: 'en',                    // Always fall back to English
  load: 'languageOnly',                 // 'de' not 'de-DE' unless regional variants exist
  returnEmptyString: false,             // Treat empty strings as missing
  missingKeyHandler: (lngs, ns, key) => {
    console.warn(`Missing translation: ${key} for ${lngs.join(', ')}`);
    // In production, report to monitoring (Sentry, Datadog, etc.)
  },
  interpolation: {
    escapeValue: false,                 // React already escapes
  },
});
```

### Step 7: Download Verification

Test that the full download-build cycle works end-to-end.

```bash
echo "=== Download Verification ==="

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Download with production settings
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --original-filenames=true \
  --directory-prefix="" \
  --export-empty-as=base \
  --unzip-to "$TEMP_DIR/" 2>&1

# Verify files exist and are non-empty
FILE_COUNT=$(find "$TEMP_DIR" -name "*.json" | wc -l)
echo "Downloaded $FILE_COUNT locale files"

if [[ $FILE_COUNT -eq 0 ]]; then
  echo "FAIL: No files downloaded"
  exit 1
fi

# Verify each file is valid JSON
for f in "$TEMP_DIR"/*.json; do
  if ! jq empty "$f" 2>/dev/null; then
    echo "FAIL: Invalid JSON: $f"
    exit 1
  fi
  keys=$(jq '[paths(scalars)] | length' "$f")
  locale=$(basename "$f" .json)
  echo "  $locale: $keys keys"
done

echo "PASS: All downloaded files are valid"
```

### Step 8: OTA Configuration (If Applicable)

If using Lokalise OTA (over-the-air) translations for mobile or web:

```bash
echo "=== OTA Configuration Check ==="

# Verify OTA SDK token (separate from API token)
if [[ -z "${LOKALISE_OTA_TOKEN:-}" ]]; then
  echo "INFO: OTA not configured (LOKALISE_OTA_TOKEN not set). Skip if not using OTA."
else
  # Test OTA bundle endpoint
  OTA_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
    "https://ota.lokalise.com/v3/public/${LOKALISE_OTA_TOKEN}/")

  if [[ "$OTA_STATUS" == "200" ]]; then
    echo "PASS: OTA endpoint reachable"
  else
    echo "FAIL: OTA endpoint returned HTTP $OTA_STATUS"
  fi

  # Verify OTA freeze window is not active
  echo "INFO: Check Lokalise dashboard > OTA > Settings for freeze windows before deploy"
fi
```

### Step 9: Contributor Access Review

```bash
echo "=== Contributor Access Review ==="

CONTRIBUTORS=$(curl -sf "https://api.lokalise.com/api2/teams" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}")

echo "Review the following in the Lokalise dashboard before go-live:"
echo "  1. Remove any test/demo contributors from the production project"
echo "  2. Verify all contributors have the minimum required role"
echo "  3. Ensure no shared/generic accounts exist"
echo "  4. Confirm two-factor authentication is enabled for admins"
echo "  5. Review and remove any unused API tokens"
echo ""
echo "Roles reference:"
echo "  - Admin: Full access (limit to 2-3 people)"
echo "  - Manager: Can manage contributors and keys"
echo "  - Developer: Upload/download, no contributor management"
echo "  - Translator: Translate only, no key management"
echo ""
echo "ACTION: Manually verify in Lokalise dashboard > Team > Members"
```

## Output

A complete pre-deployment report covering:
- Translation coverage percentage per locale (must be 100% for production)
- Missing and orphaned key counts
- Format validation results (JSON validity, placeholder consistency)
- Security audit results (no hardcoded tokens, proper gitignore)
- Rate limit handling confirmation
- Fallback language configuration status
- Download verification (end-to-end test)
- OTA readiness (if applicable)
- Contributor access review action items

## Error Handling

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Incomplete translations | Any locale < 100% | P1 — Blocks deploy | Complete translations or add missing keys |
| Hardcoded API token | Token found in source | P1 — Blocks deploy | Remove from code, rotate token immediately |
| Token in git history | Token committed previously | P1 — Blocks deploy | Rotate token, consider `git filter-repo` |
| Download produces 0 files | API error or empty project | P1 — Blocks deploy | Check project ID, token permissions, Lokalise status |
| Placeholder mismatch | `{{name}}` missing in translation | P2 — Warning | Fix in Lokalise, re-download |
| No rate limit handling | Missing 429 retry logic | P2 — Warning | Add retry with backoff before high-traffic launch |
| Empty string values | Untranslated keys exported as `""` | P3 — Info | Use `--export-empty-as=base` or `skip` |

## Examples

### Run Full Checklist

```bash
#!/bin/bash
# scripts/prod-checklist.sh — Run all checks sequentially
set -euo pipefail

echo "========================================="
echo "  Lokalise Production Checklist"
echo "  $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "========================================="
echo ""

scripts/audit-translation-coverage.sh
echo ""
scripts/detect-missing-keys.sh
echo ""
npx tsx scripts/validate-translation-format.ts
echo ""

echo "========================================="
echo "  All automated checks passed."
echo "  Complete manual checks:"
echo "    - Contributor access review"
echo "    - OTA freeze window check"
echo "    - Stakeholder sign-off"
echo "========================================="
```

### Quick Spot-Check (Single Locale)

```bash
# Fast check for a single locale before hotfix deploy
curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/languages" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq '.languages[] | select(.lang_iso == "de") | {locale: .lang_iso, progress: .statistics.progress, words_remaining: .statistics.words_to_do}'
```

## Resources

- [Lokalise Status Page](https://status.lokalise.com) — Check before any production deployment
- [Lokalise API — Project Statistics](https://developers.lokalise.com/reference/retrieve-a-project)
- [Lokalise OTA Documentation](https://docs.lokalise.com/en/articles/1400697-over-the-air-ota)
- [Lokalise Team Roles](https://docs.lokalise.com/en/articles/1400870-team-roles-and-permissions)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Next Steps

- After passing all checks, deploy using your standard pipeline
- Set up `lokalise-incident-runbook` for post-launch incident response
- Configure monitoring alerts for translation-related errors (missing keys, API failures)
- Schedule quarterly re-runs of this checklist for ongoing compliance
