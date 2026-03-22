# Apple Notes Skill Pack

> Claude Code skills for Apple Notes automation — JXA, AppleScript, Shortcuts, osascript (24 skills)

Apple Notes has no REST API. These skills use real macOS scripting technologies: JavaScript for Automation (JXA), AppleScript, osascript command-line tool, and Apple Shortcuts. All code examples are runnable on macOS via `osascript -l JavaScript`.

## Installation

```bash
/plugin install apple-notes-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `apple-notes-install-auth` | Grant macOS automation permissions, verify JXA/osascript access |
| `apple-notes-hello-world` | Create, read, list, search, delete notes via JXA |
| `apple-notes-local-dev-loop` | Hot-reload JXA dev with chokidar, test helpers |
| `apple-notes-sdk-patterns` | Node.js JXA wrapper class, batch operations, search |
| `apple-notes-core-workflow-a` | Batch note creation, template engine, folder organization |
| `apple-notes-core-workflow-b` | Export to Markdown, JSON, SQLite; full-text search |
| `apple-notes-common-errors` | Diagnose -1743, -1712, timeout, and TCC errors |
| `apple-notes-debug-bundle` | Diagnostic script: permissions, accounts, note count |
| `apple-notes-rate-limits` | iCloud sync throttling, 1 op/sec write limits |
| `apple-notes-security-basics` | TCC permissions, sandbox restrictions, export safety |
| `apple-notes-prod-checklist` | macOS automation readiness validation |
| `apple-notes-upgrade-migration` | macOS version migration, pre-upgrade backup |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `apple-notes-ci-integration` | GitHub Actions macOS runner with mocked client |
| `apple-notes-deploy-integration` | launchd service for scheduled automation |
| `apple-notes-webhooks-events` | Polling-based change detection (no native webhooks) |
| `apple-notes-performance-tuning` | SQLite cache, incremental sync, benchmark data |
| `apple-notes-cost-tuning` | iCloud storage management (Notes is free) |
| `apple-notes-reference-architecture` | Full architecture with osascript/JXA/SQLite cache |

### Flagship Skills (F19-F24)

| Skill | What It Does |
|-------|-------------|
| `apple-notes-multi-env-setup` | Multi-account configuration (iCloud, Gmail, On My Mac) |
| `apple-notes-observability` | Health monitoring script with launchd scheduling |
| `apple-notes-incident-runbook` | Recovery procedures for crashes, sync issues, permissions |
| `apple-notes-data-handling` | HTML body format, Markdown conversion, attachment handling |
| `apple-notes-enterprise-rbac` | Account and folder-based access control |
| `apple-notes-migration-deep-dive` | Migrate to/from Obsidian, Notion, Evernote |

## Key Concepts

- **No REST API** — Apple Notes is automated via osascript/JXA/AppleScript only
- **macOS only** — All automation requires a Mac with Notes.app
- **HTML body** — Note content is HTML; use converters for Markdown
- **iCloud sync** — Write operations trigger sync; throttle to 1/sec
- **TCC permissions** — macOS requires explicit automation permission grants

## License

MIT
