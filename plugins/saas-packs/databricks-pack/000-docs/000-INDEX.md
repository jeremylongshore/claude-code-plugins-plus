# 000-docs Index — databricks-pack

**Filing standard:** Document Filing System v4.3
**Last updated:** 2026-06-08 (added 014 CFO output sample, 015 v1.0 release checklist, 016 internal reference [local-only])
**Total docs:** 16

---

## BL — Business & Legal

| # | File | Description |
|---|---|---|
| 001 | `001-BL-LICN-license.txt` | MIT license |

## RL — Research & Learning

| # | File | Description |
|---|---|---|
| 002 | `002-RL-RSRC-databricks-compute-pain-research.md` | 12 pain entries: cluster lifecycle, Photon, DBR versioning, cost (citations from community.databricks.com, GH issues, KB, Medium) |
| 003 | `003-RL-RSRC-databricks-delta-streaming-research.md` | 12 pain entries: Delta Lake, Liquid Clustering, Structured Streaming, DLT |
| 004 | `004-RL-RSRC-databricks-uc-bundles-ops-research.md` | 10 pain entries: Unity Catalog migration, Asset Bundles, SCIM/SSO, secrets, networking |
| 005 | `005-RL-RSRC-anthropic-skill-architecture-patterns.md` | 10 patterns from Anthropic first-party skills (security-guidance plugin, feature-dev, mcp-builder) |
| 006 | `006-RL-RSRC-databricks-v2-rebuild-synthesis.md` | Synthesis: 34 pain entries → 5-skill + MCP architecture, CTO decisions, pilot recommendation |
| 010 | `010-RL-RSRC-databricks-mcp-official-landscape.md` | Walk of Databricks managed MCP servers (Genie, Vector Search, SQL, UC Functions) + custom/external paths + control-plane gap analysis |
| 011 | `011-RL-RSRC-databricks-mcp-community-landscape.md` | Community Databricks MCP inventory — confirms databrickslabs/mcp is deprecated, 5 community alts are 1-46 stars no-CI |
| 012 | `012-RL-RSRC-claude-code-databricks-mcp-integration.md` | How Claude Code / Cowork register Databricks MCPs; cowork-zip excludes category:mcp by design; dual-surface distribution implications |

## AT — Architecture & Technical

| # | File | Description |
|---|---|---|
| 007 | `007-AT-ADEC-databricks-v2-cto-decision.md` | Decision record: pack handling (v2.0.0 + deprecation lane), 5-skill scope, pilot, timing, demo arc |
| 013 | `013-AT-ADEC-epic1-mcp-scope-adjustment.md` | Epic 1 scope cut: drop T4/T5/T9 (subsumed by Databricks managed SQL MCP), expand T2 (3 auth flows), add T13 (App mode) + T14 (dual-surface helpers). Grounded in 010/011/012. |

**Repo-wide impact (filed at root):** Claude Code platform changelog impact lives in ` — affects validators, schema versioning, skill-creator, MCP validators, hook docs, the existing 414+ plugins, AND this databricks-pack rebuild as one downstream consumer.

## RA — Reports & Analysis

| # | File | Description |
|---|---|---|
| 008 | `008-RA-REVW-pack-handling-pressure-test.md` | Adversarial review of pack-handling decision — MODIFY verdict (add deprecation lane + tombstones) |
| 009 | `009-RA-REVW-pilot-timing-pressure-test.md` | Adversarial review of pilot/timing decision — MODIFY verdict (cut scope to 3 pains, MCP first, drop opus eval) |

## DR — Deliverables & References

| # | File | Description |
|---|---|---|
| 014 | `014-DR-REFF-databricks-cost-leak-hunter-sample-output.md` | CFO sample output for the cost-leak-hunter pilot — source-cited one-pager (live at demos.intentsolutions.io). For #790/#795 review. |

## AT — Architecture & Technical (cont.)

| # | File | Description |
|---|---|---|
| 015 | _(local-only)_ | **LOCAL-ONLY** — v1.0 release checklist (gates A–E); intentionally untracked while it references review context (not published) |

## RL — Research & Learning (cont.)

| # | File | Description |
|---|---|---|
| 016 | _(local-only)_ | **LOCAL-ONLY** — internal reference, intentionally untracked per the partner-internal policy (not published) |

---

## Quick reference — doc codes used

| CC | Category | ABCD | Type |
|---|---|---|---|
| BL | Business & Legal | LICN | License |
| RL | Research & Learning | RSRC | Research resource |
| AT | Architecture & Technical | ADEC | Architecture decision |
| AT | Architecture & Technical | PLAN | Plan / checklist |
| RA | Reports & Analysis | REVW | Review / critique |
| DR | Deliverables & References | REFF | Deliverable / reference artifact |
