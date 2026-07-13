# Architect — Reference

Detailed reference for the `portaljs-architect` skill. The executable workflow lives in
[`.claude/commands/portaljs-architect.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-architect.md).

## The six slots (default in bold)

| Slot | Options |
| --- | --- |
| Storage | repo files · **Git-LFS + R2** · Parquet on R2 · CKAN datastore / warehouse |
| Catalog | `datasets.json` · git + Frictionless · **DuckLake** · backend-native |
| Compute | papaparse preview · **DuckDB** (Wasm → server) · warehouse engine |
| Access | **static (public)** · runtime + backend RBAC |
| Hosting | **Cloudflare Pages** (static) · Cloudflare Workers (runtime) · any static host |
| Metadata | **Frictionless** profile · extended · custom · multi-profile + DCAT |

Opinionated default stack: `git + giftless/R2 + Parquet + DuckLake + DuckDB`, static on
Cloudflare Pages, Frictionless metadata. Storage stays S3-compatible, so R2 is the
default but never a hard lock-in.

## The two build-time knobs

These are the slots made concrete — the values the build skills actually read.

- **Data tier** (`inline | LFS | external`) — where a dataset's bytes live; per-dataset,
  resolved by `/portaljs-add-dataset`. `inline` only for bundled sample data or a
  no-creds OSS self-host; `LFS` is the default for anything the user adds; `external`
  for data already at a URL or Parquet queried in place on R2.
- **Query mode** (`DATA_QUERY = flat | duckdb`, `lib/datasets.ts`) — portal-wide.
  `duckdb` is the template default (ships the SQL editor; a Parquet resource always
  renders the query view). Downgrade to `flat` only for a preview-only portal that
  never needs querying.

## Decision rules

- **Storage/Catalog/Compute** scale together with data volume: tiny + preview-only stays
  on repo files/`datasets.json`/papaparse; large-with-versioning moves to Git-LFS + R2 /
  git+Frictionless / DuckDB-Wasm; analytics-grade (aggregate/join/filter, or
  many/large datasets) moves to Parquet on R2 / DuckLake / DuckDB; an existing warehouse
  or SQL-native team keeps its backend.
- **Access/Hosting** is a single fork on public vs. private: any access-controlled data
  flips the whole portal to runtime + backend RBAC on Cloudflare Workers (the larger,
  opt-in build), otherwise static on Cloudflare Pages.
- **Metadata** stays Frictionless unless harvesting or standards compliance is named,
  in which case add DCAT (DCAT-AP / national / domain profile as applicable).
- **Namespace mode** (for `/portaljs-new-portal`): single publisher → `theme`;
  multiple publishers → `owner`.
- When genuinely unsure, recommend the opinionated default rather than presenting a
  blank page — every slot has one.

## Troubleshooting

- **Brief feels off after confirmation** — corrections are welcome before "go"; the
  brief is not persisted to `ARCHITECTURE.md` until confirmed.
- **`DATA_QUERY` didn't change in the scaffolded portal** — the flat downgrade is a
  manual edit to `lib/datasets.ts` (the `perl -pi -e` one-liner in the command file),
  applied only when downgrading from the `duckdb` default.
- **A hand-off skill is marked *(planned)*** (e.g. `/connect-openmetadata`) — it isn't
  built yet; the brief still names it as the intended path and flags it as
  designed-in/built-later.
- **Mixed data tiers within one portal** — expected; name the default tier (almost
  always LFS) and flag only the datasets that deviate (e.g. a remote URL kept external).
