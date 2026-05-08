# AgentSkills.io Open Spec — Versioned Snapshot

**Snapshot ID**: 2026-05-07-initial
**Source**: https://agentskills.io/specification
**Captured**: 2026-05-07
**Refresh cadence**: Quarterly (manual PR or scheduled cron)
**Read by**: JRig Tier 3A spec-compliance check (called from `/validate-skillmd --thorough`)

---

## Why this file exists

AgentSkills.io is the open standard Claude Code follows for `compatibility`, `metadata`, and `license`. We capture it as a versioned snapshot for the same reason as the Anthropic spec snapshot — Tier 3A validates against frozen references, not live URLs.

---

## Required fields (open spec)

- `name`
- `description`

Same as Anthropic's spec floor.

---

## Optional fields (open spec)

| Field | Notes |
|---|---|
| `allowed-tools` | Optional under the open spec; IS marketplace requires it |
| `compatibility` | **Free-text string, max 500 chars.** Documents environment requirements (intended product, runtime, system packages, network access). NOT an enum. NOT a CSV platform list. The IS-invented `compatible-with` field was a closed allow-list and is deprecated. |
| `license` | SPDX identifier or human-readable description |
| `metadata` | Free-form key-value mapping for any additional context |

---

## `compatibility` field guidance (deeper)

Examples per the open spec:

```yaml
compatibility: "Designed for Claude Code"
compatibility: "Designed for Claude Code, also compatible with Codex and OpenClaw"
compatibility: "Requires Python 3.10+ with uv installed"
compatibility: "Requires git, docker, and jq on PATH"
compatibility: "Node.js >= 18, npm >= 9"
compatibility: "Designed for Claude Code; requires Bash 5+ and rg (ripgrep)"
compatibility: "Requires network access to api.example.com (port 443)"
```

Anti-pattern: enumerating a closed list of platforms. The deprecated IS `compatible-with: claude-code, codex, openclaw` was an enum — replaced by free-text `compatibility`.

---

## `metadata` field guidance

Open-ended object. Common keys observed in the wild:

- `category` (e.g., `devops`, `security`, `analytics`)
- `version` (when not at top-level — both forms valid per open spec)
- `author` (when not at top-level — both forms valid)
- `tags` (when not at top-level)
- `homepage`, `repository` (URLs to project sources)

The IS rubric prefers top-level `version` / `author` / `tags` (these are required at the IS marketplace tier). Skills that put them under `metadata` still pass, since the open spec accepts both.

---

## Refresh procedure

1. Fetch `https://agentskills.io/specification` rendered content
2. Diff against current snapshot — identify added / removed / changed fields
3. Update sections above (required, optional, `compatibility` guidance, `metadata` guidance)
4. Bump Snapshot ID to `YYYY-MM-DD-NN`
5. Open PR with the diff
6. PR review = human gate
7. Merge → Tier 3A reads new snapshot on next `--thorough` run

---

## Status

Initial seed snapshot, 2026-05-07. Captures the open-spec field facts the IS validator already enforces (`compatibility` free-text, `metadata` open object, `license` optional). First quarterly refresh will check live URL for any changes since this date.
