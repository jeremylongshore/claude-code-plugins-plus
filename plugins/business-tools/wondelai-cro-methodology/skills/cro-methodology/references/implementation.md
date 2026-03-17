# CRO Methodology - Implementation Guide

Step-by-step methodology for evidence-based conversion rate optimization using the CRE Methodology. The core principle: discover WHY visitors don't convert, then eliminate those reasons systematically.

## Step 1: Funnel Mapping

Before running any tests, map the entire conversion funnel to identify where visitors drop off.

**1a. Define the conversion goal**
- Primary conversion: what is the single most important action? (signup, purchase, demo request)
- Micro-conversions: what smaller actions lead there? (email capture, scroll depth, video play)

**1b. Map the funnel stages**
```
Traffic Source → Landing Page → Engagement → Intent Signal → Conversion
```
- Document each stage: URL, traffic volume, conversion rate, drop-off rate
- Calculate where the biggest absolute losses occur (not just the worst percentage)
- Prioritize the stage with the highest traffic × drop-off rate product

**1c. Identify friction points per stage**
- Use session recordings (Hotjar, FullStory) to watch actual user behavior
- Look for rage clicks, hesitation zones, and premature exits
- Mark every point where users stop scrolling or abandon forms

## Step 2: Customer Research (Qualitative)

Do not write a single test hypothesis without first understanding why visitors don't convert.

**2a. Exit-intent surveys**
- Deploy a one-question exit survey: "What stopped you from [action] today?"
- Collect 50+ responses before drawing conclusions
- Categorize answers: price objection, trust issue, unclear value, wrong timing, missing info

**2b. Customer interviews (5 minimum)**
- Interview recent converters AND recent abandoners
- Key questions:
  - "Walk me through your decision to [convert/not convert]."
  - "What almost stopped you?"
  - "What convinced you to trust us?"
  - "What would have made this decision easier?"
- Use the exact words customers use — these become your copy and objection-handling language

**2c. Competitor gap analysis**
- List every objection customers raise, then audit competitor pages for how they address the same objections
- Note proof elements, guarantees, and risk reversals competitors use that you don't

## Step 3: Persuasion Asset Audit

Score your current page against the 7 persuasion assets (0-2 per asset = 0-14 total):

| Asset | What to Look For | Score |
|-------|-----------------|-------|
| Social proof | Testimonials, case studies, logos, reviews | /2 |
| Authority | Credentials, press mentions, certifications | /2 |
| Trust signals | Security badges, guarantees, refund policy | /2 |
| Clarity of value | Specific, credible benefit statements | /2 |
| Objection handling | FAQs, preemptive objection responses | /2 |
| Urgency/scarcity | Legitimate, time-bound reasons to act now | /2 |
| Risk reversal | Money-back guarantee, free trial, no credit card | /2 |

Score < 8 = significant conversion opportunity without any A/B testing needed.

## Step 4: Hypothesis Formation

Each test hypothesis must follow this format:

```
Because [research insight], changing [element] to [variation]
will increase [metric] for [audience segment]
by [expected lift] because [psychological mechanism].
```

Example:
```
Because exit surveys show 40% of visitors cite "not sure if it works for my industry",
changing the hero section to include 3 industry-specific case study logos
will increase demo request rate for mid-market SaaS visitors
by ~15% because social proof reduces category uncertainty.
```

**Prioritize hypotheses using PIE score:**
- Potential: how much could this improve conversion?
- Importance: how much traffic hits this element?
- Ease: how hard is this to implement?

Score each 1-10, calculate average. Run highest PIE score first.

## Step 5: Test Design

**5a. Statistical rigor requirements**
- Minimum 95% confidence level before declaring a winner
- Minimum detectable effect: set based on business impact, not wishfulness
- Required sample size: use a calculator — most tests need 1,000+ conversions per variant
- Test duration: minimum 2 weeks to capture weekly cycles (never stop early)

**5b. Isolate one variable per test**
- Do not test multiple changes simultaneously in a single A/B test
- Exception: multivariate tests only if you have massive traffic (10,000+ conversions/week)

**5c. Set up proper tracking**
- Verify tracking fires correctly before launching (test in incognito)
- Segment results by traffic source, device type, and new vs. returning visitors
- Document pre-test baseline conversion rate and confidence interval

## Step 6: Counter-Objection Framework

For every major objection identified in research, build a dedicated counter-objection block on the page:

| Objection | Counter-objection | Proof Element |
|-----------|------------------|---------------|
| "Is this secure?" | SOC 2 certified, 256-bit encryption | Security badge + audit link |
| "Too expensive" | Calculate ROI: saves X hours/week at $Y/hour | ROI calculator widget |
| "Will it work for us?" | [Industry] companies like [Name] use it | Industry-specific case study |
| "What if it doesn't work?" | 30-day money-back guarantee, no questions | Guarantee badge + policy link |

Place objection handling in the conversion path, not just in an FAQ section at the bottom.

## Step 7: Post-Test Analysis

After each test:

1. **Declare winner only at statistical significance** — premature declarations cause regression to mean
2. **Segment the results** — a test that loses overall may win for mobile or for paid traffic
3. **Document the learning** — win or lose, record what the test revealed about your customers
4. **Calculate business impact** — convert lift % to revenue or leads per month
5. **Plan the follow-up test** — every test raises new questions; the optimization program is continuous

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Testing without research | Testing random changes → random results | Run surveys and interviews first |
| Stopping tests early | False positives → rolled back "wins" | Set sample size in advance, never stop early |
| Testing low-traffic pages | Underpowered tests → unreliable results | Prioritize pages with 500+ conversions/month |
| Using vanity metrics | "More clicks" that don't increase revenue | Track conversion metric closest to revenue |
| Only testing hero section | Missing leaks deep in the funnel | Map entire funnel before choosing test location |

## Quick-Start Checklist

- [ ] Funnel mapped with drop-off rates at each stage
- [ ] Exit-intent survey deployed and 50+ responses collected
- [ ] At least 5 customer interviews completed
- [ ] Persuasion asset audit scored (0-14)
- [ ] Top 3 hypotheses documented in hypothesis format
- [ ] PIE scores calculated for prioritization
- [ ] Sample size calculated for each planned test
- [ ] Tracking verified in staging environment before launch
