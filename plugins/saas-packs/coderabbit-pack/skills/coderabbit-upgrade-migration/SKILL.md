---
name: coderabbit-upgrade-migration
description: |
  Update CodeRabbit configuration for new features, migrate between plans, and adopt new capabilities.
  Use when CodeRabbit releases new features, upgrading from Free to Pro plan,
  or updating .coderabbit.yaml schema for new options.
  Trigger with phrases like "upgrade coderabbit", "coderabbit new features",
  "update coderabbit config", "coderabbit plan upgrade", "coderabbit changelog".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, migration, upgrade]

---
# CodeRabbit Upgrade & Migration

## Overview
CodeRabbit is a managed SaaS service -- there is no SDK to upgrade. Configuration changes happen by updating `.coderabbit.yaml` in your repository. This skill covers adopting new CodeRabbit features, upgrading between plans, migrating configuration formats, and staying current with CodeRabbit capabilities.

## Prerequisites
- CodeRabbit installed on repository
- `.coderabbit.yaml` in repository root
- Access to CodeRabbit dashboard at app.coderabbit.ai

## Upgrade Paths

| From | To | What Changes |
|------|----|-------------|
| Free | Pro | Private repos, more concurrent reviews, all features |
| Pro | Enterprise | SSO, dedicated support, SLA, custom limits |
| Old config format | New format | Updated YAML schema fields |
| Basic config | Advanced config | Path instructions, learnings, finishing touches |

## Instructions

### Step 1: Check Current Configuration vs Latest Schema
```markdown
# On any open PR, post this comment:
@coderabbitai configuration

# CodeRabbit replies with the active config as YAML.
# Compare with the latest schema documentation to find:
# 1. Deprecated fields you're still using
# 2. New fields available that you're not using
# 3. Fields with changed default values
```

### Step 2: Upgrade Free to Pro Plan
```markdown
# What you gain with Pro:
1. Private repository support (Free = public only)
2. More concurrent reviews (Free = 1, Pro = 5)
3. Learnings (CodeRabbit remembers your feedback preferences)
4. Finishing Touches (auto-generate docstrings, custom recipes)
5. Full path instructions and review customization
6. Priority review processing

# Steps:
1. Go to app.coderabbit.ai > Organization > Subscription
2. Select Pro plan
3. Set seat assignment policy (active committers recommended)
4. Add payment method
5. Seats activate immediately for all configured repos
```

### Step 3: Adopt New Configuration Features
```yaml
# .coderabbit.yaml - Modern configuration with latest features

language: "en-US"
early_access: false              # Set true to try beta features

reviews:
  profile: "assertive"
  request_changes_workflow: true
  high_level_summary: true
  high_level_summary_in_walkthrough: true   # Summary inside walkthrough comment
  review_status: true
  collapse_walkthrough: false
  sequence_diagrams: true                    # Visual control flow diagrams
  poem: false

  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - main
      - develop
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"

  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!**/generated/**"
    - "!dist/**"
    - "!vendor/**"

  path_instructions:
    - path: "src/api/**"
      instructions: "Review for input validation, auth middleware, error handling."
    - path: "src/db/**"
      instructions: "Review for parameterized queries, transactions, N+1 patterns."
    - path: "**/*.test.*"
      instructions: "Review for edge cases. Skip style comments."
    - path: ".github/workflows/**"
      instructions: "Pin action versions to SHA. No secrets in logs."

  # Finishing Touches (Pro+)
  finishing_touches:
    docstrings:
      enabled: true              # @coderabbitai generate-docstrings command

  # Tool integrations
  tools:
    eslint:
      enabled: true              # Lint with ESLint rules
    biome:
      enabled: true              # Biome linter
    shellcheck:
      enabled: true              # Shell script linting
    markdownlint:
      enabled: true              # Markdown linting

# Tone customization (Pro+)
tone_instructions: |
  Be concise and direct. Use bullet points for multiple suggestions.
  Include code examples for non-obvious fixes.
  Rate severity: Critical > Warning > Suggestion > Nitpick.

chat:
  auto_reply: true
```

### Step 4: Enable Finishing Touch Recipes
```yaml
# .coderabbit.yaml - Custom finishing touch recipes (Pro+)
finishing_touches:
  docstrings:
    enabled: true

  recipes:
    - name: "fix-imports"
      description: "Sort and organize imports"
      instructions: |
        Sort all imports alphabetically. Group: external packages first,
        then internal modules, then relative imports. Remove unused imports.

    - name: "tighten-types"
      description: "Replace any with proper types"
      instructions: |
        Replace all `any` types with proper TypeScript types.
        Use `unknown` for truly unknown values. Add type guards where needed.

    - name: "add-error-handling"
      description: "Add missing error handling"
      instructions: |
        Add try/catch blocks to async operations that are missing error handling.
        Include meaningful error messages and proper error propagation.
```

```markdown
# Use recipes on a PR:
@coderabbitai run fix-imports
@coderabbitai run tighten-types
@coderabbitai generate-docstrings

# Or check the boxes in the Finishing Touches section of the walkthrough comment
```

### Step 5: Enable Early Access Features
```yaml
# .coderabbit.yaml - Opt into beta features
early_access: true    # Enables experimental features as they ship

# Early access features are documented at:
# https://docs.coderabbit.ai/early-access
#
# Recent early access features have included:
# - Finishing touch recipes (now GA)
# - Tool integrations (eslint, biome, shellcheck)
# - Sequence diagrams in walkthroughs
# - Knowledge base / code guidelines auto-detection
```

### Step 6: Validate After Upgrade
```bash
set -euo pipefail

echo "=== Post-Upgrade Validation ==="

# 1. Validate YAML syntax
echo "--- YAML Validation ---"
python3 -c "
import yaml
config = yaml.safe_load(open('.coderabbit.yaml'))
print(f'YAML: VALID ({len(str(config))} chars)')

# Check for new features
reviews = config.get('reviews', {})
ft = reviews.get('finishing_touches', {})
tools = reviews.get('tools', {})
tone = config.get('tone_instructions', '')
early = config.get('early_access', False)

print(f'Finishing touches: {\"enabled\" if ft else \"not configured\"}')
print(f'Tool integrations: {len(tools)} tools configured')
print(f'Tone instructions: {\"set\" if tone else \"default\"}')
print(f'Early access: {early}')
" 2>&1

# 2. Verify config is active
echo ""
echo "--- Verify on PR ---"
echo "Post '@coderabbitai configuration' on any open PR to verify"
echo "the new configuration is active."
```

### Step 7: Migration Checklist
```markdown
# When updating configuration:
- [ ] YAML syntax validated before committing
- [ ] Config committed to main branch (CodeRabbit reads from base branch)
- [ ] @coderabbitai configuration verified on a test PR
- [ ] Team notified of any behavior changes
- [ ] Old deprecated fields removed
- [ ] New features tested on a non-critical PR first
```

## Output
- Configuration updated to latest CodeRabbit schema
- New features (finishing touches, tool integrations, tone) enabled
- Plan upgrade completed (if applicable)
- Post-upgrade validation passed
- Migration checklist completed

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| New field ignored | Not on Pro/Enterprise plan | Upgrade plan for full feature access |
| Config not applied after update | Committed to wrong branch | Merge config changes to the base branch |
| YAML parse error | Invalid syntax | Validate YAML before committing |
| Feature not available | Requires `early_access: true` | Enable early access in config |
| Finishing touches not working | Not on Pro plan | Upgrade to Pro for finishing touches |

## Resources
- [CodeRabbit Changelog](https://docs.coderabbit.ai/changelog)
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit Pricing](https://coderabbit.ai/pricing)
- [CodeRabbit Early Access](https://docs.coderabbit.ai/early-access)
- [Finishing Touches](https://docs.coderabbit.ai/finishing-touches)

## Next Steps
For CI integration after upgrade, see `coderabbit-ci-integration`.
