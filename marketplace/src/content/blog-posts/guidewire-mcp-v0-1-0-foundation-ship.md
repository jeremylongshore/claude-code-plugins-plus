---
title: "Guidewire MCP v0.1.0: Carrier-Native Server Blueprint"
description: "How v0.1.0 of guidewire-mcp-for-claude shipped six foundation packages, five carrier-vocabulary tools, and a 30k-word blueprint in one day."
date: "2026-05-04"
tags: ['mcp', 'enterprise-integration', 'guidewire', 'architecture', 'claude-code']
featured: false
---

[Guidewire MCP for Claude](https://github.com/jeremylongshore/guidewire-mcp-for-claude) v0.1.0 is a carrier-native [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that lets a Claude Code session ask a Guidewire PolicyCenter, BillingCenter, or ClaimCenter tenant questions in the language an underwriter or claims handler would actually use — `find-submissions-waiting-on-me`, `summarize-this-submission`, `did-we-lose-this-account` — instead of the API verbs an integration engineer would reach for. The v0.1.0 cut shipped on 2026-05-04 as 30 merged PRs (+14,521 / -819 lines), comprising six foundation packages, five read-only PolicyCenter tools, a Claude Code plugin manifest, and a live architecture diagram on a custom subdomain. Alongside the code, ~30k words of blueprint documents — business case, PRD, architecture, user journey, technical spec, roadmap — landed in `blueprint/` on the same day. (All 30 merged PRs are visible at [github.com/jeremylongshore/guidewire-mcp-for-claude/pulls?q=is%3Apr+is%3Amerged](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pulls?q=is%3Apr+is%3Amerged).)

The thesis: shipping a v0.1.0 carrier-native MCP server in one day is only possible when the blueprint, the foundation packages, and the safety harness are designed as one system from the start — not bolted on after. Each piece in the v0.1.0 cut depends on architectural decisions that were locked into the blueprint *before* any package code was written. That sequencing — design as an artifact, not a retrofit — is what made the parallel construction of six independently-versioned packages tractable on a one-day clock.

This post walks through what's actually in v0.1.0, how the blueprint set functions as load-bearing infrastructure rather than after-the-fact documentation, why the harness pattern (`plan → policy → approval → execute → audit → rollback`) is the spine of the entire writes story, and where the limits of the cut sit honestly. There is also a parallel sister-pack rebuild that landed the same day in a separate repo, which is worth covering because the two artifacts compose in ways that matter for anyone trying to ship enterprise integrations on a Claude Code substrate.

## What v0.1.0 actually contains

The v0.1.0 cut is best read as four concentric layers that correspond to the four epics opened in the roadmap: foundation (E1), read-only tools (E2), harness scaffold (E3), and on-disk profile loader (E4). The package boundaries are deliberate — each one stands alone, has its own README, owns its own tests, and is consumed only through its public exports.

| Layer | Artifact | What it does |
|---|---|---|
| E1 | `@gw/schemas` | Zod schemas for every Guidewire payload the runtime touches. Type errors become validation errors at the boundary, not crashes deep in tool code. |
| E1 | `@gw/observability` | OpenTelemetry tracing + pino structured logs + Sentry error sink. Wired in from day 1, defaulted off until the operator points them somewhere. |
| E1 | `@gw/auth` | Guidewire Hub OAuth client + JWT propagation. Actor identity flows through every tool call — there is no shared service-account key with read-all scopes. |
| E1 | `@gw/audit` | Postgres-backed audit log with hash-chain. Each row's hash includes the previous row's hash, so tampering is detectable. |
| E1 | `@gw/client-sdk` | Cloud API client built on undici. Two-key idempotency: client-side request key plus Cloud API native idempotency header. |
| E1 | `@gw/mcp-runtime` | MCP protocol implementation with both stdio and HTTP transports. Tools register themselves through a typed factory; runtime handles dispatch, validation, and observability. |
| E2 | 5 PolicyCenter tools | `find-submissions-waiting-on-me`, `show-policies-for-this-insured`, `summarize-this-submission`, `did-we-lose-this-account`, `pull-this-submission`. All read-only. All speak carrier vocabulary, not REST verbs. |
| E3 | Harness library + CLI | Plan / policy / approval / execute / audit / rollback pipeline. Skeleton in #80 — wiring real writes to this is E3+ work. |
| E4 | `--profile <path>` loader | On-disk profile scaffold (#75). Loads tenant connection details, role mappings, and per-tool overrides from a YAML file the operator maintains. |

Fifty-four tests pass across the foundation packages. The plugin manifest landed in #76, which means installation is a single command in any Claude Code session:

```bash
/plugin install jeremylongshore/guidewire-mcp-for-claude
```

Once installed, the runtime expects four environment variables to talk to a tenant:

```bash
export GUIDEWIRE_OAUTH_CLIENT_ID="your-client-id"
export GUIDEWIRE_OAUTH_CLIENT_SECRET="your-client-secret"
export GUIDEWIRE_TOKEN_ENDPOINT="https://<your-hub>.guidewire.net/oauth2/v1/token"
export GUIDEWIRE_PC_BASE_URL="https://<your-tenant>.pc.guidewire.net/pc/api"
```

A live architecture diagram of the whole stack is published at [guidewire-mcp.intentsolutions.io](https://guidewire-mcp.intentsolutions.io/) (PR [#53](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/53)). The page is itself a credibility artifact — the architecture is not just documented in markdown inside the repo, it is rendered as a public artifact a prospect can read without cloning anything.

## Carrier vocabulary as the dominant abstraction

The five tools in v0.1.0 are deliberately named the way an underwriter or claims handler would describe them in a hallway conversation, not the way a Cloud API endpoint is named. That is D-001 in the architecture document, and it is the most consequential design decision in the whole cut. Every other surface — the schema names in `@gw/schemas`, the registration API in `@gw/mcp-runtime`, the user-journey scenarios in `04-USER-JOURNEY.md` — derives from it.

The contrast matters. A naive MCP server over Guidewire would expose tools that map 1:1 to Cloud API operations: `get_submission`, `list_policies_by_account`, `get_account_by_producer_code`. That surface is technically correct and operationally useless. An underwriter does not think "I need to call `list_policies_by_account` with the producer code I derived from the agency lookup." An underwriter thinks "show me the policies for this insured." The vocabulary gap is the integration's value proposition.

Concretely, `find-submissions-waiting-on-me` is not a single Cloud API call. It is a composed query: fetch the operator's role, resolve the queues they're assigned to, fetch open submissions in those queues filtered by status `Pending Underwriter Review` or `Returned for Information`, sort by SLA breach risk, and return a structured summary. The composition logic lives inside the tool. The operator never sees the underlying Cloud API plumbing.

The Zod schema for the tool's response reflects the same vocabulary discipline:

```typescript
export const SubmissionWaitingOnMe = z.object({
  submissionNumber: z.string(),
  insuredName: z.string(),
  effectiveDate: z.string(),
  premiumEstimate: z.number().nullable(),
  daysWaitingForMe: z.number(),
  slaBreachIn: z.string().nullable(),
  whyItIsWaiting: z.enum([
    'pending-underwriter-review',
    'returned-for-information',
    'awaiting-broker-response',
  ]),
});
```

`whyItIsWaiting` is a denormalized, vocabulary-correct enum. The Cloud API exposes this as a status code with carrier-specific extensions — the schema flattens that into the three states an operator actually distinguishes between. Two months from now when the underwriter is asking "why is this one still on my plate," the answer comes back in their language.

This is also what makes the harness pattern feasible later. A write tool named `bind-this-quote-with-these-changes` can produce a plan that is reviewable by a human approver in *the operator's terms*. A write tool named `submit_quote_binding_request_with_overrides` produces a plan that requires translation. The vocabulary discipline at the read layer is what unlocks the approval UX at the write layer.

## The blueprint set is load-bearing infrastructure, not documentation

The instinct on a one-day ship is to skip docs and write code. That instinct is wrong here, and the structure of the day's commits shows why. The blueprint set landed *first*, as its own PR sequence, before the bulk of E1 package code merged:

| Doc | Words | PR |
|---|---|---|
| 01-BUSINESS-CASE.md | 3.0k | [#39](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/39) |
| 02-PRD.md | 8.2k | [#35](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/35) |
| 03-ARCHITECTURE.md | 5.3k | [#38](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/38) |
| 04-USER-JOURNEY.md | 5.4k | [#42](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/42) |
| 05-TECHNICAL-SPEC.md | 7.4k | [#41](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/41) |
| 07-ROADMAP.md + E2.5 sub-epic | — | [#30](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/30), [#43](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/43) |
| Phase 0 specialist memos | 16,963 | [#27](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/27) |

The blueprint pre-commits the architecture decisions — labeled [D-001 through D-022](https://github.com/jeremylongshore/guidewire-mcp-for-claude/blob/main/000-docs/004-DR-DEC-architecture-decisions.md) in `004-DR-DEC-architecture-decisions.md` and referenced by anchor link from `03-ARCHITECTURE.md` — that the package code then implements. Without that pre-commitment, six packages cannot be built in parallel, because each package's public surface depends on assumptions the other five also have to honor. The blueprint *is* the contract between the packages.

A concrete example: D-005 ("every write passes through plan → policy → approval → execute → audit → rollback hint") and D-006 ("HARD RULE: no audit, no write") together fix the shape of `@gw/audit`'s public API *and* the contract between `@gw/mcp-runtime` and the harness *and* the shape of every future write tool's signature. If those decisions had been deferred to "we'll figure it out when we get to writes," `@gw/audit` would have shipped with an API that the harness later had to adapt around. By writing the architecture document first and committing to D-005/D-006 explicitly, every downstream package was built against a stable contract.

The same pattern holds for D-001 (carrier vocabulary as the dominant abstraction) — that decision shapes the tool naming convention in `@gw/mcp-runtime`'s registration API, the schema names in `@gw/schemas`, and the user-journey scenarios in `04-USER-JOURNEY.md`. One decision, four files, all consistent because the decision was a written artifact before any of them got built.

The Phase 0 specialist memos (16,963 words across four memos) covered the harder questions that would have stalled package construction if discovered mid-build: which Guidewire APIs are actually stable across InsuranceSuite versions, what the real OAuth flow looks like with Hub, what the carrier-vocabulary mapping should be for the operator queries the PRD enumerates, and what the harness runtime needs to look like to support the eventual write surface. Those memos became the librarian KB entries `005-DR-REF-guidewire-public-resources` through `009-DR-MEMO-harness-runtime`, which means the same content is reachable both from the blueprint's narrative reading order and from the librarian's topic-keyed lookup. Two access paths, one source of truth.

## The five read-only tools, in operator language

The tools shipped in v0.1.0 cover the high-frequency PolicyCenter operator queries. Each one takes natural-language-ish parameters that match how an underwriter would describe the question, not how the Cloud API expresses it. A short tour:

**`find-submissions-waiting-on-me`** — the morning-coffee query. Returns the operator's queue of submissions where the next required action is theirs. The tool resolves the operator's role and queue assignments from the JWT, fetches the queue contents, and ranks results by SLA breach risk. No parameters needed beyond the implicit identity. Sample session interaction:

```
> use find-submissions-waiting-on-me

Found 7 submissions waiting on you:
  1. SUB-2398471 — Acme Manufacturing — 3 days waiting — SLA breach in 2 days
  2. SUB-2398502 — Bayside Logistics — 2 days waiting — returned for information
  ...
```

**`show-policies-for-this-insured`** — the account-context query. Takes an insured name or account number and returns the active policy book, including effective dates, premium, lines of business, and producer of record. Resolves the account first (with a fuzzy match that surfaces ambiguity rather than guessing), then pulls the policy list.

**`summarize-this-submission`** — the deep-dive query. Takes a submission number and returns a structured summary that an underwriter would want before opening the full submission UI: insured, broker, lines of business requested, current quote (if any), open underwriting questions, attachments, and the latest activity entry. The summary structure is pinned to the underwriter's mental model of "what do I need to decide about this submission?" not to the Cloud API's resource hierarchy.

**`did-we-lose-this-account`** — the loss-context query. Takes an account number or insured name and returns whether any of the account's submissions ended in `Not Taken` or `Declined` over the last N days, with the recorded reason. This is the kind of query that takes three or four Cloud API calls to assemble and that an underwriter asks several times a week — perfect candidate for a single tool.

**`pull-this-submission`** — the deep-fetch query. The escape hatch when the structured summary is not enough. Returns the full submission payload as the Cloud API renders it, with no flattening or vocabulary mapping. Useful for the rare case where the operator needs to see something the structured tools don't surface.

The five tools cover roughly 70% of the read-side queries enumerated in the PRD's user-journey section. The remaining 30% — the long-tail queries that BillingCenter and ClaimCenter operators run, plus the more specialized PolicyCenter queries around portfolio analysis and producer performance — are the E2.5 and E3 work. Five tools is enough to make the runtime useful for a real PolicyCenter operator from day one; it is not enough to be a complete operator workbench, and the README says so.

## The harness pattern: plan → policy → approval → execute → audit → rollback

Read-only tools are the easy part. The interesting design question is what happens when v0.2.0 starts adding write tools that can issue a quote, bind a policy, or post a payment. The harness pattern — scaffolded in [#80](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/80) — is the answer.

Every write call passes through six stages:

| Stage | What it does | Failure mode |
|---|---|---|
| **plan** | Tool produces a structured proposal of the intended change. No mutation yet. | Plan rejected → no write, no audit row needed. |
| **policy** | Policy engine evaluates the plan against tenant rules (role, dollar threshold, business hours, blackout dates). | Policy denial → no write, audit row records the denial. |
| **approval** | If policy requires human approval, the request is queued and the tool returns. Approval can come from another Claude Code session, a UI, or a Slack/email channel. | Timeout or denial → audit row records outcome, no write. |
| **execute** | Cloud API call with two-key idempotency. The plan's structure constrains what the executor is allowed to do — no off-plan side effects. | Cloud API error → audit row records full request/response, executor returns structured error. |
| **audit** | Append a hash-chained row to Postgres covering the actor, plan, policy decision, approval (if any), and the execute result. | Audit insert failure → **the entire write is rolled back**. No audit row, no completed write. |
| **rollback hint** | Tool returns a structured rollback descriptor the operator can later use to undo the change if something downstream goes wrong. | Tool may decline to provide a rollback (e.g., for irreversibly-bound policies) — the hint is then "manual reversal required" with full context. |

The hard rule from D-006 is the load-bearing one: **no audit, no write**. If the audit insert fails, the executor's state-change must not survive. In practice that means the executor wraps the Cloud API call and the audit insert in a coordination boundary — for non-transactional Cloud API endpoints, the rollback step has to fire to undo the executed change before reporting failure. The alternative — let writes happen with no audit row — would mean a tenant could accumulate state changes that have no provenance, which destroys the entire trust model.

Why is this pattern in v0.1.0 even though there are no write tools yet? Because the harness library has to exist, with its public API stable, before any write tool can be built. The scaffold landed in #80 as a deliberate pre-commitment. When the first write tool gets written, the harness contract is already there — the tool author cannot accidentally ship a tool that bypasses any stage, because the runtime's tool-registration API for write tools requires a plan/policy/audit hook set.

Karate adopted in [#79](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/79) covers the contract layer for the Cloud API client. Karate scenarios pin the request/response shapes of the underlying Cloud API endpoints, so that a Guidewire-side schema drift surfaces as a contract test failure rather than a runtime error in production. The contract layer is scaffolded but not yet exercised against a real tenant — that's E3+ work.

## Observability wired in, defaulted off

D-013 is one of the smaller-looking decisions in the architecture document and one of the most consequential in practice: observability is wired in from day 1, not bolted on. The `@gw/observability` package provides OpenTelemetry trace context, pino structured logs, and a Sentry error sink — and every tool call, every Cloud API request, every audit insert flows through those instruments by default.

The "defaulted off" half of the decision matters as much as the "wired in" half. The runtime ships with no OTel collector endpoint, no Sentry DSN, and pino's transport set to a local file. The instruments are alive but they are silent until the operator points them somewhere. A prospect cloning the repo and running it locally does not need to decide on an observability stack to make the runtime work — and the runtime is not phoning home through some default-on telemetry channel that would compromise the local-first trust story.

When the operator is ready, the standard OTel and Sentry environment variables turn the instruments on:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-collector:4318"
export SENTRY_DSN="https://your-sentry-key@sentry.io/your-project"
```

Bolting observability on later is the path the design avoided. A package that has no trace context at the boundaries cannot retroactively gain it without rewriting every call site. A package that does not log structured fields cannot retroactively gain them without changing every log line. Wiring observability through `@gw/observability` from the first commit means every package built on top of it inherits the same boundary instrumentation, with no per-package work.

The audit and observability layers are deliberately separate. The audit log is the legally-relevant record of what happened, lives in the customer's Postgres, and has a hash chain. The observability stack is the operational record of how things are running, lives wherever the operator points OTel and Sentry, and has no integrity guarantees. Conflating the two — using Sentry as the audit trail, for example — would be a category error: Sentry is for the operator running the system, not for the compliance team auditing it.

## Why local-first changes the OSS calculus

The trust model decision in `03-ARCHITECTURE.md` is short and consequential: the runtime is local-first and customer-hosted. There is no "Intent Solutions cloud" zone in the architecture. The OSS repo does not phone home. The audit database is in the customer's own Postgres. The tenant credentials live in the customer's own secret store. When a Claude Code session uses the MCP server, the only network traffic is between the session, the local MCP runtime, and the customer's own Guidewire tenant.

That decision changes what the OSS repo *does* in a sales motion. A vendor-hosted integration product would need a security-review cycle, a SOC 2 review, a legal review of the data-processing agreement, and a procurement cycle before any prospect could even try it. A local-first OSS repo collapses that to "clone the repo, point it at your sandbox tenant, run a tool against your own data." The credibility artifact is not a slide deck — it is the artifact itself, on the prospect's own machine, talking to their own tenant, with a public architecture diagram explaining exactly what it is and is not doing.

D-009 and D-010 in the architecture doc make this explicit: the OSS repo is not a complete product. It is a credibility artifact and a lead magnet for custom build engagements. The full carrier-specific build — the 39-tool catalog from the PRD, the harness wired to real writes, the on-disk profiles validated against a specific tenant's role model — is the engagement. The OSS repo is what convinces the prospect the engagement is worth scoping.

This is also why the JWT-propagated actor identity decision matters. Every tool call carries the operator's JWT, and the audit row records *who* asked. There is no shared service-account key whose audit trail collapses every action into "the integration did it." When a carrier's compliance team asks "who pulled this submission?", the answer is the actual human, not "the MCP server." That property is non-negotiable for any regulated insurance workload, and it had to be wired through `@gw/auth` from day 1 — adding it later would have required reworking every tool call's signature.

The two-key idempotency in `@gw/client-sdk` is a quieter but related decision. The client generates a deterministic request key from the tool call's plan (or, for read calls, from the canonicalized query parameters) and passes it both as a client-tracked dedup key and as the Cloud API's native idempotency header. If the same request retries — because the operator's session was interrupted, because the network blipped, because the harness's executor stage retried after a transient failure — the Cloud API recognizes the duplicate and returns the original response rather than executing the call twice. That property matters enormously for any future write tool: a retry that succeeds twice could double-bind a policy or double-post a payment. Wiring two-key idempotency into the SDK at v0.1.0, when there are no writes, is what makes write tools safe to add at v0.2.0 without a per-tool retry-safety review.

## The parallel sister-pack rebuild

A second thread ran in parallel the same day in [`claude-code-plugins-plus-skills`](https://github.com/jeremylongshore/claude-code-plugins-plus-skills): twelve commits rebuilt the `guidewire` skill pack to A-grade across every skill in the marketplace, prepared for the v4.30.0 release.

| Skill | PR | What changed |
|---|---|---|
| `install-auth` | [#668](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/668) | Production-grade Hub OAuth + tenant connection. |
| `sdk-patterns` | [#669](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/669) | Cloud API client patterns lifted to A-grade. |
| `local-dev-loop` | [#670](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/670) | Fast Gosu iteration loop for tenant-side rule changes. |
| `core-workflow-a` | [#671](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/671) | PolicyCenter end-to-end workflow. |
| `core-workflow-b` | [#672](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/672) | ClaimCenter end-to-end workflow. |
| `security-and-rbac` | [#673](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/673) | Merge of `security-basics` + `enterprise-rbac` — single source for RBAC patterns. |
| `observability-and-incident-response` | [#674](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/674) | Merge of three observability skills into one. |
| `ci-cd-pipeline` | [#675](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/675) | Merge of four CI/CD skills into a single coherent pipeline. |
| `webhooks-integrations` | [#676](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/676) | Renamed and deepened — covers the actual Guidewire webhook event shapes. |
| `migration-and-upgrade` | [#677](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/677) | Merge of two migration skills. |
| Pack v2.0.0 cleanup | [#678](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/678) | Pack-level metadata, version bump, README sync. |
| `chore(release): prepare v4.30.0` | `3a2d27d63` | Marketplace release prep. |

The two repos compose. The MCP server (`guidewire-mcp-for-claude`) is the runtime — the thing that talks to a tenant. The skill pack (`guidewire` in the marketplace) is the body of operator know-how — patterns for how to use the runtime, how to debug Guidewire integrations, how to set up CI/CD around a Cloud API project, how to think about RBAC on top of carrier identity. Installing both gives a Claude Code session the runtime *and* the operator playbook in one go. Neither one is sufficient on its own; together they're the carrier integrator's working environment.

The same-day timing matters. If the MCP server had shipped without the skill-pack rebuild, an operator installing the runtime would still have been operating against the previous pack's lower-grade material. Pulling both threads on the same clock means the v0.1.0 announcement carries both artifacts at once.

## What didn't ship — the limits of v0.1.0

Honest scoping. v0.1.0 is not the full product. The cut is deliberately a foundation, and it stops at well-defined boundaries:

- **All five tools are read-only.** No writes in v0.1.0. The harness scaffold exists; no tool uses it yet.
- **The Karate contract layer is scaffolded, not exercised.** A real run against a sandbox tenant is E2.5 work.
- **The `--profile <path>` loader is scaffolded, not validated against a real tenant.** The YAML schema is defined; the integration test that loads a profile and uses it to talk to a live sandbox is E4 follow-up.
- **The PRD's full 39-tool catalog is mostly future work.** Five tools is enough to make the runtime useful for the most common PolicyCenter operator queries; it is not enough to be a complete underwriting workbench.
- **BillingCenter and ClaimCenter tools are not in v0.1.0.** PolicyCenter only. The other centers have schema scaffolding in `@gw/schemas` but no live tools yet.
- **The audit hash-chain is not yet wired to an external anchor (e.g., periodic notarization).** Tampering is detectable within the chain, but the chain's tip is not yet anchored anywhere external. That's a v0.3.0+ concern.
- **No formal carrier reference deployment yet.** The runtime has been exercised against synthetic tenants and the public Guidewire developer sandbox shapes; a real carrier production deployment would require its own engagement.

These limits are stated in the README and in `07-ROADMAP.md`. A prospect reading the repo gets an accurate picture of where the line is between "shipped and usable" and "promised in the roadmap."

## Read-only first: the alternatives that lost

A reasonable critique of v0.1.0 is "five read-only tools is not very impressive — write tools are the real value." The critique is fair on its face and wrong on the substance. Read-only first was a deliberate choice over two alternatives, both of which would have produced a more impressive-looking v0.1.0 and a less defensible one.

**Alternative 1: ship one or two write tools to demonstrate the harness.** A v0.1.0 that includes `bind-this-quote` or `post-this-payment` would have been a louder announcement. It would also have required exercising the harness's policy stage, approval stage, and rollback stage against a real tenant — none of which the day's clock allowed. Shipping write tools without the harness fully exercised would have meant shipping write tools whose safety story was an unverified assertion. The credibility cost of that — particularly in a regulated insurance context — would have outweighed the announcement value.

**Alternative 2: ship the full PRD's 39-tool catalog as read-only stubs.** A v0.1.0 with 39 tools registered, even if most were unimplemented, would have looked like more progress on the catalog. It would also have meant shipping a surface that an operator could call and get back a "not yet implemented" error from. That is the kind of artifact that erodes trust: the prospect tries the tool that matters most to them, gets a stub error, and concludes the product is not real. Five tools that all work end-to-end against a real PolicyCenter shape are a stronger artifact than 39 tools where 34 are scaffolds.

The lesson generalizes: when shipping an enterprise integration on a one-day clock, the shape of the cut matters more than the surface area. A small, tight, fully working surface is a credibility artifact. A large, partial, mostly-stubbed surface is a credibility liability. Five working PolicyCenter tools is the right v0.1.0 cut for both.

## Tests as a precondition, not a follow-up

Fifty-four tests pass across the foundation packages in v0.1.0. That number is not a vanity metric — it is the gating condition for letting six packages ship together. Each foundation package has its own test suite covering its public surface in isolation, plus a small set of integration tests that exercise the contract between packages (e.g., that `@gw/mcp-runtime` correctly threads a JWT from `@gw/auth` into a tool call, that `@gw/audit`'s hash chain survives a write under load, that `@gw/client-sdk`'s idempotency keys are deterministic across retries).

The discipline that mattered: no foundation package was allowed to merge without its own README, its own tests, and its own CI green. A package that ships without tests becomes a package that other packages have to defensively wrap, which destroys the composition story. Holding the line at the package level — every package independently green — is what kept the parallel construction from collapsing into a tangled coupled mess at the end of the day.

The Karate contract layer is the next rung up. Once it is exercised against a real sandbox tenant, a Cloud API schema drift will surface as a contract test failure during CI rather than as a production runtime error against a customer's tenant. That gap between "shipped contract layer" and "exercised contract layer" is named explicitly in the roadmap so an operator reading the repo knows what coverage they actually have.

## The audit register closed the same day

The audit follow-ups from the GW-1.9 register all closed the same day across four themes:

- [#74](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/74): manifest schema cluster — tightened the plugin manifest schema and resolved drift between declared and actual capabilities.
- [#78](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/78): audit-DB role separation — the role that writes audit rows has insert-only privilege, separate from the role that reads them.
- [#73](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/73): doc-set hygiene — cross-reference fixes and stale-link cleanup across the blueprint set.
- [#81](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/81): final theme — closed the rest of the GW-1.9 register.

A separate librarian-audit fix landed in [#44](https://github.com/jeremylongshore/guidewire-mcp-for-claude/pull/44): D-016, a rename-lag patch applied across the PRD and memos so that a terminology rename done mid-day did not leave a half-renamed surface for later readers to trip on. The whole GW-1.9 register went to zero open items by end of day.

The librarian KB itself deserves a moment. The five memos — `005-DR-REF-guidewire-public-resources` (the catalog of public Guidewire reference material worth pinning), `006-DR-MEMO-mcp-safety` (the safety patterns that informed the harness), `007-DR-MEMO-carrier-vocabulary` (the vocabulary mapping that became D-001), `008-DR-MEMO-guidewire-api` (the Cloud API surface analysis that informed the SDK), and `009-DR-MEMO-harness-runtime` (the harness runtime design that became E3) — are reachable both through the blueprint's narrative reading order and through the librarian's topic-keyed index. That dual access matters because the blueprint is the right entry point for a new contributor reading the architecture top-down, and the librarian KB is the right entry point for a contributor who needs to re-find a specific decision later. Same content, two indexes, no duplication.

Closing the audit register the same day the cut shipped matters because an audit register left open is a known-bad signal to anyone reading the repo as a credibility artifact. A v0.1.0 with zero open audit items is a different artifact from a v0.1.0 with a backlog of "we'll fix this later" items. The operator reading the repo can take it at face value.

## The implication for shipping enterprise integrations

The composability of the v0.1.0 cut is the point. The architecture decisions, the package boundaries, the harness pattern, the audit semantics, the JWT propagation — none of these were retrofitted. Each one was a written commitment in the blueprint before any package code merged, which is what made the parallel construction tractable.

For anyone trying to ship enterprise integrations on a similar clock, the pattern that travels:

1. **Write the architecture as a committed artifact before writing the packages.** Decisions like "actor identity propagates through every call" or "audit failure rolls back the write" cannot be retrofitted without reworking every tool. Pre-commit them in writing.
2. **Make the design doc the contract between packages.** Six packages cannot be built in parallel unless the contract between them is locked into a document everyone can read. The blueprint isn't a deliverable; it's the substrate.
3. **Scaffold the safety pattern even when you have no writes yet.** A harness library that exists in v0.1.0 with zero callers is a hard constraint on every future write tool. A harness library that doesn't exist is a constraint on nothing.
4. **Local-first changes the sales motion.** A repo that runs entirely on the prospect's own infrastructure collapses the procurement cycle. The architecture decision and the go-to-market motion are the same decision.
5. **Compose runtime and operator know-how on the same release clock.** The MCP server and the skill pack are the same product viewed from two angles. Shipping one without the other ships half a product.
6. **Pick the cut shape that earns trust, not the cut shape that maximizes surface.** Five working tools beat thirty-nine stubs. A foundation that holds beats a feature that breaks. The shape of the v0.1.0 cut is the prospect's first impression of what the product *is* — make that impression accurate.
7. **Close the audit register the same day.** A v0.1.0 with a backlog of "we'll fix this later" items is a different artifact from a v0.1.0 with zero open items. Operators reading the repo as a credibility artifact can take the second one at face value and have to discount the first.

The v0.1.0 cut is foundation work — by design. The real test is whether the foundation holds when v0.2.0 starts wiring real writes through the harness and the first carrier-side engagement starts pressure-testing the on-disk profile loader against a live tenant role model. Three things are likely to surface:

- **Policy expressiveness.** The harness's policy stage will need to express tenant rules that don't reduce to "role + dollar threshold." Real carrier rules involve combinations of underwriting authority, line of business, geographic restrictions, treaty constraints, and time-of-day. The policy language has to be expressive enough to encode those without becoming a Turing-complete DSL nobody can review.
- **Profile schema durability.** The `--profile` YAML schema is opinionated about how tenant connection details, role mappings, and per-tool overrides are structured. The first real tenant may push on that schema in ways the synthetic test fixtures didn't predict. Schema versioning is in place; schema migration is not yet rehearsed against a live profile.
- **Audit-row volume.** The hash-chain audit table works fine at low volume. At a real carrier's submission flow rate, the chain's tip-anchor question becomes pressing, and the read query patterns for the compliance team's audit access surface real index requirements. Both are anticipated in the roadmap; neither is exercised yet.

Each of those is a known unknown that the v0.1.0 foundation was deliberately built to allow room for. None of them require rewriting the package boundaries. That property — extensibility at the seams that matter — is the test of whether the architecture decisions held up. The next post in this arc covers that test when it happens.

The carrier-native vocabulary discipline, the harness pattern, the local-first trust model, the audit-as-precondition rule — none of these are novel in isolation. The composition is what's load-bearing. v0.1.0 ships with all of them already wired together because the blueprint forced the wiring decisions to land before the code did. Anyone reaching for the same shape on a similar clock will benefit from doing the blueprint work first, even when the instinct is to skip it and start coding.

The repo is at [github.com/jeremylongshore/guidewire-mcp-for-claude](https://github.com/jeremylongshore/guidewire-mcp-for-claude). The architecture diagram is at [guidewire-mcp.intentsolutions.io](https://guidewire-mcp.intentsolutions.io/). Plugin install is `/plugin install jeremylongshore/guidewire-mcp-for-claude` from any Claude Code session. Sandbox tenant credentials are required to exercise the tools end-to-end; the README documents the four environment variables and points to the Guidewire developer portal for sandbox provisioning.

Issue tracker, blueprint set, and roadmap are all in the repo. The next cut is E2.5 (BillingCenter and ClaimCenter read tools) plus the first harness-wired write tool, on a clock that is yet to be named.

## Related Posts

- [Claude Code Plugin Marketplace Launch](/blog/claude-code-plugin-marketplace-launch/) — the marketplace this plugin and its sister-pack ship through
- [Building a Production-Ready Research Tool That Outperforms Anthropic's](/blog/building-production-ready-research-tool-outperforms-anthropic/) — another MCP-fronted system, different domain
- [IRSB Ecosystem](/irsb-ecosystem/) — companion ecosystem hub for the broader Intent Solutions integration story
