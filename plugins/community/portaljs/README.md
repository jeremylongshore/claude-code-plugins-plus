<p align="center">
  <img src="assets/portaljs-logo-spin.svg" alt="PortalJS" width="96" height="96" />
  <h1 align="center">PortalJS</h1>
  <p align="center">
    <b>The AI-native framework for building data portals.</b>
    <br />
    Describe the portal you want — your agent helps you choose an architecture, scaffolds it, and loads your data.
    <br />
    <br />
    <a href="https://www.portaljs.com/docs">Docs</a>
    ·
    <a href="https://github.com/datopian/portaljs/discussions">Discussions</a>
    ·
    <a href="https://github.com/datopian/portaljs/issues/new">Report a bug</a>
    <br />
    <br />
    <a href="https://www.npmjs.com/package/create-portaljs"><img src="https://img.shields.io/npm/v/create-portaljs?logo=npm&logoColor=white&label=create-portaljs&color=cb3837" alt="npm version" /></a>
    <a href="https://github.com/datopian/portaljs/stargazers"><img src="https://img.shields.io/github/stars/datopian/portaljs?logo=github&logoColor=white&label=Stars&color=blue" alt="GitHub stars" /></a>
    <a href="https://discord.gg/krmj5HM6He"><img src="https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white" alt="Join our Discord" /></a>
    <a href="license"><img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT License" /></a>
  </p>
</p>

---

## Quickstart

**Create a portal** — one command, nothing to install beyond Node 22+:

```bash
npm create portaljs@latest my-portal
cd my-portal
npm run dev      # → http://localhost:3000
```

You get the three surfaces — Home, a Catalog (`/search`), and a dataset Showcase
(`/@<namespace>/<slug>`) — over sample data. Plain, editable Next.js, no lock-in. Add your
own CSV/JSON to `datasets.json` and it renders automatically.

**Build it with your AI assistant** — PortalJS ships [Claude Code](https://claude.com/claude-code)
skills that do the assembly. Install them once (into `~/.claude/commands`):

```bash
curl -fsSL https://raw.githubusercontent.com/datopian/portaljs/main/scripts/install-portaljs-skills.sh | bash
```

Then, in a Claude Code session from any directory:

```text
/portaljs-architect    not sure what stack you need? start here
/portaljs-new-portal   "Auckland Council open data portal"
/portaljs-add-dataset  ./data/air-quality.csv
```

`/portaljs-new-portal` scaffolds the three surfaces; `/portaljs-add-dataset` (or `/portaljs-add-resource`) loads data;
`/portaljs-connect-ckan` points it at a CKAN backend; `/portaljs-deploy` ships it. ([All skills + install →](.claude/INSTALL.md))

**Prefer the bare template** — plain Next.js, no AI, no lock-in:

```bash
npx tiged datopian/portaljs/examples/portaljs-catalog my-portal
cd my-portal && npm install && npm run dev      # → http://localhost:3000
```

You get Home, a Catalog (`/search`), and a dataset Showcase (`/@<namespace>/<slug>`) over
sample data. Add your own CSV/JSON to `datasets.json` and it renders automatically.

⭐ If it's useful, a star helps others find it.

## Why PortalJS

Building a data portal has always meant more than a website. You have to decide where
the data lives, how it's versioned, how people search it, how it's served, and how it's
governed — and then wire a frontend on top. Teams either over-build on a heavy data
warehouse they don't need, or under-build on a pile of scripts that doesn't scale.

PortalJS is an **open-source, agentic skills framework that helps data teams build,
develop, and ship data portals — and the data infrastructure underneath them.** It isn't
only a frontend. The skills do two jobs:

- **Advise** — given _what you're building_, _what your data is_, and _what it's for_,
  they recommend an architecture: storage, compute, catalog, access, hosting, metadata.
- **Build** — they scaffold that stack as plain, editable Next.js code with no lock-in.

It is **opinionated but open**: the recommended modern path is git + object storage
(Cloudflare R2) + Parquet, queried with [DuckDB](https://duckdb.org/) — an open lakehouse
instead of a classic warehouse. For living, incremental tables you can layer on
[DuckLake](https://ducklake.select/), and a traditional datastore (CKAN, a warehouse)
stays a first-class option when you need it. You always own plain code.

Built and maintained in the open by [Datopian](https://www.datopian.com/) and the
PortalJS community.

## Architecture at a glance

```text
        🧑  you describe what you want to build
        │
        ▼
╭─ 🤖  AGENTIC SKILLS ──────────────────────────────────  decide + build
│   /portaljs-architect · /portaljs-new-portal · /portaljs-add-dataset · /portaljs-add-chart · /portaljs-add-map …
╰─  generates plain, editable Next.js code — no lock-in
        │
        ▼
╭─ 🖥️  SURFACES ────────────────────────────────────────  what users see
│   🏠 Home /      🔎 Catalog /search      📊 Showcase /@ns/slug
╰─  read data through one DataProvider contract
        │
        ▼
╭─ 🔌  PROVIDERS ───────────────────────────────────────  pluggable backends
│   📁 static·git     🐘 CKAN     🔭 OpenMetadata     🗂️ git-LFS + R2
╰─  swap the source without touching a page
        │
        ▼
📦  STORAGE + COMPUTE  —  choose your point on the spectrum:

      flat files  ─▶  Git-LFS + R2  ─▶  Parquet on R2 + 🦆 DuckDB  ─▶  warehouse / CKAN
      simplest                       ⭐ open lakehouse (default)        heaviest
                                     (+ DuckLake for living tables)

☁️  Substrate  —  Cloudflare R2 (storage) · Workers (runtime) · D1 (catalog) · Pages (static)
     object storage stays S3-compatible — R2 is the default, never a lock-in
```

**Three surfaces.** Every data portal is built from three: a **Home** page that explains
it and offers search, a **Catalog** (`/search`) to discover datasets, and a **Showcase**
(`/@<namespace>/<slug>`) to explore one dataset — metadata, preview, download/API, and
charts/maps. ([Core concepts →](https://www.portaljs.com/docs/core-concepts))

**One seam.** The surfaces read data only through a `DataProvider`, so the source — static
files today, a CKAN or lakehouse backend tomorrow — can change without touching a page.

See [`ROADMAP.md`](ROADMAP.md) for the full model and the
[architecture decision framework](https://www.portaljs.com/docs/architecture/decision-framework)
for how `/portaljs-architect` turns your needs into a stack.

## Build a portal with your AI assistant

PortalJS ships [Claude Code](https://claude.com/claude-code) skills that turn a brief into
a working portal.

### Setup

Install the skills once into your personal scope so they're available from **any**
directory:

```bash
curl -fsSL https://raw.githubusercontent.com/datopian/portaljs/main/scripts/install-portaljs-skills.sh | bash
```

Restart Claude Code (or open a new session) and type `/` to see them. See
[`.claude/INSTALL.md`](.claude/INSTALL.md) for other install options (versioned plugin, or
running straight from a clone of this repo).

### Use

If you're not sure how to set up your portal, start with the advisor, then build:

```text
/portaljs-architect    we have ~200 public CSVs, updated quarterly, and must publish DCAT-AP
/portaljs-new-portal   "Auckland Council open data portal"
/portaljs-add-dataset  ./data/air-quality.csv
/portaljs-add-dataset  https://example.com/parks.geojson
```

The skills are **interactive** — if your brief is thin, they interview you in short rounds
rather than erroring. `/portaljs-architect` recommends a stack and hands off; `/portaljs-new-portal`
scaffolds the three surfaces; `/portaljs-add-dataset` appends to the `datasets.json` manifest and
the showcase renders automatically at `/@<namespace>/<slug>`. Run `npm run dev` and you
have a portal.

**Prefer to build by hand?** The skills are a convenience, not a requirement — scaffold the
template directly with the CLI:

```bash
npm create portaljs@latest my-portal
```

(Or grab the bare template with no prompts: `npx tiged datopian/portaljs/examples/portaljs-catalog my-portal`.)

### Available skills

<!-- BEGIN:skills-table -->

| Skill | What it does |
| ----- | ------------ |
| [`/portaljs-architect`](.claude/commands/portaljs-architect.md) | Advisory — turns your needs (data, scale, governance) into a recommended architecture before you build. Start here if you're unsure of the stack. |
| [`/portaljs-new-portal`](.claude/commands/portaljs-new-portal.md) | Scaffold a new portal (Home + Catalog + Showcase) from a brief — copies the template, substitutes your project name and description, installs deps, verifies the build. |
| [`/portaljs-add-dataset`](.claude/commands/portaljs-add-dataset.md) | Add a CSV, TSV, JSON, or GeoJSON dataset — registers it in the catalog and renders its showcase automatically; large local files are pushed to Cloudflare R2 via Git LFS for you. |
| [`/portaljs-add-resource`](.claude/commands/portaljs-add-resource.md) | Attach another file (data dictionary, methodology, extra data) to an existing dataset — it becomes multi-resource and the showcase renders a section per file. |
| [`/portaljs-add-chart`](.claude/commands/portaljs-add-chart.md) | Add a line, bar, area, pie, or scatter chart to a dataset's showcase. |
| [`/portaljs-add-map`](.claude/commands/portaljs-add-map.md) | Render a GeoJSON dataset on an interactive map and register it on the home page. |
| [`/portaljs-define-schema`](.claude/commands/portaljs-define-schema.md) | Infer a Frictionless Table Schema from a dataset's data, add license/source/keyword metadata, and surface a typed field table on its showcase. |
| [`/portaljs-add-dcat`](.claude/commands/portaljs-add-dcat.md) | Make the portal harvestable — emit standards-compliant DCAT feeds (DCAT 2/3, DCAT-AP, DCAT-US, national profiles) in JSON-LD, Turtle, and RDF/XML so national/EU/US open-data portals can harvest its datasets. |
| [`/portaljs-connect-ckan`](.claude/commands/portaljs-connect-ckan.md) | Wire the portal to a CKAN backend over its API instead of static files. |
| [`/portaljs-check-data-quality`](.claude/commands/portaljs-check-data-quality.md) | Validate a dataset against its schema and flag quality issues (type mismatches, missing values, constraint violations). |
| [`/portaljs-migrate`](.claude/commands/portaljs-migrate.md) | Harvest or migrate a whole catalog into the portal from CKAN, Socrata, OpenDataSoft, ArcGIS, or DCAT-US, over a canonical Frictionless/DCAT model. |
| [`/portaljs-deploy`](.claude/commands/portaljs-deploy.md) | Build a static export and publish it to PortalJS Arc — Datopian-managed hosting on Cloudflare — with a live `<slug>.arc.portaljs.com` URL. |

<!-- END:skills-table -->
<!-- Generated from scripts/skills-manifest.mjs — edit there and run `npm run gen:skills`. -->

Large-data scaling — big files pushed to Cloudflare R2 via Git LFS — already ships in
`/portaljs-add-dataset`. More skill families — metadata schemas (Frictionless/DCAT), more
backends (OpenMetadata), a browser DuckDB query layer, and access control — are on the
[roadmap](ROADMAP.md). Write your own — see [`.claude/AUTHORING.md`](.claude/AUTHORING.md).

## What's in this repo

```text
.claude/commands/    the agentic skills (slash commands)
examples/            reference portals — portaljs-catalog is the canonical template
packages/
  core/              layout/UI components            (@portaljs/core)
  ckan/              CKAN catalog UI + React          (@portaljs/ckan)
  ckan-api-client-js/ pure CKAN API client            (@portaljs/ckan-api-client-js)
site/                portaljs.com — the marketing site + docs
ROADMAP.md           direction, the four contracts, sequencing
```

The canonical template, [`examples/portaljs-catalog`](examples/portaljs-catalog/), is where
the three surfaces and the `DataProvider` seam live — read it before building.

## What makes it different

- 🌱 **Open source, MIT, no lock-in** — every skill emits plain Next.js you can fork and own.
- 🧭 **Advisory, not just generative** — `/portaljs-architect` helps you _decide_ the infrastructure, not only scaffold a UI.
- 🦆 **Open lakehouse by default** — git + R2 + Parquet queried with DuckDB, over a heavy warehouse; add DuckLake for living/incremental tables. A datastore/warehouse stays a supported choice.
- ☁️ **Cloudflare-first, portable** — R2 / Workers / D1 / Pages as the default substrate, but object storage stays S3-compatible.
- 🧩 **Decoupled, any backend** — one `DataProvider` contract in front of [CKAN](https://ckan.org/), [DKAN](https://getdkan.org/), [OpenMetadata](https://open-metadata.org/), [DataHub](https://datahubproject.io/), GitHub, [Frictionless](https://frictionlessdata.io/), plain files — or your own.
- 🎨 **Bring your own stack** — adopt the template or lift the skills and the three-surface model into an app you already have.

## Examples

Reference implementations live in [`examples/`](examples/):

| Example | Backend |
|---------|---------|
| [`portaljs-catalog`](examples/portaljs-catalog/) | **Canonical template** — Home + Catalog + Showcase over a static manifest |
| [`portaljs-template`](examples/portaljs-template/) | Minimal single-page starter |
| [`ckan`](examples/ckan/) · [`ckan-ssg`](examples/ckan-ssg/) | CKAN |
| [`github-backed-catalog`](examples/github-backed-catalog/) | GitHub |
| [`dataset-frictionless`](examples/dataset-frictionless/) | Frictionless Data Package |
| [`fivethirtyeight`](examples/fivethirtyeight/) · [`openspending`](examples/openspending/) · [`turing`](examples/turing/) | Real-world portals |

## Community & support

- 💬 **Discord** — live chat and help: [join the server](https://discord.gg/krmj5HM6He)
- 🗣️ **Discussions** — questions, ideas, show-and-tell: [github.com/datopian/portaljs/discussions](https://github.com/datopian/portaljs/discussions)
- 🐛 **Issues** — bugs and feature requests: [open an issue](https://github.com/datopian/portaljs/issues/new)
- 📖 **Docs** — [portaljs.com/docs](https://www.portaljs.com/docs)

## Contributing

PortalJS is built in the open and we welcome contributions of all sizes — new skills,
examples, docs, and fixes. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started, and read
[ROADMAP.md](ROADMAP.md) and [VISION.md](VISION.md) for where the project is headed.

## License

[MIT](license) © [Datopian](https://www.datopian.com/)
