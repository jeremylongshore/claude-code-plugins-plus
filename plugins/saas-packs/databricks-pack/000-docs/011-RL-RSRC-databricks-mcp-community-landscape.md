# Databricks MCP Server Community Landscape (2026)

## Executive Summary

The Databricks MCP ecosystem in 2026 is **fragmented between official Databricks-managed offerings and 4–5 lightweight community alternatives**, none of which are production-grade. The official Databricks AI Gateway is the only enterprise-safe path; community servers are weekend projects (1–46 stars, no CI/CD, minimal test coverage) suitable only for internal prototyping or hobbyist use. **Strategic recommendation:** consume official Databricks MCP for enterprise work; the gap for a truly comprehensive third-party MCP is significant and defensible.

---

## Catalog of Community MCPs

| Name | Author | URL | Stars | Last Update | License | Maturity | Primary Capabilities |
|------|--------|-----|-------|-------------|---------|----------|----------------------|
| **RafaelCartenet/mcp-databricks-server** | Rafael Cartenet | [GitHub](https://github.com/RafaelCartenet/mcp-databricks-server) | 40 | 2026 | MIT | Beta | UC metadata exploration, SQL execution, lineage analysis, notebook discovery |
| **JustTryAI/databricks-mcp-server** | JustTryAI | [GitHub](https://github.com/JustTryAI/databricks-mcp-server) | 46 | 2026 | MIT | Beta | Clusters, jobs, notebooks, SQL, file system, 80% test coverage target |
| **leminkhoa/databricks-mcp** | Leminkhoa | [GitHub](https://github.com/leminkhoa/databricks-mcp) | 1 | May 2025 (v0.0.1) | Unspecified | Alpha | Cluster mgmt, SQL warehouses, command execution, library install, workspace objects |
| **markov-kernel/databricks-mcp** | Markov Kernel | [GitHub](https://github.com/markov-kernel/databricks-mcp) | ~5 (estimated) | 2026 | Unspecified | Alpha | Clusters, jobs, notebooks, SQL execution |
| **JordiNeil/mcp-databricks-server** | JordiNeil | [GitHub](https://github.com/JordiNeil/mcp-databricks-server) | ~10 (estimated) | 2026 | Unspecified | Alpha | SQL queries, job listing, job status, data lakehouse bridge |
| **databrickslabs/mcp** (Official) | Databricks Labs | [GitHub](https://github.com/databrickslabs/mcp) | 89 | Recent | License present | **Deprecated** | UC functions, vector search, Genie spaces; **marked for migration to managed MCP** |

---

## Gap Analysis: What's NOT Covered

### Critical Operational Gaps

- **No cluster forensics tools** — no `clusters.events` streaming, no instance_pool diagnostics, no node-level debugging
- **No cost/billing instrumentation** — no `system.billing.usage` SQL wrapper, no cost attribution per job/cluster
- **No DLT pipeline diagnostics** — no pipeline state, update history, or failure forensics
- **No streaming observability** — no `system.streaming.query_progress`, no backlog metrics, no failure propagation
- **No warehouse health checks** — no query queue depth, no resource contention metrics, no query history analytics
- **No workspace governance tools** — no workspace-level permission audits, no object ownership tracking, no access review automation

### Quality/Completeness Gaps

- **No rate-limit handling** — community servers do no request throttling or backoff
- **No multi-tenant support** — all are designed for single personal/org token, not multi-customer isolation
- **No formal auth lifecycle** — no token rotation, no credential refresh, no secret management
- **No error recovery** — no retry logic, no circuit breakers, no graceful degradation on API failure
- **No observability hooks** — no request tracing, no error categorization, no audit logging for compliance

---

## Quality Assessment by Tier

### Tier 1: Production-Safe (Only Official)

**Databricks AI Gateway (Managed MCP)**

- Enterprise control plane with Unity Catalog enforcement
- Tested at scale by Databricks engineering
- Can delegate single-workspace operations to LLMs at acceptable risk
- **Use case:** internal Databricks operations, supervised workflows only

**Why the others don't qualify:**

- **RafaelCartenet** (40 ⭐): No releases, 1 open issue, no explicit CI, single contributor. Docker support is a plus. But 18 commits is thin for a Delta Lake integration.
- **JustTryAI** (46 ⭐): Has pytest harness + GitHub Actions (CI), 80% coverage target is good intention. But 9 commits, no actual releases, and no production deployment pattern documented. The higher star count is misleading.
- **leminkhoa** (1 ⭐): v0.0.1 from May 2025, zero forks, zero engagement. Orphaned.
- **databrickslabs/mcp** (89 ⭐, Official): Explicitly marked **DEPRECATED** — Databricks is actively discouraging its use in favor of managed MCP.

### Tier 2: Viable for Internal R&D

**RafaelCartenet** and **JustTryAI** are minimally viable for:

- Claude-assisted internal Databricks operations (cluster listings, SQL exploration)
- Proof-of-concept LLM→Databricks workflows
- Development/sandbox environments only, not production
- Single-token auth with a service principal (no user isolation)

### Tier 3: Do Not Use

**leminkhoa, markov-kernel, JordiNeil** — too early-stage, no signal of continued maintenance.

---

## Strategic Recommendation

### Option A: Consume Databricks Official ✅ (Recommended)

- **When:** You're building agent workflows that operate *within* a single Databricks workspace
- **Boundary:** Unity Catalog metadata, SQL warehouses, Genie spaces only
- **Advantage:** Zero risk, enterprise SLA, enforced permissions
- **Limitation:** Single-workspace scope; not suitable for multi-customer platforms

### Option B: Consume + Extend Community Server (Medium Risk)

- **When:** You need cluster/pipeline/streaming diagnostics that official MCP doesn't expose
- **Target:** RafaelCartenet/mcp-databricks-server (highest quality of the bunch)
- **Work required:** Add missing tools for cost, DLT, streaming; implement backoff/retry; add request tracing; write integration tests; establish release cadence
- **Risk:** Inherits single-contributor, no-CI, minimal-test baggage; you own quality assurance
- **Timeline:** 2–3 weeks to harden for internal use; 6–8 weeks for production readiness

### Option C: Build Our Own (Highest Upside) ✅ (Pragmatic)

- **Why:** The operational gaps (cost, DLT, streaming, forensics) are **real and unaddressed** by any community option
- **Differentiation:** Comprehensive observability + multi-account credential isolation + audit trail
- **Market:** Every Databricks shop running LLM agents will eventually need cost/perf diagnostics; position as the answer
- **Precedent:** This is what we built successfully with Nixtla integration
- **Scope:** 1 week for MVP (UC metadata + SQL + basic job diagnostics); 3–4 weeks for comprehensive set
- **Quality bar:** Match JustTryAI's intent (80%+ coverage, CI, releases) but cover the gaps they didn't

### Summary

**Consume official Databricks MCP for managed/governed workflows.** If you're building **agent-native operational tools** (cost attribution, failure root-cause, capacity planning), the community options are insufficient — **build your own** with the gaps above as the spec.

---

## Sources

- [Databricks MCP Documentation (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- [GitHub - RafaelCartenet/mcp-databricks-server](https://github.com/RafaelCartenet/mcp-databricks-server)
- [GitHub - JustTryAI/databricks-mcp-server](https://github.com/JustTryAI/databricks-mcp-server)
- [GitHub - databrickslabs/mcp](https://github.com/databrickslabs/mcp)
- [Truto Blog: Best MCP Server for Databricks in 2026](https://truto.one/blog/best-mcp-server-for-databricks-in-2026-give-ai-agents-secure-access-to-lakehouse-data/)
- [Atlan: MCP Server for Databricks](https://atlan.com/know/mcp/mcp-server-for-databricks/)
- [MCPServers.org - Databricks MCP](https://mcpservers.org/servers/databrickslabs/mcp)
- [Awesome MCP Servers](https://mcpservers.org/servers/RafaelCartenet/mcp-databricks-server)
- [Databricks Community: MCP Servers on Databricks](https://community.databricks.com/t5/community-articles/mcp-servers-on-databricks/td-p/153690)
