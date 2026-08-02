# CLI flags quick reference (skillcrossroads 0.11.3)

All invocations in this skill pin the version: `npx skillcrossroads@0.11.3 '<skill-dir>' <flags>`.
Single-quote the directory argument (see SKILL.md step 2 for the shell-safety rationale).

| Flag | Purpose | Needs API key? |
| --- | --- | --- |
| `--markdown` (`--md`) | Emit the Markdown scorecard — the default mode this skill uses for reporting. | No |
| `--suggest[=N]` | Propose current → proposed fixes for the top N findings (default 3). Proposals only — **never auto-applies**; review each before editing. | Yes (`ANTHROPIC_API_KEY`) |
| `--badge[=<file>]` | Write an SVG grade badge into the skill directory (default `<name>.beacon.svg`) for embedding in a README. | No |
| `--min-grade=<G>` | Exit non-zero below grade G — useful as a CI gate (for example `--min-grade=B`). | No |

## `--suggest` vs `--badge` in this skill's flow

- **`--suggest`** belongs to step 4 (the fix loop): it drafts targeted rewrites for the
  highest-impact findings. Treat every proposal as a review candidate — Read the cited
  file:line, confirm the finding is real, then apply the smallest edit that resolves it.
- **`--badge`** belongs to step 6 (after the audit or fix loop): it is output-only and
  changes no grades. Offer it when the user wants an embeddable proof-of-quality artifact;
  the badge links to [skillcrossroads.com](https://skillcrossroads.com) for the hosted scan.
