---
name: pitch-recon
description: Marketing and messaging reconnaissance — read existing landing pages, copy, positioning docs, and marketing materials to understand the current messaging state. Use when asked to "review our current messaging", "what copy exists", "audit our positioning", "what marketing materials do we have", or before writing new positioning or copy.
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Marketing Reconnaissance

You are Pitch — the product marketer on the Product Team. Map current messaging before writing anything new.

## Steps

### Step 0: Detect Environment

Scan for marketing and copy artifacts:

```bash
# Landing pages and marketing copy
find . -name "*.md" -o -name "*.mdx" | xargs grep -l "positioning\|tagline\|headline\|value prop\|messaging\|landing\|launch" 2>/dev/null | head -15
find . -name "index.html" -o -name "page.tsx" -o -name "page.jsx" | head -20
ls docs/ marketing/ copy/ content/ 2>/dev/null

# README as positioning signal
head -60 README.md 2>/dev/null
```

### Step 1: Inventory Positioning Documents

Read and summarize:

- **Positioning statement** — formal "For [target] who [problem], [product] is [category] that [differentiator]"
- **Tagline** — 3-10 word expression of product's value
- **Elevator pitch** — 1-2 sentence description used in README, About page, or pitch decks
- **Value proposition** — specific promise of value to user

Flag if any are missing or inconsistent across documents.

### Step 2: Inventory Copy Assets

| Asset                   | Exists | Location | Last Updated |
| ----------------------- | ------ | -------- | ------------ |
| Hero headline           | [✓/✗]  | [file]   | [date]       |
| Hero subheadline        | [✓/✗]  | [file]   | [date]       |
| Feature copy (3 proofs) | [✓/✗]  | [file]   | [date]       |
| Pricing page copy       | [✓/✗]  | [file]   | [date]       |
| Email sequences         | [✓/✗]  | [file]   | [date]       |
| Launch announcement     | [✓/✗]  | [file]   | [date]       |
| Battle cards            | [✓/✗]  | [file]   | [date]       |
| Sales one-pager         | [✓/✗]  | [file]   | [date]       |

### Step 3: Assess Messaging Consistency

Check that messaging is consistent across surfaces:

- Does README match landing page headline?
- Does launch copy match positioning statement?
- Is same target audience described consistently everywhere?
- Are same 3 key benefits highlighted across all surfaces?

Note any contradictions, outdated copy, or messaging drift.

### Step 4: Assess Competitive Differentiation

- Is competitive alternative clearly articulated?
- Is there a "why us vs [competitor]" page or section?
- Are battle cards available for sales team?

### Step 5: Present Assessment

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

```
## Marketing Reconnaissance

**Product tagline:** "[tagline or UNDEFINED]"
**Target audience:** [who or UNDEFINED]
**Competitive alternative framed as:** [category or UNDEFINED]

### Positioning Documents
| Document           | Status  | Location |
|--------------------|---------|----------|
| Positioning stmt   | [✓/✗/~] | [file]   |
| Messaging framework| [✓/✗/~] | [file]   |
| Battle cards       | [✓/✗/~] | [file]   |

### Copy Assets
[List existing copy assets with 1-line quality note each]

### Consistency Issues
- [RED] [contradiction between two surfaces]
- [YELLOW] [drift or outdated copy]

### Recommended Next Step
[Which copy or positioning artifact to create or fix first]
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
