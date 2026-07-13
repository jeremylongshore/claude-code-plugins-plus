# Add Dataset — Reference

Detailed reference for the `portaljs-add-dataset` skill. The executable workflow lives in
[`.claude/commands/portaljs-add-dataset.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-dataset.md).

## `datasets.json` entry fields

Each entry matches the `Dataset` shape from `lib/providers/types.ts`:

| Field | Required | Purpose |
| --- | --- | --- |
| `slug` | yes | URL-safe identifier; unique per `namespace`. |
| `namespace` | yes | Subject (theme portals) or publisher (owner portals) grouping. |
| `name` | yes | Human-readable title shown in the catalog and showcase. |
| `description` | no | One-line summary; omit if genuinely absent. |
| `file` | yes | `MANIFEST_PATH` — a bare filename (inline) or an absolute URL (passthrough/R2). |
| `format` | yes | One of `csv \| tsv \| json \| geojson`, lowercase. |

`resourceUrl()` in `lib/datasets.ts` is the one place that resolves `file`: a repo-relative
name resolves under `/data/<file>`, an absolute URL passes straight through. Never branch on
source at the call site — only at registration time (Step 4 of the workflow).

## Data routing — local vs R2 vs URL

| Source | Default | Bytes go to | Manifest `file` |
| --- | --- | --- | --- |
| Local file | R2 via Git LFS | `data/<slug>.<ext>` (LFS pointer) → Giftless → R2 | absolute R2 URL |
| Local file (fenced) | inline | `public/data/<slug>.<ext>` | bare filename |
| Remote URL | passthrough | left where it is, never copied | the URL, unchanged |
| Remote URL (opt-in) | adopt into R2 | downloaded, then routed as a local file | absolute R2 URL |

The inline route is a **fenced exception** (bundled sample data, or an OSS self-host with no
R2 credentials) — it is not a size threshold. Remote URLs default to passthrough because
copying third-party data creates duplication and staleness; adopting one into R2 is an
explicit opt-in, useful when the portal needs in-browser range/DuckDB queries that the
original host's CORS/range support can't serve.

## Git LFS → R2 mechanics

- `git lfs install --local` must run once per repo before `git lfs track`, otherwise `git add`
  commits raw bytes instead of a ~134 B pointer.
- `git lfs track "data/<slug>.<ext>"` is per-file (a path entry in `.gitattributes`), not an
  extension glob — LFS routing is format-agnostic.
- The Arc API mints a short-TTL, write-scoped LFS token; set it as `git config lfs.url` (local
  only, never committed). Use the `_jwt` Basic-auth piggyback — a global `http.extraHeader`
  gets replayed onto the presigned R2 PUT and fails with `400`.
- A GitHub remote is optional. `lfs.url` alone determines where bytes stream; a local-only
  scaffold pushes LFS objects through a throwaway local remote (`git remote add r2-lfs .`).
- `git lfs prune` reclaims local disk after the push — without it, the working tree and
  `.git/lfs` cache each hold a copy.

## Troubleshooting

- **`datasets.json` missing** — the portal predates the catalog template; confirm with the
  user before proceeding rather than assuming the file should be created from scratch.
- **Build fails after appending an entry** — almost always a trailing comma or unescaped
  quote in the JSON; re-open the file and validate it parses before re-running the build.
- **Dataset doesn't appear at `/@namespace/slug`** — check `(namespace, slug)` matches
  exactly what was appended; `getStaticPaths` reads the pair verbatim from `datasets.json`.
- **CORS/range errors when querying a passthrough URL** — the remote host doesn't support
  range requests; re-run with the adopt option to host the file in R2 instead.
