# Obsidian Skill Pack

> 24 Claude Code skills for Obsidian plugin development — from first scaffold to community plugin submission.

Every skill uses real Obsidian Plugin API: `Plugin`, `Vault`, `MetadataCache`, `ItemView`, `Modal`, `Editor`, `FuzzySuggestModal`. No stubs, no placeholders.

## Installation

```bash
/plugin install obsidian-pack@claude-code-plugins-plus
```

## What You Get

**Plugin Lifecycle** — Scaffold a plugin from scratch (`core-workflow-a`), add views/modals/context menus (`core-workflow-b`), set up hot-reload dev loop (`local-dev-loop`), apply production patterns (`sdk-patterns`), validate for release (`prod-checklist`), publish to community plugins (`deploy-integration`).

**Vault Operations** — Typed settings with versioned migration, safe file CRUD with `normalizePath`, frontmatter access via `processFrontMatter`, `MetadataCache` queries for tags/links/backlinks, debounced `modify` handlers, IndexedDB for large datasets.

**Debugging & Ops** — Structured logger with ring buffer, metrics collector with p95 timers, error tracker with deduplication, debug sidebar panel, diagnostic bundle collector, systematic incident runbook.

**Performance** — Lazy initialization, batch processing with UI yielding, LRU cache with mtime invalidation, per-file debounce, virtual scrolling, `requestAnimationFrame` coalescing, memory leak prevention.

**Migration & Enterprise** — Notion/Evernote/Roam/Bear/Apple Notes migration scripts, RBAC permission checker plugin, config lockdown with SHA-256 hashing, multi-environment vault management, CI/CD with GitHub Actions.

## Skills (24)

### Standard (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `obsidian-install-auth` | Clone sample plugin, install deps, symlink into dev vault |
| `obsidian-hello-world` | Commands, settings tab, ribbon icon, modal, status bar |
| `obsidian-local-dev-loop` | esbuild watch, hot reload, DevTools debugging, vitest mocks |
| `obsidian-sdk-patterns` | Settings migration, safe vault ops, event cleanup, MetadataCache |
| `obsidian-core-workflow-a` | Full plugin scaffold: Plugin class, esbuild, manifest, commands |
| `obsidian-core-workflow-b` | ItemView, FuzzySuggestModal, editor commands, context menus, Vault API |
| `obsidian-common-errors` | Fix 6 frequent errors: null workspace, bad manifest, missing CSS |
| `obsidian-debug-bundle` | Collect vault diagnostics: plugins, theme, stats, console errors |
| `obsidian-rate-limits` | Debounce, batch, throttle, async write queue, registerInterval |
| `obsidian-security-basics` | Credential encryption, XSS prevention, URI validation, HTTPS |
| `obsidian-prod-checklist` | Manifest validation, console.log audit, memory leak check, mobile |
| `obsidian-upgrade-migration` | API version migration, settings schema upgrade, CM5-to-CM6 |

### Pro (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `obsidian-ci-integration` | GitHub Actions build/release/validate workflows, BRAT beta |
| `obsidian-deploy-integration` | Community plugin submission, version bump, release assets |
| `obsidian-webhooks-events` | Vault/workspace/MetadataCache events, DOM events, custom event bus |
| `obsidian-performance-tuning` | Profiling, lazy init, LRU cache, virtual scrolling, WeakMap |
| `obsidian-cost-tuning` | Sync storage audit, API caching, Publish optimization, self-hosted sync |
| `obsidian-reference-architecture` | Modular project structure, service layer, command/view registries |

### Flagship (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `obsidian-multi-env-setup` | Dev/test/prod vaults, env detection, vault templates, sync config |
| `obsidian-observability` | Logger, MetricsCollector, ErrorTracker, debug sidebar panel |
| `obsidian-incident-runbook` | Plugin crash recovery, vault corruption, sync conflicts, CSS reset |
| `obsidian-data-handling` | loadData/saveData, Vault I/O, processFrontMatter, IndexedDB |
| `obsidian-enterprise-rbac` | Permission model, write interception, plugin allowlist, config lockdown |
| `obsidian-migration-deep-dive` | Notion/Evernote/Roam/Bear migration with link conversion |

## API Coverage

| Obsidian API | Skills Using It |
|-------------|----------------|
| `Plugin` (lifecycle, commands, settings) | All 24 |
| `Vault` (read, create, modify, delete) | core-workflow-b, sdk-patterns, data-handling, rate-limits |
| `MetadataCache` (tags, links, frontmatter) | sdk-patterns, data-handling, webhooks-events |
| `ItemView` (sidebar panels) | core-workflow-b, observability, reference-architecture |
| `Modal` / `FuzzySuggestModal` | core-workflow-b, hello-world |
| `Editor` (selections, cursor) | core-workflow-b, hello-world, common-errors |
| `PluginSettingTab` / `Setting` | hello-world, core-workflow-a, reference-architecture |
| `processFrontMatter` | data-handling, rate-limits, upgrade-migration |
| `registerEvent` / `registerInterval` | sdk-patterns, webhooks-events, rate-limits |
| `requestUrl` | security-basics |
| `debounce` | sdk-patterns, rate-limits, performance-tuning |
| `Platform` / `FileSystemAdapter` | security-basics, prod-checklist |

## Usage

Skills trigger automatically when you discuss Obsidian topics:

- "Help me create an Obsidian plugin" -> `obsidian-core-workflow-a`
- "My plugin crashes on startup" -> `obsidian-common-errors`
- "Set up CI for my Obsidian plugin" -> `obsidian-ci-integration`
- "Migrate my Notion notes to Obsidian" -> `obsidian-migration-deep-dive`
- "My plugin is slow on large vaults" -> `obsidian-performance-tuning`

## License

MIT
