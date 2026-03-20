---
name: lokalise-reference-architecture
description: |
  Implement Lokalise reference architecture with best-practice project layout.
  Use when designing new Lokalise integrations, reviewing project structure,
  or establishing architecture standards for Lokalise applications.
  Trigger with phrases like "lokalise architecture", "lokalise best practices",
  "lokalise project structure", "how to organize lokalise", "lokalise layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Reference Architecture

## Overview

A production-ready architecture for integrating Lokalise into web applications. Covers the end-to-end translation flow from source code through CI/CD and Lokalise to deployed translations, recommended project structure for i18n, file organization conventions, multi-app translation sharing, and the tradeoffs between OTA (over-the-air) and build-time translation loading.

## Prerequisites

- Node.js 18+ with TypeScript
- `@lokalise/node-api` SDK installed (`npm install @lokalise/node-api`)
- An i18n framework selected (i18next, react-intl, vue-i18n, or equivalent)
- Lokalise project created with at least one source language configured
- Basic understanding of CI/CD pipelines (GitHub Actions, GitLab CI, or equivalent)

## Instructions

### Step 1: Architecture Diagram

The translation lifecycle follows this flow:

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│ Source Code  │────▶│  CI/CD   │────▶│  Lokalise   │
│             │     │ (upload) │     │  (TMS)      │
│ en.json     │     └──────────┘     │             │
│ t('key')    │                      │  ┌────────┐ │
└─────────────┘                      │  │Transla-│ │
                                     │  │ tors   │ │
                                     │  └────────┘ │
┌─────────────┐     ┌──────────┐     │             │
│   Deploy    │◀────│  CI/CD   │◀────│  Download   │
│             │     │ (build)  │     │             │
│  CDN/Server │     └──────────┘     └─────────────┘
└──────┬──────┘                      ┌─────────────┐
       │                             │  Lokalise   │
       │         (OTA path)          │  OTA CDN    │
       │◀────────────────────────────│             │
       │                             └─────────────┘
┌──────▼──────┐
│    Users    │
│  (browser/  │
│   mobile)   │
└─────────────┘
```

**Two delivery paths:**
1. **Build-time** (solid arrows): Translations downloaded during CI build, bundled into the application. Changes require a new deployment.
2. **OTA** (dashed arrow): Translations fetched from Lokalise CDN at runtime. Changes appear without redeployment. Adds a network dependency.

### Step 2: Project Structure for i18n

Organize your codebase to separate translation concerns from business logic:

```
project-root/
├── src/
│   ├── i18n/
│   │   ├── index.ts              # i18n initialization and configuration
│   │   ├── client.ts             # Lokalise API client wrapper
│   │   ├── loader.ts             # Translation loader (build-time or OTA)
│   │   ├── fallback.ts           # Fallback translation logic
│   │   ├── types.ts              # TypeScript types for translation keys
│   │   └── middleware.ts         # Express/Next.js locale detection middleware
│   │
│   ├── locales/
│   │   ├── en.json               # Source language (committed to git)
│   │   ├── de.json               # Downloaded from Lokalise (gitignored or committed)
│   │   ├── fr.json
│   │   ├── es.json
│   │   └── ja.json
│   │
│   ├── locales-fallback/         # Static fallback copy (always committed)
│   │   ├── en.json
│   │   ├── de.json
│   │   └── ...
│   │
│   └── components/
│       └── ...                   # Components use t('key') from i18n
│
├── scripts/
│   ├── lokalise-pull.sh          # Download translations from Lokalise
│   ├── lokalise-push.sh          # Upload source strings to Lokalise
│   ├── validate-translations.ts  # Check coverage, placeholders, format
│   └── generate-types.ts         # Generate TypeScript types from en.json
│
├── .github/workflows/
│   ├── lokalise-upload.yml       # Upload on push to main
│   └── lokalise-download.yml     # Download during build
│
└── lokalise.config.ts            # Lokalise project configuration
```

### Step 3: Core Configuration

```typescript
// src/i18n/index.ts
import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';  // or vue-i18n, svelte-i18n, etc.
import en from '../locales/en.json';

export const SUPPORTED_LOCALES = ['en', 'de', 'fr', 'es', 'ja'] as const;
export type SupportedLocale = typeof SUPPORTED_LOCALES[number];
export const DEFAULT_LOCALE: SupportedLocale = 'en';

i18next
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en } },
    lng: DEFAULT_LOCALE,
    fallbackLng: DEFAULT_LOCALE,
    supportedLngs: [...SUPPORTED_LOCALES],
    load: 'languageOnly',             // 'de' not 'de-DE'
    returnEmptyString: false,         // Treat '' as missing → use fallback
    interpolation: { escapeValue: false },
    detection: {
      order: ['cookie', 'navigator', 'htmlTag'],
      caches: ['cookie'],
    },
  });

export default i18next;
```

### Step 4: Lokalise API Client Wrapper

```typescript
// src/i18n/client.ts
import { LokaliseApi } from '@lokalise/node-api';

interface LokaliseClientConfig {
  apiToken: string;
  projectId: string;
  rateLimitPerSec?: number;
}

export class LokaliseClient {
  private api: LokaliseApi;
  private projectId: string;
  private requestTimestamps: number[] = [];
  private maxRequestsPerSec: number;

  constructor(config: LokaliseClientConfig) {
    this.api = new LokaliseApi({ apiKey: config.apiToken });
    this.projectId = config.projectId;
    this.maxRequestsPerSec = config.rateLimitPerSec ?? 6;
  }

  /**
   * Download all translation files as a zip bundle URL.
   */
  async downloadTranslations(options?: {
    format?: string;
    branch?: string;
  }): Promise<string> {
    await this.rateLimit();
    const projectId = options?.branch
      ? `${this.projectId}:${options.branch}`
      : this.projectId;

    const response = await this.api.files().download(projectId, {
      format: options?.format ?? 'json',
      original_filenames: true,
      directory_prefix: '',
      export_empty_as: 'base',
      export_sort: 'first_added',
    });

    return response.bundle_url;
  }

  // Additional methods: listKeys(), getStatistics(), uploadFile()
  // follow the same pattern — call this.rateLimit() before each API call.

  /**
   * Simple rate limiter: 6 requests per second max.
   */
  private async rateLimit(): Promise<void> {
    const now = Date.now();
    this.requestTimestamps = this.requestTimestamps.filter(t => now - t < 1000);

    if (this.requestTimestamps.length >= this.maxRequestsPerSec) {
      const oldestInWindow = this.requestTimestamps[0];
      const waitMs = 1000 - (now - oldestInWindow);
      if (waitMs > 0) {
        await new Promise(resolve => setTimeout(resolve, waitMs));
      }
    }

    this.requestTimestamps.push(Date.now());
  }
}
```

### Step 5: File Organization Conventions

Follow these conventions for translation file organization:

**Flat keys** (recommended for most projects — simpler grep, no nesting ambiguity):

```json
{
  "homepage.hero.title": "Welcome to MyApp",
  "homepage.hero.subtitle": "The best app ever",
  "settings.profile.name_label": "Full Name",
  "errors.not_found": "Page not found"
}
```

**Nested keys** work better for large projects with clear module boundaries, where each top-level key maps to a feature area. Both formats are supported by Lokalise and i18next.

**Key naming conventions:**
- Use dot notation: `module.section.element`
- Use snake_case for key segments: `user_profile`, not `userProfile`
- Prefix by feature area: `checkout.payment.card_label`
- Use consistent suffixes: `_title`, `_label`, `_button`, `_error`, `_placeholder`
- Keep keys under 100 characters (Lokalise hard limit is 1024 chars per key name)

**File naming:**
- One file per locale: `en.json`, `de.json`, `fr.json`
- For large apps, split by namespace: `common.json`, `auth.json`, `dashboard.json`
- Namespace files go in subdirectories: `locales/en/common.json`, `locales/en/auth.json`

### Step 6: Multi-App Translation Sharing

When multiple applications share translations (e.g., web app + mobile app + marketing site):

```
Lokalise Project: "MyCompany Shared"
├── Tags: shared, web-only, mobile-only, marketing-only
│
├── Shared keys (tag: shared)
│   ├── common.button.ok
│   ├── common.button.cancel
│   └── common.error.generic
│
├── Web-only keys (tag: web-only)
│   ├── web.nav.dashboard
│   └── web.nav.settings
│
└── Mobile-only keys (tag: mobile-only)
    ├── mobile.nav.home
    └── mobile.permissions.camera
```

Download by tag to get only the keys each app needs:

```bash
# Web app — download shared + web-only
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --filter-tags "shared,web-only" \
  --original-filenames=false \
  --bundle-structure "locales/%LANG_ISO%.json" \
  --unzip-to "./"

# Mobile app — download shared + mobile-only
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --filter-tags "shared,mobile-only" \
  --original-filenames=false \
  --bundle-structure "src/translations/%LANG_ISO%.json" \
  --unzip-to "./"
```

**Alternative: Separate projects with key linking.** Lokalise does not natively share keys across projects, so tag-based filtering within a single project is the recommended approach for shared translations.

### Step 7: OTA vs Build-Time Translation Loading

Choose the right delivery strategy based on your requirements:

| Factor | Build-Time | OTA |
|--------|-----------|-----|
| **Latency** | Zero (bundled) | Network request on first load |
| **Update speed** | Requires deployment | Instant (CDN cache) |
| **Offline support** | Full | Needs initial fetch + local cache |
| **Bundle size** | Increases with locales | Minimal (loaded on demand) |
| **Reliability** | No external dependency | Depends on Lokalise CDN |
| **Best for** | Server-rendered apps, SPAs with CI/CD | Mobile apps, rapid copy changes |

**Build-time implementation** (recommended for most web apps):

```typescript
// src/i18n/loader-buildtime.ts
// Translations are imported statically — bundled at build time
import en from '../locales/en.json';
import de from '../locales/de.json';
import fr from '../locales/fr.json';

const translations: Record<string, Record<string, unknown>> = { en, de, fr };

export function loadTranslation(locale: string): Record<string, unknown> {
  return translations[locale] ?? translations['en'];
}
```

**OTA implementation** (for instant translation updates without redeployment):

```typescript
// src/i18n/loader-ota.ts
import i18next from 'i18next';
import LocizeBackend from 'i18next-locize-backend';  // or i18next-http-backend

// Lokalise OTA requires the @lokalise/i18next-ota-plugin or a custom backend
// pointing at the Lokalise OTA endpoint.
i18next
  .use(LocizeBackend)
  .init({
    backend: {
      // Lokalise OTA SDK endpoint
      // See: https://docs.lokalise.com/en/articles/1400697-over-the-air-ota
      loadPath: `https://ota.lokalise.com/v3/public/${process.env.LOKALISE_OTA_TOKEN}/{{lng}}/{{ns}}`,
    },
    fallbackLng: 'en',
    ns: ['translation'],
    defaultNS: 'translation',
  });
```

**Hybrid approach** (recommended for production):

```typescript
// src/i18n/loader-hybrid.ts
import bundledEn from '../locales/en.json';

/**
 * Load bundled translations immediately, then attempt OTA update.
 * User sees bundled content instantly; OTA updates appear on next render.
 */
export async function loadWithOtaFallback(locale: string): Promise<Record<string, unknown>> {
  // 1. Start with bundled translations (instant)
  const bundled = await import(`../locales/${locale}.json`)
    .then(m => m.default)
    .catch(() => bundledEn);

  // 2. Attempt OTA fetch in background (non-blocking)
  fetchOtaTranslations(locale)
    .then(ota => {
      if (ota) {
        // Merge OTA translations over bundled (OTA wins on conflicts)
        Object.assign(i18next.store.data[locale].translation, ota);
        i18next.emit('loaded');
      }
    })
    .catch(() => { /* OTA failed, bundled translations are sufficient */ });

  return bundled;
}

async function fetchOtaTranslations(locale: string): Promise<Record<string, unknown> | null> {
  const otaToken = process.env.LOKALISE_OTA_TOKEN;
  if (!otaToken) return null;

  const response = await fetch(`https://ota.lokalise.com/v3/public/${otaToken}/${locale}/translation`, {
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) return null;
  return response.json();
}
```

### Step 8: TypeScript Type Safety

Generate types from your source locale to get compile-time checks on translation keys:

```typescript
// scripts/generate-types.ts
import fs from 'fs';

const sourceLocale = JSON.parse(fs.readFileSync('src/locales/en.json', 'utf-8'));

function generateTypes(obj: Record<string, unknown>, prefix = ''): string[] {
  const keys: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'object' && value !== null) {
      keys.push(...generateTypes(value as Record<string, unknown>, fullKey));
    } else {
      keys.push(`  | '${fullKey}'`);
    }
  }
  return keys;
}

const typeContent = `// Auto-generated by scripts/generate-types.ts — do not edit
export type TranslationKey =
${generateTypes(sourceLocale).join('\n')};
`;

fs.writeFileSync('src/i18n/types.ts', typeContent);
console.log('Generated src/i18n/types.ts');
```

Usage in components:

```typescript
import type { TranslationKey } from '../i18n/types';

// Type-safe translation function
function t(key: TranslationKey, options?: Record<string, string>): string {
  return i18next.t(key, options);
}

t('homepage.hero.title');       // OK
t('homepage.hero.titl');        // TypeScript error: not a valid key
```

## Output

After applying this skill, the project will have:
- A clear architecture showing the translation flow from source code through Lokalise to deployment
- Organized project structure with separated i18n concerns
- Lokalise API client wrapper with built-in rate limiting
- File organization following naming conventions
- Multi-app translation sharing via tag-based downloads
- The appropriate translation loading strategy (build-time, OTA, or hybrid) selected and implemented
- TypeScript type generation for compile-time key validation

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular imports in i18n module | Importing translations before i18n init | Initialize i18n in a separate module, import lazily |
| Missing locale at runtime | Locale file not included in build | Add all locale files to build config; use dynamic `import()` |
| Stale translations after deploy | Cache not invalidated | Version your translation bundles or use cache-busting query params |
| Type generation fails | Nested key with array value | Filter out arrays in the type generator; Lokalise should not produce arrays |
| OTA translations flash on load | Bundled translations replaced by OTA after render | Use the hybrid approach: render bundled, merge OTA silently |
| Bundle size too large | All locales bundled statically | Use dynamic imports to load only the active locale |
| Tag-based download returns empty | Misspelled tag name | Verify tags in Lokalise dashboard; tags are case-sensitive |

## Examples

### Minimal vs Enterprise Setup

**Minimal** (5 files): `src/i18n/index.ts`, `src/locales/en.json`, `src/locales/de.json`, `scripts/lokalise-pull.sh`, `scripts/lokalise-push.sh`.

**Enterprise** adds: `client.ts` (Step 4), `loader-hybrid.ts` (Step 7), `fallback.ts`, `middleware.ts`, `types.ts` (Step 8), `locales-fallback/` directory, `validate-translations.ts`, `generate-types.ts`, and CI workflows. See the full tree in Step 2.

## Resources

- [Lokalise Node SDK Documentation](https://lokalise.github.io/node-lokalise-api/)
- [Lokalise CLI v2 Reference](https://docs.lokalise.com/en/articles/3659951-lokalise-cli-tool)
- [Lokalise OTA Documentation](https://docs.lokalise.com/en/articles/1400697-over-the-air-ota)
- [i18next Documentation](https://www.i18next.com/)
- [react-intl Documentation](https://formatjs.io/docs/react-intl/)
- [vue-i18n Documentation](https://vue-i18n.intlify.dev/)
- [Lokalise File Formats](https://docs.lokalise.com/en/articles/1400767-supported-file-formats)

## Next Steps

- Set up `lokalise-ci-integration` to automate the upload/download cycle in CI
- Configure `lokalise-multi-env-setup` for per-environment project isolation
- Run `lokalise-prod-checklist` before launching to validate coverage and security
- Implement the TypeScript type generator as a pre-commit hook to keep types in sync
