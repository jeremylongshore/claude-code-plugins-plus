# Metadata profiles

The **metadata-profile contract** is the seam that defines how a dataset's
**schema** and **descriptive metadata** are authored and surfaced. It sits beside
the other two seams:

| Contract | Module | Answers |
|----------|--------|---------|
| data-provider | `lib/providers` | *which datasets exist* |
| data-query | `lib/query` | *how to compute over a dataset's data* |
| **metadata-profile** | **`lib/metadata`** | **how a dataset's schema + metadata are authored & surfaced** |

The model is **Frictionless-native**: a dataset is authored as a Frictionless Data
Package — a [Table Schema](https://specs.frictionlessdata.io/table-schema/)
(`fields[]` with types + constraints) plus the Data Package descriptor fields a
catalog cares about (`title`, `licenses`, `sources`, `keywords`, ...). **DCAT /
DCAT-AP is a serialization + harvest layer ON TOP of this model** (`dcat.ts`) — the
portal emits a DCAT-3 `/catalog.jsonld` so external catalogs can harvest it.

```
   the showcase surface  /@<namespace>/<slug>
              |  getProfile(dataset.profile)
        +-----v--------+
        | MetadataProfile |  <- the contract (types.ts)
        +-----+--------+
              |
   +----------+------------------------------+
   |                                          |
 frictionlessTabularProfile (L0, default)   custom profiles (L1/L2) via registry (L3)
   |
   +-- validate(schema + rows) -> ValidationResult
```

## The contract

```ts
interface MetadataProfile {
  readonly id: string
  readonly name: string
  readonly version: string
  readonly schema?: TableSchema           // a pinned template schema, if any
  validate(input: ValidationInput): ValidationResult
}
```

A dataset (in `datasets.json`, read through the provider) carries the optional
fields the profile describes:

```jsonc
{
  "slug": "country-codes", "namespace": "reference", "name": "Country Codes",
  "file": "country-codes.csv", "format": "csv",
  "profile": "frictionless-tabular",      // which profile validates/surfaces it
  "schema": {
    "primaryKey": "alpha3",
    "fields": [
      { "name": "name",   "type": "string", "constraints": { "required": true } },
      { "name": "alpha3", "type": "string", "constraints": { "unique": true, "pattern": "^[A-Z]{3}$" } }
    ]
  },
  "licenses": [{ "name": "ODbL-1.0", "path": "https://opendatacommons.org/licenses/odbl/1-0/" }],
  "sources":  [{ "title": "ISO 3166-1", "path": "https://www.iso.org/iso-3166-country-codes.html" }],
  "keywords": ["countries", "iso", "reference"],
  "version": "1.0.0"
}
```

All of it is optional — a dataset with no `schema`/metadata still lists and previews;
the showcase degrades cleanly.

## The L0 → L3 ladder

The same "use the default / extend it / replace it / register many" ladder as the
other contracts. **Only L0 ships built**; L1–L3 are how-to.

### L0 — the default profile (built)

`frictionlessTabularProfile` (id `frictionless-tabular`) is the registered default.
It validates whatever Table Schema a dataset declares against the loaded rows:
type-coercion + a constraint subset (`required`, `unique`, `enum`, `min`/`max`,
`minLength`/`maxLength`, `pattern`, `primaryKey` uniqueness). Deep, spec-complete
row validation is a TODO — L0 catches the common authoring errors.

```ts
import { getProfile } from './lib/metadata'

const profile = getProfile(dataset.profile)        // -> frictionlessTabularProfile
const result = profile.validate({ schema: dataset.schema, rows })
if (!result.valid) console.warn(result.errors)
```

### L1 — extend L0 with extra fields

Compose a profile that reuses L0's `validate` and adds your own checks/fields:

```ts
import { frictionlessTabularProfile, registerProfile, type MetadataProfile } from './lib/metadata'

const govProfile: MetadataProfile = {
  ...frictionlessTabularProfile,
  id: 'gov-tabular',
  name: 'Government tabular (adds a required publisher)',
  validate(input) {
    const base = frictionlessTabularProfile.validate(input)
    if (!input.metadata?.sources?.length) {
      base.errors.push({ message: 'a publisher source is required' })
    }
    return { ...base, valid: base.errors.length === 0 }
  },
}
registerProfile(govProfile)
```

### L2 — a fully custom profile

Implement `MetadataProfile` from scratch — your own `schema` template and
`validate()` — when the Frictionless model isn't the right base at all.

### L3 — the registry (the seam)

`registry.ts` holds a profile per id; a portal mixes profiles (one per dataset
type / domain) and surfaces resolve the right one off the dataset's `profile`
field:

```ts
import { getProfile, registerProfile, listProfiles } from './lib/metadata'

registerProfile(govProfile)          // at module load
getProfile('gov-tabular')            // resolve by id
getProfile(undefined)                // -> the L0 default
getProfile('nope')                   // unknown -> falls back to L0 default
```

## DCAT interop

`dcat.ts` is the serialization + harvest layer over the Frictionless-native model.
DCAT/DCAT-AP is how a portal **exposes** its catalog for harvest and **ingests**
from external catalogs. The Frictionless fields map onto DCAT-3 JSON-LD
(`title→dct:title`, `keywords→dcat:keyword`, `licenses→dct:license`,
`sources→dct:source`, `file/format→dcat:distribution`).

```ts
import { toDCAT, fromDCAT, toDCATCatalog, fromDCATCatalog } from './lib/metadata'

toDCAT(dataset, { baseUrl, identifier, landingPage })  // one Frictionless dataset → dcat:Dataset
toDCATCatalog(datasets, { baseUrl, title })            // the whole catalog → dcat:Catalog
fromDCAT(node) / fromDCATCatalog(catalog)              // harvest/import back to Frictionless
```

**The harvest endpoint.** `scripts/generate-dcat.ts` reads the catalog through the
data provider and writes the feed files under `public/`. It runs automatically on
`predev`/`prebuild`, so they're always fresh — and because they're static files they
harvest on **any** host (static Cloudflare Pages, a CDN, a Worker), no runtime
required. Set `SITE_URL` to emit absolute landing/download URLs; without it links are
root-relative (fine for same-origin harvest).

### DCAT application profiles (harvest-compatible)

`dcat.ts` is the DCAT-3 core; `dcat-profiles.ts` is the **application-profile layer** on
top of it — what national/EU/US portals actually harvest. A profile adds the extra
namespaces, mandatory fields (`dct:publisher`, `dcat:contactPoint`, …), and
`dct:conformsTo` a specific harvester requires, then reports what's still missing rather
than silently claiming conformance (`dcat-validate.ts`). `dcat-rdf.ts` serializes the
same graph to **Turtle** and **RDF/XML** alongside JSON-LD.

```ts
import { getDcatProfile, serialize, validateDcat } from './lib/metadata'

const profile = getDcatProfile('dcat-ap')      // dcat-2 | dcat-3 | dcat-ap | dcat-us | dcat-ap-se | …
const feed = profile.apply(baseDcat3Catalog, dcatConfig)   // augment to the profile
validateDcat(feed, profile.id)                 // mandatory-field gaps
serialize(feed, 'ttl')                         // 'jsonld' | 'ttl' | 'rdf'
```

Profiles are a **pluggable registry**: national profiles are config, not code —
`registerDcatProfile(makeNationalProfile({ id, label, conformsTo, context }))`. A portal
can emit several profiles at once. Which profiles + serializations to emit, and the
catalog-level org/contact metadata they need, are authored in `dcat.config.json` and
wired by the [`/portaljs-add-dcat`](/docs/skills/portaljs-add-dcat) skill.

**What DCAT does not carry.** DCAT has no inline field schema — the Table Schema is
referenced via a distribution's `dcat:describedBy`, not embedded. So `fromDCAT`
recovers package metadata + the distribution (file/format), **not** the field-level
schema. That asymmetry is intrinsic to DCAT.

## Out of scope here

- `/portaljs-define-schema` authoring skill (the interview/build layer) — see that skill.
- Deep SHACL validation of a profiled feed — `dcat-validate.ts` does a structural
  mandatory-field check; run the official DCAT-AP/DCAT-US SHACL shapes (or the
  data.europa.eu / resources.data.gov validators) for authoritative conformance. The
  [`/portaljs-add-dcat`](/docs/skills/portaljs-add-dcat) skill wires the whole feed
  pipeline (profiles, serializations, autodiscovery, validation).
