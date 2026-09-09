# Distribution Strategy for claude-reflect

This document outlines submission materials for maximizing plugin distribution across Claude Code plugin marketplaces and awesome-lists.

## Priority Targets (Ranked by Impact)

### Tier 1: High Impact

| Platform | Type | Estimated Reach | Status |
|----------|------|-----------------|--------|
| [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | Official Marketplace | Highest | [PR #111](https://github.com/anthropics/claude-plugins-official/pull/111) |
| [ccplugins/awesome-claude-code-plugins](https://github.com/ccplugins/awesome-claude-code-plugins) | Curated List | ~1k+ stars | [PR #8](https://github.com/ccplugins/awesome-claude-code-plugins/pull/8) |
| [jeremylongshore/claude-code-plugins-plus](https://github.com/jeremylongshore/claude-code-plugins-plus) | Marketplace (243+ plugins) | High | [PR #241](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/241) |

### Tier 2: Medium Impact

| Platform | Type | Status |
|----------|------|--------|
| [GiladShoham/awesome-claude-plugins](https://github.com/GiladShoham/awesome-claude-plugins) | Marketplace | Ready |
| [hekmon8/awesome-claude-code-plugins](https://github.com/hekmon8/awesome-claude-code-plugins) | Curated List | Ready |
| [jmanhype/awesome-claude-code](https://github.com/jmanhype/awesome-claude-code) | Curated List | Ready |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Workflows/Hooks Focus | Ready |

### Tier 3: Additional Reach

| Platform | Type | Status |
|----------|------|--------|
| [claudecodecommands.directory](https://claudecodecommands.directory/submit) | Web Directory | Ready |
| [claude-plugins.dev](https://claude-plugins.dev) | Community Registry | Ready |
| [ananddtyagi/cc-marketplace](https://github.com/ananddtyagi/claude-code-marketplace) | Marketplace | Ready |

---

## Submission 1: anthropics/claude-plugins-official

**Target**: `external_plugins/claude-reflect/`

**Requirements**:
- Must meet quality and security standards
- Standard plugin structure with `.claude-plugin/plugin.json`
- README documentation
- No hardcoded secrets

### PR Title
```
feat: Add claude-reflect - self-learning system for CLAUDE.md
```

### PR Description
```markdown
## Summary

Adds **claude-reflect** to external_plugins - a self-learning system that captures user corrections during Claude Code sessions and syncs them to CLAUDE.md.

## What it does

- **Automatic capture**: Hooks detect correction patterns ("no, use X", "actually...", "remember:") and queue them
- **Human review**: `/reflect` command processes queue with user approval before writing
- **Multi-target sync**: Updates ~/.claude/CLAUDE.md, ./CLAUDE.md, and AGENTS.md (industry standard)
- **Historical scan**: `/reflect --scan-history` finds corrections from past sessions

## Plugin Features

| Feature | Description |
|---------|-------------|
| Hooks | PreCompact (backup queue), PostToolUse (post-commit reminder) |
| Commands | `/reflect`, `/skip-reflect`, `/view-queue` |
| Pattern Detection | Corrections, positive feedback, explicit "remember:" markers |
| Confidence Scoring | 0.60-0.90 based on pattern strength |

## Quality Checklist

- [x] Standard plugin structure with `.claude-plugin/plugin.json`
- [x] Comprehensive README with usage examples
- [x] MIT License
- [x] No hardcoded secrets or credentials
- [x] Tested locally
- [x] Scripts have proper permissions

## Installation

```bash
/plugin install claude-reflect@claude-plugins-official
```

## Links

- Repository: https://github.com/bayramannakov/claude-reflect
- License: MIT
```

---

## Submission 2: ccplugins/awesome-claude-code-plugins

**Category**: Workflow Orchestration (or Development Engineering)

### PR Title
```
Add claude-reflect to Workflow Orchestration
```

### Entry to Add (in README.md under "Workflow Orchestration")
```markdown
- [claude-reflect](https://github.com/bayramannakov/claude-reflect) - Self-learning system that captures corrections during sessions and syncs to CLAUDE.md. Features hook-based detection, confidence scoring, and multi-target export to AGENTS.md.
```

---

## Submission 3: GiladShoham/awesome-claude-plugins

**Structure**: Full plugin directory under `plugins/claude-reflect/`

### Required Files

```
plugins/claude-reflect/
├── .claude-plugin/
│   └── plugin.json       # Copy from repo
├── hooks/
│   └── hooks.json        # Copy from repo
├── commands/
│   ├── reflect.md
│   ├── skip-reflect.md
│   └── view-queue.md
└── README.md             # Summary version
```

### plugin.json
```json
{
  "name": "claude-reflect",
  "version": "1.4.1",
  "description": "Self-learning system for Claude Code that captures corrections and updates CLAUDE.md automatically",
  "author": {
    "name": "Bayram Annakov",
    "url": "https://github.com/bayramannakov"
  },
  "repository": "https://github.com/bayramannakov/claude-reflect",
  "license": "MIT",
  "keywords": [
    "claude-code",
    "self-learning",
    "corrections",
    "CLAUDE.md",
    "memory",
    "learnings"
  ],
  "hooks": "./hooks/hooks.json"
}
```

### PR Description
```markdown
## Add claude-reflect plugin

A self-learning system for Claude Code that:
- Captures corrections during sessions via hooks
- Queues learnings with confidence scoring
- Processes with human review via `/reflect`
- Syncs to CLAUDE.md and AGENTS.md

### Validation
- [x] Ran `./validate-plugins.sh` successfully
- [x] JSON schema valid
- [x] No duplicate names
- [x] All references accurate
```

---

## Submission 4: jeremylongshore/claude-code-plugins-plus

**Option A: External Sync Request** (Recommended - maintainers mirror from your repo daily)

Email to: jeremy@intentsolutions.io
```
Subject: External Plugin Sync Request: claude-reflect

Hi Jeremy,

I'd like to request external plugin synchronization for claude-reflect:

Repository: https://github.com/bayramannakov/claude-reflect
Category: Workflow Orchestration / Development Tools

Description: Self-learning system that captures corrections during Claude Code sessions and syncs them to CLAUDE.md. Features:
- Hook-based pattern detection (corrections, positive feedback, explicit markers)
- Confidence scoring (0.60-0.90)
- Human review via /reflect command
- Multi-target export (CLAUDE.md + AGENTS.md)

The plugin is production-ready with MIT license. Happy to provide any additional information needed.

Best,
Bayram Annakov
```

**Option B: Direct PR**

Add to `plugins/community/claude-reflect/` with standard structure.

---

## Submission 5: hekmon8/awesome-claude-code-plugins

### PR Title
```
Add claude-reflect - self-learning CLAUDE.md manager
```

### Entry to Add
```markdown
### Workflow Orchestration
- [claude-reflect](https://github.com/bayramannakov/claude-reflect) - Captures corrections during sessions and syncs to CLAUDE.md with human review. Includes hooks for automatic detection and confidence scoring.
```

---

## Submission 6: jmanhype/awesome-claude-code

### Category: Plugins & Extensions

### Entry to Add
```markdown
- **[claude-reflect](https://github.com/bayramannakov/claude-reflect)** - Self-learning system that captures corrections and updates CLAUDE.md automatically
  ```bash
  /plugin marketplace add bayramannakov/claude-reflect
  /plugin install claude-reflect@claude-reflect-marketplace
  ```
```

---

## Submission 7: hesreallyhim/awesome-claude-code

### Category: Hooks (primary) + Agent Skills

### Entry to Add
```markdown
### Hooks
- [claude-reflect](https://github.com/bayramannakov/claude-reflect) - Self-learning hooks that capture corrections (PreCompact backup, PostToolUse reminders) and sync to CLAUDE.md via `/reflect` command.
```

---

## Submission 8: claudecodecommands.directory

**URL**: https://claudecodecommands.directory/submit

### Form Fields

| Field | Value |
|-------|-------|
| Name | claude-reflect |
| Description | Self-learning system that captures corrections during Claude Code sessions and syncs them to CLAUDE.md with human review |
| Repository URL | https://github.com/bayramannakov/claude-reflect |
| Category | Workflow / Development Tools |
| Commands | /reflect, /skip-reflect, /view-queue |
| Author | Bayram Annakov |

---

## Submission 9: claude-plugins.dev

**GitHub**: https://github.com/Kamalnrf/claude-code-plugins

### PR to add to registry

Check their CONTRIBUTING.md or open an issue requesting addition.

---

## Marketing Copy

### One-liner
> Self-learning system for Claude Code that captures corrections and syncs to CLAUDE.md

### Short Description (125 chars)
> Captures user corrections during sessions, queues with confidence scoring, processes with human review via /reflect command

### Full Description
> claude-reflect is a two-stage self-learning system for Claude Code. Stage 1 automatically captures corrections via hooks - detecting patterns like "no, use X", "actually...", and explicit "remember:" markers. Stage 2 is the `/reflect` command where you review queued learnings before they're written to CLAUDE.md. Supports confidence scoring, historical session scanning, semantic deduplication, and multi-target export to AGENTS.md (Codex, Cursor, Aider, Jules, Zed, Factory).

### Key Features (Bullet Points)
- Automatic correction detection via hooks
- Confidence scoring (0.60-0.90)
- Human review before writing
- Historical session scanning
- Multi-target sync (CLAUDE.md + AGENTS.md)
- Semantic deduplication

---

## Execution Checklist

1. [ ] Fork anthropics/claude-plugins-official → PR to external_plugins/
2. [ ] Fork ccplugins/awesome-claude-code-plugins → PR with entry
3. [ ] Fork GiladShoham/awesome-claude-plugins → PR with full plugin structure
4. [ ] Email jeremylongshore for external sync OR fork claude-code-plugins-plus
5. [ ] Fork hekmon8/awesome-claude-code-plugins → PR with entry
6. [ ] Fork jmanhype/awesome-claude-code → PR with entry
7. [ ] Fork hesreallyhim/awesome-claude-code → PR with entry
8. [ ] Submit form at claudecodecommands.directory/submit
9. [ ] Open issue/PR at Kamalnrf/claude-code-plugins

---

## Notes

- Keep descriptions consistent across platforms
- Link back to main repo: https://github.com/bayramannakov/claude-reflect
- Use MIT license (already in place)
- Version at time of submission: 1.4.1
