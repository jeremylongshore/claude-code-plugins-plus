# Apify Production Checklist — Worked Examples

Concrete examples of running the checklist against a real Actor, plus the
console output each monitoring helper produces.

## Example 1: First production deploy of a scraper

You have `username/product-scraper` passing locally. Run the checklist:

1. Read `.actor/actor.json` and confirm `name`, `title`, `description` are set.
2. Confirm `Dockerfile` pins `apify/actor-node:20` (not `latest`).
3. `apify push`, then `apify builds ls` to confirm the build succeeded.
4. Smoke-test on-platform with a tiny input:

```bash
apify actors call username/product-scraper \
  --input='{"startUrls":[{"url":"https://target.com"}],"maxItems":10}'
```

1. Create the daily schedule and completion webhook (see
   [implementation.md](implementation.md) Steps 2–3).

## Example 2: Health check output

Running `checkActorHealth('username/product-scraper', 24)` prints:

```text
Actor: username/product-scraper
Last 24h: 3 runs, 66.7% success
Failed: 1, Timed out: 0
Total cost: $0.4213
ALERT: Failed runs detected!
```

A success rate below 100% with `ALERT:` present is your cue to open the failed
run's log in Apify Console and cross-reference the Error Handling table in SKILL.md.

## Example 3: Cost guard aborting a runaway run

Calling `runWithCostGuard(actorId, input, 5.0)` on a job that blows past budget:

```text
Cost guard: $5.0018 exceeds $5. Aborting.
```

The run is aborted mid-flight, `waitForFinish()` returns the aborted run object,
and the poller is cleared — no orphaned interval.

## Example 4: Rolling back a bad build

Build 42 shipped a regression. Roll back to build 41 without redeploying code:

```bash
apify builds ls
curl -X POST \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/acts/username~product-scraper?build=41"
```

The Actor's default build pointer moves back to 41; the next scheduled run uses it.
