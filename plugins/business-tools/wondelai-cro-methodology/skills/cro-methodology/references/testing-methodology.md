# CRO Testing Methodology

Deep-dive into experiment design, statistical rigor, and test prioritization from the CRE Methodology.

## The Philosophy of Bold Testing

### Why "Meek Tweaks" Fail

Most A/B tests fail because they're too small to detect. Button color changes, minor copy tweaks, and micro-optimizations suffer from:

1. **Insufficient sample size** - Small changes require massive traffic to reach significance
2. **Interaction effects** - Minor changes get lost in noise
3. **Opportunity cost** - Time spent on 2% wins could find 200% wins

**Rule: Test big changes that could double conversion, not small changes that might move it 5%.**

### The 10x Mindset

Before any test, ask: "Could this 10x our results?" If not, is it worth testing?

- **Worth testing:** Complete page redesign, new value proposition, fundamentally different offer
- **Not worth testing:** Button color, font size, image swap

---

## A/B Testing vs. Multivariate Testing

### A/B Testing (Split Testing)

Compare two (or more) complete versions against each other.

| Aspect | Details |
|--------|---------|
| **Best for** | Testing big concepts, page redesigns, offers |
| **Traffic needed** | Lower (split between 2-4 variants) |
| **Insights** | Which version wins overall |
| **Limitation** | Doesn't show which elements contributed |

**When to use:**
- You have a hypothesis about a major change
- Traffic is limited
- You're comparing conceptual approaches

### Multivariate Testing (MVT)

Test multiple elements simultaneously to find optimal combination.

| Aspect | Details |
|--------|---------|
| **Best for** | Optimizing elements after winning concept proven |
| **Traffic needed** | Much higher (combinations multiply) |
| **Insights** | Which specific elements drive results |
| **Limitation** | Requires significant traffic |

**When to use:**
- You have a winning page to optimize further
- High traffic (100k+ monthly visitors)
- Clear, isolated elements to test

### Traffic Requirements

**A/B Test:**
```
Minimum sample per variant = 250-500 conversions
For 2 variants with 5% conversion: 10,000-20,000 visitors needed
```

**Multivariate Test:**
```
Combinations = (Options for Element 1) × (Options for Element 2) × ...
Example: 3 headlines × 3 images × 2 CTAs = 18 combinations
Each combination needs 250+ conversions = 90,000+ conversions total
```

**Recommendation:** Start with A/B tests. Only move to MVT when you have:
- Proven winning page concept
- 100k+ monthly visitors
- Mature testing program

---

## Statistical Significance

### What It Means

Statistical significance tells you: "How likely is this result due to chance vs. a real effect?"

**Industry standard:** 95% confidence (p-value < 0.05)
- 95% confident the difference is real
- 5% chance it's random noise

### Common Mistakes

**1. Peeking and stopping early**

Checking results daily and stopping when you see a winner leads to false positives.

- **Wrong:** "We're at 95% confidence after 3 days—ship it!"
- **Right:** Pre-determine sample size and test duration; don't stop early

**2. Calling tests with insufficient data**

| Visitors | Conversions | Can you call it? |
|----------|-------------|------------------|
| 500 | 15 vs 20 | No |
| 5,000 | 150 vs 200 | Possibly |
| 50,000 | 1,500 vs 2,000 | Yes |

**3. Ignoring practical significance**

A statistically significant 0.1% lift isn't worth implementation complexity.

**4. Multiple comparison problem**

Testing 20 variants? One will show "significance" by chance alone.

### Sample Size Calculation

Before testing, calculate required sample size:

**Inputs needed:**
- Baseline conversion rate
- Minimum detectable effect (MDE) you care about
- Statistical power (typically 80%)
- Significance level (typically 95%)

**Rule of thumb:**
```
For 5% baseline, 20% relative lift detection:
~25,000 visitors per variant needed

For 5% baseline, 50% relative lift detection:
~4,000 visitors per variant needed
```

**Key insight:** The smaller the effect you want to detect, the more traffic you need. This is why bold changes are better—they're detectable with less traffic.

### Test Duration

**Minimum test duration:**
- At least 1 full business cycle (typically 1-2 weeks)
- Include weekdays AND weekends
- Account for seasonality

**Why?**
- Visitor behavior differs by day of week
- Friday buyers differ from Monday researchers
- Monthly cycles affect B2B especially

---

## ICE Prioritization Framework

Prioritize test ideas using ICE scores:

### Impact (1-10)
"If this wins, how big would the impact be?"

| Score | Impact Level |
|-------|--------------|
| 10 | Could double conversion rate |
| 7-9 | Major improvement (30-50%+) |
| 4-6 | Moderate improvement (10-30%) |
| 1-3 | Minor improvement (<10%) |

### Confidence (1-10)
"How confident are we this will work?"

| Score | Confidence Level |
|-------|------------------|
| 10 | Proven in research, worked before |
| 7-9 | Strong research supports it |
| 4-6 | Reasonable hypothesis |
| 1-3 | Gut feeling, unvalidated |

### Ease (1-10)
"How easy is this to implement and test?"

| Score | Ease Level |
|-------|------------|
| 10 | Text change only |
| 7-9 | Design change, no dev needed |
| 4-6 | Requires development |
| 1-3 | Major technical lift |

### ICE Score Calculation

```
ICE Score = (Impact + Confidence + Ease) / 3
```

Or weighted:
```
ICE Score = (Impact × 2 + Confidence × 1.5 + Ease × 1) / 4.5
```

### Sample Prioritization

| Test Idea | Impact | Confidence | Ease | Score |
|-----------|--------|------------|------|-------|
| New headline from customer research | 8 | 9 | 10 | 9.0 |
| Add video testimonial | 7 | 7 | 6 | 6.7 |
| Redesign checkout flow | 9 | 6 | 3 | 6.0 |
| Change button color | 2 | 2 | 10 | 4.7 |

---

## Test Documentation

### Before the Test

Document:
1. **Hypothesis:** "If we [change X], then [metric Y] will improve because [reason based on research]"
2. **Primary metric:** One metric that determines winner
3. **Secondary metrics:** Additional metrics to monitor
4. **Guardrail metrics:** Metrics that shouldn't decrease
5. **Sample size requirement**
6. **Test duration**
7. **Traffic allocation**

### After the Test

Document:
1. **Results:** Raw numbers, conversion rates, confidence interval
2. **Statistical significance:** p-value, confidence level
3. **Practical significance:** Is the lift worth implementing?
4. **Learnings:** What does this teach us about our customers?
5. **Next steps:** Ship winner, iterate, or abandon?

### Learnings Database

Every test should add to organizational knowledge:

| Test | Hypothesis | Result | Learning | Applicable to |
|------|------------|--------|----------|---------------|
| Homepage headline A/B | Customer language converts better | Winner: +27% | Customers care about outcomes, not features | All landing pages |
| Form length test | Shorter forms convert better | Loser: no diff | Our audience expects detailed forms | Lead gen pages |

---

## When Tests Fail

### Types of "Failure"

**1. No winner (inconclusive)**
- Sample size too small
- Effect size too small to detect
- Test needed to run longer

**2. Control wins**
- New version is worse
- Hypothesis was wrong
- Still a learning!

**3. Technical problems**
- Tracking broke
- Experience differed from plan
- Sample contamination

### What to Do

1. **Document the learning** - "We learned customers prefer X"
2. **Investigate why** - Go back to research
3. **Don't give up on the page** - The opportunity exists, you just haven't found the solution
4. **Try a bolder change** - Maybe the change wasn't big enough

**Critical insight:** A failed test that teaches you something is more valuable than a winning test you don't understand.

---

## CRO Team Dynamics

### Roles in a CRO Program

| Role | Responsibility |
|------|----------------|
| **CRO Lead** | Strategy, prioritization, stakeholder management |
| **Researcher** | User research, surveys, analytics analysis |
| **Designer** | Wireframes, mockups, user flows |
| **Developer** | Test implementation, technical QA |
| **Analyst** | Results analysis, statistical rigor |

### Getting Stakeholder Buy-In

**Common objections:**

| Objection | Counter |
|-----------|---------|
| "We already know what works" | "Then testing will confirm it quickly" |
| "Testing takes too long" | "Shipping wrong things costs more" |
| "Our traffic is too low" | "Then we test bigger changes" |
| "The CEO wants X" | "Let's test to validate the idea" |

**Building credibility:**
1. Start with quick wins (high-traffic pages, obvious problems)
2. Document and share learnings widely
3. Quantify impact in revenue terms
4. Build testing into the culture, not just a project

### Test Velocity

**Goal:** Increase valid tests per month over time.

| Maturity | Tests/Month | Characteristics |
|----------|-------------|-----------------|
| Beginner | 1-2 | Manual processes, ad-hoc |
| Developing | 4-6 | Established backlog, regular cadence |
| Advanced | 10-20 | Parallel testing, mature process |
| Expert | 20+ | Multiple simultaneous tests, automated |

---

## Testing Platform Comparison

| Platform | Best For | Limitations |
|----------|----------|-------------|
| Google Optimize | Beginners, free tier | Sunsetting, limited features |
| VWO | Mid-market, visual editor | Can be slow, limited targeting |
| Optimizely | Enterprise, complex tests | Expensive, learning curve |
| LaunchDarkly | Dev-centric, feature flags | Not optimized for marketing |
| Custom | Full control | Development cost |

### Key Features to Look For

- Visual editor for non-developers
- Robust statistical engine
- Segment targeting
- Integrations (analytics, CDP, etc.)
- Flicker prevention
- Mutually exclusive experiments
