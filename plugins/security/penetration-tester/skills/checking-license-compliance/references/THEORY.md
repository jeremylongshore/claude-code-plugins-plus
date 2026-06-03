# THEORY — License Compliance for Software Distribution

## Why this is a security skill

License compliance isn't a vulnerability in the CVE sense, but the
consequences ladder is real:

1. **Re-licensing obligation.** Strong-copyleft contamination can
   force you to release proprietary source code or accept a
   distribution restriction you didn't intend.
2. **Contract breach.** Customer contracts often include
   representation-and-warranty clauses about license posture. A
   GPL-contaminated proprietary product can breach those.
3. **M&A blocker.** Code audits during M&A surface license issues
   as a categorical risk; unresolved findings can re-price or kill
   a deal.
4. **Revenue impact.** Public AGPL-licensed code in a SaaS product
   can force source disclosure of the entire service, including
   business logic.

The penetration-tester pack treats this as a security concern
because the failure modes (compliance gap, retroactive obligation,
brand impact) overlap with what a security program is chartered to
prevent.

## SPDX as the canonical vocabulary

SPDX (Software Package Data Exchange, ISO/IEC 5962:2021) is the
industry-standard way to express a license. The SPDX license list
covers ~600 licenses with a canonical short identifier (`MIT`,
`Apache-2.0`, `GPL-3.0-or-later`, etc.).

License expressions support boolean composition:

- `MIT OR Apache-2.0` — either license at the user's choice (common for permissively dual-licensed packages)
- `MIT AND CC-BY-4.0` — both licenses apply (e.g. code + docs split)
- `Apache-2.0 WITH LLVM-exception` — Apache + a named exception clause

The skill's parser handles the `OR`/`AND`/`WITH` cases by taking the
head license for classification. For OR-licensed packages, this is
conservative — the package is usable under the most permissive
option, but the classifier flags the most restrictive one in the
expression.

## License families (broad classification — NOT legal advice)

| Family | Examples | Obligation |
|---|---|---|
| Public domain | CC0-1.0, Unlicense, 0BSD | None |
| Permissive | MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC | Attribution required; source disclosure NOT required |
| Weak copyleft | LGPL, MPL-2.0, EPL-2.0, CDDL-1.0 | Source disclosure of MODIFIED parts only; static-linking implications vary |
| Strong copyleft | GPL-2.0, GPL-3.0 | Source disclosure of the ENTIRE distributed work |
| Network copyleft | AGPL-3.0 | Source disclosure even when work is offered as a network service (no SaaS exception) |
| Custom / non-SPDX | "Proprietary", "Commercial", "All rights reserved" | Requires manual review; default copyright applies if no terms |
| Unknown | Empty license field, "UNKNOWN" | Requires investigation; default copyright applies |

The most-stepped-on case is **AGPL in a SaaS service**. AGPL was
designed specifically to close the "service" loophole in GPL: if
you offer GPL-licensed code as a network service, GPL doesn't
require source disclosure (you're not distributing). AGPL DOES.
This bites teams that pulled in AGPL deps thinking SaaS deployment
sidesteps the obligation.

## Copyleft contamination — the propagation model

Copyleft licenses include "viral" or "inheriting" clauses that
require any derivative work to be licensed under the same family.
The propagation rules vary by license:

- **GPL family** — propagates through static linking, dynamic linking, and code inclusion. A C library statically linked into your binary causes GPL inheritance.
- **LGPL family** — explicitly carves out an exception for dynamic linking, allowing LGPL libraries to be used by proprietary code at runtime.
- **MPL-2.0** — file-scoped copyleft; only modifications to MPL-licensed files trigger source disclosure, not the entire project.
- **EPL** — file-scoped, with patent grant.

For an interpreted language like Python or JavaScript, the
distinction between "static" and "dynamic" linking blurs.
Importing a GPL Python module into a non-GPL project arguably
creates a derivative work; conservative legal practice treats it
as GPL contamination.

## Common incompatibility pairs

The license-pair-incompatibility table is a minefield. Examples:

| Pair | Conflict |
|---|---|
| GPL-2.0-only + Apache-2.0 | GPLv2 has no patent grant; Apache-2.0's patent clauses conflict with GPLv2 terms. (GPLv3 resolves this.) |
| GPL-2.0-only + CDDL-1.0 | File-scoped vs project-scoped copyleft mutually incompatible. |
| MPL-1.1 + GPL-2.0-only | Old MPL (1.1) was not GPL-compatible; MPL-2.0 resolves it. |
| Apache-2.0 in GPL-2.0-only project | Apache patent termination clause incompatible with GPL-2.0. |

The skill flags known-incompatible pairs as HIGH severity. The
list is not exhaustive — true legal analysis requires counsel.

## When permissive licenses still create obligations

Even MIT and Apache-2.0 — the "permissive everything" licenses —
require:

- **Attribution.** The copyright notice and license text must
  travel with the redistributed code. Failure to attribute is
  technically a license violation.
- **NOTICE file for Apache-2.0.** If the project has a NOTICE
  file, distributors must include it.

For a binary distribution (compiled app, mobile app, Electron
desktop, Lambda zip), the attribution requirement still applies —
you must include LICENSE / NOTICE / equivalent. The `--emit-attribution`
flag in this skill auto-generates a NOTICE.md listing every
permissively-licensed dep.

## Service-only vs binary distribution

AGPL's obligation triggers on "service" use. For a SaaS product:

- **You use AGPL code internally for tooling** → no obligation
  (not distributed).
- **You use AGPL code in your service** → obligation: offer source
  to every user of the service.

For a binary product:

- **You include AGPL code** → obligation: source disclosure to
  every recipient of the binary.

Service-only deployment doesn't sidestep GPL, LGPL, or AGPL the
way some teams assume. The skill's CRITICAL findings flag this
explicitly when a project's stated `project_license` is
permissive but a dep is in the strong-copyleft family.

## Why "UNKNOWN" license is high-risk

A package with no license declaration is, by default, copyrighted
with all rights reserved. You technically have NO redistribution
rights. Even if the package is freely available on a public
registry, the absence of an explicit license doesn't grant you
permission to use it.

The skill flags UNKNOWN-license packages as MEDIUM severity. In
strict-compliance environments (regulated industries, government
contracts), MEDIUM should be promoted to HIGH.

## License-detection limitations

The skill reads metadata, not source. Specific failure modes:

1. **License declared incorrectly in metadata.** Some packages declare MIT in `package.json` but actually contain GPL code. Source-level inspection (e.g. ScanCode, FOSSology) is the gold standard.
2. **Multi-licensed packages with file-level variation.** Some packages have different licenses per file. Metadata captures the top-level intent but misses file-level exceptions.
3. **License changes between versions.** A package may switch from MIT to BUSL-1.1 in version N+1; if you pin to N you're under the old license. The skill audits the installed version.

For high-stakes legal posture (M&A, regulated products), pair this
skill with a source-level scanner.
