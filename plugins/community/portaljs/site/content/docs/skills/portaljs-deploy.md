---
metatitle: /portaljs-deploy – Publish a PortalJS Portal to PortalJS Arc
metadescription: The /portaljs-deploy skill builds a static export of your portal and publishes it to PortalJS Arc — Datopian-managed hosting on Cloudflare — returning a live <slug>.arc.portaljs.com URL. One command, one target.
title: /portaljs-deploy
description: Build a static export and publish it to PortalJS Arc — a live <slug>.arc.portaljs.com URL in one command.
---

`/portaljs-deploy` takes a PortalJS portal live on [**PortalJS Arc**](/docs/arc) — Datopian's
managed static hosting on Cloudflare. It builds a static export, uploads it, and prints a
live `https://<slug>.arc.portaljs.com` URL. Re-running redeploys the same portal in place.

It is a **single-target** skill: it publishes to PortalJS Arc only. If you'd rather host
the portal yourself, the build output in `out/` is a plain static site you can upload to any
host (Vercel, your own Cloudflare, Netlify, S3, …) — you don't need this skill for that.

## When to use it

Run it once the portal looks right locally — the last step after
[`/portaljs-new-portal`](/docs/skills/portaljs-new-portal), [`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset) /
[`/portaljs-migrate`](/docs/skills/portaljs-migrate), and any enrichment skills.

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| Portal directory | No | Path to the portal project. Defaults to the current directory; must be a Next.js portal. |
| Slug | No | The subdomain to publish under (`<slug>.arc.portaljs.com`). Defaults to the project name; override with `--slug <name>`. |
| Arc token | No | A PortalJS Arc token, read from `PORTALJS_TOKEN` or `~/.portaljs/credentials`. If neither is set, `/portaljs-deploy` signs you in on demand — one browser click, no separate step. |

## Example

```
/portaljs-deploy
```

Publish under a specific slug:

```
/portaljs-deploy --slug auckland-open-data
```

## What it produces

The skill ensures a static export (`output: 'export'`), builds and verifies it (never
reporting success on a failing build), uploads `out/` to Arc, and reports:

```
✓ Deployed to PortalJS Arc
  - URL:   https://auckland-open-data.arc.portaljs.com
  - Files: 44   (820 KB uploaded)
  - Slug:  auckland-open-data  (re-run /portaljs-deploy to update)
```

## Auth

Auth happens on demand — there's no separate login step. The first time you `/portaljs-deploy` on a
machine with no token, it runs a device-authorization flow (the `gh auth login` /
`wrangler login` model): it opens your browser, you sign in with GitHub and click **Authorize**
once, and the token is saved to `~/.portaljs/credentials` (mode 0600). Later deploys reuse it
silently; if a token is revoked or expires, the next `/portaljs-deploy` re-authenticates automatically.

For CI or non-interactive use, skip the browser flow by setting `PORTALJS_TOKEN` (mint a token
in the dashboard at [arc.portaljs.com](https://arc.portaljs.com)) — it takes precedence over
the credentials file:

```bash
export PORTALJS_TOKEN=<token>
# …or save it for re-use:
mkdir -p ~/.portaljs && printf '{"token":"<token>"}\n' > ~/.portaljs/credentials
```

The token is never committed to your repo.

## Notes

- **Static only (for now).** Arc serves static exports — the catalog template,
  `/portaljs-add-dataset`, `/portaljs-migrate`, and `/portaljs-connect-ckan` (SSG) all export cleanly. A portal that
  relies on `getServerSideProps` (SSR) isn't hosted on Arc yet; self-host it instead.
- **Idempotent.** The slug is your portal's permanent address; re-deploying replaces the
  site in place.

## Where to go next

- **[PortalJS Arc](/docs/arc)** — what the managed hosting is and how it works.
- **[`/portaljs-connect-ckan`](/docs/skills/portaljs-connect-ckan)** — point the portal at a live backend
  before deploying.

<DocsPagination prev="/docs/skills/portaljs-check-data-quality" />
