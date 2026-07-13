---
name: portaljs-deploy
description: Deploy a PortalJS portal to PortalJS Arc — Datopian-managed static hosting on Cloudflare. Builds a static export, uploads it, and returns a live SLUG.arc.portaljs.com URL. One command, one target. Use when a portal is ready to publish or redeploy to a live URL.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(curl:*)
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - deploy
  - hosting
  - cloudflare
  - static
---

# PortalJS — Deploy

## Overview

Publish an existing PortalJS portal to **PortalJS Arc** — Datopian's managed static
hosting on Cloudflare. Build a static export, upload it to the Arc API, and print a live
`https://SLUG.arc.portaljs.com` URL. Re-running redeploys the same portal (idempotent on
the slug). This is a single-target skill — it deploys to Arc only. For self-hosting, run
`npm run build` and upload `out/` to any static host; no skill required for that path.
Arc serves static exports only — SSR is not hosted on Arc yet.

## Prerequisites

- A PortalJS portal directory with a `package.json` that lists `next` as a dependency.
- Node 18+ and npm on PATH (the Arc device-login flow uses Node's global `fetch`).
- `curl` and `tar` available for packaging and upload.
- A PortalJS Arc token — read from `PORTALJS_TOKEN`, or `~/.portaljs/credentials`
  (`{"token":"…"}`). If neither exists, the skill signs in on demand via a device-code
  flow; no manual token copying required.
- If the portal stores large data in Git LFS/R2, do not run `git lfs pull` before
  deploying — large datasets are served from Cloudflare R2 via absolute URLs in
  `datasets.json`, not copied into the export.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-deploy.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-deploy.md) — the
single source of truth. Read and follow it when executing. Summary:

1. Gather input — portal directory (default `.`) and slug (default from `package.json`
   name or directory name, slugified). Confirm the directory is a Next.js project; reject
   reserved slugs (`www`, `api`, `admin`, `staging`, `arc`).
2. Resolve the Arc token: read `PORTALJS_TOKEN`, else `~/.portaljs/credentials`; if
   missing, run the device-authorization sign-in flow and save the returned token.
3. Ensure `next.config.js` sets `output: 'export'` and `images: { unoptimized: true }`,
   then run `npm run build`; stop if the build fails.
4. Verify the export carries no dataset bytes — run `npm run check-export` (or
   `scripts/check-export.mjs`) to catch Git LFS pointer leaks and oversized data files.
5. Tar the `out/` directory and `POST` it to `$PORTALJS_ARC_API/v1/deploy?slug=<slug>`
   with the bearer token; handle 200/401/409/400/413 responses distinctly.
6. Report the live URL, file count, upload size, and R2-vs-inline dataset counts.

## Output

- **Modified (if needed):** `next.config.js` — adds `output: 'export'` and
  `images: { unoptimized: true }` when absent, preserving the rest of the config.
- **Created (on first sign-in):** `~/.portaljs/credentials` (mode `0600`).
- **Verified:** `npm run build` exits 0, `out/index.html` exists, the export-hygiene
  check passes.
- **Result:** the portal is live at `https://SLUG.arc.portaljs.com`; re-running updates
  the same slug in place.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| `NOT_A_PORTAL` error | No `next` dependency found in `PORTAL_DIR/package.json` | Run from a valid portal directory, or pass the correct path. |
| Slug rejected | Derived slug is reserved (`www`, `api`, …) or not a valid DNS label | Pass an explicit `--slug <name>`. |
| Build fails (non-zero exit) | App/config error surfaced in `npm run build` | Print the log, fix the error, never deploy a failing build. |
| `check-export` fails | Git LFS pointer leaked into `out/`, or a data file exceeds the size budget | Reference large data by absolute R2 URL via `portaljs-add-dataset`; don't `git lfs pull` before building. |
| `401` on upload | Token invalid, expired, or revoked | Re-run the device sign-in flow once, retry the upload; stop if it 401s again. |
| `409` on upload | Slug already taken by another account | Choose a different `--slug`. |
| `400` / `413` on upload | Malformed slug or export too large | Read the JSON `error` field and address the specific cause. |

## Examples

### Example 1 — Deploy the current directory with the default slug

```
/portaljs-deploy
```

### Example 2 — Deploy with an explicit slug

```
/portaljs-deploy --slug my-open-data
```

### Example 3 — Non-interactive deploy from CI with a token env var

```bash
export PORTALJS_TOKEN=arc_live_xxxxxxxx
/portaljs-deploy ./portals/city-budget --slug city-budget
```

## Resources

- Full workflow: [`.claude/commands/portaljs-deploy.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-deploy.md)
- Deploy internals reference: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-new-portal`, `portaljs-add-dataset`, `portaljs-connect-ckan`
- PortalJS Arc dashboard (sign in, manage tokens): <https://arc.portaljs.com>
