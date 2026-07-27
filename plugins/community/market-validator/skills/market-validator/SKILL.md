---
name: market-validator
description: |
  When the user asks you to validate a business idea, research a niche,
  or check if there is demand for a product idea.

  Trigger phrases:
  - "validate this idea"
  - "is there a market for"
  - "research this niche"
  - "check if this is worth building"
  - "demand check for"
allowed-tools: Bash, Read, Write, Edit, Glob
version: 1.0.0
author: Carl Johnson <gupsspam@users.noreply.github.com>
license: MIT
compatibility: agentskills.io/specification
tags: [research, market, validation, business, product, entrepreneurship]
---

# Market Validator

## Overview

This skill gives Claude Code a structured, time-boxed process ... for validating a business or niche idea *before* the user invests time building it. Most products fail not because they were built badly, but because nobody wanted them. The skill works through five phases — idea scrubbing, competition scan, demand signal check, monetization check, and verdict — gathering real-world evidence (existing competitors, forum complaints, search-interest proxies, comparable pricing) and compressing it into a single structured report with a GREEN / YELLOW / RED verdict. The goal is not to kill ideas; it is to make the user's next step (build, test with an MVP, or walk away) an evidence-based decision instead of a hopeful one.

## Prerequisites

- **curl** — for fetching public web pages, APIs, and search results from the command line
- **jq** — for parsing JSON responses from APIs (GitHub search, Product Hunt, Reddit's public JSON endpoints)
- **Python 3** — for quick revenue math and any scraping/parsing curl+jq can't handle cleanly
- **Web search access** — a web search tool if available in the session; otherwise curl against public endpoints (Reddit `.json` URLs, GitHub search API, Hacker News Algolia API)
- **Write access to the working directory** — the final report is saved as a markdown file
- **Common sense** — the numbers in Phase 4 are estimates, not forecasts; the skill is honest about uncertainty and you should be too

No paid accounts or API keys are required. Everything uses free, public endpoints.

## Instructions

### Phase 1: Idea Scrubbing (~5 min)

1. Ask the user to state the idea in **one sentence**. If they can't, that is the first finding — a fuzzy idea cannot be validated. Help them compress it before continuing.
2. Extract the three core assumptions from that sentence and write them down explicitly:
   - **Who** is the customer? (a specific person, not "everyone")
   - **What pain** do they have today, and what are they doing about it right now?
   - **Why would they pay** — what is the pain costing them in money or time?
3. Flag red-flag phrasings immediately and tell the user why they matter:
   - *"Everyone needs X"* → nobody is the customer; demand claims can't be tested.
   - *"It's like Y but for Z"* → verify Z actually has Y's problem before proceeding.
   - *"There's no competition"* → treat as a claim to test in Phase 2, not a selling point.

### Phase 2: Competition Scan (~15 min)

4. Search the web for existing solutions using 3–5 query variants: the idea's plain description, "[problem] tool", "[problem] software", "best [category] 2026", and "[category] alternatives".
5. Classify every product found into one of three buckets:
   - **Direct competitor** — solves the same problem for the same customer
   - **Indirect substitute** — solves the problem differently (spreadsheets, a VA, a manual workflow)
   - **Adjacent** — same customer, neighboring problem (could expand into this space)
6. For each direct competitor, note: approximate age (check domain/first release), pricing if visible, and any funding signals (Crunchbase mentions, "backed by" pages, team size hints).
7. Check the fresh-entry channels for recent activity in the niche:
   - Product Hunt: search the category, note launches in the last 12 months
   - GitHub: search repositories by keywords, sort by stars
   - App stores / Chrome Web Store if the idea is app-shaped
8. Count the field. Interpret it honestly:
   - **3–10 competitors, some thriving** → the market is real; the question becomes differentiation.
   - **20+ competitors** → saturated; only proceed with a sharp unique angle.
   - **ZERO competitors** → this is a **yellow flag, not a green one**. Either the search terms are wrong (retry with different vocabulary) or nobody wants this. Absence of competition usually means absence of demand.

### Phase 3: Demand Signal Check (~10 min)

9. Search for organic complaint posts: "I wish there was a tool", "is there an app that", "how do I [pain]" combined with the niche keywords — on Reddit, Hacker News (Algolia API), and Stack Overflow where relevant. Count distinct mentions in roughly the last 6 months.
10. Check search-interest proxies. Google Trends if reachable; otherwise use free keyword tools or autocomplete signals. Note whether interest is rising, flat, or declining.
11. Find the 2–3 Reddit communities where the target customer lives. Look for *recurring* pain-point threads — one viral complaint is noise; the same complaint monthly is signal.
12. Read review pages of the top 2 competitors (G2, app store reviews, GitHub issues). The 1–3 star reviews are a gift: they list exactly what an entrant could do better. Note the top 3 recurring complaints.

### Phase 4: Monetization Check (~5 min)

13. List 3–5 comparable products with their actual prices. This anchors what the market will bear — the user's idea will not magically command 5× the going rate.
14. Estimate realistic revenue with the standard funnel: **addressable audience × conversion rate × price**. Size the audience from Phase 3 data (subreddit sizes, search volumes), not wishful TAM slides.
15. Apply honest conversion rates: most **B2C products convert at 1–5%** of engaged audience, most **B2B at 5–15%**. Use the low end unless the demand signals in Phase 3 were exceptional.
16. Run the numbers with Python and present low/mid/high scenarios. Then answer the real question: does the mid scenario justify the build time?

### Phase 5: Verdict (~5 min)

17. **🟢 GREEN** — clear, recurring demand signals; competition exists but is beatable or the niche is underserved; comparable products prove people pay; revenue math clears the user's bar. Recommendation: build a focused MVP now.
18. **🟡 YELLOW** — mixed signals: demand exists but the market is saturated, or the idea is novel but demand is unproven, or monetization is unclear. Recommendation: name the single riskiest assumption and propose the cheapest test for it (landing page, waitlist, 5 customer interviews) before writing code.
19. **🔴 RED** — no organic demand signals, a saturated market with entrenched free options, or no credible path to payment. Recommendation: do not build; state which single finding was disqualifying, and note any adjacent pivot the research surfaced. Then write the full report to a file named `validation-[idea-slug].md`.

## Output

The user gets a structured research report saved as `validation-[idea-slug].md`:

```markdown
# Market Validation: [Idea Name]

## Verdict: 🟢 GREEN / 🟡 YELLOW / 🔴 RED

One-paragraph justification citing the strongest evidence for and against.

## Competition Analysis
| Competitor | Type | Age | Notes |
|------------|------|-----|-------|
| ...        | direct/indirect/adjacent | ~N yrs | pricing, funding, weaknesses |

## Demand Signals
- Forum posts: N mentions in last 6 months (links to strongest 3)
- Search volume proxy: rising / flat / declining, with source
- Comparable products: N products priced $X–$Y
- Top competitor complaints: the 3 recurring gripes an entrant could exploit

## Revenue Estimate
- Realistic monthly: $X (N users × $Y/mo × Z% conversion)
- Low / mid / high scenarios
- Break-even: M months at N hours/week of build time

## Next Steps
Concrete, ordered actions matched to the verdict (build MVP / run cheap test / pivot or drop).
```

Every claim in the report links to its source so the user can audit the evidence.

## Error Handling

- **Web search tool unavailable** — fall back to curl against public JSON endpoints: Reddit (`/search.json`), Hacker News (Algolia API), GitHub search API. Note in the report that coverage was reduced.
- **Reddit returns 403/429** — Reddit blocks default user agents. Retry with `curl -A "market-validator/1.0"` and add a 2-second sleep between requests. If still blocked, use HN and GitHub issues as substitute complaint sources.
- **Google Trends unreachable** — it has no free API. Substitute: search autocomplete presence, keyword counts from free tools, or relative subreddit/community sizes as a demand proxy. Label the proxy clearly in the report.
- **Zero search results for the niche** — before concluding "no market," retry with 2–3 alternative vocabularies (the customer may name the problem differently than the founder does). Only after vocabulary retries does zero-results become evidence.
- **Paywalled competitor pricing** — check the Wayback Machine, review sites that quote pricing (G2, Capterra), or note "pricing opaque — itself a data point" in the table.
- **User can't state the idea in one sentence** — do not proceed to Phase 2. Loop on Phase 1: offer 2–3 candidate one-liners based on what they described and let them pick or correct one.
- **Ambiguous verdict (evidence genuinely split)** — default to YELLOW and say which single additional data point would tip it either way. Never inflate to GREEN to please the user.

## Examples

### Example 1: "Validate the idea of a CLI tool that converts markdown to beautifully formatted PDFs"

- Phase 2 finds: Pandoc (14+ yrs, free, dominant), md2pdf, Typst (fast-growing), PrinceXML (commercial) — 4+ strong direct competitors, several free.
- Phase 3 finds: high demand — hundreds of GitHub issues and forum threads about markdown→PDF styling pain, broken page breaks, and LaTeX installation misery.
- Phase 4 finds: comparables are mostly free/open-source; PrinceXML charges $495+ but serves enterprises.
- **Verdict: 🟡 YELLOW** — demand is real and recurring, but the market is saturated with free incumbents.

### Example 2: "Is there a market for a Twitch clip generator?"

- Phase 2 finds: Streamlabs Cross Clip, ClipFlow, Opus Clip, plus custom in-house pipelines — active, funded direct competitors; market is growing, not stale.
- Phase 3 finds: creators actively *hiring* human clippers on job boards; Whop clip-farming programs pay per approved clip.
- Phase 4 finds: established pricing at $10–30/mo per creator, plus a proven pay-per-clip model.
- **Verdict: 🟢 GREEN** — validated demand, clearly identified customer, existing payment model.

### Example 3: "Check if this is worth building: a social network for people who own pet rocks"

- Phase 2 finds: zero direct competitors — yellow flag.
- Phase 3 finds: pet rock is a nostalgia joke; mentions are one-off memes, not recurring pain.
- Phase 4 finds: no comparable paid product; no costing pain to price against.
- **Verdict: 🔴 RED** — no demand, no pain, no payment path.

## Resources

- [The Mom Test](https://www.momtestbook.com/) — Rob Fitzpatrick's methodology for extracting honest demand signals
- [Y Combinator: How to Get Startup Ideas](https://www.ycombinator.com/library/8g-how-to-get-startup-ideas)
- [Google Trends](https://trends.google.com/)
- [Hacker News Algolia Search API](https://hn.algolia.com/api)
- [GitHub Search API](https://docs.github.com/en/rest/search)
- [Product Hunt](https://www.producthunt.com/)
- [Indie Hackers](https://www.indiehackers.com/)
- [MicroConf talks](https://microconf.com/)
