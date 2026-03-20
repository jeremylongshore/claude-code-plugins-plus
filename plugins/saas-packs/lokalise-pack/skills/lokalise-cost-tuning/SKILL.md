---
name: lokalise-cost-tuning
description: |
  Optimize Lokalise costs through plan selection, usage monitoring, and efficiency.
  Use when analyzing Lokalise billing, reducing costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "lokalise cost", "lokalise billing",
  "reduce lokalise costs", "lokalise pricing", "lokalise budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Cost Tuning

## Overview
Optimize Lokalise localization spending across plan costs, contributor seats, and machine translation usage. Lokalise pricing combines per-seat subscription (Team plan: ~$120/user/month) with optional pay-per-use for Translation Memory matches, machine translation, and AI features.

## Prerequisites
- Lokalise Admin role for billing access
- Understanding of translation workflow (human, MT, or hybrid)
- Access to project usage statistics

## Instructions

### Step 1: Audit Current Spending
```bash
set -euo pipefail
# Check project stats: keys, words, languages
curl "https://api.lokalise.com/api2/projects/PROJECT_ID/statistics" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" | \
  jq '{
    total_keys: .statistics.keys_total,
    words_total: .statistics.words_total,
    languages: .statistics.languages_total,
    translated_pct: .statistics.progress_total
  }'
```

### Step 2: Reduce Per-Seat Costs
```yaml
# Instead of adding every translator as a full seat:
optimization_strategies:
  use_contributor_groups: true  # Share access via groups instead of individual invites
  use_task_based_access: true   # Add translators only when tasks are active, remove after
  leverage_translation_agencies: true  # Agency integration avoids individual seats

# Cost comparison:
# 10 individual seats: ~$1,200/month
# 3 seats + agency integration: ~$360/month + agency per-word fees
```

### Step 3: Maximize Translation Memory Hits
```typescript
// Before sending new keys for translation, check TM coverage
const tmSearch = await lok.translationProviders().list({ project_id: projectId });
// Keys with 100% TM match = $0 translation cost
// Keys with fuzzy match (75-99%) = reduced cost
// Keys with no match = full translation cost

// Strategy: translate similar projects sequentially to build TM, not in parallel
```

### Step 4: Use Machine Translation Strategically
```bash
set -euo pipefail
# Pre-translate low-risk content with MT, reserve human for critical strings
curl -X POST "https://api.lokalise.com/api2/projects/PROJECT_ID/files/download" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  -d '{
    "format": "json",
    "filter_untranslated": true
  }'
# Identify untranslated keys, apply MT only to: tooltips, help text, logs
# Keep human translation for: UI labels, marketing copy, legal text
```

### Step 5: Clean Up Unused Keys
```bash
set -euo pipefail
# Find keys not used in code (phantom keys waste per-word costs)
curl "https://api.lokalise.com/api2/projects/PROJECT_ID/keys?filter_archived=include&limit=500" \  # HTTP 500 Internal Server Error
  -H "X-Api-Token: $LOKALISE_API_TOKEN" | \
  jq '.keys[] | select(.is_archived == false) | {key_name: .key_name.web, translations_count: (.translations | length), modified: .modified_at}'
# Cross-reference with source code to find orphaned keys
# Archive unused keys to stop paying for their translations
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High per-word costs | Human translating MT-suitable content | Apply MT to low-risk strings first |
| Seat costs growing | Adding contractors as full seats | Use contributor groups and task-based access |
| TM not matching | Different key naming across projects | Standardize key names to improve TM reuse |
| Budget overrun | New languages added without planning | Budget per-language before adding to projects |

## Examples

**Solo project with 5 languages**: You have 2 full-time translators and 8 freelancers. Move freelancers to task-based access (add when task opens, remove on completion). Result: seats drop from 10 to 2, saving ~$960/month.

**Multi-app suite sharing terminology**: Three apps (web, iOS, Android) use overlapping UI strings. Translate the largest project first to seed Translation Memory, then translate the others sequentially. TM matches on shared strings (buttons, navigation, error messages) cut human translation volume by 30-50%.

**MT triage for a 10,000-key project**: Tag keys by content type. Apply machine translation to `tooltip.*`, `help.*`, and `log.*` prefixes. Route `legal.*`, `marketing.*`, and `ui.cta.*` to human translators. Pre-translating the low-risk 40% of keys with MT saves roughly $2,000 per target language.

## Output

- Cost audit report: current spend breakdown by seats, translation volume, and MT usage
- Seat optimization plan with contributor group structure and task-based access schedule
- List of orphaned/archived keys with cross-reference against source code
- MT triage matrix mapping key prefixes to translation method (human vs. MT)
- Projected monthly savings with before/after comparison

## Resources

- [Lokalise Pricing Plans](https://lokalise.com/pricing) -- plan tiers, per-seat costs, feature comparison
- [Lokalise API: Project Statistics](https://developers.lokalise.com/reference/retrieve-a-project) -- `GET /projects/{id}` returns key counts and progress
- [Translation Memory in Lokalise](https://docs.lokalise.com/translation-memory/) -- TM leverage, match thresholds, cross-project sharing
- [Lokalise Machine Translation](https://docs.lokalise.com/machine-translation/) -- supported MT engines, pre-translation setup
- [Keys API: List and Filter](https://developers.lokalise.com/reference/list-all-keys) -- `filter_archived`, pagination for key cleanup