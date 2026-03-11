---
name: strategic-clarity
description: Guided workflow for establishing team identity, boundaries, and strategic clarity. Use when starting a new role, inheriting ambiguity, when a team lacks clear identity, or when you need to define "what we own" vs "what we don't". Triggers include "strategic clarity", "team identity", "new role", "inherited ambiguity", "what does my team own", or "define our boundaries".
argument-hint: [phase: absorb/audit/articulate/align]
---

# Strategic Clarity Workflow

## Overview

A 4-phase workflow for establishing team identity and strategic positioning.

```
+---------+    +---------+    +-----------+    +---------+
| ABSORB  | -> |  AUDIT  | -> | ARTICULATE| -> |  ALIGN  |
|         |    |         |    |           |    |         |
| Context |    | Reality |    | Identity  |    | Buy-in  |
+---------+    +---------+    +-----------+    +---------+
```

**When to use:** Starting a new role, inherited ambiguity, team lacks clear identity
**Output:** Team charter, value proposition, capability audit

### Advanced Patterns

1. **The inherited narrative trap** — When you inherit a team, everyone will tell you what the team does. Their descriptions will conflict. Don't average them — map the contradictions. Where people disagree about team scope is exactly where boundaries are unclear and where future conflicts will emerge. The contradictions are the diagnosis
2. **Capability vs. responsibility** — Teams often confuse what they *can* do with what they *should* do. A messaging team that *can* build email doesn't mean email is their responsibility. During the audit phase, separate capabilities (what the code does) from responsibilities (what stakeholders expect). Mismatches between these create the biggest organizational friction
3. **The "without us" test** — To find your team's real value, ask: "If our team disappeared tomorrow, what would break first?" The thing that breaks first is your core value. The thing that breaks second is your growth opportunity. The thing nobody notices is your candidate for deprecation. This test cuts through aspirational mission statements to find ground truth
4. **Adjacent team mapping** — Don't just define what you own. Explicitly define the boundary with each adjacent team: "We own the push delivery pipeline. Platform team owns the notification scheduling. We hand off at [specific interface]." Vague boundaries between teams cause more organizational damage than vague team charters. Name the seams
5. **The 30-60-90 checkpoint** — Strategic clarity isn't a one-time exercise. At 30 days, you should have hypotheses. At 60 days, you should have a charter draft. At 90 days, you should have stakeholder alignment. If you're still "absorbing" at day 60, you're avoiding the hard work of articulating a position. Set a deadline for yourself

## How This Skill Works

I'll guide you through each phase with:
1. **Questions** to gather context
2. **Activities** to complete
3. **AI-assisted prompts** for each deliverable
4. **Checklists** to track progress

Tell me which phase you're in (or starting fresh), and I'll help you through it.

---

## Phase 1: ABSORB (Week 1)

### Goal
Understand what exists before forming opinions.

### Activities
- Read all existing documentation
- Meet with team members
- Study handover notes
- Review historical decisions

### AI Assistance

**Prompt: Synthesize Context**
Share your notes and I'll help you:
1. Identify key themes
2. Surface tensions or contradictions
3. List what's still unclear

**Prompt: Question Generation**
Based on your context, I'll suggest:
- Questions you should be asking
- Who to talk to for answers
- What documents to read next

### Phase 1 Checklist
- [ ] Reading notes captured
- [ ] Key questions documented
- [ ] Initial mental model forming

---

## Phase 2: AUDIT (Week 2)

### Goal
Understand what actually exists vs. what's claimed.

### Activities
- Systematic codebase review
- Map capabilities to code
- Identify gaps
- Compare reality to documentation

### AI Assistance

**Prompt: Capability Mapping**
Share your team's claimed responsibilities and I'll help build an audit template:
- Capability name
- Status (exists/partial/missing)
- Evidence (code files/patterns)
- Gap description
- Impact assessment

**Prompt: Codebase Exploration**
Point me at code or systems and I'll help you understand:
- What product capability it represents
- The business logic encoded
- Use cases supported
- What's notably missing

### Phase 2 Checklist
- [ ] Capability audit document created
- [ ] Gap inventory prioritized
- [ ] Reality vs. perception documented

### Output: Capability Audit Template

```markdown
# Capability Audit: [Team Name]

| Capability | Status | Evidence | Gap | Impact |
|------------|--------|----------|-----|--------|
| [Capability 1] | Exists | [code/system] | — | — |
| [Capability 2] | Partial | [code/system] | [missing piece] | [user impact] |
| [Capability 3] | Missing | — | [full description] | [business impact] |
```

---

## Phase 3: ARTICULATE (Week 3)

### Goal
Define and document team identity clearly.

### Activities
- Draft mission statement
- Define responsibility boundaries
- Create value proposition
- Build communication frameworks

### AI Assistance

**Prompt: Mission Drafting**
Share what you actually own vs. don't own, and I'll help draft:
- Clear mission statement
- Distinction from adjacent teams
- Concrete, not vague language

**Prompt: Charter Structure**
I'll help structure a one-page team charter:
- What we're accountable for
- What we explicitly don't own
- How we create value
- Key metrics we move

**Prompt: Value Narrative**
I'll help create communication frameworks:
- One-sentence pitch
- "Without us, [consequence]" statements
- Boundary explanations for adjacent teams
- Leadership-friendly framing

### Phase 3 Checklist
- [ ] Team charter drafted
- [ ] Value proposition documented
- [ ] Boundary contract defined

### Output: Team Charter Template

```markdown
# [Team Name] Charter

## Mission
[One sentence: what we do and why it matters]

## We Own
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

## We Don't Own
- [Adjacent area 1] — owned by [other team]
- [Adjacent area 2] — owned by [other team]

## Value Proposition
Without us: [what breaks or doesn't exist]
With us: [what users/business gets]

## Key Metrics
- [Primary metric we move]
- [Secondary metric]

## Boundaries
| Area | Us | Them |
|------|----|----- |
| [Shared area] | [Our part] | [Their part] |
```

---

## Phase 4: ALIGN (Week 4)

### Goal
Validate and socialize the work.

### Activities
- Present to manager
- Discuss with peer PMs
- Gather feedback
- Iterate based on input

### AI Assistance

**Prompt: Stakeholder Role-Play**
Tell me who you're presenting to and their likely concerns — I'll role-play as them to help you prepare for pushback.

**Prompt: Presentation Polish**
Share your draft charter and I'll help:
- Sharpen the language
- Anticipate objections
- Add evidence for claims
- Make it memorable

### Phase 4 Checklist
- [ ] Manager alignment achieved
- [ ] Peer PM feedback incorporated
- [ ] Final documents published
- [ ] Communication plan for broader sharing

---

## Document Checklist

| Document | Location | Status |
|----------|----------|--------|
| Reading notes | `context/` | [ ] |
| Capability audit | `analysis/capability-audit.md` | [ ] |
| Team charter | `strategy/team-charter.md` | [ ] |
| Value proposition | `strategy/value-proposition.md` | [ ] |
| Stakeholder map | `analysis/stakeholder-map.md` | [ ] |

---

## Success Criteria

By the end of this workflow, you should be able to:

- [ ] Articulate team value in one sentence
- [ ] Explain boundary with adjacent teams clearly
- [ ] Have manager endorsement of your framing
- [ ] Have peer PMs understand what you own
- [ ] Feed gap inventory into roadmap planning

---

## Getting Started

Tell me:
1. **What's your situation?** (New role? Inherited team? Identity crisis?)
2. **What phase are you in?** (Or starting fresh?)
3. **What do you have so far?** (Notes? Docs? Nothing?)

I'll guide you through the appropriate phase.
