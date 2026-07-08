# Data query (the compute seam)

Where the [data-provider contract](../providers) answers *which datasets exist*,
the **data-query contract** answers *how to compute over a dataset's data* —
running SQL over it, beyond a flat-file preview.

```ts
interface DataQuery {
  readonly engine: string                 // e.g. 'duckdb-wasm'
  open(source: QuerySource): Promise<void> // expose the file as the table `data`
  query(sql: string): Promise<QueryResult> // run SQL, get rows + column order
  close(): Promise<void>                   // release engine resources
}
```

`DATA_QUERY = 'duckdb'` in `lib/datasets.ts` is the template default, so every
tabular dataset (and any Parquet resource) renders `components/DataExplorer.tsx`,
which drives the engine below. Downgrading to `DATA_QUERY = 'flat'` skips this —
the showcase just previews the CSV with papaparse. This is the **compute** slot on
the storage + compute spectrum (see `ROADMAP.md`).

## DuckDB-Wasm — two execution paths

`lib/query/duckdb.ts` runs DuckDB entirely in the browser (no server, no
datastore). `@duckdb/duckdb-wasm` and the wasm/worker bundles load on demand from
jsDelivr only when a query view actually mounts — preview-only (`'flat'`) portals
never pay for it, and the default portal defers the cost until a query view renders.
`open()` picks one of two paths by the source:

| | Range query | Buffered |
|---|---|---|
| **When** | remote Parquet URL (`https://…`, e.g. on R2) | local/bundled files, and all CSV/TSV |
| **How** | `registerFileURL` + a `VIEW` over `read_parquet(url)` | `fetch` whole file → `registerFileBuffer` → `TABLE` |
| **Bytes fetched** | Parquet footer + only the row groups / columns each query touches | the entire file, up front |
| **Ceiling** | bounded by the query, not the file — a phone can hit a multi-GB file | Wasm memory (~4 GB) holds the whole file |

The range path is the **no-download query tier** (epic po-g9y, phase 6).
Projection and predicate pushdown reach the file over HTTP range requests, so a
`SELECT a, b FROM data WHERE … LIMIT …` pulls a few MB out of an arbitrarily large
file. It requires the object store to serve range requests + CORS — configured
and verified on R2 in `giftless/r2-cors.json`. CSV can't be range-queried (no
columnar structure / footer); convert it first — see below.

## Publishing a dataset for the range tier

1. **Convert** CSV/TSV → Parquet at publish time:
   ```bash
   scripts/csv-to-parquet.sh data/orders.csv data/orders.parquet
   ```
   (columnar + compressed; tune `ROW_GROUP_SIZE` for finer-grained range reads).
2. **Version** the `.parquet` with Git LFS — already routed in `.gitattributes`,
   so its bytes stream to R2 via Giftless and only a pointer stays in git.
3. **Point** the dataset's `resource.path` at the **R2 URL** with
   `format: "parquet"`. The showcase queries it in place — no download.

## Device-tier / fallback guidance

DuckDB-Wasm runs on the **client**, so performance is device-bound: a single
thread unless the page is cross-origin isolated (COOP/COEP), the ~4 GB Wasm memory
wall, and mobile is slower. Design for graceful degradation, not browser-only:

- **Lean on the range path.** Pushdown means weak clients process only the bytes
  they need. Keep a `LIMIT` on exploratory queries and never `SELECT *` a huge
  table into a phone.
- **Pre-aggregate / partition at publish time.** Ship summary tables; paginate
  and cap result sets.
- **Route heavy work off-device.** The `DataQuery` interface is the seam: the same
  SQL can run in a different *location*. For data too big for the browser, or a
  known-weak audience, a future engine implementation can target an edge Worker
  (ducklings, Workers Paid) or MotherDuck — without touching the UI. That edge
  tier is a deliberately deferred follow-on; the browser path is the zero-infra
  default.
- **Heuristic** (used by `/portaljs-architect`): browser DuckDB by default for
  datasets up to ~low-hundreds-MB Parquet / simple aggregations; route to
  edge/MotherDuck above that.
