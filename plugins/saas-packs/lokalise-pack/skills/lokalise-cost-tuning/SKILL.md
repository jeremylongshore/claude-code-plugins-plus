---
name: lokalise-cost-tuning
description: |
  Optimize Lokalise costs through plan selection, usage monitoring, and efficiency.
  Use when analyzing Lokalise billing, reducing costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "lokalise cost", "lokalise billing",
  "reduce lokalise costs", "lokalise pricing", "lokalise budget".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lokalise, monitoring, cost-optimization]

---
# Lokalise Cost Tuning

## Overview
Optimize Lokalise localization spending across plan tiers, contributor seats, Translation Memory (TM) leverage, machine translation (MT) triage, and dead key cleanup. Lokalise pricing is per-seat subscription (Essential ~$120/user/month, Pro ~$290/user/month) with optional pay-per-use for MT and AI features.

## Prerequisites
- Lokalise Admin role for billing and usage visibility
- `LOKALISE_API_TOKEN` with read access to project statistics
- Understanding of translation workflow (human, MT, or hybrid)
- `curl` and `jq` for API queries

## Instructions

### Step 1: Audit Current Usage

```bash
set -euo pipefail
echo "=== Lokalise Usage Audit ==="

# Get all projects with statistics
PROJECTS=$(curl -sf "https://api.lokalise.com/api2/projects?limit=100&include_statistics=1" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}")

echo "$PROJECTS" | jq -r '.projects[] | [.name, .statistics.keys_total, (.statistics.languages // [] | length), .statistics.progress_total] | @tsv' \
  | column -t -s $'\t' -N "Project,Keys,Languages,Progress%"

# Totals
TOTAL_KEYS=$(echo "$PROJECTS" | jq '[.projects[].statistics.keys_total] | add')
TOTAL_LANGS=$(echo "$PROJECTS" | jq '[.projects[] | (.statistics.languages // [] | length)] | max')
PROJECT_COUNT=$(echo "$PROJECTS" | jq '.projects | length')

echo ""
echo "Totals: ${PROJECT_COUNT} projects, ${TOTAL_KEYS} keys, up to ${TOTAL_LANGS} languages"
echo ""

# Contributor count (seats = cost driver)
TEAMS=$(curl -sf "https://api.lokalise.com/api2/teams" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}")
echo "$TEAMS" | jq -r '.teams[] | "Team: \(.name) — \(.users_count) users (seats)"'
```

### Step 2: Reduce Per-Seat Costs

Seats are the largest cost driver. Strategies to minimize:

```typescript
import { LokaliseApi } from "@lokalise/node-api";
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Audit: Find inactive contributors (no activity in 90 days)
async function findInactiveContributors(projectId: string): Promise<void> {
  const contributors = await lok.contributors().list({
    project_id: projectId,
    limit: 500,
  });

  console.log("=== Contributor Activity Audit ===");
  for (const c of contributors.items) {
    const langs = c.languages
      .map((l: { lang_iso: string }) => l.lang_iso)
      .join(", ");
    console.log(
      `${c.fullname} <${c.email}> — ` +
      `admin: ${c.is_admin}, reviewer: ${c.is_reviewer}, ` +
      `languages: [${langs}]`
    );
  }

  console.log(`\nTotal contributors: ${contributors.items.length}`);
  console.log(
    "Review: Remove freelancers between tasks. " +
    "Use contributor groups for batch management."
  );
}

// Strategy: Use task-based access for freelance translators
// - Add freelancers when a translation task opens
// - Remove them when the task closes
// - This avoids paying for idle seats
// Cost example: 10 individual seats = ~$1,200/month
//               3 permanent + task-based freelancers = ~$360/month
```

### Step 3: Maximize Translation Memory (TM) Hits

TM matches reduce human translation volume. Keys with 100% TM match cost zero for translation.

```typescript
// Strategy: Translate similar projects sequentially to build TM
// Don't translate 3 apps in parallel — do one first, seed the TM,
// then the others get 30-50% free matches on shared strings

// Enable automations on upload to apply TM automatically
const uploadResult = await lok.files().upload(projectId, {
  data: base64FileData,
  filename: "en.json",
  lang_iso: "en",
  use_automations: true,      // Apply TM + MT suggestions
  replace_modified: true,
  detect_icu_plurals: true,
});

// Check TM coverage after upload
const languages = await lok.languages().list({ project_id: projectId, limit: 50 });
for (const lang of languages.items) {
  console.log(
    `${lang.lang_iso}: ${lang.statistics?.progress ?? 0}% translated, ` +
    `${lang.statistics?.words_to_do ?? "?"} words remaining`
  );
}
```

### Step 4: Machine Translation Triage

Pre-translate low-risk content with MT. Reserve human translation for critical strings.

```bash
set -euo pipefail
# Identify untranslated key volume per language
curl -sf "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/languages" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq '.languages[] | {
    locale: .lang_iso,
    progress: .statistics.progress,
    words_to_do: .statistics.words_to_do
  }'
```

**MT triage matrix — decide by key prefix:**

| Key Prefix | Content Type | Translation Method | Cost Impact |
|-----------|-------------|-------------------|-------------|
| `tooltip.*`, `help.*` | Tooltips, help text | Machine Translation | Low risk, high volume savings |
| `log.*`, `debug.*` | Log messages | MT or skip | These rarely face users |
| `ui.label.*`, `nav.*` | UI labels, navigation | Human | Medium risk, must be natural |
| `marketing.*`, `cta.*` | Marketing copy, CTAs | Human (senior) | High risk, brand-critical |
| `legal.*`, `tos.*` | Legal text | Human + legal review | Compliance-critical |

### Step 5: Clean Up Dead Keys

Orphaned keys waste per-word costs and clutter the project.

```typescript
import { readFileSync } from "fs";

async function findOrphanedKeys(
  projectId: string,
  sourceCodeDir: string
): Promise<string[]> {
  // Get all keys from Lokalise
  const allKeys: string[] = [];
  let cursor: string | undefined;
  do {
    const page = await lok.keys().list({
      project_id: projectId,
      limit: 500,
      ...(cursor ? { cursor } : {}),
    });
    for (const k of page.items) {
      allKeys.push(k.key_name.web ?? k.key_name.other ?? "");
    }
    cursor = page.hasNextCursor() ? page.nextCursor() : undefined;
  } while (cursor);

  console.log(`Lokalise keys: ${allKeys.length}`);

  // Compare against source code references
  // (simplified — adjust grep pattern for your i18n framework)
  const { execSync } = await import("child_process");
  const sourceRefs = execSync(
    `grep -roh "t(['\"][^'\"]*['\"])" ${sourceCodeDir} 2>/dev/null || true`,
    { encoding: "utf-8" }
  )
    .split("\n")
    .map((line) => line.replace(/^t\(['"]/, "").replace(/['"]\)$/, ""))
    .filter(Boolean);

  const sourceKeySet = new Set(sourceRefs);
  const orphaned = allKeys.filter((k) => !sourceKeySet.has(k));

  console.log(`Source code references: ${sourceKeySet.size}`);
  console.log(`Orphaned keys: ${orphaned.length}`);

  return orphaned;
}

// Archive orphaned keys to stop paying for their translations
async function archiveKeys(projectId: string, keyNames: string[]): Promise<void> {
  // Look up key IDs
  for (const name of keyNames.slice(0, 50)) {
    const result = await lok.keys().list({
      project_id: projectId,
      filter_keys: name,
      limit: 1,
    });
    if (result.items.length > 0) {
      await lok.keys().update(result.items[0].key_id, {
        project_id: projectId,
        is_archived: true,
      });
    }
    await new Promise((r) => setTimeout(r, 170)); // Rate limit
  }
}
```

### Step 6: Monitor Monthly Spend

```bash
set -euo pipefail
echo "=== Monthly Cost Estimate ==="

# Count total seats across teams
SEAT_COUNT=$(curl -sf "https://api.lokalise.com/api2/teams" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq '[.teams[].users_count] | add')

# Estimate based on plan tier (adjust rate for your plan)
RATE_PER_SEAT=120  # Essential plan — adjust to 290 for Pro
MONTHLY_COST=$((SEAT_COUNT * RATE_PER_SEAT))

echo "Active seats: ${SEAT_COUNT}"
echo "Estimated monthly cost: \$${MONTHLY_COST} (at \$${RATE_PER_SEAT}/seat)"
echo ""
echo "Cost reduction levers:"
echo "  1. Remove inactive contributors (task-based access)"
echo "  2. Use contributor groups instead of individual invites"
echo "  3. Pre-translate with MT to reduce human translation volume"
echo "  4. Archive orphaned keys to reduce per-word charges"
echo "  5. Translate similar projects sequentially to maximize TM"
```

## Output
- Usage audit report: projects, keys, languages, contributor seat count
- Inactive contributor identification for seat optimization
- TM leverage strategy (sequential translation, automation-enabled uploads)
- MT triage matrix mapping key prefixes to translation method
- Orphaned key detection and archival workflow
- Monthly cost estimate with reduction levers

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High per-word costs | Human translating MT-suitable content | Apply MT to low-risk strings first |
| Seat costs growing | Adding contractors as full seats | Use task-based access: add when task opens, remove on close |
| TM not matching | Different key naming across projects | Standardize key names to improve TM reuse |
| Budget overrun | New languages added without planning | Budget per-language before adding to projects |
| Orphaned keys missed | Source code scan incomplete | Use multiple grep patterns matching your i18n framework |

## Examples

### Cost Comparison Scenarios

**Solo project with 5 languages**: 2 full-time translators + 8 freelancers. Move freelancers to task-based access. Seats drop from 10 to 2, saving ~$960/month.

**Multi-app suite sharing terminology**: Three apps share UI strings. Translate the largest first to seed TM, then translate the others. TM matches on shared strings cut human translation volume by 30-50%.

**10,000-key project MT triage**: Tag keys by content type. Apply MT to `tooltip.*`, `help.*`, `log.*` prefixes (40% of keys). Route `legal.*`, `marketing.*`, `ui.cta.*` to humans. Saves ~$2,000 per target language.

## Resources
- [Lokalise Pricing Plans](https://lokalise.com/pricing)
- [Lokalise API: Project Statistics](https://developers.lokalise.com/reference/retrieve-a-project)
- [Translation Memory in Lokalise](https://docs.lokalise.com/en/articles/1400533-translation-memory)
- [Lokalise Machine Translation](https://docs.lokalise.com/en/articles/1400534-machine-translation)
- [Keys API: List and Filter](https://developers.lokalise.com/reference/list-all-keys)

## Next Steps
For monitoring translation pipeline health and costs over time, see `lokalise-observability`.
