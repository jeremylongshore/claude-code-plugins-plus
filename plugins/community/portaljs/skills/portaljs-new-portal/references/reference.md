# New Portal — Reference

Detailed reference for the `portaljs-new-portal` skill. The executable workflow lives in
[`.claude/commands/portaljs-new-portal.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-new-portal.md).

## Placeholder tokens

Every file under the copied template carries these tokens; the skill substitutes them
with `perl -pi` across `*.tsx, *.ts, *.json, *.js, *.css, *.md, .lfsconfig`:

| Token | Replaced with | Where it shows up |
| --- | --- | --- |
| `__PROJECT_NAME__` | The portal's display name | Navbar brand text, page titles, hero copy |
| `__PROJECT_SLUG__` | Lowercase, hyphenated slug of the name | Destination directory, `.lfsconfig` Git LFS endpoint URL |
| `__DESCRIPTION__` | One-line description | Hero subtitle, `<meta>` description |

Values are escaped for `/`, `\`, and `&` before substitution so URLs or ampersands in
the description don't break the `perl` replacement.

## Three surfaces (what gets scaffolded)

| Surface | Route | File | Notes |
| --- | --- | --- | --- |
| Home | `/` | `pages/index.tsx` | Hero + search box + suggested-query chips |
| Catalog | `/search` | `pages/search.tsx` | Client-side full-text filter over `datasets.json` |
| Showcase | `/@<namespace>/<slug>` | `pages/[owner]/[slug].tsx` | Metadata, `Table` preview, Download & API, Views slot |

`lib/datasets.ts` exposes `getDatasets()`, `getDataset(slug)`,
`getDatasetByNamespace(ns, slug)`, `datasetHref(d)`, and the `NAMESPACE_TYPE` constant
(`'theme'` — single publisher, grouped by subject — or `'owner'` — multiple
publishers, grouped by who published).

## Template source resolution

The skill defaults to a **remote** fetch (`npx tiged "datopian/portaljs/examples/portaljs-catalog#main"`)
so every scaffold gets the latest template. It only uses a **local** checkout when both
hold: the resolved git root has the current template (verified by the presence of
`pages/[owner]/[slug].tsx`), and the destination is outside that repo. Plain `degit` is
avoided — its silent full-clone fallback on tarball failure would drop the whole
monorepo into the target; `tiged` extracts the subdirectory correctly.

## Troubleshooting

- **Scaffolded portal has `pages/datasets/[slug].tsx` instead of `pages/[owner]/[slug].tsx`**
  — an old local template was used. Force remote mode by scaffolding from outside any
  portaljs clone, or set `PORTALJS_TEMPLATE_REF` explicitly.
- **`npm install` hangs or fails** — check Node.js is >=22; the template's dependencies
  target the current Next.js 14 / React 18 baseline.
- **`.next/` corruption / 404s after scaffolding** — never run `next build` right after
  scaffolding while `npm run dev` is active; verify with `npx tsc --noEmit` instead.
- **Portal still shows the PortalJS logo in production** — branding is a placeholder;
  swap `public/icon.svg`, `public/favicon.ico`, `public/apple-touch-icon.png`, and
  `public/icon-512.png` for the client's own marks.
