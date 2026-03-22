---
name: windsurf-ci-integration
description: |
  Integrate Windsurf Cascade workflows into CI/CD pipelines and team automation.
  Use when automating Cascade tasks in GitHub Actions, enforcing AI code quality gates,
  or setting up Windsurf config validation in CI.
  Trigger with phrases like "windsurf CI", "windsurf GitHub Actions",
  "windsurf automation", "cascade CI", "windsurf pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, ci-cd, github-actions, automation]

---
# Windsurf CI Integration

## Overview
Integrate Windsurf configuration validation and AI code quality gates into CI/CD pipelines. Covers validating `.windsurfrules`, enforcing team policies for AI-generated code, and automating Windsurf config distribution.

## Prerequisites
- GitHub repository with Actions enabled
- Windsurf configuration files in repository
- Team agreement on AI code review policy

## Instructions

### Step 1: Validate Windsurf Config in CI

```yaml
# .github/workflows/windsurf-config.yml
name: Windsurf Config Validation

on:
  pull_request:
    paths:
      - '.windsurfrules'
      - '.codeiumignore'
      - '.windsurf/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check .windsurfrules exists and is valid
        run: |
          if [ ! -f .windsurfrules ]; then
            echo "::error::.windsurfrules is missing"
            exit 1
          fi
          CHARS=$(wc -c < .windsurfrules)
          if [ "$CHARS" -gt 6000 ]; then
            echo "::error::.windsurfrules exceeds 6000 char limit ($CHARS chars)"
            exit 1
          fi
          echo ".windsurfrules: $CHARS chars (limit: 6000)"

      - name: Check .codeiumignore covers secrets
        run: |
          REQUIRED_PATTERNS=(".env" "*.pem" "*.key" "credentials")
          MISSING=()
          for pattern in "${REQUIRED_PATTERNS[@]}"; do
            if ! grep -q "$pattern" .codeiumignore 2>/dev/null; then
              MISSING+=("$pattern")
            fi
          done
          if [ ${#MISSING[@]} -gt 0 ]; then
            echo "::warning::.codeiumignore missing patterns: ${MISSING[*]}"
          fi

      - name: Validate workspace rules frontmatter
        run: |
          for rule in .windsurf/rules/*.md; do
            [ -f "$rule" ] || continue
            if ! head -1 "$rule" | grep -q "^---"; then
              echo "::error::$rule missing YAML frontmatter"
              exit 1
            fi
            # Check for required trigger field
            if ! grep -q "^trigger:" "$rule"; then
              echo "::warning::$rule missing 'trigger:' in frontmatter"
            fi
          done
```

### Step 2: AI Code Quality Gate

```yaml
# .github/workflows/ai-code-review.yml
name: AI Code Quality Gate

on: pull_request

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - name: Detect large AI-generated changesets
        run: |
          FILES_CHANGED=$(git diff --name-only origin/main..HEAD | wc -l)
          if [ "$FILES_CHANGED" -gt 20 ]; then
            echo "::warning::Large changeset ($FILES_CHANGED files). If AI-generated, ensure thorough review."
          fi

      - name: Enforce tests for new source files
        run: |
          NEW_SRC=$(git diff --name-only --diff-filter=A origin/main..HEAD | grep -cE '\.(ts|js|tsx|jsx)$' || true)
          NEW_TEST=$(git diff --name-only --diff-filter=A origin/main..HEAD | grep -cE '\.(test|spec)\.' || true)
          if [ "$NEW_SRC" -gt 3 ] && [ "$NEW_TEST" -eq 0 ]; then
            echo "::error::$NEW_SRC new source files added without tests"
            exit 1
          fi

      - name: Check for hardcoded secrets in new files
        run: |
          git diff origin/main..HEAD -- '*.ts' '*.js' '*.tsx' '*.jsx' | \
            grep -E '(sk_live|sk_test|AKIA|ghp_|glpat-|xoxb-)' && {
              echo "::error::Potential hardcoded secret detected"
              exit 1
            } || true
```

### Step 3: Distribute Windsurf Config Templates

```yaml
# .github/workflows/sync-windsurf-config.yml
name: Sync Windsurf Config

on:
  push:
    branches: [main]
    paths: ['windsurf-templates/**']

jobs:
  distribute:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        repo: [frontend, backend, mobile]
    steps:
      - uses: actions/checkout@v4
      - name: Push config to child repos
        run: |
          gh api repos/${{ github.repository_owner }}/${{ matrix.repo }}/contents/.windsurfrules \
            --method PUT \
            --field message="chore: sync windsurf config from monorepo" \
            --field content="$(base64 -w0 windsurf-templates/.windsurfrules)"
        env:
          GH_TOKEN: ${{ secrets.REPO_SYNC_TOKEN }}
```

### Step 4: Cascade-Generated Commit Convention

Enforce commit message conventions for AI-generated code:

```yaml
# In branch protection or CI
- name: Check AI commit convention
  run: |
    COMMITS=$(git log origin/main..HEAD --pretty=format:"%s")
    # If PR has many file changes, warn about AI commit tagging
    FILES=$(git diff --stat origin/main..HEAD | tail -1 | awk '{print $1}')
    if [ "$FILES" -gt 10 ]; then
      if ! echo "$COMMITS" | grep -q "\[cascade\]"; then
        echo "::notice::Large changeset without [cascade] tag. If AI-generated, tag commits with [cascade] prefix."
      fi
    fi
```

### Step 5: MCP Server Health Check (Optional)

```yaml
- name: Validate MCP config
  run: |
    MCP_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
    if [ -f "$MCP_CONFIG" ]; then
      python3 -c "import json; json.load(open('$MCP_CONFIG'))" || {
        echo "::error::MCP config is invalid JSON"
        exit 1
      }
    fi
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| .windsurfrules over limit | Too many rules | Split into workspace rules in `.windsurf/rules/` |
| Secret detected in diff | AI generated hardcoded key | Remove, rotate, add to `.codeiumignore` |
| Config sync fails | Token lacks repo access | Update `REPO_SYNC_TOKEN` permissions |
| Frontmatter validation fails | Missing trigger field | Add `trigger: always_on` or appropriate mode |

## Examples

### Branch Protection Rules
```yaml
# Recommended for teams using Windsurf Cascade
required_status_checks:
  - "windsurf-config"
  - "ai-code-review"
  - "test"
```

### Pre-Commit Hook for .windsurfrules
```bash
#!/bin/bash
# .git/hooks/pre-commit
CHARS=$(wc -c < .windsurfrules 2>/dev/null || echo 0)
if [ "$CHARS" -gt 6000 ]; then
  echo "ERROR: .windsurfrules exceeds 6000 char limit ($CHARS chars)"
  exit 1
fi
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Windsurf Admin Guide](https://docs.windsurf.com/windsurf/guide-for-admins)

## Next Steps
For deployment patterns, see `windsurf-deploy-integration`.
