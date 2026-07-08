---
metatitle: /portaljs-add-dcat – Emit DCAT Feeds So Your Portal Is Harvestable
metadescription: The /portaljs-add-dcat skill makes a PortalJS portal harvestable by national, EU, and US open-data portals — it emits standards-compliant DCAT catalog feeds (DCAT 2/3, DCAT-AP, DCAT-US, and pluggable national profiles) in JSON-LD, Turtle, and RDF/XML at build, with feed autodiscovery and per-profile conformance checking.
title: /portaljs-add-dcat
description: Make the portal harvestable — emit standards-compliant DCAT feeds (DCAT 2/3, DCAT-AP, DCAT-US, national profiles) in JSON-LD, Turtle, and RDF/XML so open-data portals can harvest its datasets.
---

`/portaljs-add-dcat` turns a PortalJS portal into a **harvestable** data catalog. It emits
standards-compliant [**DCAT**](https://www.w3.org/TR/vocab-dcat-3/) metadata feeds so
external catalogs and government data portals — [data.europa.eu](https://data.europa.eu),
[data.gov](https://data.gov), and national portals — can discover and harvest its datasets
automatically.

PortalJS is Frictionless-native (a dataset is a Data Package — see
[`/portaljs-define-schema`](/docs/skills/portaljs-define-schema)); **DCAT is the
serialization + harvest layer on top**. This skill selects one or more DCAT **application
profiles**, maps every dataset's metadata to them, and writes static feed files at build so
they harvest on **any** host — static Cloudflare Pages, a CDN, a Worker — with no runtime.

## When to use it

Run it once your datasets carry proper metadata (title, description, license, keywords —
add them with [`/portaljs-define-schema`](/docs/skills/portaljs-define-schema)) and you want
the portal to be found and harvested by a larger catalog. If you're targeting a **national
or EU open-data portal**, pick the `dcat-ap` profile; for a **US federal** portal, pick
`dcat-us`. Skip it for a purely internal portal that nothing else harvests.

## What it produces

The feeds are wired into `predev`/`prebuild` (via `scripts/generate-dcat.ts`), so they're
always fresh and regenerate from `datasets.json` + `dcat.config.json`:

| File | What |
|------|------|
| `public/catalog.jsonld` · `catalog.ttl` · `catalog.rdf` | **Canonical** feed (first profile) in JSON-LD, Turtle, RDF/XML — the stable autodiscovery targets |
| `public/catalog.<profile>.{jsonld,ttl,rdf}` | One feed per configured profile × serialization (e.g. `catalog.dcat-ap.ttl`) |
| `public/catalog-feeds.json` | Machine-readable index of every emitted feed |
| `<link rel="alternate" …>` in `_document.tsx` | Autodiscovery — how harvesters find the feed from any page |

Only `dcat.config.json` is committed; the feeds themselves are build artifacts (gitignored).

## Supported profiles

Profiles live in a **pluggable registry** (`lib/metadata/dcat-profiles.ts`) — national
profiles are config, not hardcoded, and a portal can emit several at once.

| id | Profile |
|----|---------|
| `dcat-3` | DCAT 3 (W3C) — the default |
| `dcat-2` | DCAT 2 (W3C) |
| `dcat-ap` | DCAT-AP — the European profile (data.europa.eu) |
| `dcat-us` | DCAT-US 3.0 — US federal / Project Open Data (data.gov) |
| `geodcat-ap` | GeoDCAT-AP — DCAT-AP + spatial coverage (INSPIRE / geospatial catalogs) |
| `croissant` | Croissant — MLCommons schema.org ML-dataset metadata (JSON-LD only) |
| `dcat-ap-se` · `dcat-ap-ch` · `dcat-ap-de` | National profiles (Sweden / Switzerland / Germany) |

Add another national profile without touching skill code:
`registerDcatProfile(makeNationalProfile({ id, label, conformsTo, context }))`, then list
its id in `dcat.config.json`. See the metadata contract's `lib/metadata/README.md`.

## Honest conformance

DCAT-AP and DCAT-US **require** a publisher (`dct:publisher`) and a contact point
(`dcat:contactPoint`); DCAT-US also requires an access level. The skill asks for these when
you choose those profiles. The generator still emits the feed if they're missing — but it
**warns exactly what's absent** and never silently claims conformance. For a rigorous check
it points you at the official SHACL shapes and the hosted validators
([data.europa.eu](https://data.europa.eu/mqa/shacl-validation/) for DCAT-AP,
[resources.data.gov](https://resources.data.gov/resources/dcat-us/) for DCAT-US).

## Example

```
/portaljs-add-dcat profiles=dcat-ap,dcat-us
```
The skill asks for your publishing organization, a contact, and the site URL, writes
`dcat.config.json`, ensures the autodiscovery link and the multi-profile generator are in
place, generates the feeds in JSON-LD + Turtle + RDF/XML for both profiles, reports any
missing mandatory fields, verifies the build, and tells you the feed URL to register with
the harvester.

Next: publish with [`/portaljs-deploy`](/docs/skills/portaljs-deploy), then register your
portal with the target harvester pointing at `<your-site>/catalog.jsonld`.
