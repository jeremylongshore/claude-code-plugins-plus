---
name: portaljs-new-portal
description: Scaffold a new PortalJS data portal from a brief. Copies the canonical template from examples/portaljs-catalog and substitutes project tokens. Use when starting a brand-new data portal project from scratch.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(cp:*), Bash(mkdir:*), Bash(git:*)
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - scaffold
  - nextjs
  - template
  - catalog
---

# PortalJS — New Portal

## Overview

Scaffold a production-ready PortalJS data portal from a brief. The skill is
**interactive**: if the brief is thin it interviews the user in three short rounds
(mapped to the template's three surfaces — Home, Catalog, Showcase), echoes a brief
back for confirmation, then copies `examples/portaljs-catalog` (locally or via a
remote `tiged` fetch), substitutes placeholder tokens, sets the namespace mode, seeds
any datasets named in the interview, installs dependencies, and verifies the scaffold
with a type check.

## Prerequisites

- Node.js >=22 and npm available on `PATH`.
- Network access, unless a current local checkout of the portaljs repo is available
  (the resolver defaults to a remote fetch of the template).
- A destination directory name that does not already contain files (or user consent
  to overwrite one that does).

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-new-portal.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-new-portal.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Interview the user in up to three rounds — Home/basics, Catalog & discovery
   (datasets, namespace mode `theme` vs `owner`), Showcase/views — skipping any round
   already answered by the input brief. Accept "use defaults" at any point.
2. Confirm a short brief (name, slug, description, namespace, datasets, views) before
   building.
3. Resolve the template source: prefer a remote `tiged` fetch of
   `examples/portaljs-catalog` at `main` (or `PORTALJS_TEMPLATE_REF`); use a local
   checkout only when it is current (has `pages/[owner]/[slug].tsx`) and the
   destination is outside that repo.
4. Materialize the template into `./PROJECT_SLUG`, asking first if the destination
   already exists and is non-empty.
5. Substitute `__PROJECT_NAME__`, `__PROJECT_SLUG__`, `__DESCRIPTION__` tokens
   across all files with `perl -pi`, escaping `/`, `\`, and `&` in the values.
6. Set `NAMESPACE_TYPE` (`'theme'` or `'owner'`) in `lib/datasets.ts` per the
   interview.
7. Seed datasets captured in Round 2 (via `/portaljs-add-dataset` or by hand), or
   clear `datasets.json` to `[]` if none were named.
8. Run `npm install` inside the scaffolded portal.
9. Verify with `npx tsc --noEmit` (never `next build` here — it would corrupt a
   running dev server's `.next/` directory).
10. Report the scaffolded routes, namespace mode, and next steps.

## Output

- **Created:** a new directory `./PROJECT_SLUG/` containing the full
  `examples/portaljs-catalog` template with tokens substituted.
- **Modified:** `lib/datasets.ts` (`NAMESPACE_TYPE`); `datasets.json` (seeded
  datasets or cleared to `[]`).
- **Verified:** `npx tsc --noEmit` passes inside the scaffolded portal.
- **Result:** a runnable portal at `./PROJECT_SLUG` with Home (`/`), Catalog
  (`/search`), and Showcase (`/@<namespace>/<slug>`) surfaces wired up.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| `DIR_EXISTS` | `./PROJECT_SLUG` already exists and is non-empty | Ask the user for a different name or consent to remove it; then proceed. |
| Remote fetch fails | Bad `PORTALJS_TEMPLATE_REF`, network outage, or `tiged` unavailable | Tell the user plainly and ask to retry, use a different ref, or check network. |
| Stale local scaffold (`pages/datasets/[slug].tsx`) | Old local clone missing `pages/[owner]/[slug].tsx` | Resolver already falls back to remote in this case — do not force local mode. |
| `npm install` fails | Node <22 or no network | Report the error and ask the user to check Node version and connectivity. |
| `tsc --noEmit` fails | Token substitution or manifest error | Print the log and fix before reporting success — never report success with a failing type check. |

## Examples

### Example 1 — Full brief up front

```
/portaljs-new-portal Auckland Open Data Portal — datasets published by several council
departments (multiple publishers). Start with ./data/parks.csv and ./data/budget.csv.
```
Infers name + description, picks `NAMESPACE_TYPE = 'owner'`, asks for namespace
values (e.g. `parks-dept`, `finance`), confirms the brief, scaffolds the template, and
seeds both datasets at `/@parks-dept/parks` and `/@finance/budget`.

### Example 2 — No arguments, full interview

```
/portaljs-new-portal
```
Runs all three interview rounds from scratch, accepting "use defaults" for any round,
then confirms the brief before scaffolding.

### Example 3 — Single-publisher portal with no datasets yet

```
/portaljs-new-portal Reference Data Hub — a single-team reference catalog, no data yet.
```
Picks `NAMESPACE_TYPE = 'theme'` with namespace `reference`, clears `datasets.json` to
`[]`, and reports `/portaljs-add-dataset` as the next step.

## Resources

- Full workflow: [`.claude/commands/portaljs-new-portal.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-new-portal.md)
- Template and token reference: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-add-dataset`, `portaljs-add-chart`, `portaljs-add-map`, `portaljs-connect-ckan`
- PortalJS documentation: <https://portaljs.org>
