---
title: "Photo to Listing: Barcode Decoding and LLM Re-rank"
description: "Exact issue identification is retrieval work, not vision work. How a photo to listing pipeline puts the LLM in the re-rank seat behind an evidence gate."
date: "2026-09-01"
tags: ["architecture", "ai-agents", "typescript", "testing"]
featured: false
canonical: "https://startaitools.com/posts/barcode-first-vision-model-second/"
---
A comic shop employee photographs a back issue on a phone. The system has to come back with the right title, the right issue number, and the right variant, because a first-print variant and a common reprint of the same book are the same picture with different economics. That is the identification problem in **intent-longbox**, a photo to listing pipeline that ended 2026-09-01 at v0.2.1 after eleven commits.

The research that preceded the build settled the architecture in one finding: LLM vision alone is not viable for issue-exact and variant-exact identification. Every incumbent that actually works in this space runs image-similarity retrieval against a reference cover corpus. The model is a ranker, never the source of truth.

So the pipeline puts the [deterministic parts first](https://startaitools.com/posts/llm-legible-deterministic-architecture/).

```
barcode decode → candidate retrieval → LLM re-rank → human confirm → condition + price → Shopify draft
```

Nothing publishes without a person. The Shopify product lands as a DRAFT for owner review. The pilot shop is Gotham City Limit, running free.

The deterministic front of that chain is a barcode parser with no model in it at all. Post-1990 comics carry a 12-digit UPC-A that identifies the series, plus a 5-digit UPC supplement encoding issue, cover variant, and printing:

```ts
const supp = digits.slice(12);
return {
  ok: true,
  upc,
  supplement: {
    raw: supp,
    issue: Number(supp.slice(0, 3)),
    cover: Number(supp[3]),
    printing: Number(supp[4]),
  },
};
```

When that supplement is readable, the variant question is already answered by arithmetic. The model never gets asked.

The honest version of that diagram is that the retrieval leg is not built yet. v0 ships barcode plus vision plus human pick, with no similarity index behind the candidate step. So a barcode miss (pre-1990 stock, a damaged code, a variant with no UPC) falls to vision plus the gate below plus a mandatory human confirmation, which is the weakest path in the system and the one the pilot is meant to measure. That gap is tracked as the project's top open decision, not as a solved problem.

## The database refuses to mutate

Every event in a scan session is a separate immutable row, which makes the table an audit trail rather than a current-state cache. `scan_session` is the identity. `candidate_set` holds the deterministic result (barcode decode plus similarity k-NN, FK'd to a `corpus_version`). `llm_rerank` holds the probabilistic value: provider, model, prompt hash, the verbatim response, confidence, band, contradiction flag, tokens, cost. It annotates the candidate set. It cannot edit it.

Then `human_confirmation`, `condition_assessment`, `pricing_snapshot`, `shopify_draft`, `cost_log`. Every shop-scoped table carries `shop_id`. The only UPDATE anywhere in the codebase is on `scan_session.status`.

The obvious way to enforce append-only is code discipline. Write no UPDATE statements, review for them, move on. I rejected that, because it holds exactly as long as every future query is well behaved. A migration script, a hotfix, or one psql session at two in the morning ends the guarantee quietly, and the tell is that the audit trail looks fine afterward.

So the rule lives in the database:

```sql
CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'table % is append-only (Hickey model): % not allowed', TG_TABLE_NAME, TG_OP;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'corpus_version','scan_photo','candidate_set','llm_rerank','human_confirmation',
    'condition_assessment','pricing_snapshot','shopify_draft','cost_log'
  ] LOOP
    EXECUTE format(
      'CREATE TRIGGER %I_append_only BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_mutation()',
      t, t);
  END LOOP;
END $$;
```

Verified against a real Postgres, not asserted in a comment. An UPDATE on `cost_log` raises `table cost_log is append-only (Hickey model)`.

One more schema decision belongs here. Condition is a grade range label, and no numeric grade type exists anywhere in the schema, the API, the prompts, or the UI copy:

```sql
grade_range_low  text NOT NULL CHECK (grade_range_low  IN ('PR','FR','GD','VG','FN','VF','NM')),
grade_range_high text NOT NULL CHECK (grade_range_high IN ('PR','FR','GD','VG','FN','VF','NM')),
```

A 9.4 is a claim a phone photo does not entitle anyone to make. If the type does not exist, nobody adds it later under deadline pressure.

## The evidence contradiction gate

Confidence scores from a model are self-reported. Asking for one and thresholding on it is the cheap version of a quality gate, and it fails in the direction you care about, because a model is most fluent when it is wrong about a plausible thing.

The `VisionProvider` interface therefore requires structured evidence alongside the answer:

```ts
/** REQUIRED structured evidence. The contradiction gate's raw material (R7). */
export interface Evidence {
  issue_number_read: string | null;
  price_box_text: string | null;
  logo_era_guess: string | null;
}
```

The prompt states the same requirement in the model's own terms:

```
- evidence fields are REQUIRED: report exactly what you can read on the cover
  (issue number printed, cover price box text, publisher logo era guess).
  Use null only when genuinely unreadable.
```

Now there is something to check. `src/services/rerank.ts` cross-validates each field against the top candidate's metadata. Issue number read against the candidate's issue. Cover price against a coarse US newsstand era table. Logo era decade against the candidate year:

```ts
if (evidence.price_box_text !== null && top.year !== undefined) {
  const priceMatch = evidence.price_box_text.match(/(\d+)\s*[¢c]|\$\s*(\d+(?:\.\d{1,2})?)/);
  if (priceMatch) {
    const cents =
      priceMatch[1] !== undefined ? Number(priceMatch[1]) : Math.round(Number(priceMatch[2]) * 100);
    const era = priceEraBounds(cents);
    if (era && (top.year < era.min || top.year > era.max)) {
      reasons.push(
        `price_box_text "${evidence.price_box_text}" implies ~${era.min}-${era.max}, contradicts candidate year ${top.year}`
      );
    }
  }
}
```

The era bounds are deliberately loose. The gate catches decade-scale misses and does not quibble about a two-year overlap.

A contradiction then costs the model its fast path:

```ts
export function applyContradiction(band: Band, contradiction: boolean): Band {
  if (!contradiction) return band;
  return band === "high" ? "medium" : band;
}
```

Three bands drive the phone UI. High is a one-tap confirm. Medium is a candidate grid with a forced pick. Low is manual search. Downgrading high to medium means a confident but self-contradicting answer costs the employee one extra tap instead of putting a wrong book into inventory.

The transferable piece has nothing to do with comics. Do not ask a model how sure it is. Make it report the specific things it read, then check those against something deterministic you already trust.

Seeded cases in the test suite all flag and downgrade: a wrong issue number read, a twelve cent price box on a 1988 book, a 1960s logo on a modern year.

The provider seam behind that gate is a [bring your own key provider architecture](https://startaitools.com/posts/the-moat-is-the-trust-layer-nexus-byok-rag/) per shop, with an Anthropic adapter (Messages API, image blocks, `claude-sonnet-5` as default and reference model) and an OpenAI-compatible adapter (chat completions, `image_url` data URIs). Resolution order is a gateway override first, then a shop credential row whose `key_ref` names an env var, then a global env fallback. Raw keys never enter the database, only refs to env var names. Two pieces of reliability lore carried over from the estate's existing provider registry shape in `@intentsolutions/refiner` and the Transport seam in `@intentsolutions/jrig-cli`: a 2048 max-output-token floor, and a parser that strips `<think>` blocks before it goes looking for JSON.

## One snapshot per source, and no source can block

The 23:56 commit added a second seam. A `PricingProvider` declares a `source`, a `kind` of `live_asks` or `historical_fmv`, and returns comps plus a low/median/high summary plus `fetched_at` plus a stub flag. Two adapters implement it: a new eBay Browse adapter (OAuth2 client-credentials app token, cached until near expiry, query built from title, issue number, and variant against the comics category) and PriceCharting refined behind the same interface.

Two decisions in that step went against the obvious version.

First, provider isolation over sequencing. Calling two pricing APIs in a row is simpler to write and means the second one never runs when the first one has a bad morning:

```ts
const settled = await Promise.allSettled(args.providers.map((p) => p.getComps(args.query, shopCtx)));
```

A failed source is reported in the outcome list with its error and writes no snapshot row, because nothing was fetched. The other source still prices the book.

Second, one snapshot row per source, with the overall suggestion stamped on every row:

```ts
for (const result of fulfilled) {
  const res = await db.query(
    `INSERT INTO pricing_snapshot
       (scan_session_id, shop_id, source, query, comps, suggested_cents, override_cents, policy_id, fetched_at)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id`,
    [
      args.sessionId,
      args.shopId,
      result.source,
      queryText,
      JSON.stringify(result.comps),
      suggested,
      args.overrideCents ?? null,
      args.policyId,
      result.fetched_at,
    ]
  );
}
```

Per-source suggested prices would have been more honest-looking and worse to consume. The draft step would have needed to know which source wins before it could read a price, which is ordering ambiguity in a table that no one is allowed to correct afterward. Stamping the overall figure on every row keeps one rule for the draft step: the latest snapshot carries the price of record.

Precedence is fixed rather than clever:

```ts
export function pickDrivingResult(results: PricingResult[]): PricingResult | undefined {
  const real = (r: PricingResult) => !r.stub && r.comps.length > 0;
  return (
    results.find((r) => r.kind === "historical_fmv" && real(r)) ??
    results.find((r) => r.kind === "live_asks" && real(r)) ??
    results.find(real)
  );
}
```

Historical fair market value beats live asking prices, because an ask is a wish. When neither source has real comps, the shop's policy floor wins. The UI shows both sources side by side, highlights the driving one, and labels stubs as stubs.

## Governance, tests, and the release cycle

Governance came first, at 18:07, through the `/repo-dress` pass: LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SUPPORT.md, AGENTS.md, CI. The 18:12 commit authored the six master planning docs (business case, PRD with R1 through R20 MoSCoW-tagged, architecture, user journeys, technical spec, status) alongside the index and the project CLAUDE.md, which brought `000-docs/` to eight filed documents with the competitor analysis and the approved build plan already in the tree. Then an isolated beads workspace with prefix `longbox`. Five automated release commits took version.txt from v0.1.0 to v0.2.1.

The API is shop-scoped by path prefix, `/api/shops/:shopId/scan-sessions`, chosen over a header because a path is visible in logs, cacheable, and curl-friendly. Onboarding a shop is one command, `pnpm register-shop`. Every model call writes a cost row from day one.

Verification at end of day: `pnpm lint`, `format:check`, and `typecheck` green. 118 unit tests, up from 92 at the core-pipeline commit. Coverage 99.67% of lines against a floor of 80. Fourteen integration and smoke tests green against a dockerized `postgres:16`, including one that asserts two snapshot rows come out of a single price call. Migration `002` extends the `shop_credentials.kind` CHECK with `ebay` and leaves `001` untouched. `tests/TESTING.md` was re-pinned with `audit-harness init`.

## What this does not do yet

Both pricing sources are stubs in real terms right now. PriceCharting's live field mapping needs verification the day the Premium token lands, and eBay returns a flagged stub without credentials.

No similarity index exists. That is a locked decision rather than an oversight: v0 ships barcode plus vision plus human pick, and if the pilot shows real misses the plan is to buy before building. Ximilar sells a commercial comics visual-search API and a quote is pending. A self-built cover-image index would rest on a fair-use posture instead of a granted license, which is the project's top logged risk.

The CI static eval regression set is a Phase 2 exit item that has not been built. The `human_confirmation` table is designed to grow into that eval set, and it currently holds nothing. The UI `override_cents` smoke assertion is still pending.

And none of this has met a real comic. Every number above came from a test suite and a Docker container. The pilot has not run.

Also shipped that day, both routine pipeline output: the blog automation dual-published the previous day's post `working-is-not-proven` to tonsofskills.com/blog, and the comehomealabama journal published a piece on July coastal market numbers.

## Common questions

### Why not use a vision model alone for comic identification?

Issue-exact and variant-exact identification is retrieval work. Every incumbent that works in this space runs image similarity against a reference cover corpus, which is why the model here sits in the re-rank seat instead of the identifier seat. A first print and a common reprint of the same book are the same picture with different economics, and that difference is carried by metadata rather than by the image.

### Should barcode decoding run before or after the vision model?

Before. Post-1990 comics carry a 12-digit UPC-A plus a 5-digit supplement that encodes issue, cover variant, and printing, so a readable supplement answers the variant question by arithmetic and the model is never asked. Vision is the fallback for the books that arithmetic cannot reach, and today that fallback runs without a similarity index behind it.

### How do you stop a vision model from confidently returning a wrong answer?

Require structured evidence alongside the answer, then check that evidence against something deterministic. This pipeline asks for the issue number read, the cover price box text, and the logo era, then cross-validates each against the top candidate's metadata. A contradiction downgrades the confidence band from high to medium, which costs the employee one extra tap and keeps a wrong book out of inventory.

## Related Posts

- [Shipping a CAD Agent from Zero: DXF Parsing, Edit Engines, and LLM Planner Interfaces](https://startaitools.com/posts/building-cad-dxf-agent-from-zero-to-v010/)
- [Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/)
- [Noise-Robust LLM-Judge Evals: Don't Sign a Coin Flip](https://startaitools.com/posts/noise-robust-signed-llm-judge-evals/)
