<!-- doc-class: record -->

---

filing_code: AT-ADEC-SECURITY-PACK-MCP-SERVER-BOUNDARY-2026-05-29
date: 2026-05-29
acting_head_of_board: Jeremy Longshore
status: locked
scope: plugins/packages/security-pro-pack/mcp/ (shared MCP server for security pack v2)
inputs:

- 000-docs/684-AT-PLAN-security-pack-option-c-uplift.md
- 000-docs/685-AT-ADEC-security-pack-option-c-scope.md
- Reference: plugins/saas-packs/langchain-py-pack/ (shared MCP at pack level)
- Reference: plugins/saas-packs/databricks-pack/ (planned shared MCP per pack v2 research docs 002-RL-RSRC through 006-RL-RSRC)
- MCP spec: 000-docs/anthropic-skills-spec-snapshot.md, validate-mcp skill references
  affects: 3 HEAVY plugins + umbrella + 4 SUBSTANTIAL plugins (all wire to one shared MCP server), Phase 2.3 implementation bead claude-md8s

---

# Security Pack Shared MCP Server — Boundary Decision

## Mission

The Option C plan calls for a shared MCP server at the pack level. This decision locks (a) the scope boundary (what the MCP serves vs. what stays in skill-side scripts), (b) the language/runtime choice, (c) the alternative of per-heavy-hitter MCP servers and why it was rejected.

## What goes IN the MCP server

The server exposes **reference-data lookup**: data that is large, slow to fetch, license-encumbered for redistribution, or otherwise unsuitable for embedding in every skill's references/ dir.

### Confirmed tools (v0.1.0)

1. **`cve_lookup(cve_id)`** → returns NVD details for a single CVE (description, CVSS, affected products, references, exploit availability).
2. **`cve_search(query, severity_floor, max_age_days)`** → returns matching CVEs from NVD feed. Used by scanners to enrich findings.
3. **`owasp_top10_get(year)`** → returns the canonical OWASP Top 10 list for a given year (2017, 2021, 2024) with category descriptions and example weaknesses.
4. **`control_crosswalk(source_framework, source_control_id, target_framework)`** → maps a control across frameworks (e.g. NIST SP 800-53 AC-2 → ISO 27001 A.9.2.1 → PCI DSS v4.0 Req 8.2 → HIPAA §164.308(a)(4) → GDPR Article 32 → SOC2 CC6.1). Returns the target-framework control(s) and a confidence score.
5. **`framework_list_controls(framework, family)`** → enumerates controls in a given framework family (e.g. NIST 800-53 family AC = Access Control).
6. **`attack_pattern_lookup(mitre_id)`** → returns Mitre ATT&CK technique details (T1190 → "Exploit Public-Facing Application" with sub-techniques, detections, mitigations).

### Future tools (v0.2.0+, not blocked by v2.0.0 cut)

- `cwe_lookup`, `epss_score` (exploit prediction), `kev_check` (CISA Known Exploited Vulnerabilities catalog), `nvd_recent_feed`, `osv_lookup` (Open Source Vulnerabilities).

## What stays OUT of the MCP server

The server is **read-only reference lookup**. The following remain in skill-side scripts because they perform mutations, execute against user systems, or are policy-decisions where the model needs to read source code:

- **Scanning execution** — `security_scanner.py` (penetration-tester), `dependency_check.sh` (dependency-checker), `jwt_analyzer.py` (authentication-validator). These run against the user's target and produce findings.
- **Report generation** — `generate_soc2_report.py` and equivalents. These compose findings into deliverables.
- **Configuration validation** — `validate_cors.py`, `audit_log_analyzer.py`. These read user-side configs and policy files.
- **Remediation suggestions** — model-side reasoning over scan findings + reference data. Not an MCP tool; it's the skill's prompt + tool-use pattern.

The rule: **if it reads a static reference (NVD/OWASP/ATT&CK/control crosswalks), it goes in the MCP. If it executes against user systems or composes user-specific output, it stays in skill scripts.**

## Per-heavy-hitter MCP servers — REJECTED

Considered: give penetration-tester, dependency-checker, authentication-validator each their own MCP server.

**Why rejected:**

1. **4 servers means 4 process startups** (umbrella + 3 individual) for a user running the full stack. ~1.5s additional startup per server = ~4.5s overhead.
2. **Duplicate code** — every server would need its own NVD client, OWASP cache, crosswalk dataset. Maintenance burden 4x.
3. **No domain-specific advantage** — none of the 3 HEAVY plugins needs lookup tools the others don't. They all want CVE/OWASP/ATT&CK/crosswalks.
4. **Future heavy-hitters multiply the problem.** If `cors-policy-validator` and `database-audit-logger` get promoted in Phase N, that's 5–6 MCP servers.

Single umbrella MCP wins on every axis. Plugins under the umbrella declare the dependency in their `plugin.json` `mcpServers` block, all pointing to the same server entry.

## Language / runtime choice — TypeScript

**Chosen:** TypeScript using `@modelcontextprotocol/sdk`.

**Why TypeScript:**

1. **Matches Anthropic's first-party MCP servers.** Most reference implementations in `modelcontextprotocol/servers` are TS. New contributors recognize the pattern.
2. **Faster cold start than Python** when the dependency tree is small. The server is mostly HTTP-fetch + JSON-shape transforms — perfect TS use case.
3. **Easier to vendor static lookup tables** as TS modules with types. CVE crosswalk → typed const struct, not a runtime SQLite open.
4. **Existing infra precedent** — the `claude-code-plugins` repo already builds MCP servers in TS at `plugins/mcp/*/src/` per the repo CLAUDE.md ("MCP server plugins: TypeScript source in src/, built to dist/index.js").

**Alternative (Python, rejected):** the skill scripts are Python. Could share types. But the MCP server doesn't share types with skill scripts — it serves a JSON-RPC API. Python would mean a longer cold start, no precedent in this repo, and a second build pipeline.

## File layout

```
plugins/packages/security-pro-pack/mcp/
├── package.json
├── tsconfig.json
├── src/
│ ├── index.ts # MCP server entrypoint
│ ├── tools/
│ │ ├── cve.ts # cve_lookup, cve_search
│ │ ├── owasp.ts # owasp_top10_get
│ │ ├── crosswalk.ts # control_crosswalk, framework_list_controls
│ │ └── mitre.ts # attack_pattern_lookup
│ ├── data/ # Static crosswalks shipped with the server
│ │ ├── nist-800-53.json
│ │ ├── iso-27001.json
│ │ ├── pci-dss-v4.json
│ │ ├── hipaa-security-rule.json
│ │ ├── gdpr-article-32.json
│ │ ├── soc2-tsc.json
│ │ └── crosswalks/<framework-pair>.json
│ ├── fetchers/ # External-API clients (NVD, OWASP feed, Mitre)
│ │ ├── nvd.ts
│ │ ├── owasp.ts
│ │ └── mitre.ts
│ └── cache/ # In-memory LRU + on-disk staleness check
└── dist/index.js # Built output, executable shebang
```

Build via `pnpm build` to produce `dist/index.js` per the repo MCP plugin convention.

## External-API dependencies

| External source | API                                                                                 | Auth                                   | Caching strategy                                                          |
| --------------- | ----------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------- |
| NVD CVE feed    | https://services.nvd.nist.gov/rest/json/cves/2.0                                    | optional API key (rate limit increase) | 24h TTL per CVE, persistent on-disk under ~/.cache/security-pro-pack/nvd/ |
| OWASP Top 10    | https://owasp.org/Top10/ (static JSON snapshots per year)                           | none                                   | shipped statically with the server; updated on minor version bumps        |
| Mitre ATT&CK    | <id>                                                                                | none                                   | 7d TTL persistent                                                         |
| CISA KEV        | https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | none                                   | 6h TTL persistent (high churn)                                            |

NVD API key (optional but recommended) is a config field, not a hardcoded secret. Per `plugin.json` `requiredEnvironmentVariables`:

```json
{
  "requiredEnvironmentVariables": [
    {
      "name": "NVD_API_KEY",
      "prompt": "Optional NVD API key (https://nvd.nist.gov/developers/request-an-api-key). Increases rate limit from 5/30s to 50/30s.",
      "optional": true
    }
  ]
}
```

## Validation / testing posture

1. **Unit tests** on each fetcher + each tool handler (mocked HTTP).
2. **Integration tests** that hit real NVD/Mitre with rate-limited fixtures (run in CI only on tagged releases, not every PR).
3. **`@intentsolutions/audit-harness`** installed per the Testing SOP.
4. **`validate-mcp` skill** runs on every PR — validates the `.mcp.json` schema and server announcement.
5. **Hash-pinning** for the static `data/*.json` files — schema bumps require re-hashing per the harness policy.

## Versioning

- `security-pro-pack/mcp` follows independent semver. v0.1.0 ships with security-pro-pack v2.0.0.
- Breaking changes to the MCP tool interface bump major; skill-level wires update at the same time.
- The MCP server is published as `@intentsolutions/security-pack-mcp` to npm (matches the audit-harness publication pattern).

## What this AT-ADEC does NOT decide

- **Per-skill MCP tool selection** — which skills use which MCP tools. That's skill-author judgment, locked per heavy-hitter promotion bead.
- **Future tool additions beyond v0.2.0** — incremental decisions; no AT-ADEC needed unless scope changes (e.g., adding write tools, which would re-open the read-only boundary).
- **External-API authentication for paid feeds** — not relevant for v0.1.0; all confirmed APIs are free-tier.

## Status

**LOCKED 2026-05-29.** Implementation in Phase 2.3 (bead `claude-md8s`).
