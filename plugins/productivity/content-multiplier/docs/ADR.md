# ADR: content-multiplier — instruction-driven skills over local brand files

**Author:** localplugins
**Date:** 2026-07-12
**Status:** Accepted

## Context

content-multiplier turns one source into on-brand, multi-channel, multi-language content,
driven by a brand profile the team owns in its own repository. The PRD requires that the
plugin run with no accounts, API keys, or native dependencies (FR-5), and that every asset
be checked against the saved brand profile before delivery (FR-4). The three skills
(`brand-voice`, `channel-formats`, `transcreation`) do the reading-and-writing work; the two
agents (`strategist`, `brand-guardian`) plan and review. If the skills reached for the
network or a broad shell, the plugin would break its no-setup promise and widen the attack
surface for content that is ultimately published.

## Decision

We implement each capability as an instruction-driven skill that reads local brand and spec
files and writes local output files — nothing more. The skills declare the minimal scoped
tool set `Read, Write, Glob`. No skill declares Bash, WebFetch, WebSearch, or Edit. Channel
specs and brand templates ship inside the plugin so no download is ever required.

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| Give skills broad `Bash` for file wrangling | Unscoped shell is an over-broad attack surface for a content tool that only needs to read and write Markdown; violates least privilege. |
| Fetch channel specs / examples over the network (WebFetch) | Breaks the no-accounts/no-network promise (FR-5) and makes output non-deterministic; specs are bundled instead. |
| One monolithic skill | Poor progressive disclosure and triggering; three focused skills map cleanly to the real jobs (voice, format, locale). |

## Consequences

**Positive:**

- Runs anywhere with zero setup; deterministic and auditable (local files only).
- Least-privilege tool scope keeps the review-then-publish path low-risk.
- Focused skills trigger accurately and keep each SKILL.md small, with detail in `references/`.

**Negative / accepted tradeoffs:**

- No live data (trends, competitor pages) can inform drafts — the user must supply sources.
- Bundled channel specs must be maintained in-repo as platforms change, rather than pulled live.

## Tool-permission scope

Every skill declares `allowed-tools: Read, Write, Glob` — least privilege for reading brand
profiles and specs and writing generated assets. No skill needs a shell, network, or editor.

| Tool | Why it's needed |
| ---- | --------------- |
| Read | Load the four brand-profile files, per-locale overrides, bundled channel specs, and the source content. |
| Glob | Locate the active brand profile (`content/brand/`, `content/brands/<name>/`, `locales/<xx-XX>/`) and the correct channel spec without hardcoded paths. |
| Write | Save finished, copy-paste-ready assets (`<channel>.md`, `<locale>/<channel>.md`) and index/calendar files. |
| Bash (not declared) | Not needed — no skill shells out; unscoped Bash would be an unjustified attack surface. |
| WebFetch / WebSearch (not declared) | Not needed — the plugin is offline by design (FR-5); sources are user-supplied and specs are bundled. |
| Edit (not declared) | Not needed — skills produce new output files rather than mutating existing project files in place. |
