# CLI flags quick reference (skillcrossroads 0.11.4)

All invocations in this skill pin the version and pass `--no-llm`:
`npx skillcrossroads@0.11.4 '<skill-dir>' --no-llm <flags>`.
Single-quote the directory argument (see SKILL.md step 2 for the shell-safety rationale).

⚠️ **`--no-llm` is not the CLI's own default.** Without it, the CLI sends content to
Anthropic's Messages API whenever `ANTHROPIC_API_KEY` is present in the environment — it does
not prompt first. This skill therefore passes it explicitly on every command except the
opt-in `--suggest` in step 4.

The column that matters is what leaves the machine, not whether a key is required:

| Flag | Purpose | Sends your content off-machine? |
| --- | --- | --- |
| `--no-llm` | Force the fully local path: all six rubric categories scored deterministically. **This skill passes it on every command below.** | **No — never.** |
| `--markdown` (`--md`) | Emit the Markdown scorecard — the default mode this skill uses for reporting. | No, as this skill invokes it (`--no-llm`). Without `--no-llm` and with a key set, yes: per-check excerpts of 1,500-2,500 characters. |
| `--badge[=<file>]` | Write an SVG grade badge for embedding in a README. Writes to the **current working directory** as `<name>.beacon.svg`, not into the skill directory - pass `--badge=<path>` to place it explicitly. | No, as this skill invokes it (`--no-llm`). |
| `--min-grade=<G>` | Exit non-zero below grade G — useful as a CI gate (for example `--min-grade=B`). | No, as this skill invokes it (`--no-llm`). |
| `--suggest[=N]` | Propose current → proposed fixes for the top N findings (default 3). Proposals only — **never auto-applies**; review each before editing. | **Yes — up to 24,000 characters of the entry file**, to `api.anthropic.com`, billed to your own `ANTHROPIC_API_KEY`. Requires explicit user consent (SKILL.md step 4). |

Model results are cached on disk by content hash: `./.beacon-cache` if present, else
`%LOCALAPPDATA%\skillcrossroads\cache` (Windows), `$XDG_CACHE_HOME/skillcrossroads` when set,
otherwise `~/.cache/skillcrossroads`.

## `--suggest` vs `--badge` in this skill's flow

- **`--suggest`** belongs to step 4 (the fix loop) and is the only off-machine command here,
  so it runs only after the user agrees: it drafts targeted rewrites for the
  highest-impact findings. Treat every proposal as a review candidate — Read the cited
  file:line, confirm the finding is real, then apply the smallest edit that resolves it.
- **`--badge`** belongs to step 6 (after the audit or fix loop): it is output-only and
  changes no grades. Offer it when the user wants an embeddable proof-of-quality artifact;
  the badge links to [skillcrossroads.com](https://skillcrossroads.com) for the hosted scan.
