---
name: ci-automation
description: "Use when running GitHub Actions locally, creating task runner recipes, generating changelogs from git history, managing GitHub PRs/issues/releases programmatically, or creating encrypted backups"
allowed-tools: [Bash(gh*), Bash(just*), Bash(act*), Bash(git-cliff*), Bash(restic*), Read, Write, Glob]
version: 1.0.0
author: ykotik
license: MIT
---

# CI Automation

## When to Use
- Running GitHub Actions workflows locally before pushing
- Creating or running project task recipes (build, test, deploy)
- Generating changelogs from conventional commit history
- Creating GitHub releases with auto-generated release notes
- Managing GitHub PRs, issues, or Actions runs programmatically
- Creating encrypted backups before destructive operations

## Tools

| Tool | Purpose | Structured output |
|------|---------|-------------------|
| **gh** | GitHub CLI — PRs, issues, releases, Actions, API | `--json` on most commands |
| **just** | Task runner with Makefile-like recipes (Justfile) | N/A (runs commands) |
| **act** | Run GitHub Actions workflows locally in Docker | Terminal output (mirrors Actions logs) |
| **git-cliff** | Generate changelogs from conventional commits | `--output` for file, stdout by default |
| **restic** | Encrypted incremental backups | `--json` for JSON status output |

## Patterns

### Run a specific GitHub Actions job locally
```bash
act -j build
```

### Run Actions with a specific event trigger
```bash
act push
```

### Run Actions with secrets from .env file
```bash
act --secret-file .env -j test
```

### List available Actions workflows and jobs
```bash
act -l
```

### Run Actions with specific platform image
```bash
act -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

### Create a Justfile with common recipes
Create `Justfile`:
```just
# List available recipes
default:
    @just --list

# Run tests
test:
    pytest -v

# Lint and format
lint:
    ruff check --fix .
    ruff format .

# Build and tag Docker image
build tag="latest":
    docker build -t myapp:{{tag}} .

# Deploy to staging
deploy-staging: test lint
    ./scripts/deploy.sh staging
```

### Run a just recipe
```bash
just test
```

### Run recipe with arguments
```bash
just build v1.2.3
```

### List available recipes
```bash
just --list
```

### Generate changelog for all history
```bash
git-cliff --output CHANGELOG.md
```

### Generate changelog for latest release only
```bash
git-cliff --latest
```

### Generate changelog since a specific tag
```bash
git-cliff --tag v1.0.0..HEAD
```

### Generate changelog with custom config
```bash
git-cliff --config cliff.toml --output CHANGELOG.md
```

### GitHub: Create a release with changelog
```bash
git-cliff --latest --strip header | gh release create v1.2.3 --notes-file -
```

### GitHub: List open PRs as JSON
```bash
gh pr list --json number,title,author,createdAt
```

### GitHub: Create a PR
```bash
gh pr create --title "feat: add new feature" --body "Description of changes"
```

### GitHub: View Actions run status
```bash
gh run list --json status,name,conclusion --limit 10
```

### GitHub: Re-run a failed Actions workflow
```bash
gh run rerun <run-id> --failed
```

### GitHub: Create an issue
```bash
gh issue create --title "Bug: description" --body "Steps to reproduce..." --label bug
```

### GitHub: Query the GitHub API directly
```bash
gh api repos/{owner}/{repo}/releases --jq '.[0:5] | .[].tag_name'
```

### Restic: Initialize a backup repository
```bash
restic init --repo /path/to/backup
```

### Restic: Create a backup
```bash
restic backup --repo /path/to/backup --json ./important-data
```

### Restic: List snapshots
```bash
restic snapshots --repo /path/to/backup --json
```

### Restic: Restore from backup
```bash
restic restore latest --repo /path/to/backup --target /path/to/restore
```

## Pipelines

### Generate changelog → create GitHub release
```bash
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")
git-cliff --latest --strip header | gh release create "$VERSION" --notes-file - --title "$VERSION"
```
Each stage: git-cliff generates changelog for latest version, gh creates release with those notes.

### Run local CI → create PR if passing
```bash
act -j test && act -j lint && gh pr create --title "feat: ready for review" --body "Local CI passed (test + lint)"
```
Each stage: act runs test job, act runs lint job, gh creates PR only if both pass.

### Backup → deploy → verify
```bash
restic backup --repo /backup --json ./data && ./scripts/deploy.sh production && curl -sf https://myapp.com/health
```
Each stage: restic backs up current state, deploy script runs, curl verifies health endpoint.

### List PRs → show CI status for each
```bash
gh pr list --json number,title,statusCheckRollup --jq '.[] | {pr: .number, title: .title, checks: [.statusCheckRollup[]? | {name: .name, status: .conclusion}]}'
```

## Prefer Over
- Prefer **just** over `make` for task recipes — better syntax, built-in arguments, no tab sensitivity
- Prefer **act** over push-and-pray for CI debugging — test Actions locally before pushing
- Prefer **git-cliff** over manual changelog writing — auto-generated from conventional commits
- Prefer **gh** CLI over GitHub web UI for batch operations — scriptable, JSON output, faster

## Do NOT Use When
- Simple git operations (commit, push, branch) — use git directly
- CI debugging that requires the exact GitHub runner environment — act uses Docker approximations
- One-time file copy — don't use restic for simple `cp` operations
- Project doesn't use conventional commits — git-cliff won't produce useful output
