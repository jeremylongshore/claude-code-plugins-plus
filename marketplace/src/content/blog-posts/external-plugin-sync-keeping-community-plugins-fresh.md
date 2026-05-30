---
title: "Building External Plugin Sync: How We Keep 258 Community Plugins Fresh"
description: "How we built daily automated sync infrastructure to keep community plugins fresh in the claude-code-plugins marketplace, featuring the n-skills pattern with GitHub Actions and auto-PR creation."
date: "2026-01-03"
tags: ["claude-code", "automation", "github-actions", "open-source", "plugin-marketplace"]
featured: false
---
## The Problem: Static Forks Go Stale

We got a PR from [Numman Ali](https://github.com/numman-ali) adding two plugins to our Claude Code marketplace:

- **gastown**: Multi-agent orchestrator for Claude Code
- **zai-cli**: Vision, search, reader, and GitHub exploration

But then he commented:

> "Hey, I'm constantly updating the plugin and this will become stale very quickly, I don't think it's a good idea to publish like this. You might want to add a sync mechanism like I've done for dev-browser by Sawyer Hood"

He was absolutely right. Copying plugins creates stale forks. His plugins evolve rapidly in his [n-skills repository](https://github.com/numman-ali/n-skills). We needed a better approach.

## The n-skills Pattern: Daily Automated Sync

Numman's n-skills marketplace solves this with external sync:

1. **sources.yaml** - Manifest listing external repos
2. **GitHub Actions cron** - Runs daily at midnight UTC
3. **sync script** - Pulls latest from upstream repos via GitHub API
4. **.source.json** - Attribution metadata per synced skill
5. **Auto-PR** - Creates PR with changes for review

This pattern keeps authors in control while the marketplace stays fresh.

## Building Our Sync Infrastructure

### Phase 1: Validation (The Messy Part)

First, we ran our validators on Numman's plugins. This revealed missing 2025 schema fields:

```bash
$ node scripts/validate-plugin.js plugins/community/gastown/

❌ SKILL.md missing required fields:
   - allowed-tools (REQUIRED for 2025 schema)
   - version (REQUIRED for 2025 schema)
```

The 2025 Claude Code skills schema requires:

```yaml
name: skill-name
description: |
  What this skill does with trigger phrases
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
license: Apache-2.0
author: Name <email>
```

We fixed both plugins manually, adding the missing fields so validation passed. This raised a question: when sync runs, will our local fixes get overwritten by Numman's source files?

**Answer**: Yes, and that's correct. The sync should pull his latest. We just needed to document the 2025 schema fields for him to add on his end.

### Phase 2: The Sync Engine

Created `scripts/sync-external.mjs` (337 lines):

```javascript
import https from 'https';
import yaml from 'js-yaml';

// Fetch file content from GitHub API
async function fetchFromGitHub(repo, filePath, branch = 'main') {
  const url = `https://api.github.com/repos/${repo}/contents/${filePath}?ref=${branch}`;

  // Add auth token if available
  const headers = {
    'User-Agent': 'claude-code-plugins-sync',
    'Accept': 'application/vnd.github.v3+json',
  };

  if (process.env.GITHUB_TOKEN) {
    headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
  }

  // Fetch and decode base64 content
  // Compare with local files
  // Write updates and .source.json
}
```

**Key features:**

- GitHub API with auth token support
- Recursive directory fetching
- Glob pattern include/exclude filtering
- Dry-run mode for testing
- Source-specific filtering (`--source=NAME`)
- Provenance tracking via `.source.json`

**The js-yaml dependency issue:**

When testing locally, we hit:

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'js-yaml'
```

We tried installing via npm but the local environment had issues. Then we realized: **the GitHub Actions workflow installs js-yaml at runtime**. Local testing failure doesn't matter because production runs in CI.

This was a good reminder: don't over-optimize local dev environments when CI is the target.

### Phase 3: sources.yaml Configuration

Created the external source manifest:

```yaml
sources:
  - name: gastown
    description: Multi-agent orchestrator for Claude Code
    repo: numman-ali/n-skills
    source_path: skills/tools/gastown
    target_path: plugins/community/gastown
    author:
      name: Numman Ali
      github: numman-ali
      email: numman.ali@gmail.com
    license: Apache-2.0
    category: community
    verified: true
    include:
      - "SKILL.md"
      - "README.md"
      - "references/**"
    exclude:
      - "node_modules/**"
      - ".git/**"
      - "*.log"

  - name: zai-cli
    description: Z.AI vision, search, reader, and GitHub exploration
    repo: numman-ali/n-skills
    source_path: skills/tools/zai-cli
    target_path: plugins/community/zai-cli
    # ... same pattern
```

The include/exclude patterns give authors control over what gets synced.

### Phase 4: GitHub Actions Workflow

Created `.github/workflows/sync-external.yml`:

```yaml
name: Sync External Plugins

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch:
    inputs:
      force:
        description: 'Force sync even if no changes detected'
        type: boolean
        default: false
      source:
        description: 'Sync only this source (leave empty for all)'
        type: string
        default: ''
      dry_run:
        description: 'Dry run - show what would change'
        type: boolean
        default: false

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install js-yaml

      - name: Run sync script
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ARGS="--verbose"
          if [ "${{ inputs.force }}" = "true" ]; then
            ARGS="$ARGS --force"
          fi
          if [ -n "${{ inputs.source }}" ]; then
            ARGS="$ARGS --source=${{ inputs.source }}"
          fi
          if [ "${{ inputs.dry_run }}" = "true" ]; then
            ARGS="$ARGS --dry-run"
          fi
          node scripts/sync-external.mjs $ARGS

      - name: Create Pull Request
        if: steps.changes.outputs.has_changes == 'true'
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: |
            chore(sync): update external plugins from upstream
          title: "🔄 Sync external plugins"
          branch: sync/external-plugins
          labels: automated, sync, external-plugins
```

**Workflow features:**

- Daily cron at midnight UTC
- Manual dispatch with options (force, source filter, dry-run)
- Auto-PR creation with peter-evans/create-pull-request
- Change detection to avoid empty PRs

### Phase 5: Testing the Workflow

Triggered a dry-run manually:

```bash
$ gh workflow run sync-external.yml \
  --repo jeremylongshore/claude-code-plugins-plus-skills \
  -f dry_run=true
```

Results:

```
📦 Syncing: gastown
   Found 6 files in source
   📝 Would update: SKILL.md
   📝 Would create: references/commands.md
   📝 Would create: references/concepts.md
   📝 Would create: references/setup.md
   📝 Would create: references/troubleshooting.md
   📝 Would create: references/tutorial.md

📦 Syncing: zai-cli
   Found 2 files in source
   📝 Would update: SKILL.md
   📝 Would create: references/advanced.md

✅ 8 file(s) would be synced
```

Perfect! The sync discovered Numman's reference documentation that we didn't have locally.

## Technical Decisions

### Why GitHub API Instead of Git Submodules?

**Submodules are brittle:**

- Require recursive clones
- Break easily when upstream changes
- Complicated for contributors
- Hard to manage at scale (258 plugins)

**GitHub API is clean:**

- Simple HTTP requests
- No git state to manage
- Easy error handling
- Rate limits are generous with auth token

### Why Auto-PR Instead of Direct Commit?

**Safety and transparency:**

- Review changes before merging
- Catch breaking updates
- Audit trail for all syncs
- Can add validation checks to PR

### Why .source.json for Attribution?

**Legal and ethical:**

- Clear provenance tracking
- License compliance
- Author attribution
- Upstream repo visibility

Each synced plugin gets `.source.json`:

```json
{
  "synced_from": {
    "repo": "numman-ali/n-skills",
    "path": "skills/tools/gastown",
    "branch": "main"
  },
  "last_sync": "2026-01-03T02:48:45.000Z",
  "author": {
    "name": "Numman Ali",
    "github": "numman-ali"
  },
  "license": "Apache-2.0",
  "files_synced": 6
}
```

## What We Learned

### 1. Validate Before You Sync

Running validators on Numman's plugins **before** building sync infrastructure revealed the 2025 schema gap. If we'd built sync first, we would've synced non-compliant plugins.

**Lesson**: Validate inputs, not just outputs.

### 2. Local != Production

The js-yaml dependency worked fine in CI but failed locally. We spent time trying to fix the local environment before realizing: **CI is the target, local is nice-to-have**.

**Lesson**: Don't over-optimize for local dev when CI/CD is the real environment.

### 3. Documentation Is Infrastructure

Adding the "External Plugin Sync" section to README.md wasn't just documentation - it's the **contributor onboarding flow**. Authors need to know:

- How to request sync
- What fields are required
- How often sync runs
- How to update their source

**Lesson**: README sections are product features, not afterthoughts.

### 4. Author Ownership > Marketplace Control

The best part of this pattern: **authors own their code**. We mirror it, but they control:

- Release timing
- Feature development
- Documentation updates
- Version bumping

**Lesson**: Enable creators, don't gatekeep.

## Results and Impact

**Immediate:**

- 2 plugins (gastown, zai-cli) now sync daily
- 8 files will update on first real sync (tonight at midnight UTC)
- Reference docs from n-skills will appear in our marketplace

**Future:**

- Open path for more community authors
- Marketplace stays fresh without manual PRs
- Authors can develop at their own pace

**Infrastructure:**

- 585 lines added (sources.yaml, sync script, workflow, README)
- 100% automated after initial setup
- Zero maintenance for plugin authors

## Call to Action: Request External Sync

If you maintain Claude Code plugins in your own repo and want us to sync them:

1. **Open an issue** with:
   - Your GitHub repo URL
   - Path to your plugin/skill
   - Brief description

2. **We'll add you to `sources.yaml`**

3. **Daily sync begins automatically**

**Requirements:**

- Must follow 2025 skills schema (we'll help you validate)
- Open source license (MIT, Apache-2.0, etc.)
- Stable repo structure

We handle the sync, you keep coding.

## Related Posts

- AI-Assisted Technical Writing Automation Workflows - Another example of automation reducing manual work
- Building Post-Compaction Recovery with Beads - How we solve context loss in AI sessions
- AI Dev Transformation Part 4: Dual AI Workflows - Combining human and AI strengths

## Resources

- **Marketplace**: https://claudecodeplugins.io/
- **Sync Infrastructure**: [Commit 4c006c58](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/commit/4c006c58)
- **Numman's n-skills**: https://github.com/numman-ali/n-skills
- **Request Sync**: [Open an issue](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues)

*Built with Claude Code. The entire sync infrastructure - from problem identification to production deployment - happened in a single session.*
