# Five Whys Root Cause Analysis

The Five Whys is a root cause analysis technique adapted from the Toyota Production System for use in startups. When something goes wrong, most teams fix the symptom and move on. The Five Whys forces you to dig past symptoms to find the underlying systemic issue. In a startup context, it serves a dual purpose: fixing problems and making proportional investments in prevention. The technique is deceptively simple but requires discipline and practice to execute well.

## The Core Principle

When a problem occurs, ask "why" five times. Each answer becomes the basis for the next question. By the fifth "why," you typically arrive at a root cause that is systemic, not situational.

**The insight:** Surface problems are symptoms of deeper process failures. Fixing symptoms leads to recurring problems. Fixing root causes prevents entire categories of future problems.

## Step-by-Step Process

### Step 1: Define the Problem

State the problem as a specific, observable event. Not "the product has bugs" but "Customer X received an incorrect invoice on Tuesday."

**Good problem statements:**
- "Three customers reported receiving duplicate emails on March 15"
- "The deploy on Friday caused a 2-hour outage for all users"
- "New user onboarding completion dropped from 65% to 40% this week"

**Bad problem statements:**
- "Our quality is poor" (too vague)
- "Users are unhappy" (too broad)
- "Things are broken" (not specific)

### Step 2: Assemble the Right People

Include everyone directly involved in the problem. Not managers looking over shoulders, but the people who touched the code, the process, or the customer interaction.

**Who to include:**
- The person who discovered the problem
- The person(s) who contributed to the problem
- A facilitator (someone not directly involved)
- Optionally, one person with organizational context (can explain process history)

**Who not to include:**
- Senior leaders who will inhibit honest answers
- People looking to assign blame
- Anyone not directly connected to the incident

### Step 3: Ask Why (Five Times)

Work through the chain, ensuring each "why" is answered with a factual, verifiable statement.

### Step 4: Identify Proportional Investments

For each level of "why," make an investment in prevention that is proportional to the severity. Small problems get small fixes. Recurring problems get larger systemic changes.

### Step 5: Assign and Track

Each investment gets an owner and a deadline. Follow up in the next cycle.

## Complete Example 1: Deployment Outage

**Problem:** Friday deploy caused a 2-hour outage for all users.

| Level | Question | Answer |
|-------|----------|--------|
| Why 1 | Why did the deploy cause an outage? | A database migration script failed halfway through, leaving the schema in an inconsistent state. |
| Why 2 | Why did the migration script fail? | It timed out because the users table has 2 million rows and the script added an index without a timeout setting. |
| Why 3 | Why was there no timeout setting? | The developer was not aware that large table migrations need special handling. |
| Why 4 | Why was the developer not aware? | There is no documentation or checklist for database migrations in the team. |
| Why 5 | Why is there no migration checklist? | We have never formalized our deployment process; it has been tribal knowledge. |

**Proportional investments:**

| Level | Investment | Effort | Owner | Deadline |
|-------|-----------|--------|-------|----------|
| 1 | Fix the specific migration and restore service | 2 hours | DevOps lead | Immediate |
| 2 | Add timeout settings to migration runner | 1 hour | Backend dev | This week |
| 3 | Create migration best practices document | 4 hours | Senior dev | Next week |
| 4 | Add migration checklist to PR review template | 2 hours | Tech lead | Next week |
| 5 | Schedule monthly "process gap" reviews | 1 hour/month | Engineering manager | Ongoing |

## Complete Example 2: Customer Churn Spike

**Problem:** Monthly churn rate doubled from 4% to 8% in February.

| Level | Question | Answer |
|-------|----------|--------|
| Why 1 | Why did churn double in February? | 60% of churned customers cited "product does not meet needs" in exit surveys. |
| Why 2 | Why does the product not meet their needs? | These customers were acquired through a January campaign targeting a new segment (enterprise) with different requirements. |
| Why 3 | Why were enterprise customers targeted when the product is built for SMBs? | Marketing optimized for signup volume without qualifying for product fit. |
| Why 4 | Why was there no product-fit qualification? | Marketing and product teams do not share a definition of "ideal customer." |
| Why 5 | Why is there no shared customer definition? | The teams have separate OKRs and do not have a regular alignment process. |

**Proportional investments:**

| Level | Investment | Effort | Owner | Deadline |
|-------|-----------|--------|-------|----------|
| 1 | Reach out to churned enterprise customers; offer refund or alternative solution | 1 day | Customer success | This week |
| 2 | Pause the enterprise campaign until product-fit is assessed | Immediate | Marketing lead | Today |
| 3 | Add lead qualification criteria to campaign setup process | 4 hours | Marketing ops | This week |
| 4 | Create shared ideal customer profile (ICP) document | 1 day | Product + Marketing leads | Next 2 weeks |
| 5 | Establish monthly product-marketing alignment meeting with shared metrics | 2 hours/month | VP Product | Ongoing |

## Complete Example 3: Feature Launch Failure

**Problem:** New collaboration feature launched to 0.5% adoption after 30 days (target was 15%).

| Level | Question | Answer |
|-------|----------|--------|
| Why 1 | Why is adoption at 0.5%? | Most users never discovered the feature. Only 8% of users saw the feature announcement. |
| Why 2 | Why did only 8% see the announcement? | The announcement was an in-app banner that appeared only on first login after release, and 92% of active users did not log in that day. |
| Why 3 | Why was the announcement limited to a single-day banner? | There is no systematic feature launch process; the team improvised the announcement. |
| Why 4 | Why is there no feature launch process? | Product and marketing have not collaborated on launches; engineering ships and "hopes people notice." |
| Why 5 | Why do product and marketing not collaborate on launches? | Launch planning is not part of the product development workflow. Features are considered "done" when code ships. |

**Proportional investments:**

| Level | Investment | Effort | Owner | Deadline |
|-------|-----------|--------|-------|----------|
| 1 | Create persistent in-app tooltip and email campaign for the feature | 1 day | Product + Marketing | This week |
| 2 | Implement multi-touch announcement system (in-app, email, changelog) | 3 days | Product | Next sprint |
| 3 | Create feature launch checklist template | 4 hours | Product manager | Next week |
| 4 | Add "launch plan" as required section in feature specs | 2 hours | Product lead | Next week |
| 5 | Include marketing in sprint planning for launch-relevant features | 1 hour/sprint | Product lead | Ongoing |

## The Proportional Investment Principle

This is the most important aspect of Five Whys in a startup context. The investment at each level should be proportional to the problem severity.

**For a minor issue (first occurrence, low impact):**
- Level 1: Fix the specific instance (minutes to hours)
- Level 2: Add a check or guard (hours)
- Levels 3-5: Document the root cause but do not invest heavily in prevention yet

**For a major issue (customer-facing, recurring, or high impact):**
- All levels: Make meaningful investments
- Level 5: Expect systemic changes (new processes, new tools, organizational changes)

**For a critical issue (data loss, security breach, major outage):**
- All levels: Invest heavily
- Level 5: May require leadership changes, architecture overhauls, or cultural shifts

The point is not to boil the ocean on every small problem. It is to make small, incremental investments that compound over time into a robust system.

## When Five Whys Works

Five Whys is most effective when:

- The problem is specific and observable
- The people involved are in the room
- The culture is blame-free
- The problem is relatively contained (not a vague "culture problem")
- There is willingness to invest in fixes at every level
- Follow-up happens (investments are tracked)

## When Five Whys Does Not Work

### Problem: The "Why" Chain Diverges

Sometimes each "why" has multiple valid answers, and the chain branches into a tree instead of a line.

**Solution:** When a branch point occurs, follow the path most likely to lead to a systemic cause. You can explore other branches in separate sessions. Prioritize the branch that feels most within your control.

### Problem: Blame Creeps In

"Why did the database fail?" leads to "Because John wrote bad code."

**Solution:** Redirect to process: "Why was John in a position to write code that could cause this failure?" This shifts from blame to systems thinking. If a person is the root cause, the actual root cause is the system that allowed one person's mistake to reach production.

### Problem: Five Is Not Enough (or Too Many)

Some root causes emerge at "Why 3" and some require "Why 7."

**Solution:** Five is a guideline, not a rule. Stop when you reach a cause you can address systemically. If you reach "Why 5" and the answer is "because the universe is unfair," you went too far. Back up one level.

### Problem: Root Cause Is Outside Your Control

"Why did the API fail?" eventually leads to "Because the third-party provider had an outage."

**Solution:** Redirect to what you can control: "Why did our system fail when the third-party provider had an outage?" This leads to resilience and redundancy investments.

### Problem: The Team Is Too Large

With more than 6-8 people, Five Whys sessions become unwieldy. Discussions go in circles, and dominant voices take over.

**Solution:** Keep the group small. Include only people directly involved. Share findings with the broader team afterward.

## Integrating Five Whys Into Team Culture

### Cadence

- **After every significant incident:** Mandatory Five Whys within 48 hours
- **Weekly or bi-weekly:** Review outstanding investments from past Five Whys
- **Monthly:** Look for patterns across multiple Five Whys sessions

### Making It Routine

1. **Template the process.** Use a standard document or tool for every session.
2. **Assign a rotating facilitator.** Everyone should practice leading Five Whys.
3. **Time-box sessions.** 30-45 minutes maximum. If unresolved, schedule a follow-up.
4. **Track investments.** Use a shared tracker (Jira ticket, Notion database, spreadsheet) for every investment from every session.
5. **Celebrate systemic fixes.** When a Five Whys investment prevents a future incident, highlight it publicly.

### Five Whys Session Template

```
FIVE WHYS SESSION
=================
Date: _______________
Facilitator: _______________
Participants: _______________

PROBLEM STATEMENT
What happened: _______________
When: _______________
Impact: _______________
How it was discovered: _______________

ROOT CAUSE ANALYSIS
Why 1: _______________
Why 2: _______________
Why 3: _______________
Why 4: _______________
Why 5: _______________

PROPORTIONAL INVESTMENTS
Level 1: _______________  Owner: ___  Deadline: ___
Level 2: _______________  Owner: ___  Deadline: ___
Level 3: _______________  Owner: ___  Deadline: ___
Level 4: _______________  Owner: ___  Deadline: ___
Level 5: _______________  Owner: ___  Deadline: ___

FOLLOW-UP
Review date: _______________
```

## Common Facilitation Mistakes

| Mistake | Consequence | Prevention |
|---------|-------------|------------|
| Allowing blame language | People become defensive; honesty stops | Establish blame-free ground rules at the start of every session |
| Stopping at "Why 1" | Only symptoms get fixed; problems recur | Insist on at least three levels before considering stopping |
| Accepting vague answers | Root cause remains hidden | Push for specific, verifiable answers at each level |
| Skipping the investment step | Analysis without action; problems recur | Require at least one investment per level before ending the session |
| Not following up | Investments are forgotten; trust erodes | Track investments in a shared system; review in next session |
| Running sessions without affected parties | Analysis is speculative; investments miss the mark | Include the people who were there, not their managers |
| Combining multiple problems | Session becomes unfocused; no clear root cause | One problem per session; schedule separate sessions for related problems |
| Facilitator leading the witness | Answers reflect facilitator's theory, not reality | Facilitator asks questions only; does not suggest answers |

Five Whys is a practice, not a technique. It improves with repetition. The first few sessions will feel awkward and forced. After a dozen, it becomes the natural response to any problem. That shift, from "who do we blame" to "what system allowed this," is the real transformation.
