---
metatitle: /portaljs-connect-ckan – Wire a PortalJS Portal to a CKAN Backend over its API
metadescription: The /portaljs-connect-ckan skill generates a tiny server-side fetch client (no runtime dependency), feeds the catalog at /search and dataset showcases at /@<namespace>/<slug> from CKAN as plain editable code, and verifies the build — the decoupled, any-backend path.
title: /portaljs-connect-ckan
description: Wire a portal to a CKAN backend over its API instead of static files — the decoupled, any-backend path.
---

`/portaljs-connect-ckan` connects an existing PortalJS portal to a live [CKAN](/ckan)
backend. The portal stops reading the static `datasets.json` manifest and
`/public/data/` files, and instead feeds both surfaces — the catalog at `/search`
and the dataset showcases at `/@<namespace>/<slug>` — straight from a CKAN
instance's REST API (`package_search` / `package_show`) through a tiny generated
`fetch` client. The output is plain, editable Next.js code with **no runtime
dependency** — no opaque framework wiring.

## When to use it

Use it for the **decoupled / any-backend** path: you have a CKAN data management
system (your own or a public one) and want a browseable portal in front of it.
CKAN calls run **server-side** in `getStaticProps` / `getStaticPaths`, so the
catalog is pre-rendered at build time and the site can still be statically deployed.

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| CKAN base URL | Yes | The root of the instance, e.g. `https://demo.dev.datopian.com`. Must be publicly reachable. |
| Org filter | No | One or more CKAN organization names to restrict the catalog to. |
| Group filter | No | One or more CKAN group names to restrict the catalog to. |
| Portal directory | No | Path to the portal project. Defaults to the current directory. |

The skill verifies the CKAN API is reachable (and that any named orgs exist)
before generating code.

## Example

```
/portaljs-connect-ckan https://demo.dev.datopian.com
```

Restricted to specific organizations:

```
/portaljs-connect-ckan https://demo.dev.datopian.com --org transport,environment
```

## What it produces

- `lib/ckan.ts` — a small, editable `fetch`-based client (no package added to
  `package.json`, no `tsconfig` changes). The CKAN URL is the default, overridable at
  deploy time via the `DMS` env var; org/group filters and a build-time page cap
  (`MAX_DATASETS`) are plain constants you can edit.
- `pages/search.tsx` rewritten so the catalog lists datasets from `package_search`.
- `pages/[owner]/[slug].tsx` — the showcase route, repointed to pre-render one
  showcase per dataset at `/@<namespace>/<slug>` via `package_show`, previewing
  CSV/TSV resources through the template's `Table`.

It verifies the build before reporting success. When it finishes:

```
✓ Connected to CKAN: https://demo.dev.datopian.com
  - Client:    lib/ckan.ts (DMS overridable via env var)
  - Catalog:   pages/search.tsx → lists datasets from package_search
  - Showcase:  pages/[owner]/[slug].tsx → package_show at /@<namespace>/<slug>, CSV/TSV preview via <Table>
```

> The default is static generation (data fixed at build time — rebuild to pick up
> new CKAN datasets). For always-live data, deploy to a Node host and switch to
> `getServerSideProps` or `getStaticPaths` `fallback: 'blocking'`.

## Where to go next

- **[Core concepts](/docs/core-concepts)** — why the frontend is decoupled from the
  backend.
- **[`/portaljs-deploy`](/docs/skills/portaljs-deploy)** — publish the connected portal.

<DocsPagination prev="/docs/skills/portaljs-add-map" next="/docs/skills/portaljs-migrate" />
