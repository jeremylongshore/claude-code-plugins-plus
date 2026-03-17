# CRO Methodology -- Implementation Guide

## Overview

Apply Conversion Rate Optimization methodology to improve landing pages, onboarding flows, and checkout processes through systematic testing.

## CRO Process (5 Stages)

### 1. Research & Discovery

```markdown
## Heuristic Audit Checklist

Landing Page:
- [ ] Above-the-fold value proposition is clear within 5 seconds
- [ ] CTA is prominent (contrast, size, placement)
- [ ] Social proof is visible (reviews, logos, testimonials)
- [ ] Form fields are minimal (ask only what is needed)
- [ ] Mobile layout is usable (tap targets >= 44px)

Checkout:
- [ ] Progress indicator shows step count
- [ ] Error messages are specific and helpful
- [ ] Trust signals are near the payment button
- [ ] Guest checkout is offered
```

### 2. Hypothesis Formation

**Template:**
```
Because [observation from data/research],
if we [change X],
then [metric Y] will improve by [estimated Z%],
because [reasoning].

Primary metric: [conversion rate / revenue per visitor / sign-up rate]
Secondary metric: [bounce rate / time on page]
Risk: [potential negative side effects]
```

### 3. Test Design

**Minimum detectable effect (MDE) calculator:**
```python
import math

def minimum_sample_size(
    baseline_rate: float,     # e.g., 0.03 for 3%
    mde: float,               # minimum effect to detect, e.g., 0.20 for 20% relative lift
    alpha: float = 0.05,      # significance level
    power: float = 0.80,      # statistical power
) -> int:
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    z_alpha = 1.96 if alpha == 0.05 else 2.576
    z_beta = 0.842 if power == 0.80 else 1.282
    n = (z_alpha + z_beta) ** 2 * (p1*(1-p1) + p2*(1-p2)) / (p2 - p1) ** 2
    return math.ceil(n)

# Example: 3% baseline, detect 20% relative lift
n = minimum_sample_size(0.03, 0.20)
print(f"Need {n} visitors per variant ({n*2} total)")
```

### 4. Analysis

```markdown
## A/B Test Result Template

**Test name:** [description]
**Hypothesis:** [from above template]
**Duration:** [start date] to [end date]
**Sample:** Control [n=X, CR=Y%] | Variant [n=X, CR=Y%]
**Relative lift:** [+/- Z%]
**Statistical significance:** [p-value < 0.05 = significant]
**Decision:** Ship / Iterate / Abandon
**Learning:** [one sentence describing what we learned]
```

### 5. Iteration

- Document all test results (wins AND losses)
- Build a test backlog ordered by ICE score (Impact x Confidence x Ease)
- Run 2-4 tests concurrently on independent pages

## ICE Prioritization

```markdown
| Hypothesis | Impact (1-10) | Confidence (1-10) | Ease (1-10) | ICE Score |
|-----------|--------------|------------------|------------|----------|
| Simplify signup form (3 -> 1 field) | 8 | 9 | 8 | 576 |
| Add social proof near CTA | 7 | 7 | 9 | 441 |
| Test headline copy variant | 6 | 6 | 9 | 324 |
```

## References

- Eisenberg, B. & Eisenberg, J. (2006). *Call to Action.*
- [ConversionXL CRO Guide](https://cxl.com/blog/cro-guide/)
