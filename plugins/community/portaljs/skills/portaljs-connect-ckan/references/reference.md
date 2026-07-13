# Connect CKAN — Reference

Detailed reference for the `portaljs-connect-ckan` skill. The executable workflow lives in
[`.claude/commands/portaljs-connect-ckan.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-connect-ckan.md).

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DMS` | No | Overrides the CKAN base URL baked into `lib/ckan.ts` at deploy time, without editing code. Falls back to the URL provided when the skill ran. |

## CKAN API endpoints used

`lib/ckan.ts` wraps two CKAN Action API endpoints via a single `ckanAction` helper, called
as `GET <DMS>/api/3/action/<action>?<params>`:

| Action | Used by | Purpose |
| --- | --- | --- |
| `package_search` | `pages/search.tsx`, `getStaticPaths` in `pages/[owner]/[slug].tsx` | List datasets for the catalog and enumerate build-time pages. Supports `start`, `rows`, and an `fq` filter query built from org/group/tag lists. |
| `package_show` | `getStaticProps` in `pages/[owner]/[slug].tsx` | Fetch full metadata and resources for one dataset by its CKAN `name`. |
| `organization_show` | Setup verification (step 3) | Validate an org filter exists before writing it into `lib/ckan.ts`. |
| `organization_list` | Setup verification (step 3) | List valid orgs when a supplied filter doesn't match, so the user can pick correctly. |

Extend the client the same way for more actions — `organization_list`, `group_list`,
`tag_list`, `datastore_search?resource_id=…` — each is one more `ckanAction('<name>', {…})`
call plus a typed return shape.

## Filters and build scaling

- `ORG_FILTER` / `GROUP_FILTER` are plain string arrays in `lib/ckan.ts`; empty means no
  filter. They feed into the Solr `fq` clause CKAN's `package_search` accepts, OR-ed within
  each field.
- `MAX_DATASETS` caps both the catalog page size and the number of static pages generated
  by `getStaticPaths`. Every dataset becomes one `package_show` request and one prerendered
  page, so raising the cap on a large instance increases build time proportionally.
- Namespaces map to CKAN organizations: a dataset's `@<namespace>` segment is its
  `organization.name`, falling back to `@dataset` when the package has no organization.

## Troubleshooting

- **Empty catalog after connecting** — the org/group filter name doesn't match any dataset
  on the instance. Clear the filter in `lib/ckan.ts` or re-run `organization_list` /
  `group_list` to find the correct name.
- **Build fails or times out** — confirm `CKAN_URL` was substituted correctly (no trailing
  slash duplication) and that the instance is reachable from the build environment, not just
  from a browser.
- **Resource preview fails but Download link works** — the resource host blocks
  cross-origin requests; `<Table>` fetches client-side. Prefer datastore-backed resources,
  which CKAN serves through its own API and are CORS-friendly.
- **Need live (non-static) data** — switch to `getServerSideProps` or set `fallback:
  'blocking'` in `getStaticPaths`, and deploy to a Node host instead of a static export.
