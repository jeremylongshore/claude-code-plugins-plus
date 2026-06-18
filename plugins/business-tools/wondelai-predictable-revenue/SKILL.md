---
name: predictable-revenue
description: 'Build a scalable outbound B2B sales process with specialized roles (SDR, AE, CSM). Use when the user mentions "outbound sales", "Cold Calling 2.0", "prospecting emails", "sales pipeline", "SDR process", "B2B SaaS sales", "sales development", or "pipeline velocity". Also trigger when setting up a sales team from scratch, designing cold email sequences, or building qualification frameworks to improve close rates. Covers lead generation, qualification frameworks, and separating prospecting from closing. For offer design, see hundred-million-offers. For persuasion science, see influence-psychology.'
license: MIT
metadata:
  author: wondelai
  version: "1.2.0"
---

# Predictable Revenue Framework

A systematic approach to building a scalable, predictable B2B sales machine — the outbound prospecting system that helped Salesforce add $100M in recurring revenue.

## Core Principle

**Predictable lead generation drives predictable revenue.** The biggest mistake in sales is having the same people prospect AND close — specialization creates a repeatable, scalable machine. Traditional cold calling is dead; Cold Calling 2.0 (mass, personalized cold emails that generate referrals to the right person) is the new outbound.

## Scoring

**Goal: 10/10.** Rate any sales process 0-10 on predictability, specialization, and process maturity: 10/10 means clear role separation, repeatable prospecting, and predictable pipeline generation; lower scores mean ad-hoc sales or reliance on heroics. Always give the current score and the specific improvements needed to reach 10/10.

## The Three Types of Leads

**Not all leads are equal — treat them differently.**

| Type | Source | Conversion | Cost | Example |
|------|--------|------------|------|---------|
| **Seeds** | Word of mouth, referrals, organic | Highest | Lowest (takes time) | Customer referral, NPS-driven |
| **Nets** | Marketing campaigns, inbound | Medium | Medium | Content, SEO, webinars |
| **Spears** | Outbound prospecting | Lower but predictable | Higher (people-intensive) | Cold Calling 2.0 |

**Key insight:** Most companies over-invest in nets and under-invest in spears; seeds are the best but can't be manufactured quickly. Invest accordingly — customer success and referral programs (seeds), content and paid acquisition (nets), SDR team (spears).

See: [references/lead-types.md](references/lead-types.md) for lead source strategy and investment allocation.

## Sales Role Specialization

**The #1 principle: separate prospecting from closing.** When AEs prospect and close, they hate prospecting and pipeline becomes feast-or-famine.

| Role | Focus | Metrics |
|------|-------|---------|
| **SDR (Sales Development Rep)** | Outbound prospecting → qualified opportunities | Qualified meetings/month |
| **MDR (Market Development Rep)** | Inbound lead qualification | Qualified leads/month |
| **AE (Account Executive)** | Close deals | Revenue closed, win rate |
| **CSM (Customer Success Manager)** | Retain and grow accounts | Retention, expansion revenue |

### SDR (Sales Development Rep)

Generate qualified pipeline: research target accounts, send Cold Calling 2.0 emails, get referred to the right person, qualify with ANUM, pass to AEs. Not their job: closing, inbound leads, or existing customers. One SDR typically generates 10-20 qualified opportunities per month — measure opportunities, response rate, meetings booked, and pipeline value.

### AE (Account Executive)

Close deals from qualified pipeline: run discovery, demo, negotiate, close, hand off to CSM. Not their job: prospecting (SDR), inbound qualification (MDR), or post-sale management (CSM). Measure revenue closed, win rate, average deal size, and sales cycle length.

### CSM (Customer Success Manager)

Retain and grow accounts: onboard, drive adoption, surface expansion opportunities, prevent churn. Measure net revenue retention, churn rate, expansion revenue, and NPS/CSAT.

**The virtuous cycle:** SDR generates pipeline → AE closes → CSM retains/grows → happy customer refers (Seeds).

See: [references/roles.md](references/roles.md) for role definitions, career paths, and hiring profiles.

## Cold Calling 2.0

**Outbound prospecting that replaces traditional cold calling**, which fails on every front: 1-3% connection rate, gatekeepers, brand damage, no scalability.

```
1. Build list → 2. Send mass email → 3. Get referral → 4. Call the referral → 5. Qualify
```

### Step 1: Build Target Account List

Define your Ideal Customer Profile (company size, industry, tech stack, geography, pain points), then build the list via LinkedIn Sales Navigator, ZoomInfo/Apollo/Clearbit, or industry directories. Target 200-500 accounts per SDR per quarter.

### Step 2: The Referral Email

**The core innovation: don't email the decision maker — email above them and ask for a referral down.** Senior people forward emails, and referrals get 3-5x higher response because the introduction comes from inside the company.

**Subject:** Quick question

> Hi [Name],
>
> I'm not sure if you're the right person to speak to about [specific topic] at [Company], but I was hoping you could point me to the right person.
>
> We help [companies like theirs] with [specific value prop].
>
> Would you mind pointing me to the right person to talk to?
>
> Thanks,
> [Your name]

Keep it short (<100 words), no pitch, no attachments or links; ask for a referral, not a meeting; make it easy to forward. Response rate: 9-15% vs. 1-3% for traditional cold emails.

### Step 3: Follow Up

| Day | Action |
|-----|--------|
| 1 | Send referral email |
| 3 | Follow up if no response |
| 7 | Second follow-up (different angle) |
| 14 | Break-up email ("Should I close your file?") |
| 30 | Re-engage (new trigger event or content) |

Break-up emails work because people respond to losing the opportunity (scarcity):

> Hi [Name],
>
> I haven't heard back from you. I don't want to be a pest.
>
> Should I close your file, or would it make sense to chat?

### Step 4: Qualify with ANUM

| Criteria | Question | Strong Signal | Weak Signal |
|----------|----------|---------------|-------------|
| **A**uthority | Can this person decide? | Decision maker or strong influencer | No buying power |
| **N**eed | Do they have the problem you solve? | Active pain, seeking solutions | "Nice to have" |
| **U**rgency | When must they solve it? | This quarter, budget allocated | "Someday" |
| **M**oney | Can they afford it? | Budget exists, within range | No budget, too expensive |

Call structure: rapport (2 min) → set agenda ("understand your situation, see if there's a fit") → discovery questions with ANUM built in (10-15 min) → next steps (if qualified, schedule AE demo).

### Step 5: Hand Off to AE

Include account background and ICP match, contact details and role, pain points, ANUM notes, agreed next steps, and competitive intel. SDR introduces AE on a brief 3-way call or email, then drops off.

**Ethical boundary:** Comply with spam laws (CAN-SPAM, GDPR), honor opt-outs immediately, and represent your offer honestly — referral emails work because they're genuine requests, not tricks.

See: [references/cold-calling-2.md](references/cold-calling-2.md) for email templates, sequences, and scripts; [references/qualification.md](references/qualification.md) for ANUM discovery questions.

## Pipeline Math

Work backward from the revenue goal:

```
Revenue Goal ÷ Average Deal Size = Deals Needed
Deals Needed ÷ Win Rate = Opportunities Needed
Opportunities Needed ÷ SDR Conversion = Prospects Needed
Prospects Needed ÷ Response Rate = Emails Needed
```

**Example:** $1M ARR ÷ $20K deals = 50 deals; ÷ 25% win rate = 200 opportunities; at 10% response rate and 10% response-to-qualified conversion = 20,000 emails ≈ 2-3 SDRs (each sends 300-500/month).

| Metric | Benchmark |
|--------|-----------|
| Emails per SDR per day | 50-100 |
| Response rate | 9-15% |
| Qualified opportunities per SDR per month | 10-20 |
| AE demo-to-close rate | 20-30% |
| Average sales cycle | 30-90 days |

See: [references/pipeline-math.md](references/pipeline-math.md) for revenue modeling templates.

## Building the Sales Development Team

### Hiring SDRs

Hire for coachability (the most important trait), curiosity, strong writing, resilience, and organization — experience is optional. Source recent graduates, career changers, and internal transfers. Career path: SDR (6-18 months) → Senior SDR → AE or SDR Manager.

### SDR Ramp Time

| Phase | Timeline | Expectations |
|-------|----------|-------------|
| Training | Weeks 1-2 | Product knowledge, tools, process |
| Shadowing | Weeks 3-4 | Observe experienced SDRs, practice |
| Ramping | Months 2-3 | 50% of quota |
| Full quota | Month 4+ | 100% of quota |

Expect 3-4 months to full productivity.

### SDR Compensation

Base + variable, typically 60/40 or 70/30. Pay variable per qualified opportunity generated, with bonuses for opportunities that close and for exceeding quota.

See: [references/team-building.md](references/team-building.md) for hiring, onboarding, and compensation detail.

## Metrics and Dashboards

### Leading Indicators (Predictive)

Emails sent per SDR per day, response rate, meetings booked per week, qualified opportunities per month, pipeline value generated.

### Lagging Indicators (Results)

Revenue closed, win rate, average deal size, sales cycle length, customer acquisition cost (CAC).

### Efficiency Metrics

Cost per qualified opportunity, SDR:AE ratio (typically 2-3 SDRs per AE), LTV:CAC (target >3:1), payback period.

**Cadence:** daily activity metrics → weekly pipeline → monthly revenue → quarterly efficiency.

See: [references/metrics.md](references/metrics.md) for dashboard templates.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **AEs prospecting** | Feast-or-famine pipeline | Hire dedicated SDRs |
| **Long, pitchy emails** | Low response rate | Short, referral-focused emails |
| **No ICP definition** | Effort wasted on wrong accounts | Define ICP before hiring SDRs |
| **Too few SDRs** | Not enough pipeline | Work backward from revenue goal |
| **No hand-off process** | Leads fall through cracks | Standardize SDR→AE handoff |
| **Measuring activity, not results** | Busy but not productive | Track qualified opportunities, not emails |

## Quick Diagnostic

Audit any B2B sales process:

| Question | If No | Action |
|----------|-------|--------|
| Are prospecting and closing separated? | SDRs doing both = bottleneck | Create dedicated SDR role |
| Is there a defined outbound process? | Ad-hoc prospecting | Implement Cold Calling 2.0 |
| Can you predict pipeline 3 months out? | Revenue is unpredictable | Build pipeline math model |
| Do you know your lead type mix? | Over-reliance on one source | Balance seeds, nets, spears |
| Is SDR→AE handoff standardized? | Leads lost in transition | Create handoff checklist |

## Reference Files

- [lead-types.md](references/lead-types.md): Seeds, nets, spears strategy and investment
- [roles.md](references/roles.md): SDR, MDR, AE, CSM role definitions and hiring
- [cold-calling-2.md](references/cold-calling-2.md): Email templates, sequences, follow-up cadence
- [pipeline-math.md](references/pipeline-math.md): Revenue modeling, capacity planning
- [team-building.md](references/team-building.md): Hiring, onboarding, compensation, career paths
- [metrics.md](references/metrics.md): Dashboard templates, KPI tracking
- [qualification.md](references/qualification.md): ANUM framework, discovery questions
- [case-studies.md](references/case-studies.md): Salesforce, HubSpot, and scaling stories

## Further Reading

For the complete system:

- [*"Predictable Revenue"*](https://www.amazon.com/Predictable-Revenue-Business-Practices-Salesforce-com/dp/0984380213?tag=wondelai00-20) by Aaron Ross & Marylou Tyler
- [*"From Impossible to Inevitable"*](https://www.amazon.com/Impossible-Inevitable-Hyper-Growth-Companies-Predictable/dp/1119166713?tag=wondelai00-20) by Aaron Ross & Jason Lemkin (scaling to $100M+ ARR)

## About the Author

**Aaron Ross** built the outbound sales process at Salesforce.com that added $100M+ in recurring revenue, and co-founded Predictable Revenue Inc. His book *Predictable Revenue* — known as "The Bible of Outbound Sales" — made Cold Calling 2.0 the standard for B2B outbound prospecting.
