---
title: "Run the Readiness Audit Before You Flip DNS"
description: "An adversarial readiness audit found a payment-path bug that would have charged every customer, then returned HTTP 500 — before the irreversible DNS flip."
date: "2026-07-01"
tags: ["migration", "self-hosting", "devops", "testing", "stripe", "vps"]
featured: false
---
## The cutover that would have taken the money and then broken

The DiagnosticPro migration moved a live product off Firebase, Firestore, GCP, and Vertex AI onto a single self-hosted VPS. New database engine, new secrets model, new LLM client, new proxy, new deployment shape — the whole substrate replaced at once. The plan ended with the usual last step: flip `diagnosticpro.io` DNS from the old host to the new one and watch the traffic move over.

That last step is the one that cannot be un-done cheaply. The moment DNS propagates, real customers hit the new stack with real credit cards. Everything before that moment is reversible: the old host is still authoritative, rollback costs a config revert. Everything after it is a live incident.

So before the flip, the new stack was put through an *adversarial readiness audit*: not a smoke test against the happy path, but a deliberate, multi-lens attempt to find how the migration would fail in production — run against the deployed stack while the old host was still authoritative and rollback was still free. It found a failure, and it was the worst possible kind.

## The single most damning finding

The live VPS database was missing **every column the payment and membership write-paths depended on** — nine columns on the `submissions` table, three on the `analyses` table. The schema the code was written against and the schema actually deployed on the box had drifted apart.

Trace what that means through a real Stripe checkout:

1. Customer enters card details and completes checkout. **Stripe charges the card.**
2. Stripe fires `checkout.session.completed` to the webhook.
3. The webhook handler tries to write the submission row — including columns that do not exist on the live table.
4. The write throws. The handler returns **HTTP 500.**

The customer has already been charged. The system then errors out and cannot record the purchase, cannot queue the diagnostic, cannot deliver the report. This is the worst kind of failure: **the money moves, the system errors, and no record survives on either side.** Not a declined card, not a graceful "try again" — a completed charge followed by a server error, with no record on your side that the transaction happened.

Every single paid checkout after the DNS flip would have hit this. Not an edge case. The main revenue path, guaranteed to fail, on a stack that had already collected the customer's money.

### The fix: migrate the schema on boot, idempotently

The repair was not a one-time hand-run `ALTER TABLE` on the box — that fixes today's database and silently rots the next time a fresh environment comes up. The fix was to make the application **upgrade its own schema on startup**, so any database it boots against converges to the schema the code expects.

The migration reads the current shape of each table, compares it to what the code needs, and applies only the missing changes:

```js
function migrateSchema(db) {
  const cols = db.prepare("PRAGMA table_info(submissions)").all();
  const have = new Set(cols.map((c) => c.name));

  const wanted = {
    stripe_session_id: "TEXT",
    payment_status:    "TEXT",
    membership_tier:   "TEXT",
    // ...the rest of the drifted columns
  };

  for (const [name, type] of Object.entries(wanted)) {
    if (!have.has(name)) {
      db.exec(`ALTER TABLE submissions ADD COLUMN ${name} ${type}`);
    }
  }
}
```

`PRAGMA table_info` gives the current columns; the loop only issues `ALTER TABLE` for the ones that are absent. That `have.has(name)` guard is load-bearing: SQLite's `ALTER TABLE ADD COLUMN` has no `IF NOT EXISTS` clause before version 3.37, so it throws if the column is already there — the idempotency lives in the JavaScript check, not the SQL. Run it twice and the second pass is a clean no-op. A brand-new database converges to the full schema; an old drifted one gets exactly the missing columns added in place. (The `${name} ${type}` interpolation is safe only because both come from a hardcoded object in the same file — never substitute column names or types from untrusted input; SQLite won't bind them as parameters.)

Verified against the live VPS database, it applied **12 migrations in place** — the exact drift the audit had predicted, closed before a single customer touched the new stack. A regression test locks the behavior in: create an old-shape database, boot the app, assert the columns exist, boot again, assert the second boot is a clean no-op.

## What else the audit dragged into the light

The schema drift was the headline, but an irreversible cutover has more than one way to go wrong. The audit was multi-lens on purpose — many independent passes, several review angles, each finding adversarially re-verified rather than trusted on first sight. Several of the others were also invisible until someone actually paid.

**A GCP secrets client on a non-GCP host.** The code carried a Google Secret Manager client inherited from its Firebase/GCP life. On a GCP host that client silently uses the platform's identity. On a self-hosted VPS there is no GCP metadata server — so the client hunts for one, and that hunt can hang process startup while it waits on a network endpoint that will never answer. You inherit this hazard for free when you self-host code that assumed it was running inside Google's platform. The fix was an env-first secrets model: secrets materialized at deploy time from an encrypted store into the process environment, and the cloud SDKs removed entirely — `@google-cloud/secret-manager` and `google-auth-library` deleted, pruning **63 npm packages** from the install.

**A dead gateway URL on the success page.** The deployed frontend bundle was still calling a decommissioned GCP gateway host — a stale fallback URL baked into the post-payment success page. It would only fire *after* a customer paid, which is precisely why a normal click-through of the site never surfaced it. The path a paying customer takes is often the least-tested path on the whole site.

**A login guaranteed to throw.** The Whop login flow referenced an undeclared `membership` variable — residue from the deleted Firestore code path. Every login attempt would hit a `ReferenceError` and break. Not intermittent, not conditional: a guaranteed crash on a core flow, left behind by the migration itself.

**Webhook replay with no idempotency guard.** Stripe re-delivers webhooks; `checkout.session.completed` can arrive more than once for the same session. Without a guard, a duplicate delivery re-queues the diagnostic work and re-runs the LLM — double cost, double side effects. The fix keys on the session ID and treats any already-seen event as a no-op acknowledgement.

### Two testing traps the cold-CI sweep caught

The same discipline — replicate the real environment instead of trusting the local one — surfaced two test bugs a warm laptop hides:

**An exact-string environment gate.** The backend gates its mock-LLM path on the *exact* string `'true'`. The end-to-end test set `TEST_MOCK_LLM=1`. Environment variables are always strings in Node, so the gate compares `"1" !== 'true'` — the test would have driven a **real, keyless LLM call** and failed the full-flow run for a reason that had nothing to do with the code under test. The lesson is unforgiving and portable: know exactly which value your gate compares against. `"1"`, `"true"`, `"yes"`, and `true` are four different things, and a strict-equality check honors exactly one of them.

**"Passes locally" that CI never saw.** A `ts-jest` inline `tsconfig` omitted `lib`. TypeScript derives its default `lib` from `target`, and `target: es2022` defaults to `["ES2022"]` — which has no `DOM`. Locally the project-level `tsconfig` still supplied `DOM`, so compilation passed; the inline `ts-jest` config didn't inherit it, so CI type-checked against the bare `es2022` defaults and the DOM globals — `window`, `IntersectionObserver` — failed to resolve. The green checkmark on the laptop came from config the CI transform never read. The fix pinned `lib: ["ES2022", "DOM", "DOM.Iterable"]` and turned on `isolatedModules`. A related trap in the same suite: the Playwright job ran `vite preview` without building `dist` first, so the preview server errored with "directory dist does not exist." Both share a moral — **"it works on my machine" can quietly mean "it works with config and build artifacts CI never sees."** CI is cold and empty by design — which is exactly why an adversarial audit replicates the deploy environment instead of reading the code and trusting it.

## The remediation discipline

The audit ran **independent, adversarial review of the new stack before the irreversible step, while rollback was still free.** Many separate passes, several review lenses, every finding re-verified against the actual live artifacts rather than the code as written. The drift between "what the code assumes" and "what is actually deployed" is exactly the gap that a happy-path smoke test steps right over.

Finding the bugs was half the job. The other half was making sure they stayed fixed. Before the flip, a revenue-path test suite was installed and gated in CI:

- **7 backend test suites, 92 tests total.**
- **Stripe** — first delivery, replay/idempotency, signature validation, and the checkout-session contract.
- **Whop** — Standard-Webhooks verification, legacy HMAC, a length-mismatch path that must return 401, and the OAuth flow.
- **Reports routes**, plus a **rate-limit** test asserting the 11th submission returns 429.
- **Schema-migration regression** — old database upgrades cleanly, and a double boot is idempotent.
- **PDF generation** — output exceeds 10 KB and starts with the `%PDF-` header.
- **Backend coverage: 84.6% of lines, with a 60% floor gated in CI.**

The pre-remediation grade was recorded as **D+** in a `TEST_AUDIT.md`. That honest starting grade mattered: it named the gap in writing so the revenue-path P0s could be tracked and closed rather than waved through. By the flip, every revenue-path P0 was closed.

## The stack the audit ran against

For context on the scope of the drift, here is the substrate the traffic landed on — every layer new relative to the Firebase/GCP original, which is why nothing about the old deployment could be assumed to still hold:

- **SQLite via `better-sqlite3` in WAL mode** for the database, with the local filesystem for artifacts — no managed database, no object store.
- **OpenAI `gpt-4o` through an OpenAI-compatible client.** The old `callVertexAI` became `callLLM`; the provider is now a pure environment swap, not a code change.
- **Env-first secrets**, materialized from an encrypted (SOPS) source at deploy time — no cloud secrets SDK in the running process.
- **A multi-stage Dockerfile with docker-compose**, fronted by **Caddy** proxying `/api` on the VPS, on **Node 20.**
- **Firebase and Firestore deleted from the client entirely**, and every Google Cloud dependency removed.

The result: `diagnosticpro.io` DNS was flipped off Firebase and went live on the VPS on 2026-07-01.

## Before you flip DNS — a short checklist

Take this to your own cutover:

1. **Audit the deployed artifact, not the source.** The schema drift was invisible in the code — it lived in the gap between the repo and the live box. Point your verification at what is actually running.
2. **Walk the money path end to end.** The success page, the webhook write, the receipt — the paths a paying customer takes are often the least-exercised on the whole site, and the most expensive to get wrong.
3. **Grep the new host for assumptions from the old one.** Cloud SDKs, metadata-server calls, gateway URLs, identity clients — anything that quietly depended on the previous platform is now a boot hazard or a dead call.
4. **Make schema changes converge, not command.** A boot-time idempotent migration fixes every environment forever; a hand-run `ALTER TABLE` fixes exactly one database until the next fresh deploy rots it.
5. **Trust cold CI over a warm laptop.** "Passes locally" can mean "passes with config and build artifacts CI never sees." Run it clean before you believe it.

## The rule

The moment before an irreversible cutover is the **cheapest time you will ever have** to find catastrophic bugs. After the DNS flip, the schema drift is a live payment incident with charged customers and no records. Before it, it is a diff. The distance between those two costs is one adversarial audit of the new stack plus a revenue-path test suite — run while rollback is still nothing more than reverting a config. Buy the safety while it is free.
