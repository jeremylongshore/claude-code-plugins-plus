# THEORY — Why Transitive Vulnerability Tracing Matters

## The reachability problem

A modern dependency graph has hundreds to thousands of nodes. A CVE
attached to one of those nodes affects every transitive consumer.
The question "can this CVE actually be exploited in my code path?"
has three possible answers:

1. **Yes, directly** — the vulnerable code is loaded at runtime and
   reachable through normal program flow.
2. **Maybe** — the dep is loaded but its vulnerable function is
   only called in a configuration you don't use.
3. **No, but it's still on disk** — the vulnerable code is installed
   but never imported (test fixtures, lazy-loaded plugins, etc.).

Most audit tools (npm audit, pip-audit) answer "is the vulnerable
version installed?" — that's case 1+2+3 collapsed into a single
finding. This skill doesn't solve the reachability problem fully
(true reachability requires program analysis), but it does
distinguish *graph reachability* — which direct deps would have to
be touched to clear the finding.

## Why deep transitive depth is risky

A CVE at depth 0 (direct dep) is easy to remediate — bump the
version pin. A CVE at depth 1 (one parent away) is also easy —
bump that parent if it has a newer release, or pin the transitive
dep explicitly.

A CVE at depth 3+ becomes interesting:

- The relationship to your code is multi-step. The vulnerable
  function may not be reachable through any code path you use.
- Multiple direct deps may converge on the same vulnerable
  transitive — a bump in one direct dep doesn't necessarily clear
  the finding because another direct dep still pulls in the
  vulnerable version.
- The "blast radius" of the package is hard to estimate. Deep deps
  are often utility libraries (string parsers, date handlers,
  serializers) whose call graph touches everything.

The skill bumps deep-transitive findings to at-least HIGH severity
to surface this. The override-or-vendor decision is more often the
right answer at depth 3+ than at depth 1.

## Graph traversal and cycle handling

The skill's path tracer does a depth-first search from a target
package back through its parents to a direct dep. Cycles can occur:

- Package A depends on B, which depends on A (rare but real in npm)
- Self-references in poorly-published packages
- Optional peer-dep cycles where each declares the other

The tracer maintains a `visiting` set during traversal and breaks
on cycle detection. The reported depth is the shallowest path from
a direct dep — practically what an operator can target.

## SBOM standards

The Software Bill of Materials concept formalizes what this skill
builds locally. The major standards:

| Standard | Maintained by | Output | Strengths |
|---|---|---|---|
| CycloneDX | OWASP | JSON / XML / protobuf | Vulnerability mapping built-in |
| SPDX 3.0 | Linux Foundation | JSON-LD / RDF | License-aware; ISO/IEC 5962 standardization |
| SWID Tags | ISO/IEC 19770-2 | XML | Enterprise asset-management focused |

For a pentester's purposes, CycloneDX is the most practical because
it natively maps SBOMs to CVE findings via `vulnerabilities` arrays.
The skill currently builds an in-memory graph rather than emitting
a full CycloneDX BOM; emitting CycloneDX is a planned addition.

## Why this skill is graph-based, not query-based

An alternative implementation would query a vulnerability database
for each installed package. That approach has two failures:

1. Network round-trip per package — slow.
2. Stale results — the audit tool's CVE database may diverge from
   the query API.

The graph + intersect approach trusts the per-language audit tool's
output and adds the graph-walking layer locally. The audit tool's
authority is preserved; this skill is a triage assistant, not a
re-implementation.

## Exploit Prediction Scoring System (EPSS)

CVSS measures intrinsic severity; EPSS measures real-world
exploitation probability. A high-CVSS finding with low EPSS is
"theoretically severe but not actively exploited." A medium-CVSS
finding with high EPSS is "actively exploited despite a modest
intrinsic score."

The skill currently doesn't query EPSS; the per-language audit
skills can be extended to fetch EPSS via the FIRST.org API
(api.first.org/data/v1/epss) and pass through enrichment. Planned
integration via the `mcp__pen-tester-cve` MCP server.

## When override is safe, when it's not

The skill recommends `npm overrides` / pip pin / poetry constraint
for findings reachable via multiple direct deps. Conservative
operators worry about overrides because they can cause runtime
breakage. The risk profile:

| Situation | Override safety |
|---|---|
| Patch-version override (1.0.4 → 1.0.5) | Almost always safe; SemVer guarantees compatible API |
| Minor-version override (1.0.x → 1.1.x) | Usually safe; may introduce new APIs but shouldn't remove old |
| Major-version override (1.x.x → 2.x.x) | RISKY; major-version changes commonly break parent's API expectations |
| Pre-release override (1.0.4 → 2.0.0-beta) | RISKY in production; reserve for emergency CVE response |

The recommendation in the skill's remediation text defaults to
"check the parent's changelog and bump the parent if possible" —
that's the lower-risk path. Override is the escape hatch when
parent-bump isn't available.

## Why the "highest-leverage upgrade" recommendation matters

When an audit produces 20+ findings, the natural impulse is to fix
them in arbitrary order. The leverage report inverts that: identify
the single direct-dep bump that clears the most findings, do that
first, re-run, repeat.

This isn't novel — it's textbook gradient-descent applied to
dependency hygiene. But because audit tools don't natively
aggregate findings by direct-ancestor, most operators don't see the
shape of their CVE surface and end up fixing trivial findings while
missing the high-leverage one.

The skill computes the leverage map after path tracing, emits the
top-5 direct-dep upgrade candidates by count, and lets the operator
pick the order. The expected next step is a follow-up trace run
post-upgrade to confirm clearance.
