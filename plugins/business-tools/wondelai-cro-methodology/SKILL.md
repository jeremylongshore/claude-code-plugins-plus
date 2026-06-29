---
name: cro-methodology
description: 'Audit websites and landing pages for conversion issues and design evidence-based A/B tests. Use when the user mentions "landing page isnt converting", "conversion rate", "A/B test", "why visitors leave", "objection handling", "bounce rate", "split testing", "conversion funnel", "increase signups", "people add to cart but dont buy", or "improve conversions". Also trigger when diagnosing why signups are low, designing experiment hypotheses, or auditing checkout flows for friction points. Covers funnel mapping, persuasion assets, and objection/counter-objection frameworks. For overall marketing strategy, see one-page-marketing. For usability issues, see ux-heuristics.'
license: MIT
metadata:
  author: wondelai
  version: "1.4.0"
---

# CRO Methodology

Scientific, customer-centric approach to conversion rate optimization based on the CRE Methodology(TM). Extraordinary improvements come from understanding WHY visitors don't convert, not from copying competitors or applying generic tips.

## Core Principle

**Don't guess -- discover.** Every visitor who doesn't convert has a reason. Discover those reasons through research, then systematically eliminate them with evidence and proof. This evidence-based approach consistently outperforms "best practices", intuition, competitor copying, and expert opinion.

## Scoring

**Goal: 10/10.** Rate any landing page, funnel, or conversion flow 0-10 against the principles below. Report the current score and the specific improvements needed to reach 10/10.

## The CRO Frameworks

### 1. The CRO Process

**Core concept:** A systematic 9-step process moving from defining success metrics through research and experimentation to scaling wins across the business.

**Why it works:** Random optimization skips research. The process forces you to understand visitors before changing anything, so every change rests on evidence, not opinion.

**Key insights:**
- Define success metrics aligned with business KPIs before touching any page
- Map the entire funnel to find "blocked arteries" (high-traffic underperforming paths) and "missing links" (absent funnel stages)
- Research visitors in three dimensions: who they are, what blocks them (UX problems), what stops them (objections)
- Gather market intelligence from competitors, reviews, and other industries
- Prioritize ideas with ICE scoring; design bold experiments, not "meek tweaks"
- Run experiments with statistical rigor (95% confidence minimum, full business cycles), then scale wins across the business

**Product applications:**

| Context | CRO Process Step | Example |
|---------|-----------------|---------|
| **Landing page audit** | Define goals, map funnel, research visitors | 70% bounce because value prop is unclear |
| **Checkout optimization** | Map funnel for blocked arteries | Shipping cost shock causes 40% cart abandonment |
| **Email sequence** | Scale wins | Winning objection-handling copy reused in drip emails |

**Copy patterns:**
- "What's preventing you from [action] today?" (exit survey to discover objections)
- "Here's what [X] customers found..." (counter-objection with social proof)
- Hypothesis template: "If we [change X], then [metric Y] will improve because [reason from research]"

**Ethical boundary:** Never manipulate test results or cherry-pick data; report all tests, including failures.

See: [testing-methodology.md](references/testing-methodology.md) for ICE scoring, A/B vs. multivariate guidance, and statistical rigor.

### 2. Customer Research & Objections

**Core concept:** Visitors fail to convert for specific, discoverable reasons. Exit surveys, chat logs, support tickets, sales calls, and reviews reveal the "voice of the customer" and their real objections.

**Why it works:** Teams' guesses about why visitors leave are almost always wrong. Research uncovers objections no one anticipated, and the customer's own language out-persuades any copywriter's invention.

**Key insights:**
- Primary sources (exit surveys, live chat, tickets, sales calls) give direct visitor language; secondary sources (reviews, social media, competitors) reveal industry-wide objections
- The "Big 5" universal objections: Trust, Price, Fit, Timing, Effort
- Quantitative research (analytics, heatmaps) shows WHERE problems are; qualitative (surveys, interviews) shows WHY
- Non-converter surveys should ask ONE question for maximum response; post-purchase surveys ("What almost stopped you from buying?") reveal the objections that matter most

**Product applications:**

| Context | Research Method | Example |
|---------|---------------|---------|
| **Exit intent** | On-site survey | "What's preventing you from signing up today?" |
| **Post-purchase** | Email survey within 7 days | "What almost stopped you from buying?" |
| **Objection mining** | Support tickets + reviews | Search "but", "however", "worried about"; negative reviews = unaddressed objections |

**Copy patterns:**
- Use exact customer language in headlines and body copy -- it outperforms polished marketing copy
- "What's the one thing we could change to make you [action]?"
- "How would you describe [product] to a friend?" (reveals positioning in customer terms)

**Ethical boundary:** Anonymize data, get consent for recordings, and don't survey so aggressively that you degrade the experience.

See: [RESEARCH.md](references/RESEARCH.md) for tools, survey questions, and data analysis methods.

### 3. Persuasion Assets

**Core concept:** Every company sits on overlooked proof -- undisplayed testimonials, unmentioned awards, hidden credentials, buried guarantees. Inventory these "persuasion assets", acquire missing ones, display them.

**Why it works:** Visitors decide on evidence, not claims. A modest claim with overwhelming proof beats a bold claim with none.

**Key insights:**
- Audit five categories: Credentials & Authority, Social Proof, Risk Reversal, Data & Specificity, Process & Methodology
- Create a wish list for missing assets and actively acquire them (request testimonials, apply for awards, compile statistics)
- "Proof sandwich" structure: Claim (bold promise), then Proof (evidence), then Reinforcement (secondary proof)
- Proof hierarchy, strongest first: specific results with context > named testimonials with photos > case studies > statistics > logos > generic testimonials
- Place proof at points of friction, not in FAQs; specific numbers beat round ones ("47,832 customers" beats "About 50,000")

**Product applications:**

| Context | Persuasion Asset | Example |
|---------|-----------------|---------|
| **Landing page header** | Logo bar + rating | "Trusted by 10,000+ companies" with 5 recognizable logos |
| **Pricing page** | Risk reversal | "30-day money-back guarantee, no questions asked" |
| **Checkout flow** | Trust badges near forms | Security certification, payment logos, guarantee seal |

**Copy patterns:**
- "Here's how we did it for [Company X]..." (case study proof)
- "[Specific number] businesses trust us" (not "thousands of customers")
- Lead with benefits, not features: "Never delete another photo" beats "256GB storage"

**Ethical boundary:** Never fabricate testimonials, inflate statistics, or display fake trust badges -- all proof must be genuine and verifiable.

See: [PERSUASION.md](references/PERSUASION.md) for the full persuasion assets checklist and psychological triggers.

### 4. The O/CO Framework

**Core concept:** The Objection/Counter-Objection table is the core CRE technique: map every visitor objection to a specific, evidence-backed counter-objection.

**Why it works:** Visitors arrive with objections; if the page doesn't address them, they leave. The O/CO table ensures no objection goes unanswered, each counter placed where the objection arises in the reading flow.

**Key insights:**
- Research objections from surveys, chat logs, tickets, and sales calls -- don't guess
- Implicit objections (ones visitors won't admit) require "CO Only": counter without stating the objection
- Place counter-objections at the point of friction (credit-card objection near the payment form), not buried in FAQ
- Address primary objections above the fold; repeat the same counter in multiple formats (text, video, testimonial, data)
- Canned support responses are goldmines of tested counter-objections

**Product applications:**

| Objection | Visitor Question | Counter-Objections |
|-----------|------------------|--------------------|
| **Trust** | "Why should I believe you?" | Named testimonials, media logos, awards, guarantee |
| **Price** | "Is it worth the money?" | ROI calculator, cost comparison vs. alternatives, payment plans |
| **Fit** | "Will it work for MY situation?" | Similar-customer case studies, segmented pages, free trial |
| **Timing** | "Why act now?" | Cost-of-delay math, genuine limited offers, seasonal relevance |
| **Effort** | "How hard will this be?" | "Done for you" framing, "Set up in 5 minutes", step-by-step breakdown |

**Copy patterns:**
- Bad (states implicit objection): "Worried you're too lazy to learn a language?"
- Good (CO Only): "Let the audio do the work for you."
- "What almost stopped you from buying?" (post-purchase survey to validate the O/CO table)

**Ethical boundary:** Address real objections honestly -- never dismiss legitimate concerns or use deception to overcome valid hesitations.

See: [OBJECTIONS.md](references/OBJECTIONS.md) for the full O/CO framework, research methods, and counter-objection techniques.

### 5. Hypothesis Design

**Core concept:** Every experiment needs a documented hypothesis linking a specific change to an expected outcome for a research-grounded reason, prioritized with ICE scoring (Impact, Confidence, Ease).

**Why it works:** A hypothesis forces you to articulate WHY a change should work, grounding it in customer research. ICE scoring stops teams wasting traffic on low-impact tweaks.

**Key insights:**
- Format: "If we [change X], then [metric Y] will improve because [reason based on research]"
- Define primary (decides winner), secondary (monitoring), and guardrail (must not decrease) metrics before testing
- ICE, 1-10 each: Impact (could this double conversion?), Confidence (how strong is the research?), Ease (how easy to implement?)
- Worth testing: complete redesign, new value proposition, fundamentally different offer. Not worth testing: button color, font size, image swap
- Before testing, ask: "Could this 10x our results?" If not, reconsider priority

**Product applications:**

| Context | Hypothesis Example | ICE Score |
|---------|-------------------|-----------|
| **Headline rewrite** | "Customer language from surveys will lift conversion because visitors see their own words" | I:8, C:9, E:10 = 9.0 |
| **Checkout redesign** | "One-page checkout will lift completion because analytics show 40% drop at step 2" | I:9, C:6, E:3 = 6.0 |
| **Button color** | "Green button will lift clicks because green means go" | I:2, C:2, E:10 = 4.7 (skip) |

**Copy patterns:**
- "Based on our research, visitors' #1 objection is [X]. This test addresses it by [Y]."
- Document before: hypothesis, primary metric, sample size, duration. Document after: raw numbers, confidence interval, learnings, next steps

**Ethical boundary:** Report all results honestly -- never cherry-pick data or rerun tests until you get the answer you want.

### 6. A/B Testing Methodology

**Core concept:** Run controlled experiments comparing page versions with proper statistical rigor, so results reflect reality rather than random noise.

**Why it works:** Without rigor you can't distinguish real improvements from random variation -- peeking, undersized samples, and ignored practical significance all manufacture false winners.

**Key insights:**
- Calculate required sample size BEFORE starting (baseline rate, minimum detectable effect, 80% power, 95% significance)
- Run at least one full business cycle (1-2 weeks), covering weekdays AND weekends
- Never peek at results and stop early -- it dramatically inflates false positives
- Practical significance matters: a statistically significant 0.1% lift isn't worth implementation complexity
- Use multivariate only with 100k+ monthly visitors on a proven winning page
- Promote winners to the new control; a failed test that teaches you something beats a win you don't understand

**Product applications:**

| Context | Test Type | Example |
|---------|----------|---------|
| **Concept validation** | A/B test (2-4 variants) | Two fundamentally different layouts based on different customer insights |
| **Low traffic** | Bold A/B test | Dramatic changes detectable with smaller samples (~4,000 visitors for 50% lift) |
| **Post-test** | Scale wins | Apply winning insights to landing pages, ad copy, email sequences |

**Copy patterns:**
- "We increased [metric] by [X]% with [Y]% confidence over [Z] weeks"
- "Test showed no significant difference, teaching us that [insight about customers]"
- Document learnings: Test, Hypothesis, Result, Learning, Applicable to

**Ethical boundary:** Never manipulate statistics to manufacture significance; report confidence intervals honestly and acknowledge inconclusive results.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Copying competitors blindly** | You don't know if it even works for them | Research YOUR visitors' objections, build YOUR evidence |
| **Testing button colors before understanding objections** | Surface symptoms, tiny effects, wasted sample | Customer research first, then test big changes |
| **Assuming you know why visitors leave** | Teams are almost always wrong about motivations | Exit surveys, chat logs, support-ticket analysis |
| **Applying "best practices" unvalidated** | May not fit your audience, product, or context | Treat them as hypotheses to test, not rules |
| **HiPPO decisions** | Highest Paid Person's Opinion is not data | Let research and test results decide, not seniority |
| **Optimizing pages without funnel context** | Fixes shift problems elsewhere; misses biggest wins | Map the funnel, find blocked arteries, prioritize by impact |
| **Meek tweaks instead of bold changes** | Rarely reach significance; waste time and traffic | Test changes that could double conversion, not nudge it 2% |
| **Giving up after one failed test** | The opportunity still exists | Investigate why, return to research, try a bolder change |

## Quick Diagnostic

Audit any landing page or conversion flow:

| Question | If No | Action |
|----------|-------|--------|
| Do we know the ONE action visitors should take? | Page lacks focus | Define a single conversion goal; remove competing CTAs |
| Have we researched (not guessed) why visitors don't convert? | Optimization built on assumptions | Run exit surveys, analyze chat logs and tickets |
| Do we have an O/CO table? | Objections go unanswered | Build it from research; place counters at friction points |
| Is the value proposition clear within 5 seconds? | Visitors bounce before understanding | Run a 5-second test; rewrite headline in customer language |
| Are persuasion assets visible (testimonials, awards, guarantees)? | Claims without proof aren't believed | Audit assets, acquire missing ones, display prominently |
| Have we mapped the funnel for blocked arteries? | Optimizing the wrong page | Map traffic per stage, compare to benchmarks, prioritize |

## Quick-Start Checklist

When optimizing any page:

1. [ ] What is the ONE action visitors should take?
2. [ ] Who are the visitors? What stage of the buying journey?
3. [ ] What are their top 3-5 objections? (Research, don't guess)
4. [ ] What proof/counter-objections address each?
5. [ ] Is the value proposition clear in 5 seconds?
6. [ ] Are there UX blockers? (speed, mobile, forms)
7. [ ] What persuasion assets are missing or hidden?

## Reference Files

- [OBJECTIONS.md](references/OBJECTIONS.md): O/CO framework, research methods, counter-objection techniques
- [COPYWRITING.md](references/COPYWRITING.md): Headlines, proof elements, persuasive writing
- [PERSUASION.md](references/PERSUASION.md): Persuasion assets checklist, psychological triggers
- [RESEARCH.md](references/RESEARCH.md): Tools, survey questions, data analysis
- [testing-methodology.md](references/testing-methodology.md): A/B testing, statistical significance, ICE prioritization, multivariate testing
- [funnel-analysis.md](references/funnel-analysis.md): Blocked arteries, missing links, industry funnels, cross-sell mapping

## Further Reading

For the complete CRE Methodology(TM), detailed case studies, and advanced techniques:

- [*"Making Websites Win: Apply the Customer-Centric Methodology That Has Doubled the Sales of Many Leading Websites"*](https://www.amazon.com/Making-Websites-Win-Customer-Centric-Methodology/dp/1544500513?tag=wondelai00-20) by Dr. Karl Blanks and Ben Jesson

## About the Author

**Dr. Karl Blanks and Ben Jesson** are cofounders of Conversion Rate Experts, the agency whose CRE Methodology has doubled the sales of many leading websites -- clients include Google, Apple, Amazon, Facebook, and Dropbox -- and earned a Queen's Award for Enterprise (Innovation). Blanks holds a PhD and led usability teams at Hewlett-Packard; Jesson's background is direct-response marketing. Their book *Making Websites Win* distills the methodology into a repeatable, evidence-based process.
