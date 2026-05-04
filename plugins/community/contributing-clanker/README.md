# contributing-clanker

> Local-only OSS contribution command center. 41 deterministic gates against AI-slop failure modes.

[![version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/jeremylongshore/contributing-clanker)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/jeremylongshore/contributing-clanker/blob/master/LICENSE)
[![gates](https://img.shields.io/badge/gates-41%20installed-orange.svg)](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/005-AT-SPEC-gate-inventory.md)

**Links:** [source repo](https://github.com/jeremylongshore/contributing-clanker) · [gate inventory](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/005-AT-SPEC-gate-inventory.md) · [failure-mode catalog](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/007-DR-CATG-failure-mode-catalog.md) · [risk register](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/010-OD-RISK-operations-and-risk.md)

---

## What it does

`/contribute` becomes available in Claude Code. It walks any candidate issue through `open → shortlist → claimed → working → submitted → merged`, running phase-appropriate deterministic gates at each transition. Gates BLOCK on real-world AI-slop traps:

| Trap | Gate | What it catches |
|---|---|---|
| Issue already assigned to a human | `a01-already-assigned` | Stops scout from queuing duplicate work |
| PR already shipped, issue stale | `a02-already-shipped` | Catches "AI didn't notice this is closed" |
| Repo forbids AI-generated content | `e02-ai-strike-track` | Reads dossier policy, blocks claim |
| Branch name violates repo convention | `b02-branch-naming` | Cross-checks against dossier-cached convention |
| CI red before submit | `c12-ci-green` | Live `gh` query, blocks PR open |
| Maintainer reopened a closed issue against bot policy | `d05-no-reopen` | Blocks unilateral reopen |
| AI editor accidentally edits vendored code | `g01-no-vendored-edits` | Local-clone diff scan |

Full inventory + rationale: [`005-AT-SPEC-gate-inventory.md`](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/005-AT-SPEC-gate-inventory.md). Each gate maps to one of 62 enumerated [failure modes](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/007-DR-CATG-failure-mode-catalog.md) — every gate has a real-world trigger, no speculative guards.

## How it stays out of your way

- **Markdown-only state.** Per-repo dossiers at `~/.contribute-system/research/<owner>__<repo>.md` cache the rules (branch convention, CLA, AI policy, draft-first preference). Gates read the dossier, not live `gh`. A full pre-PR sweep is single-digit seconds.
- **No daemons.** Filesystem only. Survives any tool. Greppable, git-trackable.
- **Override with audit.** `--override-gate <ID> "reason"` for false positives. Reasons land in `~/.contribute-system/log.jsonl`. `audit-overrides.sh` reports gates you override ≥50% of the time — those are wrong, not yours.
- **Default to Design Issue, not PR.** Auto-PRs generate maintainer "whack-a-mole slopfests." The skill defaults to opening a design issue first; PR comes after maintainer approval of the approach.

## Install

```bash
/plugin install contributing-clanker
```

The post-install hook creates `~/.contribute-system/{candidates,research,gates,gates/lib,bin,check-runs}` and copies the runtime scripts in. Your candidate state and dossier history are yours — uninstall preserves them.

Prerequisites: `gh` authenticated (`gh auth status`) and `jq` on PATH.

## Verify

After install, in any Claude Code session:

```
/contribute
```

The skill activates, reports state (PRs in flight, claimed candidates, ready-to-pick queue), and stays out of the way until you give it work.

## Three layers

1. **Per-repo dossiers.** What the upstream expects of contributors — branch convention, CLA/DCO, AI policy, PR template requirements, review bots, etc. Built by `@researcher` from `CONTRIBUTING.md` + linked policy docs + bot detection. Cached, refreshable on a 14-day staleness threshold.

2. **Deterministic gates.** One small script per failure mode. `(candidate, dossier, intended action) → PASS / WARN / BLOCK / INFORM`. Read-only. Pluggable: drop a script in `~/.contribute-system/gates/`, the runner discovers it.

3. **Lifecycle workflow.** The skill itself walks each candidate through transitions, running the right gate set per transition. BLOCK refuses; WARN surfaces in the briefing.

## What this is NOT

- A bounty board — pre-2026-04-30 versions had Algora/Gumroad framing; that's gone.
- A tracker — no SQLite, no dashboard, no cloud backend. Filesystem is the tracker.
- A multi-user system — Phase 1 is single-user. Phase 3 (containerized service) only triggers if multi-user demand surfaces.
- An AI auto-PR generator — defaults to design-issue-first; never auto-submits without explicit human approval.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/contribute` doesn't activate after install | Restart Claude Code |
| `gh: not logged in` | `gh auth login` |
| `jq: command not found` | `apt-get install jq` (or equivalent for your platform) |
| Gate BLOCKs unexpectedly | Run `audit-overrides.sh` to see if it's a known false-positive cluster; override with `--override-gate <ID> "reason"` if so |
| Dossier missing for a repo | First contribution to that repo; `@researcher` auto-builds on first transition |
| Stale dossier (>14 days) | Auto-refresh on next gate run; or `@researcher refresh <owner>/<repo>` |

## License

MIT — see [LICENSE](https://github.com/jeremylongshore/contributing-clanker/blob/master/LICENSE) in the source repo.
