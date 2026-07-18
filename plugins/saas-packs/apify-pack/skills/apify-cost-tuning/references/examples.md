# Apify Cost Tuning — Worked Examples

End-to-end scenarios that chain the six steps in `implementation.md`. Each shows the
investigate → tune → guard loop against a concrete symptom.

## Example 1: "My CheerioCrawler bill tripled last month"

1. **Investigate.** Run `analyzeActorCosts('user/scraper', 30)` (Step 1). The report
   shows avg cost/run jumped from $0.02 to $0.06 and flags the most expensive run.
2. **Diagnose memory.** The Actor is provisioned at 2048 MB but it is a simple Cheerio
   crawler — the memory sweep (Step 2) succeeds all the way down to 256 MB.
3. **Apply.** Set the Actor's default memory to 512 MB (one notch above the 256 MB
   floor for headroom). CU drops ~4x because CU scales linearly with memory.
4. **Verify.** Re-run `analyzeActorCosts` after the next scheduled batch and confirm
   avg cost/run fell back toward $0.02.

## Example 2: "Residential proxy GB is eating the budget"

1. **Confirm the source.** The monthly report (Step 6) shows one Playwright Actor
   dominating spend, and its runs use a residential proxy configuration.
2. **Block heavy resources.** Add the `preNavigationHooks` route-abort from Step 4 to
   drop images, fonts, and CSS. On image-heavy sites this cuts residential GB by
   50-80% because those assets are the bulk of transferred bytes.
3. **Add stickiness.** Enable `useSessionPool` with `maxUsageCount: 100` (Step 4) so
   the crawler reuses proxy sessions instead of opening new connections per request.

## Example 3: "Guard a new Actor against a runaway bill"

Wrap the run in the budget guard from Step 5 so an accidental infinite crawl can't
burn more than a hard cap:

```typescript
// Abort automatically if this run ever exceeds $0.50
const run = await runWithBudget('user/scraper', input, 0.50);
```

The guard polls `usageTotalUsd` every 30 seconds and calls `.abort()` the moment
spend crosses the ceiling — pair it with `maxRequestsPerCrawl` (Step 3) as a
belt-and-suspenders upper bound.
