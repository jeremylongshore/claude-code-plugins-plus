---
name: traction-eos
description: |
  Implement the Entrepreneurial Operating System (EOS) to align vision and execution across a company. Use when the user mentions "EOS", "V/TO", "quarterly rocks", "Level 10 meetings", "accountability chart", or "IDS process". Covers the six EOS components: Vision, People, Data, Issues, Process, Traction. For team motivation design, see drive-motivation. For lean experimentation, see lean-startup. Trigger with 'traction', 'eos'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [business, traction-eos]
---
# Entrepreneurial Operating System (EOS)

A complete system for running a business with six key components. Designed for entrepreneurial companies ($2M-$50M revenue, 10-250 employees) that want to align vision and execution.

## Core Principle

**Most businesses suffer from the same core issues: people, vision, traction.** EOS provides a simple, complete operating system that strengthens the Six Key Components of any organization.

**The foundation:** Great vision without traction is hallucination. Traction without vision is aimless. EOS connects the two through a practical, weekly operating rhythm.

## Scoring

**Goal: 10/10.** When evaluating or implementing business processes, rate 0-10 based on EOS component strength. A 10/10 means all six components are strong, meetings are productive, and quarterly rocks are consistently achieved; lower scores indicate gaps. Always provide current score and improvements to reach 10/10.

## The Six Key Components

```
Vision → People → Data → Issues → Process → Traction
```

Every business is built on these six components. EOS strengthens all six.

### 1. Vision Component

**Question:** Does everyone in the organization know where you're going and how you plan to get there?

**Tool: Vision/Traction Organizer (V/TO)**

The V/TO answers eight questions on two pages:

| Question | What It Defines | Example |
|----------|----------------|---------|
| **Core Values** | 3-7 non-negotiable beliefs | "Own it", "Do the right thing", "Grow or die" |
| **Core Focus** | Purpose/cause/passion + niche | "Simplify small business" + "Cloud accounting" |
| **10-Year Target** | Big, hairy, audacious goal | "$100M revenue" or "10,000 customers" |
| **Marketing Strategy** | Target market, 3 uniques, proven process, guarantee | Who you serve, why you're different |
| **3-Year Picture** | What company looks like in 3 years | Revenue, profit, headcount, key metrics |
| **1-Year Plan** | Revenue, profit, measurables, goals | Specific targets for this year |
| **Quarterly Rocks** | 3-7 priorities for this quarter | The most important things to accomplish in 90 days |
| **Issues List** | All unresolved obstacles | Problems, ideas, opportunities to discuss |

**Process:**
1. Leadership team completes V/TO together (2-day off-site)
2. Share with entire organization
3. Review quarterly
4. Update annually

**Key insight:** If leadership team can't agree on V/TO, you have a bigger problem. Alignment comes first.

See: [references/vto.md](references/vto.md) for V/TO templates and exercises.

### 2. People Component

**Question:** Do you have the right people in the right seats?

**Tool: Accountability Chart**

Not an org chart—an accountability chart. Defines the structure and who owns what.

**Structure:**
```
Visionary ←→ Integrator
              ├── Sales/Marketing
              ├── Operations
              └── Finance
```

**Two key roles:**
- **Visionary:** Big ideas, culture, key relationships, creative problem solving
- **Integrator:** Runs business day-to-day, manages team, executes vision, resolves conflicts

**Rule:** One person per seat. No shared accountability.

**Tool: People Analyzer**

Evaluate every person on two dimensions:

**1. Right Person (core values fit)**

| Core Value | + (most of the time) | +/- (sometimes) | - (rarely) |
|-----------|---------------------|-----------------|------------|
| Own it | + | | |
| Do the right thing | | +/- | |
| Grow or die | + | | |

**Standard:** Must be "+" on all core values. One "+/-" is a conversation. Any "-" is wrong person.

**2. Right Seat (GWC)**
- **G**et it: Understands the role
- **W**ant it: Genuinely wants the role
- **C**apacity: Has the mental, physical, emotional capacity

**Must be "yes" on all three.** If missing any one, wrong seat.

**The formula:** Right People + Right Seats = A-players

**People decisions:**
- Right person, right seat → Keep and invest in
- Right person, wrong seat → Move to right seat
- Wrong person, right seat → Coaching/exit (hardest call)
- Wrong person, wrong seat → Exit immediately

See: [references/people.md](references/people.md) for accountability chart and people analyzer templates.

### 3. Data Component

**Question:** Are you managing based on objective data, or subjective opinions?

**Tool: Scorecard**

A weekly report card of 5-15 numbers that tell you how the business is doing.

**Scorecard rules:**
- Activity-based metrics (leading indicators), not results (lagging)
- Weekly numbers (monthly is too slow)
- Every number has an owner
- Every number has a goal
- Red/green: on track or off track

**Example Scorecard:**

| Metric | Owner | Goal | W1 | W2 | W3 | W4 |
|--------|-------|------|----|----|----|----|
| Revenue | Sales Lead | $50K/wk | ✓ | ✓ | ✗ | ✓ |
| New Leads | Marketing | 100/wk | ✓ | ✗ | ✓ | ✓ |
| Demos Completed | Sales | 20/wk | ✗ | ✓ | ✓ | ✓ |
| Customer NPS | Support | >50 | ✓ | ✓ | ✓ | ✓ |
| Cash Balance | Finance | >$200K | ✓ | ✓ | ✓ | ✓ |

**Benefits:**
- Spot problems 2-4 weeks earlier
- Reduce "gut feeling" management
- Create accountability without micromanagement
- Everyone knows the score

**Metric selection:** If you had to go on vacation for 4 weeks, what 5-15 numbers would tell you how the business is doing?

See: [references/data.md](references/data.md) for scorecard templates and metric selection.

### 4. Issues Component

**Question:** Are you identifying, discussing, and solving issues quickly?

**Tool: Issues Solving Track (IDS)**

**I**dentify → **D**iscuss → **S**olve

**Step 1: Identify**
- What's the real issue? (Not the symptom)
- Ask "Why?" until you reach root cause
- State the issue in one sentence

**Step 2: Discuss**
- Everyone gets input (not equal time)
- Tangents are stopped
- Focus on the ONE issue
- Time-boxed (usually 5-15 minutes)

**Step 3: Solve**
- Decision is made
- Action items are assigned (who + what + when)
- Move to next issue

**Three types of issues:**

| Type | Examples | Action |
|------|----------|--------|
| **Problems** | Customer churn, team conflict, system outage | IDS → solve |
| **Ideas** | New feature, process change, market opportunity | IDS → decide (yes/no/later) |
| **Obstacles** | Blocking a rock, resource constraint, dependency | IDS → remove or escalate |

**Issues list rules:**
- Everyone can add issues
- Prioritize: most important first
- Not all issues get solved every meeting
- Unsolved issues carry forward

**Common IDS mistakes:**
- Discussing symptoms, not root cause
- Rehashing same issue every week
- No clear action items
- Too much discussion, not enough solving

See: [references/issues.md](references/issues.md) for IDS facilitation guides.

### 5. Process Component

**Question:** Have you documented and consistently followed your core processes?

**Tool: Core Process Documentation**

**The 20/80 rule:** Document 20% of your processes to get 80% consistency.

**Identify core processes:**
- HR process (hiring, onboarding, reviews)
- Sales process (lead → close)
- Operations process (delivery, fulfillment)
- Customer service process (support → resolution)
- Finance process (invoicing, collections)

**Documentation format:**
1. Name the process
2. List 5-20 major steps
3. Add just enough detail (not a 50-page manual)
4. Make it visual where possible

**Example: Sales Process "The Closer"**
1. Qualify lead (BANT: Budget, Authority, Need, Timeline)
2. Discovery call (30 min, use question guide)
3. Demo (customize to their pain points)
4. Proposal (send within 24 hours)
5. Follow up (3 touches in 7 days)
6. Close or disqualify

**Followed By All (FBA):**
- Document it
- Train on it
- Measure compliance
- Update quarterly

See: [references/process.md](references/process.md) for process documentation templates.

### 6. Traction Component

**Question:** Are you executing on your vision every day?

**Two tools: Rocks and Level 10 Meetings**

#### Rocks (Quarterly Priorities)

**Definition:** The 3-7 most important things to accomplish in the next 90 days.

**Why 90 days?**
- Long enough to accomplish something meaningful
- Short enough to maintain urgency
- Natural human rhythm for focus

**Rock-setting process:**
1. Review V/TO (vision, 3-year, 1-year)
2. Brainstorm: "What must get done this quarter to stay on track?"
3. Narrow to 3-7 company rocks
4. Assign each rock to one owner
5. Each leadership member also has 3-7 individual rocks
6. Share with entire organization
7. Track weekly

**SMART rocks:**
- **S**pecific: "Launch new pricing page" not "improve pricing"
- **M**easurable: Clear completion criteria
- **A**chievable: Can be done in 90 days
- **R**ealistic: Given current resources
- **T**ime-bound: Due end of quarter

**Rock scoring:**
- **Done** = checked off (no partial credit)
- **Not done** = carried forward or dropped
- **Goal:** 80%+ completion rate

**Anti-patterns:**
- Too many rocks (>7) → Focus is diluted
- Rocks too vague → Can't tell if done
- No owner → Nobody accountable
- All rocks are "business as usual" → Not moving the needle

See: [references/rocks.md](references/rocks.md) for rock-setting exercises.

#### Level 10 Meeting (Weekly Leadership Meeting)

**The most important meeting in EOS.** Runs every week, same day, same time, same agenda.

**Duration:** 90 minutes, never longer.

**Agenda:**

| Time | Section | Purpose |
|------|---------|---------|
| 5 min | **Segue** | Good news (personal and professional) |
| 5 min | **Scorecard** | Review weekly numbers |
| 5 min | **Rock Review** | On track / Off track for each rock |
| 5 min | **Customer/Employee Headlines** | Quick updates |
| 5 min | **To-Do List** | Review last week's to-dos (done or not done) |
| 60 min | **IDS** | Identify, Discuss, Solve issues |
| 5 min | **Conclude** | Recap to-dos, rate meeting 1-10 |

**Level 10 meeting rules:**
- Starts on time, ends on time (non-negotiable)
- Same day, same time every week
- No phones/laptops (except for agenda)
- IDS gets 60 of 90 minutes (most important part)
- Rate meeting 1-10 at end (target: 8+)
- If below 8, discuss what to improve

**Why "Level 10"?**
- Every meeting is rated 1-10 by participants
- Goal is to consistently achieve 10/10

**To-Do rules:**
- 7-day action items only
- Each has owner and due date
- Done = 100% complete
- 90%+ completion rate is target

See: [references/level-10.md](references/level-10.md) for meeting facilitation guides.

## EOS Implementation Timeline

**Typical rollout: 2 years to full implementation**

| Phase | Timeline | Focus |
|-------|----------|-------|
| **Focus Day** | Day 1 (8 hours) | Accountability chart, rocks, scorecard, Level 10 |
| **Vision Building Day 1** | Month 1 | V/TO: core values, core focus, 10-year target |
| **Vision Building Day 2** | Month 2 | V/TO: marketing strategy, 3-year, 1-year, rocks |
| **Quarterly Sessions** | Every 90 days | Review rocks, set new rocks, IDS major issues |
| **Annual Planning** | Yearly | Full V/TO review, set 1-year plan, Q1 rocks |

**Self-implementation vs. EOS Implementer:**
- Self: Read the book, follow the tools (free, slower)
- EOS Implementer: Certified facilitator guides the process (faster, expensive)

## Organizational Checkup

Rate your company 1-5 on each statement:

| Component | Statement | Score (1-5) |
|-----------|-----------|-------------|
| **Vision** | Leadership team is on the same page with where we're going and how to get there | |
| **People** | We have the right people in the right seats | |
| **Data** | We manage from a weekly scorecard of 5-15 numbers | |
| **Issues** | We solve issues quickly and permanently | |
| **Process** | Core processes are documented and followed by all | |
| **Traction** | We set and achieve 90-day priorities (rocks) | |

**Scoring:**
- 25-30: Strong (maintain and fine-tune)
- 20-24: Good (close gaps)
- 15-19: Average (significant work needed)
- Below 15: Weak (consider EOS implementer)

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Skipping Level 10s** | Lose weekly rhythm, issues pile up | Protect meeting, never cancel |
| **Too many rocks** | No focus, nothing gets done | Max 7 company rocks, 3-7 per person |
| **Vague rocks** | Can't tell if done | Write SMART rocks with clear criteria |
| **No scorecard** | Managing by gut, surprises | Choose 5-15 weekly numbers |
| **Wrong people kept** | Drags entire team down | Use People Analyzer, make tough calls |
| **V/TO not shared** | Team doesn't know the vision | Share with entire company |

## Quick Diagnostic

Audit any business:

| Question | If No | Action |
|----------|-------|--------|
| Does leadership agree on vision? | Misalignment | Complete V/TO together |
| Right people in right seats? | Performance issues | People Analyzer on all seats |
| Managing from data weekly? | Reactive management | Build weekly scorecard |
| Issues solved permanently? | Same problems repeat | Implement IDS in Level 10s |
| Core processes documented? | Inconsistency | Document top 5 processes |
| 90-day priorities set and tracked? | No traction | Set quarterly rocks |

## Reference Files

- [vto.md](references/vto.md): Vision/Traction Organizer templates, eight questions
- [people.md](references/people.md): Accountability chart, People Analyzer, GWC
- [data.md](references/data.md): Scorecard templates, metric selection
- [issues.md](references/issues.md): IDS process, facilitation, issue types
- [process.md](references/process.md): Core process documentation templates
- [rocks.md](references/rocks.md): Rock-setting exercises, SMART rocks
- [level-10.md](references/level-10.md): Meeting agenda, facilitation, rating
- [implementation.md](references/implementation.md): EOS rollout timeline, self-implementation guide
- [case-studies.md](references/case-studies.md): Companies that implemented EOS successfully

## Further Reading

This skill is based on the Entrepreneurial Operating System developed by Gino Wickman. For the complete system:

- [*"Traction: Get a Grip on Your Business"*](https://www.amazon.com/Traction-Get-Grip-Your-Business/dp/1936661837?tag=wondelai00-20) by Gino Wickman
- [*"Get a Grip"*](https://www.amazon.com/Get-Grip-Entrepreneurial-Fable-Business/dp/1939529824?tag=wondelai00-20) by Gino Wickman & Mike Paton (EOS as a business fable)
- [*"Rocket Fuel"*](https://www.amazon.com/Rocket-Fuel-Essential-Combination-Business/dp/1941631150?tag=wondelai00-20) by Gino Wickman & Mark C. Winters (Visionary + Integrator relationship)

## About the Author

**Gino Wickman** is the creator of EOS (Entrepreneurial Operating System) and founder of EOS Worldwide, a community of certified EOS Implementers who help companies implement the system. Wickman has worked with thousands of entrepreneurial leadership teams and has helped them get real traction. *Traction* has sold over 2 million copies and EOS is used by over 250,000 companies worldwide. His work focuses on the practical tools needed to run an entrepreneurial company.

## Overview

Implement the Entrepreneurial Operating System (EOS) to align vision and execution across a company.

## Prerequisites

- Access to the design environment or API
- Required CLI tools installed and authenticated
- Familiarity with design concepts and terminology

## Instructions

1. Assess the current state of the design configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [design implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with design |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply traction eos to a standard project setup with default configuration options.

**Advanced scenario**: Customize traction eos for production environments with multiple constraints and team-specific requirements.

## Resources

- Official design documentation
- Community best practices and patterns
- Related skills in this plugin pack
