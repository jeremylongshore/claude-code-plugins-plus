# CFO-Grokkable Output Format

_Last updated: 2026-07-02._

This is the verbatim report template the skill emits, plus the rules that make it pass
the 90-second-skim bar. The grokkability bar: _if a CFO can skim it in 90 seconds and
say "we're wasting $X on GPUs here, fix it" without needing an engineer to translate,
it works._ The pattern is one sentence + one proof — and for a CFO the proof is a
dollar number with an explicit window.

## The never-sum invariant (the load-bearing rule)

**Never sum confirmed and unconfirmed (estimated / at-risk) dollars under one verb.**
A CFO acting on "confirmed" is on solid ground; an estimate or a commitment decision is
not recoverable cash. The headline splits them; the table tags every row. This is the
one rule the ranker enforces in code and the eval-spec marks `regression_critical`.

## Two headline variants — sample vs live

- **Sample run** (no live PromQL): the per-row split is an illustrative allocation of
  an assumed total. Headline verb: _"is likely burning."_
- **Live run** (Grafana PromQL queried): confirmed figures are computed from real
  usage × rate. Headline verb: _"is burning"_ for the confirmed half; the
  estimated/at-risk half keeps a hedge ("up to").

## The verbatim template

### A — Headline block (split confirmed vs pending; the number leads)

```text
### A $180K/month CoreWeave GPU cluster is burning **~$44,986/month** (confirmed), plus up to **~$29,110/month** pending review

Trailing 30 days ending 2026-06-22. Confirmed **~$540K/year**; up to **~$349K/year** more pending review. Spend is reconstructed from PromQL against CoreWeave's managed Grafana (no billing API). Every line below is one change.
```

Shape rule: `### A $<TOTAL-SPEND>/month CoreWeave GPU cluster is burning
**~$<CONFIRMED>/month** (confirmed), plus up to **~$<ESTIMATED+AT-RISK>/month** pending
review` — then a one-line window stamp with both annualized figures and the
"reconstructed from PromQL" provenance line. (Placeholders here use UPPERCASE so the
skill body never contains a lowercase `<tag>` the validator flags as XML.)

### B — The ranked leak table (with Confidence column)

```text
| # | Where it's leaking | $/month | Confidence | The fix |
|---|---|--:|---|---|
| 1 | **Idle reserved GPUs** — reserved capacity billing around the clock below a utilization floor | **$26,280** | Confirmed | Right-size or release the reservation |
```

Per-row anatomy, in order:

- `#` — rank position (1 = highest $ impact).
- **Where it's leaking** — bold leak name, em-dash, ONE sentence root cause in business
  language (no raw DCGM counter names; translate "SM-active" to "GPU actually working").
- **$/month** — bold dollar figure, right-aligned column (`--:`).
- **Confidence** — `Confirmed` / `Estimated` / `At-risk`. Load-bearing: stops the CFO
  reading a modeled or pending number as recoverable cash.
- **The fix** — one single change (never "N clicks").

### C — The #1-line callout (immediately after the table)

```text
**The #1 line alone — idle reserved gpus (confirmed) — is ~$315K/year, fixed in one setting.**
```

Rule: annualize the top leak's monthly figure, name it, include its confidence.

### D — The assumed-vs-measured disclosure (blockquote)

```text
> **What's assumed vs. what's measured.** The monthly GPU spend is the only assumed input.
> Every per-row dollar figure is computed by multiplying PromQL usage (from CoreWeave's
> managed Grafana) by the rate card — CoreWeave exposes no dollars metric, so there is no
> single billed number to read. The Confidence column marks billed idle waste (Confirmed)
> vs. a right-sizing model (Estimated) vs. a commitment decision (At-risk).
```

## The 90-second-skim rules (enforced)

1. **The number leads.** No problem-statement prose above the fold.
2. **One sentence of what each leak is + one DOLLAR number with an explicit window.**
3. **Ranked by monthly $ impact, highest first** (`$/month` right-aligned).
4. **Root cause in BUSINESS language, not GPU jargon.** No raw `DCGM_FI_PROF_SM_ACTIVE`,
   `MFU`, or `billing:instance:total` in the CFO-visible cell — translate or gloss once.
   Keep counter names and `$/GPU-hour` rates in the developer detail artifacts.
5. **"Single change," not "N clicks."**
6. **Confirmed vs estimated vs at-risk are never summed under one verb.** (See invariant.)
7. **One assumption, everything else derived.** The only assumed number is the monthly
   spend. Every leak dollar is `usage × rate` computed by the ranker.
8. **This is the top-of-funnel hook, NOT the one-pager.** It sits in front of the full
   developer-facing detail.

## Dollar-formatting / window conventions

- **Headline waste figure:** `~$<n>/month` with a tilde, dollar bolded: `**~$44,986/month**`.
- **Always pair monthly with annualized.** Monthly uses full digits (`$44,986`);
  annualized uses `K`-abbreviated (`$540K/year`).
- **Explicit window, not just a cadence label.** The report stamps `Trailing 30 days
  ending <WINDOW-END-DATE>` — a `/month` label alone does not tell a CFO which 30 days.
  The window-end comes from the query time range and is passed as `--window-end`.
- **Monthly normalization.** The ranker normalizes the raw 30-day usage figure to a
  calendar month (`× 365/12/30`, ~1.014×), so the report total is slightly above the raw
  30-day sum.
- **Rate provenance.** CoreWeave has no dollars metric; every dollar is
  `usage_gpu_hours × rate_usd_per_gpu_hour` (or the re-price / discount variant), and the
  rate card is a dated snapshot of [coreweave.com/pricing](https://www.coreweave.com/pricing).

## Sources

1. **CoreWeave usage-monitoring docs** — no billing API; build cost from PromQL usage ×
   rate. <https://docs.coreweave.com/docs/observability/usage-monitoring>
2. **CoreWeave pricing** — on-demand rate card; up-to-60% committed-use discount.
   <https://www.coreweave.com/pricing>
