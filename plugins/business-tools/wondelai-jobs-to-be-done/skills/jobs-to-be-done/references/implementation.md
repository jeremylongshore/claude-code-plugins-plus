# Jobs-to-Be-Done -- Implementation Guide

## Overview

Apply Clayton Christensen's Jobs-to-Be-Done (JTBD) framework to understand the causal mechanism of customer choice and design products that people "hire" with confidence.

## Core Concept

Customers don't buy products -- they "hire" them to make progress in a specific circumstance.

**The JTBD statement format:**
```
When [situation/circumstance],
I want to [motivation/goal],
so I can [expected outcome/progress].
```

## Discovery: The JTBD Interview

### Interview Protocol

```markdown
## JTBD Interview Guide

Opening:
"Tell me about the last time you [bought/switched to/started using] [product category]. Walk me through exactly what happened."

Key probes:
- "What was going on in your life at that time?"
- "What made that day the day you decided to do something about it?"
- "What did you search for? What words did you use?"
- "What did you almost buy instead?"
- "What were you worried might go wrong?"
- "Who else was involved in the decision?"
- "What would it have looked like if you hadn't solved this?"

Close:
- "If you could wave a magic wand and improve one thing about [product], what would it be?"
```

### The Four Forces of Progress

```markdown
## Forces Analysis for a Recent Customer

PUSH (away from current situation):
- What was frustrating about the old way?
- What was the "last straw" moment?

PULL (toward new solution):
- What attracted them to your product?
- What progress were they imagining?

ANXIETY (about switching):
- What did they worry might go wrong?
- What questions did they need answered before buying?

HABIT (inertia of current behavior):
- What made it easy to stay with the old way?
- What had they tried before that didn't work?
```

## Segmenting by Job, Not Demographics

```markdown
## Job-Based Segment Map

Job: "Help me look competent to my boss when presenting data"

Hired-for circumstances:
- Board meeting prep (enterprise analyst)
- Client pitch (consultant)
- Quarterly review (startup founder)

Note: These may be three very different demographic segments
but share the same job. Build for the job, not the demo.
```

## Opportunity Score Analysis

```markdown
## Opportunity Score Formula (Ulwick)

Importance - max(0, Importance - Satisfaction) = Opportunity Score

| Desired Outcome | Importance (1-10) | Satisfaction (1-10) | Opportunity |
|----------------|------------------|--------------------| ------------|
| "Get results in < 1 minute" | 9 | 4 | 9 + (9-4) = 14 |
| "Share with team easily" | 8 | 7 | 8 + (8-7) = 9 |
| "Export to PDF" | 6 | 8 | 6 + 0 = 6 (over-served) |

High opportunity (>10): invest here
Over-served (<6): reduce complexity/cost
```

## References

- Christensen, C., Hall, T., Dillon, K., Duncan, D. (2016). *Competing Against Luck.* HarperBusiness.
- Ulwick, A. (2016). *Jobs to Be Done: Theory to Practice.*
