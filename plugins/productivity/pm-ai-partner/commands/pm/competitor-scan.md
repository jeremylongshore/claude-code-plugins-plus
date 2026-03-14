---
name: competitor-scan
description: Analyze the competitive landscape and identify gaps
allowed-tools: Read, Glob, Grep
---

Help me analyze the competitive landscape for: $ARGUMENTS

## Instructions

Conduct a structured competitive analysis. The goal is not a feature checklist — it's identifying where competitors are genuinely better, where we're differentiated, and what we should actually do about it.

### Process

1. **Map the landscape** — Identify direct competitors, indirect alternatives, and "do nothing" options users have
2. **Analyze positioning** — How does each competitor position themselves? What do they claim vs. deliver?
3. **Compare with insight** — Feature comparison with "so what?" for each gap
4. **Assess and recommend** — Classify each competitive gap as Ignore / Monitor / Respond / Lead

### Tools to Use

- Use web fetch to pull competitor websites, pricing pages, and changelogs
- Search for competitor reviews, G2/Capterra ratings, and app store feedback
- Look for competitor engineering blogs or public repos for technical insight
- Check social media and community forums for user sentiment

### Output Format

```markdown
# Competitive Analysis: [Market/Competitor]

## Landscape Map
| Player | Type | Positioning | Target Audience |
|--------|------|-------------|-----------------|

## Positioning Map
[Mermaid quadrant or description of how players position on key axes]

## Feature Comparison (with insight)
| Capability | Us | Competitor A | Competitor B | Insight |
|---|---|---|---|---|
| [Feature] | [status] | [status] | [status] | [Why this matters or doesn't] |

## Strengths to Defend
1. **[Strength]** — Why it matters, evidence it's real

## Gaps to Evaluate
| Gap | Who Has It | Response | Reasoning |
|-----|-----------|----------|-----------|
| [Gap] | [Competitor] | Ignore/Monitor/Respond/Lead | [Why] |

## Recommendation
1. [Prioritized action with rationale]
```

### Principles

- **Objective, not defensive** — If a competitor is genuinely better at something, say so
- **Jobs-to-be-done framing** — Competitors are whoever solves the same user need, not just the same category
- **"Why haven't they?" is as important as "why have they?"** — Missing features may signal constraints, not ignorance
- **Feature parity is a trap** — Only recommend matching features that demonstrably drive competitor advantage
