# CFO-Grokkable Output Format

This is the verbatim report template the skill emits, plus the rules that make it
pass the 90-second-skim bar. The grokkability bar: *if a CFO can skim it in 90
seconds and say "we're wasting $X here, fix it" without needing an engineer to
translate, it works.* The pattern is one sentence + one proof — and for a CFO the
proof is a dollar number with an explicit window.

## Two headline variants — sample vs live

The single template can't be honest for both a sample allocation and a live
measurement, so pick the variant matching the run:

- **Sample run** (no live data): the per-row split is an illustrative allocation of
  an assumed total. Headline verb: *"is likely burning."*
- **Live run** (`system.billing.usage` queried): confirmed figures are measured, not
  guessed. Headline verb: *"is burning"* (drop "likely") for the confirmed half; the
  at-risk/estimated half keeps a hedge ("up to").

## The verbatim template

### A — Headline block (split confirmed vs pending; the number leads)

Never sum confirmed and unconfirmed dollars under one verb. Split them:

```text
### A $100K/month Databricks workspace is burning **~$19,000/month** (confirmed), plus up to **~$8,000/month** pending review

Trailing 30 days ending 2026-06-22. Confirmed **~$228K/year**; up to **~$96K/year** more pending review. The single assumed input is the $100K/month spend. Every line below is one config change.
```

Shape rule: `### A $<total-spend>/month Databricks workspace is burning
**~$<confirmed-$>/month** (confirmed), plus up to **~$<at-risk+estimated-$>/month**
pending review` — then a one-line second sentence giving the window stamp, both
annualized figures, and naming the single assumed input.

### B — The ranked leak table (with Confidence column)

```text
| # | Where it's leaking | $/month | Confidence | The fix |
|---|---|--:|---|---|
| 1 | **Clusters that never shut themselves off** — paying around the clock for compute nobody is using ³ ⁹ | **$12,000** | Confirmed | Set auto-shutoff (e.g. 30 min) |
| 2 | **Scheduled batch jobs on the premium notebook tier** — ~3.6× the batch rate for identical work ⁴ ⁵ ⁶ | **$7,000** | Confirmed | Move job clusters to the batch tier |
| 3 | **Clusters sized for peak, idling below threshold** — typically 30–50% oversized ³ ¹⁰ | **$5,000** | Estimated | Turn on autoscaling, drop the floor |
| 4 | **A ~2× speed-engine premium on jobs that don't run faster** — only pays off at a ≥2× speedup ⁷ ⁶ | **$3,000** | At-risk | Turn off the speed engine where it adds no gain |
```

Per-row anatomy, in order:

- `#` — rank position (1 = highest $ impact).
- **Where it's leaking** — bold leak name, em-dash, ONE sentence root cause in
  business language (NO raw `DBU` unit — gloss or translate it; see rule 4) with
  cited superscripts.
- **$/month** — bold dollar figure, right-aligned column (`--:`).
- **Confidence** — `Confirmed` / `Estimated` / `At-risk`. This is load-bearing: it
  stops the CFO reading a modeled or pending number as recoverable cash.
- **The fix** — one single config change (never "N clicks").

### C — The #1-line callout (immediately after the table)

```text
**The #1 line alone — idle clusters (confirmed) — is ~$144K/year, fixed in one setting.**
```

Rule: annualize the top leak's monthly figure, name it, include its confidence, state
it's fixed in one setting.

### D — The assumed-vs-cited disclosure (blockquote)

```text
> **What's assumed vs. what's measured.** The **$100K/month workspace spend is the only assumed
> input** (your number goes here). On a live run, the **Confirmed** figures (idle clusters, jobs
> on the wrong tier) are computed directly from your own `system.billing.usage` table — never
> estimated. The **Estimated** figure (overprovisioning) is a model of spend × idle-CPU%, and the
> **At-risk** figure (the speed-engine premium) is the portion pending review against actual
> runtime gain. The per-row split shown on a sample run is an illustrative allocation, ranked by
> documented waste-category size.
```

### E — ROI scale line (optional closer)

```text
For scale: Nucleus Research measured a **375% ROI / 6-month payback** for one Databricks
customer ⁸ — the upside of getting the platform's cost posture right is real and independently audited.
```

### F — Sources section

Numbered footnotes 1–10, each: bold source name, one-line claim,
primary/authoritative link. Every superscript in the table must resolve to a numbered
source. **The renderer must emit these** — if a row carries a superscript, the
Sources block has to render it (do not show superscripts the tooling can't resolve).

## The 90-second-skim rules (enforced)

1. **The number leads.** No problem-statement prose above the fold. If the number is
   ugly enough, it sells itself.
2. **One sentence of what each leak is + one DOLLAR number with an explicit window.**
3. **Ranked by estimated monthly $ impact, highest first** (rank column, `$/month`
   right-aligned).
4. **Root cause in BUSINESS language, not Spark or platform jargon.** No raw `DBU` in
   the CFO-visible cell — `DBU` is the denominator of every dollar here and a CFO does
   not know it. Translate ("~3.6× the batch rate") or gloss once inline ("DBU =
   Databricks' billable compute unit"). Keep `$/DBU` detail in the developer detail
   artifacts, not the top table. No execution-plan / AQE / shuffle terms.
5. **"Single config change," not "N clicks."**
6. **Confirmed vs estimated vs at-risk are never summed under one verb.** The headline
   splits them; the table tags each row. A CFO acting on "confirmed" is on solid
   ground; "at-risk" is flagged as pending.
7. **One assumption, everything else cited.** The only invented number is the
   workspace spend (labeled as such). Rescaling the spend preserves the proportions.
8. **This is the top-of-funnel hook, NOT the one-pager.** It sits in front of the
   full developer-facing README.

## Dollar-formatting / window conventions

- **Headline waste figure:** `~$<n>,000/month` with a tilde, dollar bolded:
  `**~$19,000/month**`.
- **Always pair monthly with annualized.** Every headline/callout dollar gets a
  `/year` companion: `~$228K/year`, `~$144K/year`. Monthly uses full digits
  (`$19,000`); annualized uses `K`-abbreviated (`$228K`).
- **Explicit window, not just a cadence label.** The report stamps
  `Trailing 30 days ending <window-end-date>` under the headline — a `/month` label
  alone does not tell a CFO which 30 days. The window-end date comes from
  `MAX(usage_date)` (Step 2) and is passed to the renderer as `--window-end`.
- **Monthly normalization footnote.** The ranker normalizes the raw 30-day SQL figure
  to a calendar month (`× 365/12/30`, ~1.014×), so the report total is slightly above
  the raw 30-day sum. Footnote it: "monthly = calendar-month-normalized, not the raw
  30-day sum."
- **Per-row table figures:** bold, full digits, right-aligned (`--:`): `**$12,000**`.
- **Rate citations live in the developer detail, not the CFO table.** Literal per-unit
  rates (`$0.55/DBU vs $0.15/DBU`, `~2× DBU premium`) belong in the per-leak detail
  artifacts; the CFO row carries the translated multiple (`~3.6×`, `~2×`).
- **Live-run override (load-bearing):** the disclosure states that on an actual run
  the Confirmed dollars are computed from the customer's own `system.billing.usage`
  table; Estimated and At-risk are labeled as modeled/pending.
