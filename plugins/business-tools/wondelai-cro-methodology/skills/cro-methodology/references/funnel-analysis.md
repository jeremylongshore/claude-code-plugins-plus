# Funnel Analysis Framework

Deep methodology for mapping, analyzing, and optimizing conversion funnels.

## Funnel Philosophy

A funnel isn't just a visualization—it's a diagnostic tool. Every business has a funnel, whether they've mapped it or not. The question is: where is it leaking?

**Core insight:** Most businesses focus on the top of the funnel (traffic) when the biggest wins are often in the middle (conversion) or bottom (retention/expansion).

---

## Mapping Your Funnel

### The Basic Funnel Structure

```
Awareness → Interest → Consideration → Intent → Evaluation → Purchase → Retention → Advocacy
```

### Simplified Business Models

**E-commerce:**
```
Visit → View Product → Add to Cart → Begin Checkout → Complete Purchase → Repeat Purchase
```

**SaaS:**
```
Visit → Signup → Onboard → Activate → Engage → Convert (Paid) → Retain → Expand
```

**Lead Generation:**
```
Visit → Lead Magnet → MQL → SQL → Opportunity → Close → Upsell
```

**Content/Media:**
```
Visit → Read/View → Subscribe → Engage → Share → Become Regular
```

### Identifying All Steps

List every step a customer takes from first touch to desired outcome:

1. **Acquisition touchpoints** - Where do they first hear about you?
2. **Engagement actions** - What do they do before converting?
3. **Conversion moments** - Where do they make commitments?
4. **Value realization** - When do they get what they came for?
5. **Expansion opportunities** - How do they become more valuable?

---

## Blocked Arteries

A "blocked artery" is a high-traffic path with underperformance—a point where lots of visitors enter but few progress.

### How to Find Blocked Arteries

**Step 1: Map traffic volume at each stage**

```
Homepage:         10,000 visitors
Product page:     3,000 visitors (30% of traffic)
Add to cart:      600 visitors (20% of product viewers)
Checkout start:   300 visitors (50% of cart adds)
Purchase:         150 visitors (50% of checkout starts)
```

**Step 2: Calculate conversion at each step**

```
Homepage → Product:     30%
Product → Cart:         20% ← Potential blocked artery
Cart → Checkout:        50%
Checkout → Purchase:    50%
```

**Step 3: Compare to benchmarks**

| Stage | Your Rate | Industry Benchmark | Opportunity |
|-------|-----------|-------------------|-------------|
| Home → Product | 30% | 25-35% | On track |
| Product → Cart | 20% | 5-10% | Actually good |
| Cart → Checkout | 50% | 60-70% | **Blocked artery** |
| Checkout → Purchase | 50% | 70-80% | **Blocked artery** |

**Step 4: Prioritize by impact**

Impact = Traffic Volume × Conversion Gap

```
Cart → Checkout: 600 × (0.65 - 0.50) = 90 potential conversions
Checkout → Purchase: 300 × (0.75 - 0.50) = 75 potential conversions
```

### Common Blocked Arteries

| Location | Typical Causes |
|----------|----------------|
| Homepage → Category | Unclear value proposition, poor navigation |
| Category → Product | Weak product presentation, too many choices |
| Product → Cart | Missing information, price shock, no urgency |
| Cart → Checkout | Unexpected costs, account requirement, trust issues |
| Checkout → Purchase | Form friction, payment options, shipping cost shock |
| Trial → Paid | Poor onboarding, unclear value, wrong timing |

---

## Missing Links

A "missing link" is an absent or underutilized funnel stage that leaves value on the table.

### Common Missing Links

**Pre-purchase:**
- No retargeting for abandoned visitors
- No email capture before purchase intent
- No comparison tools for researchers
- No social proof at decision points

**Purchase:**
- No upsell/cross-sell offers
- No subscription/bundle options
- No referral program at purchase
- No installation/setup guidance

**Post-purchase:**
- No email onboarding sequence
- No check-in at key milestones
- No expansion offers at right time
- No advocacy program for happy customers

### Missing Link Audit

| Funnel Stage | Existing Assets | Missing Opportunities |
|--------------|-----------------|----------------------|
| Awareness | Ads, content | Referral program? |
| Interest | Landing pages | Lead magnet? |
| Consideration | Product pages | Comparison tool? |
| Intent | Cart | Save for later? |
| Purchase | Checkout | Order bump? |
| Onboarding | Email 1 | Video tutorial? |
| Retention | None | Check-in sequence? |
| Expansion | None | Usage-based prompts? |
| Advocacy | None | Referral incentive? |

### Cross-Sell Mapping

Map products that naturally pair together:

| Product A | Natural Cross-Sell | When to Offer |
|-----------|-------------------|---------------|
| Running shoes | Socks, insoles | Cart/checkout |
| SaaS subscription | Premium features | After activation |
| Course | Coaching add-on | During course |
| Software | Training | Post-purchase |

---

## Industry Funnel Patterns

### E-commerce Funnels

**Standard:**
```
Visit → Browse → Product → Cart → Checkout → Purchase
```

**Enhanced:**
```
Visit → Browse → Product → Wishlist/Email → Retarget → Cart → Checkout → Upsell → Purchase → Post-purchase email → Review request → Repeat purchase
```

**Key metrics:**
- Cart abandonment rate (benchmark: 70%)
- Checkout abandonment rate (benchmark: 25%)
- Repeat purchase rate (benchmark: 25-40%)

### SaaS Funnels

**Standard:**
```
Visit → Trial/Freemium → Activation → Engagement → Conversion
```

**Enhanced:**
```
Visit → Content → Lead magnet → Nurture → Trial → Onboarding → Activation → Engagement → Conversion → Onboarding (paid) → Expansion → Advocacy
```

**Key metrics:**
- Trial-to-paid conversion (benchmark: 3-5% freemium, 15-25% free trial)
- Activation rate (varies by product)
- Expansion revenue % (benchmark: 30%+ of revenue)

### Lead Generation Funnels

**Standard:**
```
Visit → Form → Lead → Sales contact → Opportunity → Close
```

**Enhanced:**
```
Visit → Lead magnet → Nurture → Scorecard/Quiz → MQL → SDR qualify → Demo → SQL → Proposal → Close → Onboarding → Expansion
```

**Key metrics:**
- Lead-to-MQL conversion (benchmark: 20-30%)
- MQL-to-SQL conversion (benchmark: 30-50%)
- SQL-to-close rate (benchmark: 20-40%)

### Subscription/Membership Funnels

**Standard:**
```
Visit → Free content → Subscribe → Retain
```

**Enhanced:**
```
Visit → Free content → Email opt-in → Free trial → Subscribe → Onboard → Engage → Retain → Annual upgrade → Advocacy
```

**Key metrics:**
- Free-to-paid conversion (benchmark: 2-5%)
- Monthly churn rate (benchmark: 3-7%)
- Annual vs. monthly mix (benchmark: 30%+ annual)

---

## Funnel Prioritization Framework

### Calculate Opportunity Value

For each potential improvement:

```
Opportunity = (Current Volume) × (Conversion Gap) × (Revenue per Conversion)
```

**Example:**
```
Current: 1,000 visitors, 2% conversion, $100/conversion = $2,000 revenue
Potential: 1,000 visitors, 3% conversion, $100/conversion = $3,000 revenue
Opportunity value: $1,000/month = $12,000/year
```

### Prioritization Matrix

| Opportunity | Volume | Gap | Value | Ease | Priority |
|-------------|--------|-----|-------|------|----------|
| Checkout abandonment | 500/mo | 25% | $125 | Medium | High |
| Add cross-sell | 200/mo | 30% | $20 | Easy | High |
| Reduce form fields | 1000/mo | 10% | $50 | Easy | High |
| Redesign homepage | 5000/mo | 2% | $100 | Hard | Medium |
| Add video | 300/mo | 15% | $100 | Medium | Medium |

### The 80/20 Rule in Funnels

Typically:
- 80% of revenue comes from 20% of the funnel stages
- 80% of drop-off happens at 20% of the steps
- 80% of improvement potential is in 20% of the pages

**Focus ruthlessly on the high-impact stages before optimizing everything.**

---

## Funnel Visualization

### Basic Funnel Chart

```
┌─────────────────────────────────────────┐ 10,000
│            Website Visits               │
├───────────────────────────────┐         │ 3,000 (30%)
│      Product Page Views       │
├─────────────────────┐         │         │ 600 (20%)
│   Add to Cart       │
├───────────────┐     │         │         │ 300 (50%)
│  Checkout     │
├─────────┐     │     │         │         │ 150 (50%)
│ Purchase│
└─────────┘
```

### Leakage Analysis

At each stage, map where users go instead:

```
Product Page (3,000 visitors)
├─→ Add to Cart: 600 (20%)
├─→ Exit site: 1,500 (50%)
├─→ Browse other products: 600 (20%)
├─→ Check reviews/FAQ: 200 (7%)
└─→ Contact support: 100 (3%)
```

**Insight:** 50% exit from product page—that's the primary leak to investigate.

---

## Funnel Optimization Checklist

### Before Optimizing

- [ ] Have you mapped the complete funnel?
- [ ] Do you have baseline conversion rates at each stage?
- [ ] Have you identified the biggest blocked arteries?
- [ ] Have you audited for missing links?
- [ ] Do you know your industry benchmarks?
- [ ] Have you calculated opportunity values?

### During Optimization

- [ ] Are you testing bold changes, not tweaks?
- [ ] Are you measuring the right metrics?
- [ ] Are you waiting for statistical significance?
- [ ] Are you documenting learnings?

### After Optimization

- [ ] Did conversion improve at the target stage?
- [ ] Did downstream metrics also improve?
- [ ] Did any metrics unexpectedly decrease?
- [ ] Can this learning apply to other funnels?

---

## Advanced: Multi-Touch Attribution

### The Problem

Customers don't convert in a straight line. They might:
1. See a Facebook ad
2. Google your brand
3. Read a blog post
4. Leave
5. Get retargeted
6. Return via email
7. Convert

Which touchpoint gets credit?

### Attribution Models

| Model | Description | Best For |
|-------|-------------|----------|
| First-touch | First interaction gets 100% | Brand awareness campaigns |
| Last-touch | Final interaction gets 100% | Direct response |
| Linear | Equal credit to all touches | Understanding journey |
| Time-decay | Recent touches get more credit | Short sales cycles |
| Position-based | 40% first, 40% last, 20% middle | Balanced view |
| Data-driven | Algorithm assigns based on data | Sophisticated analysis |

### Practical Recommendation

1. Start with last-touch (simplest)
2. Add first-touch to understand acquisition
3. Graduate to position-based for balanced view
4. Only use data-driven with sufficient volume
