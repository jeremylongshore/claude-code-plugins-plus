# Klaviyo Cost Tuning — Worked Examples

Concrete before/after scenarios showing how each lever in this skill moves the bill.
Pricing figures come from the tiers in `SKILL.md` § Klaviyo Pricing Model.

## Example 1: Drop a tier by suppressing unengaged profiles

A store carries 12,400 active profiles → sits in the 10,001–25,000 tier (~$150–$375/mo).
An audit (Step 1) plus the "Unengaged 180+ Days" segment (Step 2) finds 3,100 profiles
with no open/click in 180 days.

Running the suppression job (Step 3, Option 1 — unsubscribe) drops the active count to
9,300, moving the account into the 5,001–10,000 tier (~$100–$150/mo).

```text
Before: 12,400 active profiles → ~$150–$375/mo
After:   9,300 active profiles → ~$100–$150/mo
Saved:  ~$50–$225/mo, no marketable-audience loss (the 3,100 never engaged)
```

## Example 2: Cut SMS spend with an engaged-only filter

The Error Handling table flags "SMS costs spiking → Flow sending to full list."
Adding an engaged-only segment filter to the abandoned-cart flow so it only texts
profiles active in the last 30 days reduces per-message carrier charges without
touching email tier cost.

```typescript
// Gate the SMS flow on an "SMS Engaged 30d" segment instead of the full list
const engaged = await segmentsApi.getSegments({
  filter: 'equals(name,"SMS Engaged 30d")',
});
// Send only to engaged.body.data[0].id members
```

## Example 3: Shrink event ingestion with sampling

A high-traffic storefront fires `Viewed Product` and `Page View` on every session.
Applying the Step 4 sampling config keeps 100% of revenue-critical events while
sampling the high-volume, low-value ones:

```text
Placed Order      1.0   (kept — revenue attribution)
Started Checkout  1.0   (kept — cart abandonment)
Viewed Product    0.25  (25% sampled)
Page View         0.10  (10% sampled)
```

Revenue attribution stays intact; ingestion volume for the two noisy events drops
by ~75–90%.

## Example 4: Catch a runaway backfill before it hits the rate limit

Wrapping every SDK call in the Step 5 `KlaviyoUsageTracker` surfaces a nightly
backfill climbing toward the steady limit:

```text
[Klaviyo] High API rate: 620 req/min (limit: 700)
```

The warning fires at 500 req/min, giving headroom to add concurrency control before
the job trips 429 rate-limit errors.
