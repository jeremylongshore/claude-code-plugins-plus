---
title: "MCP Server Auth: The API Is the Real Boundary"
description: "Per-user tokens, a server-side write gate, and a separate access log — why an MCP server's client-side tool gate is UX, not a security boundary."
date: "2026-06-13"
tags: ["authentication", "ai-agents", "architecture", "typescript", "claude-code"]
featured: false
---
A single shared API key is fine right up until a second person uses it.

intent-brain — the system, repo `qmd-team-intent-kb`, renamed to the `intent-brain` plugin v0.4.0 this day — is a team knowledge base. A Fastify HTTP API sits over a governed memory corpus. In front of that API is an MCP server named `teamkb`, so a teammate doesn't open a dashboard or learn an endpoint. They ask in Claude Code and get a cited answer back with `qmd://` citations. That's the whole pitch: institutional memory you query in the same place you write code.

Up to this day it authenticated with one shared `TEAMKB_API_KEY`. The shared key has two failures that only show up once the tool has more than one user. First, every request looks identical, so the audit log can't say *who* asked. Second, revoking one person means rotating the key for everyone — there's no per-person handle to drop. Both are structural, not bugs you patch. You fix them by giving each person their own credential.

The work closed that gap with three things, in this order: per-user tokens (identity), a server-side write gate (authorization), and a per-read access log (audit). The through-line: the API is the real boundary. The MCP client-side tool gate is UX, not security. And the per-read access log stays separate from the governance audit trail — separate log, not no log.

## Identity: per-user tokens replace the shared key

`apps/api/src/auth/token-registry.ts`. Each token resolves to a record: `{ actor, role }`, where role is `'admin' | 'member'`. The shared key's two failures both dissolve here — every request now carries an `actor`, and revoking one person is dropping one record, not a team-wide rotation.

Tokens come from layered sources, in precedence order: explicit records → a `TEAMKB_TOKENS` JSON env → a `TEAMKB_TOKENS_FILE` (default `~/.teamkb/tokens.json`) → the legacy single `TEAMKB_API_KEY`, which becomes one admin token with actor `"shared"` for back-compat. Each entry is a bearer token resolved to an identity at request time. Malformed entries are skipped rather than crashing the boot. A record with no role defaults to `member` — least privilege, not most. In dev mode the registry is allowed to be empty and every request runs as actor `'dev'`; in production an empty registry **fails closed**.

The registry itself is small, and the interesting part is what it deliberately does *not* do:

```ts
export class InMemoryTokenRegistry implements TokenRegistry {
  private readonly records: ReadonlyArray<TokenRecord>;
  constructor(records: readonly TokenRecord[]) { this.records = records; }
  isEmpty(): boolean { return this.records.length === 0; }
  resolve(token: string): TokenIdentity | undefined {
    let found: TokenIdentity | undefined;
    for (const rec of this.records) {
      // Do not early-return on match — compare against all records so the
      // response time is independent of which (if any) token matched.
      if (timingSafeStrEq(rec.token, token)) {
        found = { actor: rec.actor, role: rec.role };
      }
    }
    return found;
  }
}
```

Two details earn their comment. The compare is constant-time (`timingSafeStrEq`) to blunt a timing attack — you don't leak token contents byte-by-byte through response timing. And `resolve()` does not early-return when it finds a match — it walks every record regardless. If it short-circuited on the first hit, a token that matched record one would resolve faster than a token that matched record fifty, and that timing delta tells an attacker something about which tokens exist and roughly where they sit. Looping the full list keeps response time independent of *which* token matched, or whether any did.

The auth middleware calls `resolve()`, then stamps `request.actor` and `request.role` onto the request. Everything downstream — the write gate, the access log — reads those two fields. Identity is established once, at the edge, and the rest of the stack trusts it.

## Authorization: a server-side write gate

`apps/api/src/middleware/write-gate.ts`. Members read and *propose*. Promoting a memory, transitioning its state, editing policy, and bulk import all require an admin token, or you get a 403. This is enforced as a Fastify `onRequest` hook that runs *after* auth has stamped `request.role`:

```ts
const ADMIN_WRITE_PREFIXES = ['/api/memories', '/api/policies', '/api/import'];
const MUTATION_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export function registerWriteGate(app: FastifyInstance): void {
  app.addHook('onRequest', async (request, reply) => {
    if (!MUTATION_METHODS.has(request.method)) return;
    const path = request.url.split('?')[0] ?? request.url;
    const isAdminWrite = ADMIN_WRITE_PREFIXES.some(
      (prefix) => path === prefix || path.startsWith(`${prefix}/`),
    );
    if (!isAdminWrite) return;
    if (request.role !== 'admin') {
      reply.status(403);
      throw new Error('This action requires an admin token. Members may read and propose; promoting, policy edits, and imports are admin-only.');
    }
  });
}
```

The gate keys on HTTP method *and* path prefix. A GET sails through untouched. A POST to a non-admin route sails through. A mutating method against `/api/memories`, `/api/policies`, or `/api/import` — exact match or any sub-path — has to clear the role check. This is the line where authorization actually happens. Not in the UI, not in the client. Here, in a hook that every request must pass, no matter how it arrived.

## The MCP client mirror is UX, not security

`apps/mcp-server/src/server.ts`. The MCP server mirrors the gate on its own side. Read tools — `teamkb_search`, `teamkb_status`, `teamkb_neighbors` — always register. Write tools register only for admin installs, switched on the same `canWrite` flag, which follows the same conditional-registration shape the server already used for its `withSync` flag (register a tool only when the capability behind it is actually available):

```ts
const canWrite = options.canWrite ?? config.role === 'admin';

// Read tools — always registered (members + admins)
server.tool('teamkb_search', /* ...cited retrieval... */);
server.tool('teamkb_status', /* ... */);
server.tool('teamkb_neighbors', /* ... */);

// Write tools — admin installs only ("Jeremy-only promote")
if (canWrite) {
  server.tool('teamkb_propose', /* ... */);
  // teamkb_import, teamkb_transition, vault_* ...
}
```

This is the heart of the thesis, so be blunt about what it is and isn't. Hiding a tool from the model is a UX affordance. It keeps members from being shown buttons they can't press — the model never proposes `teamkb_propose` to a member because the member's install never registered it. That's good product behavior. It is **not** a security control.

A member who knows the API exists can hand-craft the HTTP request — `curl`, a script, a second MCP client they configured themselves — and hit `/api/memories` directly. When they do, the MCP tool gate is irrelevant; it was never in the path. What stops them is the server-side write gate returning 403. The client gate and the server gate enforce the same rule, but only one of them is a boundary. If client gating were the *only* gate, you'd have security theater: a member who never touches the official client install is unconstrained.

The two gates exist for two different reasons. Server gate: nobody without an admin token mutates governed state, full stop. Client gate: members don't see tools that would only ever 403 anyway. Same rule, different jobs.

| Gate layer | What it does | Is it a security boundary? |
|---|---|---|
| **Server-side write gate** (HTTP `onRequest` hook) | 403s any unauthorized mutation, regardless of where the request came from | **Yes** — this is the actual boundary |
| **MCP client tool gate** (conditional registration) | Hides write tools so members aren't shown buttons they can't press | **No** — client code is user-controlled |

A member can bypass the client gate by hand-crafting an HTTP request. They cannot bypass the server gate — every request, from any client, has to clear it.

## Why not just hide the write tools and call it done?

This is the obvious approach, and it's worth naming exactly why it's wrong rather than waving at it. If you only gate the MCP client — register write tools for admins, hide them from members — you've shipped a system where security depends on every member using the official install and never reaching past it. The model is constrained, sure. But the model is not the attacker. The user behind the model is, and the user can talk to the API any way they like.

The MCP client is not the security boundary. The API is. Every credential the client holds, the user holds. Every endpoint the client calls, the user can call. The instant you treat "the tool isn't registered" as an access control, you've moved the enforcement to the one layer the user fully controls. Client gating with no server gate is theater. Server gating with no client gate works but shows members dead buttons. You want both, and you have to know which one is [load-bearing](/posts/honor-the-gate-when-the-verdict-is-inconvenient/).

## Audit: the access log is not the governance trail

`apps/api/src/routes/search.ts`. Every `POST /api/search` now emits a structured access-log line: who queried, what they queried, the scope, how many results, and the citations returned. The `actor` falls back to `'anonymous'`, but in production that branch should never fire — search sits behind the same auth middleware as everything else, and an empty registry fails closed. The fallback is belt-and-suspenders: a log line is still better than a thrown error if identity is somehow missing.

```ts
const result = await service.search(parsed.data);

// Per-read access audit. Deliberately a structured access-log line, NOT a
// governance AuditEvent — the hash-chained memory audit trail records
// governance state changes and must stay pure for `ico audit verify`.
request.log.info({
  event: 'query-access',
  actor: request.actor ?? 'anonymous',
  query: parsed.data.query,
  scope: parsed.data.scope,
  resultCount: result.totalCount,
  citations: result.hits.map((h) => h.citation).filter((c): c is string => typeof c === 'string'),
}, 'teamkb query');
```

The design decision here is the separation, and it's deliberate. intent-brain already has a governance audit trail: a hash-chained sequence of `AuditEvent` records that capture state changes — a memory promoted, a memory transitioned, a policy edited. That chain is verifiable; `ico audit verify` walks it and confirms nothing was inserted, dropped, or reordered. The chain's value comes from being *pure* — every link is a governed state change, and the hash linkage makes tampering detectable.

Reads are not state changes. If you folded "who searched for X" into the same chain, you'd be appending a high-volume read stream — every query, every teammate, all day — into a structure whose whole point is to stay small and verifiable. You'd bloat the chain and contaminate its semantics: `ico audit verify` would now be vouching for search traffic alongside governance events, and "what changed?" would be buried under "who looked." Two questions, two logs. *Who changed governed state?* is the hash chain. *Who queried what?* is the access log. Keeping them apart is what keeps each one answerable.

## Tradeoffs

The token registry is in-memory. Revoking a token or adding a teammate means editing the source (env, file, or records) and reloading the process — there's no live mutation API. At team scale that's the right amount of machinery: a restart is cheap, and the simplicity buys you an auditable, file-backed token list with no extra moving parts. When this outgrows a single team — when revocation has to be instant, or tokens should expire on their own — the reach is a backing store with short-lived tokens (refresh/rotation), not a bigger in-memory map. Name the ceiling now so the next person isn't surprised by it.

The legacy single-key fallback stays for back-compat: an existing `TEAMKB_API_KEY` keeps working as one admin token (actor `"shared"`). It's a migration ramp, not the destination. The shared-key failures it carries are exactly the ones the registry exists to fix, so it should be retired per-deployment once real tokens are issued.

## Verification

23 new tests landed: +13 on the token registry (precedence, malformed-entry skipping, role defaulting, dev-vs-prod empty behavior, the constant-time no-early-return path), +7 on the write gate (method × path-prefix matrix, member 403s, admin pass-through), and +3 on MCP role-gating. The MCP role-gating tests are the fun ones — a real in-memory MCP client lists available tools per role and asserts a member install never even *sees* `teamkb_propose` and friends. They prove the UX gate works as a UX gate. The write-gate tests are the ones that matter for security: they're what confirm the actual boundary 403s a member no matter how the request arrives. 200 api+mcp tests green.

## Also shipped

**cad-dxf-agent** got a real bring-your-own-provider story — the bundled Gemini/Vertex planner providers came out entirely, so "real AI" now means implementing the `PlannerProvider` interface and pointing `CAD_LLM_PROVIDER` at your own. It also relicensed MIT → Apache-2.0 and shipped a no-LLM `cad-analyze` CLI plus a marketplace-tier Claude Code plugin.

**intentsolutions-vps-runbook** cut notifications to Slack-only and actionable-only: routine health/uptime/backup/deploy-success events now page nobody — they're audit-logged and still visible in Netdata, but only high/urgent, security, and deploy-failure events interrupt anyone. Same day, AIDE got ripped out. It had been firing daily false positives on `node_modules`/container churn *and* had been misconfigured for a month, so even its security signal was dead — a noise source masquerading as a control.

**contributing-clanker** picked up two new gates: an engagement-frame check and a maintainer-URL-leakage check.

---

**Related posts:**

- [Green CI Proves Nothing: Why Your Tests Gate Zero Calls](/posts/when-green-ci-proves-nothing/)
- [Honor the Gate When the Verdict Is Inconvenient](/posts/honor-the-gate-when-the-verdict-is-inconvenient/)
- [When --cap-drop ALL Broke the Gate Socket](/posts/cap-drop-all-broke-the-gate-socket/)
