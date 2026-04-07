---
title: "Legal Toolkit, Epic Planning, and a Canary That Stopped Singing"
description: "A 12-skill legal toolkit with 5 parallel agents, a 117-bead execution plan reviewed by 6 auditors, and a canary CI pipeline that silently failed for 3 days. Trust but verify across three projects."
date: "2026-04-05"
tags: ["ai-agents", "claude-code", "ci-cd", "architecture", "testing", "authentication"]
featured: false
---
Three projects. Eleven commits. Every one of them is about the same thing: building systems that check their own work.

A legal toolkit that audits contracts against seven compliance frameworks. An execution plan reviewed by six specialized auditors before a single line of code ships. A canary CI pipeline that was supposed to catch failures but had been silently dead for three days. April 5th was a day about verification — and what happens when you skip it.

## The Legal Toolkit

Plugin #417 in claude-code-plugins is a 12-skill, 5-agent legal toolkit. Not a chatbot that says "consult a lawyer." An actual analysis system that reads contracts, identifies missing protections, generates documents, and audits compliance against GDPR, CCPA, ADA, PCI-DSS, CAN-SPAM, COPPA, and SOC 2.

The flagship skill is `contract-review`. It fans out to five parallel agents:

```
contract-review
├── legal-clauses      → Clause extraction and classification
├── legal-risks        → Risk identification and severity scoring
├── legal-compliance   → Framework-specific compliance gaps
├── legal-obligations  → Obligation extraction with deadline tracking
└── legal-recommendations → Remediation actions ranked by impact
```

Five agents running in parallel, each analyzing the same contract through a different lens. The clause agent finds what's there. The risk agent finds what's dangerous. The compliance agent checks against regulatory frameworks. The obligations agent extracts deadlines and deliverables. The recommendations agent synthesizes everything into prioritized actions.

The full skill roster covers the contract lifecycle:

| Skill | What it does |
|-------|-------------|
| `contract-review` | 5-agent parallel analysis |
| `risk-analysis` | Standalone risk scoring |
| `contract-compare` | Side-by-side diff of two contracts |
| `plain-english` | Translate legalese to readable language |
| `missing-protections` | Identify absent clauses |
| `freelancer-review` | Freelancer-specific contract analysis |
| `negotiate` | Suggest negotiation positions |
| `nda-generator` | Generate NDAs from parameters |
| `terms-generator` | Generate Terms of Service |
| `privacy-generator` | Generate privacy policies |
| `agreement-generator` | Generate general agreements |
| `compliance-audit` | Multi-framework compliance check |

The compliance audit skill is where the regulatory depth lives. It doesn't just check "is this GDPR compliant" as a binary. It walks the contract through framework-specific requirements: data processor agreements for GDPR, do-not-sell provisions for CCPA, WCAG conformance references for ADA, cardholder data clauses for PCI-DSS. Seven frameworks, each with their own checklist.

Sources matter for legal tooling. Every compliance check references authoritative sources: CommonPaper templates (CC BY 4.0), Bonterms standard agreements, ICO guidance for GDPR, the California AG's office for CCPA, FTC guidance, SCORE/SBA resources, IRS publications, W3C WCAG for accessibility, and PCI SSC documentation. The agent doesn't hallucinate legal requirements. It checks against published standards.

3,584 insertions across 22 files. That's the size of the initial commit. Twenty-two files is a lot for a single plugin, but the agent architecture demands it — each of the five agents has its own system prompt, its own output schema, and its own test fixtures. The skill files themselves are comparatively small. The bulk is in the agent definitions and the compliance framework checklists.

Enterprise validator score: 86.9/100. Solid but not exceptional. The gap to 95+ is mostly in the document generators — the NDA and Terms of Service generators produce structurally correct documents but lack the domain-specific edge cases that push a skill from "useful" to "authoritative." Future iterations will close that gap.

The namespace was immediately refactored from `legal-assistant` to `general-legal-assistant` to make room for future specialized variants — real-estate, startup, employment, IP. Each will share the same five-agent architecture with domain-specific knowledge bases and compliance frameworks swapped in.

A Legal & Compliance collection went up on the homepage grouping six plugins: the new general-legal-assistant plus gdpr-compliance-scanner, compliance-checker, pci-dss-validator, soc2-audit-helper, and data-privacy-scanner. Six plugins covering the compliance surface from contract-level review down to infrastructure-level scanning.

The same session also shipped an `agent-creator` skill — a meta-tool for building new agents. The agent template aligns with Anthropic's 2026 agent spec, the 16-field schema sourced directly from code.claude.com/docs. That one scored 98/100. When your template is derived from the platform vendor's own specification, the validator has very little to complain about. The agent-creator is how future legal variants will be scaffolded.

## The Dead Canary

Meanwhile in cad-dxf-agent, a canary CI pipeline had been failing for three days. Nobody noticed.

The canary runs on a schedule — a lightweight E2E test that fires every few hours to verify the deployed service still works. Authentication used Workload Identity Federation, which is Google Cloud's keyless auth mechanism for GitHub Actions. WIF trusts OIDC claims from GitHub. The problem: WIF was configured to trust claims from `push` and `pull_request` events. Scheduled runs emit a different OIDC claim. The canary authenticated against a claim type that WIF had never been told to accept.

Silent failure. The workflow ran. The auth step failed. No alert fired because the failure was in the auth preamble, not in the test itself. The canary's job is to tell you when the service is down. For three days, the canary was down and nobody knew the service status at all.

This is a specific gap in WIF's trust model. The OIDC token GitHub Actions generates includes a `job_workflow_ref` and an `event_name` claim. If your WIF pool's attribute condition filters on `event_name == "push"`, a `schedule` event gets a valid token that WIF correctly rejects. The workflow doesn't crash — the auth action fails gracefully. The subsequent steps either skip or fail with unhelpful permission errors.

The fix removed WIF from the canary entirely:

```yaml
# Before: WIF auth (only trusts push/pull_request OIDC claims)
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ vars.WIF_PROVIDER }}

# After: Firebase REST API auth (works on any trigger)
- name: Run canary tests
  env:
    E2E_TEST_EMAIL: ${{ secrets.E2E_TEST_EMAIL }}
    E2E_TEST_PASSWORD: ${{ secrets.E2E_TEST_PASSWORD }}
```

The canary doesn't need GCP service account permissions. It needs to hit the Firebase REST API as a test user. WIF was over-engineered for this use case. Simple email/password auth against the Firebase REST endpoint works on any GitHub Actions trigger — push, pull_request, schedule, workflow_dispatch. No OIDC claim issues. No silent failures.

The second fix in that commit was subtler. Manual control point alignment — where a user places corresponding points on two drawings to register them — was reporting 0% confidence. The alignment algorithm scored the user's control-point transform against full-drawing overlap metrics. When two drawings legitimately differ (which is the entire reason you're comparing them), the overlap score goes to zero. The math was correct. The metric was wrong.

The fix: confidence floor based on control-point fit quality. If the user places three control points and the affine transform fits them with sub-pixel residuals, trust the correspondence. The user is asserting "these points are the same." Score the quality of that assertion, not whether the rest of the drawing happens to overlap.

PR review caught one thing: single control point confidence was set to 0.7. The reviewer correctly flagged this as over-optimistic. One point gives you translation only — no rotation constraint. Confidence floor dropped to 0.5. Whitespace-tolerant grep was also added to the canary failure check, plus a "no results" guard for empty test output.

Six issues closed: #112, #133, #140, #142, #145, #153.

## 117 Beads, 6 Auditors, 53 Findings

intentional-cognition-os went from "we should plan this" to "the plan has been reviewed by six auditors and 53 findings have been addressed."

The execution plan: 10 epics, 117 child beads, 91 cross-epic dependencies. Each epic got its own reference document. The dependency graph maps which beads block which — you can't build the task lifecycle engine (epic-03) before the data model (epic-02), and you can't build the integration layer (epic-07) before both the API (epic-05) and the policy engine (epic-06) exist.

Then the plan went through a 6-auditor review. Not six humans. Six specialized audit perspectives:

1. **Architecture** — Does the system design hold up? Are the module boundaries correct?
2. **Security** — Prompt injection defense, API key redaction, SQL injection prevention, path traversal, audit trail integrity
3. **Risk/Dependencies** — Cross-epic dependency chains, critical path analysis, external dependency risk
4. **Test Strategy** — Integration test coverage, fixture tiers, regression guards, mutation testing readiness
5. **PM** — Task lifecycle reconciliation, concurrency policy, entity page gaps
6. **Documentation Consistency** — Do the 10 epic docs agree with each other and the summary?

53 findings. All addressed. Three new beads created from the audit. The security auditor found prompt injection vectors that needed defense-in-depth. The test strategy auditor identified a gap in cross-package integration tests — unit tests existed per package but nothing verified the packages worked together. The PM auditor caught an entity page gap and a task lifecycle state that wasn't reconciled across the epic docs.

This is the verification theme of the day distilled. The legal toolkit audits contracts against compliance frameworks. The canary CI audits deployed services against expected behavior. The 6-auditor review audits an execution plan against architectural, security, and operational standards. Different domains, same pattern: don't trust it until something independent has checked it.

## The Numbers

| Project | Commits | What shipped |
|---------|---------|-------------|
| claude-code-plugins | 6 | 12-skill legal toolkit, agent-creator, Legal & Compliance collection |
| cad-dxf-agent | 2 | Canary CI auth fix, confidence floor fix, 6 issues closed |
| intentional-cognition-os | 3 | 10-epic plan, 117 beads, 6-auditor review, v0.1.4 |
| **Total** | **11** | **Verification systems across all three projects** |

The dead canary is the one that sticks with me. Three days of silent failure. A monitoring system that wasn't being monitored. The legal toolkit checks contracts. The auditors check the plan. But who checks the checker? In this case, nobody — for three days. The fix is simple auth, but the lesson is older: every verification system needs its own verification. Turtles all the way down.

---

### Related Posts

- [Braves Booth v1 Release: Player Drilldown and Dashboard Polish](/posts/braves-booth-v1-release-player-drilldown/) — yesterday's v1 release with real-time broadcast dashboard
- [Shipping a CAD Agent from Zero: DXF Parsing, Edit Engines, and LLM Planner Interfaces](/posts/building-cad-dxf-agent-from-zero-to-v010/) — the cad-dxf-agent origin story, from empty repo to v0.1.0
- [Building Post-Compaction Recovery: Beads Issue Tracking from Scratch](/posts/building-post-compaction-recovery-beads/) — the beads system that tracks those 117 child tasks

