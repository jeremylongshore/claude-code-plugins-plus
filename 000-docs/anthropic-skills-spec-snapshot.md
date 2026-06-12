<!-- TOMBSTONE [9k5h.9]: this file previously held a versioned capture of
     https://code.claude.com/docs/en/skills (Snapshot ID 2026-05-07-initial). That
     copy diverged from later captures in intent-eval-lab and is retired — the lab
     vendored tier + the kernel are the single source for upstream spec content. -->

# Anthropic Skills Spec Snapshot — moved to the lab vendored single source

This vendored copy (2026-05-07 capture) is retired. Consult instead:

1. **Lab vendored single source** — `intent-eval-lab` `specs/_vendor/` (watcher-fed; surfaces `platform-skills-overview` + `skills-releases` and the rest of the 16-surface registry at `specs/upstream-surface-registry.v1.json`).
2. **Kernel upstream-base projection** — `@intentsolutions/core` `schemas/authoring/v1/upstream-base/skill-frontmatter.v1.json` (machine-readable composition of agentskills.io + the Claude docs folds). IS marketplace policy lives in the kernel `is-overlay/`, not in upstream captures.
3. **Live upstream** — <https://code.claude.com/docs/en/skills>.

The IS-authored interpretation docs (`6767-b-SPEC-DR-STND-claude-skills-standard.md`, `SCHEMA_CHANGELOG.md`) remain — they are synthesis, not upstream duplication.
