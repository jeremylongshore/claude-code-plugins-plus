---
name: portaljs-connect-ckan
description: Wire a scaffolded PortalJS portal to a CKAN backend over its API. Generates a tiny server-side fetch client (no runtime dependency) and feeds the /search catalog and /@namespace/slug showcases from CKAN instead of datasets.json. Use when connecting an existing portal to a live CKAN instance instead of a static manifest.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), WebFetch
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - ckan
  - backend
  - api
  - catalog
---

# PortalJS — Connect CKAN

## Overview

Connect an existing `portaljs-catalog` portal to a live CKAN backend for the "decoupled /
any backend" path. The portal stops reading the static `datasets.json` manifest (and files
in `/public/data/`) and instead feeds its two data surfaces — the **`/search` catalog** and
the **`/@namespace/slug` showcases** — straight from a CKAN instance's REST API
(`package_search` / `package_show`) through a generated fetch client. Output is plain,
editable Next.js code with **no runtime dependency** — never `@portaljs/ckan`, whose bundle
wires React UI components to React 18 internals and crashes at import under the template's
React 19. Pages fetch CKAN server-side in `getStaticProps`/`getStaticPaths`, so the catalog
is pre-rendered at build time and the site can still be statically deployed. Run this right
after `portaljs-new-portal` to swap a freshly scaffolded portal's sample data over to CKAN.

## Prerequisites

- A scaffolded PortalJS portal (see `portaljs-new-portal`) with `package.json`, `pages/`,
  `datasets.json`, `pages/search.tsx`, and `pages/[owner]/[slug].tsx` present.
- A CKAN base URL that is publicly reachable, e.g. `https://demo.dev.datopian.com`.
- Node 18+ and npm available in the portal directory (no new packages are installed).

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-connect-ckan.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-connect-ckan.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Gather input from `$ARGUMENTS` — CKAN base URL (required), org filter (optional), group
   filter (optional), portal directory (default `.`). If the URL is missing, interview the
   user; never dead-end with a missing-input error.
2. Validate the target directory is a `portaljs-catalog` portal; if not, suggest
   `portaljs-new-portal` instead of failing silently.
3. Verify the CKAN backend is reachable via `package_search?rows=1`, and validate each org
   filter via `organization_show`; on failure, explain and re-prompt rather than dead-ending.
4. Generate `lib/ckan.ts` — a self-contained server-side fetch client wrapping
   `package_search` and `package_show`, with `DMS`, `ORG_FILTER`, `GROUP_FILTER`, and
   `MAX_DATASETS` as editable constants.
5. Rewire `pages/search.tsx` to list datasets from `package_search`, linking each to
   `/@namespace/slug` via `datasetHref`; leave `pages/index.tsx` untouched.
6. Overwrite `pages/[owner]/[slug].tsx` to pre-render one page per dataset via
   `getStaticPaths` and fetch details with `package_show`, previewing tabular resources
   through the existing `Table` component.
7. Verify the build with `npx next build`; fix any error before reporting success.
8. Report what changed: client, catalog, showcase, filters, and static page count.

## Output

- **Created:** `lib/ckan.ts` (fetch wrapper client — no dependency added to `package.json`).
- **Modified:** `pages/search.tsx` (catalog reads `package_search`); `pages/[owner]/[slug].tsx`
  (showcase reads `package_show`, overwritten to drop the `datasets.json` source).
- **Unchanged:** `pages/index.tsx` (still the static search-first landing page).
- **Verified:** `npx next build` succeeds and prints the static page count.
- **Result:** `/search` and `/@namespace/slug` are served from the CKAN backend; the
  `DMS` env var can override the base URL at deploy time without editing code.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| Missing CKAN URL | User invoked the skill with no `$ARGUMENTS` | Ask for the base URL (and optional org/group filter); never error out. |
| `package_search` request fails or times out | URL isn't a reachable CKAN root | Tell the user, ask them to confirm the URL, and retry. |
| Org filter not found | `organization_show` returns `success: false` | List valid orgs from `organization_list` and ask which one was meant. |
| Catalog renders empty after connecting | Wrong org/group filter name in `lib/ckan.ts` | Clear or correct the filter constants and rebuild. |
| `next build` fails | Typo in substituted `CKAN_URL` or bad TypeScript edit | Print the log, fix the first error, and re-run before reporting success. |
| `<Table>` fails to load a resource | CKAN resource host blocks CORS | Note that the Download link still works; prefer datastore-backed resources. |

## Examples

### Example 1 — Public CKAN demo, no filters

```
/portaljs-connect-ckan url=https://demo.dev.datopian.com
```

### Example 2 — Restrict the catalog to one organization

```
/portaljs-connect-ckan url=https://demo.dev.datopian.com org=my-org
```

### Example 3 — Filter by group and target a specific portal directory

```
/portaljs-connect-ckan url=https://data.example.gov group=education dir=./my-portal
```

## Resources

- Full workflow: [`.claude/commands/portaljs-connect-ckan.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-connect-ckan.md)
- Client, filters, and troubleshooting reference: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-new-portal`, `portaljs-add-dataset`, `portaljs-deploy`
- CKAN Action API documentation: <https://docs.ckan.org/en/latest/api/>
