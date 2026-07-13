---
name: portaljs-add-dcat
description: Make a PortalJS portal harvestable by national/EU/US open-data portals — emit standards-compliant DCAT catalog feeds (DCAT 2/3, DCAT-AP, DCAT-US, national profiles) in JSON-LD, Turtle, and RDF/XML at build, with autodiscovery and per-profile conformance checking. Use when a portal needs to be harvested by data.europa.eu, data.gov, or a national open-data catalog.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*), WebFetch
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - dcat
  - interoperability
  - rdf
  - jsonld
---

# PortalJS — Add DCAT

## Overview

Turn an existing PortalJS (`portaljs-catalog`) portal into a harvestable data catalog.
PortalJS is Frictionless-native — a dataset is a Data Package (see
`portaljs-define-schema`) — and DCAT is the serialization + harvest layer on top
(`lib/metadata/dcat.ts` + `lib/metadata/dcat-profiles.ts`). This skill selects one or
more DCAT application profiles, maps every dataset's metadata to them, and writes
static feed files at build time — JSON-LD, Turtle, and RDF/XML — so external catalogs
(data.europa.eu, data.gov, national portals) can harvest the datasets automatically,
on any static host, with no runtime.

## Prerequisites

- A scaffolded PortalJS portal with `datasets.json`, `package.json`, and
  `lib/metadata/` (the metadata-profile contract) present.
- `lib/metadata/dcat.ts` (the DCAT-3 core) already in place — profiles augment it.
- Node 18+ and npm available in the portal directory.
- For DCAT-AP / DCAT-US: a publishing organization (name + homepage) and a contact
  (name + email) — both profiles require `dct:publisher` and `dcat:contactPoint`.
- Optional but recommended: network access to run SHACL conformance checks against the
  official EU ITB validator or `pyshacl`.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-add-dcat.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-dcat.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Gather input from `$ARGUMENTS` (interview if thin): portal directory (default `.`),
   profiles (default `["dcat-3"]`), site URL, publisher, contact, license, themes,
   languages, access level.
2. Validate the portal directory: confirm `datasets.json`, `package.json`, and
   `lib/metadata/` exist; stop with an `ERROR:` if the metadata contract is missing.
3. Ensure the DCAT profile layer is present — `dcat-profiles.ts`, `dcat-rdf.ts`,
   `dcat-validate.ts` — copying canonical versions from `examples/portaljs-catalog` if
   the portal predates this skill.
4. Ensure `scripts/generate-dcat.ts` is wired to `predev`/`prebuild` and emits
   per-profile x serialization feeds from `dcat.config.json`.
5. Write `dcat.config.json` with the gathered profiles, publisher, contact, license,
   themes, and access level.
6. Add feed autodiscovery: a `<link rel="alternate" type="application/ld+json">` to
   `pages/_document.tsx` pointing at `/catalog.jsonld`.
7. Generate the feeds and check conformance: run `npm run generate:dcat` and surface
   any missing mandatory fields.
8. Verify the RDF: confirm the JSON-LD parses, and cross-check that JSON-LD, Turtle,
   and RDF/XML agree; run SHACL validation (ITB for DCAT-AP, `pyshacl` for DCAT-US)
   when network/tooling allow.
9. Verify the build with `npx next build`; fix errors before reporting success.
10. Report the profiles emitted, feed paths, conformance status, and next steps
    (register with the harvester, run `portaljs-deploy`).

## Output

- **Created/modified:** `dcat.config.json` (committed config).
- **Generated (build artifacts, gitignored):** `public/catalog.jsonld` /`.ttl`/`.rdf`
  (canonical feed), `public/catalog.<profile>.{jsonld,ttl,rdf}` per configured profile,
  `public/catalog-feeds.json` (feed index).
- **Modified:** `pages/_document.tsx` (autodiscovery `<link>`), `package.json`
  (`generate:dcat` script wired to `predev`/`prebuild`).
- **Verified:** feeds are valid JSON-LD/Turtle/RDF-XML, conformance status reported,
  `npx next build` passes.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| `NO_METADATA_CONTRACT` | `lib/metadata/` not found | Portal predates the metadata-profile contract; scaffold with `portaljs-new-portal` or add `lib/metadata` first. |
| `NO_DCAT_CORE` | `lib/metadata/dcat.ts` not found | The DCAT-3 core is missing; update the portal template before adding profiles. |
| `BAD_CONFIG` | `dcat.config.json` is not valid JSON | Fix the syntax and re-run `npm run generate:dcat`. |
| `UNKNOWN_PROFILE` | Profile id not in the registry | Use one of `dcat-2`, `dcat-3`, `dcat-ap`, `dcat-us`, `geodcat-ap`, `croissant`, `dcat-ap-se`, `dcat-ap-ch`, `dcat-ap-de`, or register a national profile first. |
| Feed flagged non-conformant | `publisher`/`contactPoint` missing for DCAT-AP or DCAT-US | Ask the user for the publishing organization and contact, add to `dcat.config.json`, regenerate. |
| DCAT-US SHACL rejects the publisher | Publisher has no IRI (blank node) | Set `publisher.uri` (or `homepage`) in `dcat.config.json`. |
| `next build` fails after config change | Malformed JSON in `dcat.config.json` or `datasets.json` | Print the build log, fix the JSON, rebuild before reporting success. |

## Examples

### Example 1 — Default DCAT-3 feed, no national harvesting

```
/portaljs-add-dcat
```
Emits the canonical `public/catalog.jsonld`/`.ttl`/`.rdf` under the default `dcat-3`
profile, adds autodiscovery to `_document.tsx`, and wires `generate:dcat` into
`predev`/`prebuild`. No publisher/contact required.

### Example 2 — EU harvesting via DCAT-AP

```
/portaljs-add-dcat profiles=dcat-ap site=https://data.example.org
```
Prompts for publisher (name + homepage) and contact (name + email) since DCAT-AP
requires both, writes them into `dcat.config.json`, and emits
`public/catalog.dcat-ap.{jsonld,ttl,rdf}` plus the canonical feed with absolute links.

### Example 3 — US federal harvesting via DCAT-US

```
/portaljs-add-dcat profiles=dcat-us site=https://data.example.gov
```
Requires an IRI-identified publisher (`publisher.uri`) for SHACL conformance; emits
`catalog.dcat-us.{jsonld,ttl,rdf}` and validates against the DCAT-US 3.0 SHACL shapes
with `pyshacl` when available.

### Example 4 — Multiple profiles plus a national extension

```
/portaljs-add-dcat profiles=dcat-ap,dcat-ap-de site=https://daten.example.de
```
Emits both `catalog.dcat-ap.*` and `catalog.dcat-ap-de.*` feeds from one config; the
first profile listed also becomes the canonical, un-suffixed `catalog.jsonld`/`.ttl`/`.rdf`.

## Resources

- Full workflow: [`.claude/commands/portaljs-add-dcat.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-dcat.md)
- Profile registry, serialization formats, and validator details: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-define-schema`, `portaljs-new-portal`, `portaljs-deploy`, `portaljs-migrate`
- DCAT specification: <https://www.w3.org/TR/vocab-dcat-3/>
