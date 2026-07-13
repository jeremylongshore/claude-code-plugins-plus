# ADR: brand-forge — vector-first generation with a gated raster opt-in

**Author:** localplugins
**Date:** 2026-07-12
**Status:** Accepted

## Context

brand-forge must produce on-brand assets that are exact (correct palette and fonts),
reproducible, and safe to run anywhere — including CI and scripted contexts where no
human approves a network call or supplies a secret. Two forces pull against each other.
Vector assets (logos, social templates, documents) can be generated deterministically
and locally, with no account or key. Photographic imagery cannot: it needs an external
image model, which means a provider key, network egress, cost, and latency. Treating
both paths identically would either force credentials on the common case or hide a
paid network call behind an innocuous request. The skills also run untrusted-ish input
(brand text, headlines) into generated markup, so output handling must be safe by
construction.

## Decision

We split generation into two engines. The vector engine (generate-logo,
generate-social, generate-doc-template) runs Node generators against a saved brand
profile and emits SVG with zero network access and zero credentials. The raster engine
(generate-graphic) is the single opt-in path to an image model and runs only when both
`BRAND_FORGE_RASTER=1` and a provider key are present; otherwise it stops and offers a
vector alternative. All skills declare the same least-privilege tool set —
`Read, Write, Glob, Bash(node:*)` — route every asset through the `visual-guardian`
review pass, and never auto-post output. Text is always escaped before entering markup
and, for raster, added as a vector overlay rather than baked into the image.

## Alternatives considered

| Alternative | Why rejected |
| --- | --- |
| One engine that always calls an image model | Forces a key and network on logos, social, and docs that need neither; breaks CI and offline use. |
| Enable raster automatically when a key is present | A stray environment variable would silently trigger paid network calls without explicit intent. |
| Bake headline text into the AI image | Diffusion models render text unreliably and off-brand; vector overlays stay crisp and on-palette. |
| Declare a broad `Bash` scope for convenience | Unscoped Bash is an unnecessary attack surface; the skills only ever run `node`. |

## Consequences

**Positive:**

- The common path is free, fast, offline, and reproducible — safe to run in CI or scripts.
- Cost, latency, and network egress are confined to one clearly labeled, opt-in skill.
- Least-privilege tools and a mandatory review pass keep output on-brand and auditable.

**Negative / accepted tradeoffs:**

- Photographic output requires two setup steps (opt-in flag plus a key), which is friction the double gate deliberately accepts to prevent accidental spend.
- Adding a new asset kind means extending a Node generator, not just editing docs — accepted so output stays deterministic rather than prompt-dependent.

## Tool-permission scope

Every skill declares `Read, Write, Glob, Bash(node:*)` and nothing more. Least
privilege: the Bash scope is pinned to `node` rather than a bare `Bash`, so the skills
can run the shipped generators but nothing else.

| Tool | Why it's needed |
| --- | --- |
| Read | Load the active brand profile (`color-system.json`, `typography.json`, `visual-identity.md`) and inspect generated files before review. |
| Write | Save generated SVG (and, for raster, PNG and overlay) files under `output/`. |
| Glob | Locate the active brand directory and enumerate profile or output files. |
| Bash(node:*) | Run the shipped generators (`node lib/logo.mjs`, `lib/social.mjs`, `lib/doctpl.mjs`, `lib/raster.mjs`, `lib/genimage.mjs`, `lib/composite.mjs`). Scoped to `node` so no other command is permitted. |
