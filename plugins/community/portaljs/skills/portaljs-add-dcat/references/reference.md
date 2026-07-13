# Add DCAT — Reference

Detailed reference for the `portaljs-add-dcat` skill. The executable workflow lives in
[`.claude/commands/portaljs-add-dcat.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-dcat.md).

## Supported DCAT profiles

Profiles are a pluggable registry (`lib/metadata/dcat-profiles.ts`); national profiles
are config/data, not hardcoded, and multiple can be emitted at once.

| id | Profile | Notes |
| --- | --- | --- |
| `dcat-3` | DCAT 3 (W3C) | Default. `conformsTo` DCAT-3. |
| `dcat-2` | DCAT 2 (W3C) | Same core subset stamped as DCAT-2. |
| `dcat-ap` | DCAT-AP (data.europa.eu) | EU profile: adds foaf/vcard, publisher, contactPoint, `dcat:theme`. |
| `dcat-us` | DCAT-US 3.0 (data.gov) | US federal / Project Open Data: adds publisher, contactPoint, `dct:accessLevel`. |
| `geodcat-ap` | GeoDCAT-AP (spatial / INSPIRE) | DCAT-AP + `dct:spatial` (bbox/geometry as `gsp:wktLiteral`) from a dataset's `dcat.spatial`. |
| `croissant` | Croissant (MLCommons / schema.org) | ML-dataset metadata; JSON-LD only. |
| `dcat-ap-se` / `dcat-ap-ch` / `dcat-ap-de` | National (Sweden / Switzerland / Germany) | DCAT-AP + national `conformsTo`. |

Register another national profile without code:
`registerDcatProfile(makeNationalProfile({ id, label, conformsTo, context }))` in a
small module the app loads, then list its id in `dcat.config.json`.

## Serialization formats

Each configured profile emits three files: `catalog.<profile>.jsonld`,
`catalog.<profile>.ttl`, `catalog.<profile>.rdf`. The first profile listed in
`dcat.config.json` also gets the canonical, un-suffixed `catalog.jsonld`/`.ttl`/`.rdf` —
the stable autodiscovery target referenced from `_document.tsx`.

Conformance rules the mapping must preserve: links (`dcat:downloadURL`, `dct:license`,
`dcat:theme`, …) are IRIs, typed `"@type": "@id"` in the JSON-LD `@context`, never bare
strings; `dct:format` / `dcat:mediaType` are IRIs (EU file-type authority / IANA
media-type URIs), not literals like `"CSV"`; dates (`dct:issued/modified/created`) are
full `xsd:dateTime` timestamps.

## Conformance validation

- **DCAT-AP** — EU ITB SHACL validator REST API (`https://www.itb.ec.europa.eu/shacl/dcat-ap/api/validate`),
  `validationType: dcatap.3_0_1_base` for the harvest gate; or offline with `pip install pyshacl`
  and the [DCAT-AP SHACL shapes](https://github.com/SEMICeu/DCAT-AP/tree/master/releases).
- **DCAT-US** — `pip install pyshacl` + the
  [DCAT-US 3.0 SHACL shapes](https://raw.githubusercontent.com/DOI-DO/dcat-us/main/shacl/dcat-us_3.0_shacl_shapes.ttl).
  Requires an IRI-identified `dct:publisher` — a blank-node publisher is rejected.
- **GeoDCAT-AP** — validates as DCAT-AP for the harvest gate; full spatial profile via the
  [GeoDCAT-AP 3.0.0 SHACL shapes](https://semiceu.github.io/GeoDCAT-AP/releases/3.0.0/shacl/geodcat-ap-SHACL.ttl)
  (run with `-i rdfs` to clear subclass-range warnings).
- **Croissant** — `pip install mlcroissant`, then `mlcroissant validate --jsonld <file>` per
  dataset (extract each `dataset[i]` from the `DataCatalog` feed and re-attach the shared
  `@context` first).

If `pyshacl` and network are both unavailable, report that plainly and give the
validator URL rather than skipping the check silently.

## Troubleshooting

- **Feed missing `publisher`/`contactPoint`** — expected for `dcat-3`/`dcat-2`; for
  `dcat-ap`/`dcat-us` this is a conformance failure. Ask for the organization name +
  homepage and a contact name + email, then regenerate.
- **DCAT-US publisher rejected by SHACL** — the publisher has no IRI; set
  `publisher.uri` (or `homepage`) in `dcat.config.json` so it serializes as a resource,
  not a blank node.
- **JSON-LD/Turtle/RDF-XML triple counts disagree** — usually a serializer bug in
  `lib/metadata/dcat-rdf.ts`; parse each with `n3` (Turtle), `rdfxml-streaming-parser`
  (RDF/XML), and `jsonld` → n-quads (JSON-LD) in a scratch directory and diff.
- **`next build` fails after editing `dcat.config.json`** — almost always malformed
  JSON (trailing comma, unescaped quote); re-open the file, validate it parses, rebuild.
- **GeoDCAT-AP full-profile SHACL run shows range warnings** — expected when the
  validator can't dereference external vocabularies (publisher→`foaf:Agent`,
  theme→`skos:Concept`); these are advisory, not harvest-blocking.
