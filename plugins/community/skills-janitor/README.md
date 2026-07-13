# Skills Janitor

> Tinder for your Claude Code skills. Swipe through your collection and delete what's wasting context, in seconds.

Works with **Claude Code** and **OpenAI Codex**. 5 commands, zero dependencies.

![/janitor-swipe — swipe keep / delete / skip through every installed skill](janitor-swipe-demo.gif)

> **New in v1.4: `/janitor-swipe`.** Every installed skill becomes a card, sorted heaviest-and-least-used first. Swipe left to delete, right to keep, down to skip. Most setups clear 30–40% of their skill token cost before the deck even ends. [Jump to swipe →](#swipe-through-your-skills-v14)

Scans every place a skill lives: user, project, codex, and every skill installed via `/plugin install`. Surfaces duplicates, broken symlinks, and unused skills cluttering your context.

## Commands

| Command | What it does |
|---|---|
| `/janitor-report` | Health check: inventory, duplicates, broken skills. `--brief` for inventory only. |
| `/janitor-fix` | Auto-fix issues. `--prune` removes broken symlinks and empty dirs. |
| `/janitor-value` | Honest token costs (always-loaded descriptions vs on-demand bodies) + usage, skills and subagents. |
| `/janitor-discover` | Search GitHub for skills, or check a URL before installing. |
| `/janitor-swipe` | Interactive TUI — swipe keep/delete/skip on every installed skill, sorted most-likely-waste first. (v1.4+) |

Each has its own slash command. Or use natural language: *"check my skills"*, *"which skills are wasting context?"*, *"find an n8n skill"*.

## Install

```
/plugin marketplace add khendzel/skills-janitor
/plugin install skills-janitor
```

Or via [skills.sh](https://skills.sh):

```bash
npx skills add khendzel/skills-janitor
```

Or clone directly:

```bash
git clone https://github.com/khendzel/skills-janitor ~/.claude/skills/skills-janitor
```

## Swipe through your skills (v1.4)

Tinder-style triage for your skill collection. The deck is sorted heaviest-and-least-used first, so most users hit `← delete` through the top 5–10 cards and quit before reviewing everything.

```
!bash ~/.claude/skills/skills-janitor/scripts/swipe.sh
```

(The `!` prefix runs in your terminal, not the Claude Code Bash tool — the TUI needs a real interactive stdin.)

Controls: `←` delete, `→` keep, `↓` skip, `u` undo, `i` inspect full description, `q` quit.

Plugin skills are flagged for review (you can't `rm` individual plugin skills — they belong to a plugin). User-scope skills stage for actual deletion, applied on `y` confirmation at the end.

## What v1.3 catches that v1.2 missed

The duplicate detector now flags cross-scope overlaps that were invisible before:

```
=== Skills Janitor - Duplicate Detection ===

--- Description Overlap (Jaccard > 30%) ---

  [98%] marketing-seo-audit <-> marketing-skills:seo-audit
        Scopes: user / plugin

  [100%] marketing-content-strategy <-> marketing-skills:content-strategy
        Scopes: user / plugin
```

If you installed a plugin that re-implements a skill you already had standalone, v1.3 tells you. v1.2 couldn't, because it was blind to the plugin tree entirely.

## v1.2 → v1.3 migration

The five v1.2 aliases were removed in v1.5. Renames:

| v1.2 | v1.3 |
|---|---|
| `/janitor-audit` | `/janitor-report --brief` |
| `/janitor-usage` | `/janitor-value` |
| `/janitor-tokens` | `/janitor-value` |
| `/janitor-search` | `/janitor-discover` |
| `/janitor-precheck` | `/janitor-discover <url>` |

Full release notes: [CHANGELOG.md](CHANGELOG.md).

## Requirements

Bash, Python 3, `curl`. No pip installs, no node modules.

## Contributing

PRs welcome. Each command is self-contained in `skills/janitor-*/SKILL.md` plus a sibling script in `scripts/`.

## License

MIT
