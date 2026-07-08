# Data providers

The **data-provider contract** is the seam that keeps a PortalJS portal decoupled
from where its data lives. The three surfaces — the home page, the `/search`
catalog, and the `/@<namespace>/<slug>` showcase — read datasets **only** through a
`DataProvider`. Swap the provider and the source of data changes without touching a
single page.

```
   the three surfaces
   Home /      Catalog /search      Showcase /@<ns>/<slug>
      |              |                      |
      +--------------+----------------------+
                     |  import { provider }
              +------v-------+
              | DataProvider |   <- the contract (types.ts)
              +------+-------+
       +----------+--+-----------+--------------+
       |          |              |              |
  StaticProvider CKAN      OpenMetadata    git-LFS + R2    ...future
  (datasets.json)(api)        (api)        (object store)
```

## The contract

```ts
interface DataProvider {
  readonly name: string
  readonly capabilities: ProviderCapabilities   // search · query · write · rbac
  listDatasets(): Promise<Dataset[]>
  getDataset(namespace: string, slug: string): Promise<Dataset | null>
  search(query: DatasetQuery): Promise<Dataset[]>
}
```

See [`types.ts`](./types.ts) for the full definitions and
[`static-provider.ts`](./static-provider.ts) for the default implementation.

## Capabilities map onto the storage + compute spectrum

A provider declares what it can do; surfaces and skills branch on the flags rather
than sniffing the provider type. (See `ROADMAP.md` for the spectrum.)

| Flag | Off (static default) | On |
|------|----------------------|----|
| `search` | catalog filters client-side over `listDatasets()` | provider does server-side / faceted search |
| `query` | flat-file preview only | structured queries (DuckDB / a datastore) |
| `write` | datasets added via git (a PR) | create/update at runtime (e.g. CKAN API) |
| `rbac` | fully public | backend owns access control (needs the runtime mode) |

`search` / `write` / `rbac` being on generally implies the **opt-in runtime mode**
(SSR / API routes) rather than a purely static build — private data and live writes
can't live in a public static bundle.

## Adding a provider

1. Create `lib/providers/<name>-provider.ts` implementing `DataProvider`.
2. Set its `capabilities` honestly — surfaces rely on them.
3. Select it in [`index.ts`](./index.ts)'s `getProvider()`, usually behind an env var.

### Backends on the roadmap

- **CKAN** — `listDatasets`/`getDataset` map to `package_list`/`package_show`,
  `search` to `package_search` (`capabilities.search = true`). Adds `rbac` and, via
  the datastore, `query`. Wired by the `/portaljs-connect-ckan` skill.
- **OpenMetadata** — its REST API for catalog + governance metadata; owns its own
  `rbac`.
- **git-LFS + object store (R2)** — same model as `StaticProvider` (datasets.json +
  Frictionless metadata in git) but the bytes live in object storage via Git LFS
  (e.g. [giftless](https://github.com/datopian/giftless) → R2). The on-ramp to a
  Parquet-on-R2 + DuckLake + DuckDB lakehouse, where `query` turns on.

Keep object storage **S3-compatible** so R2 is the default but never a hard lock-in.
