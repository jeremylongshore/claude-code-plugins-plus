---
name: drive-motivation
description: 'Design motivation systems using Autonomy, Mastery, and Purpose (AMP) for products and teams. Use when the user mentions "intrinsic motivation", "gamification isnt working", "rewards arent working", "autonomy", "mastery", "purpose-driven", "my team is disengaged", or "how do I motivate people". Also trigger when designing onboarding progression, fixing broken gamification, or building team structures that sustain high performance. Covers why carrot-and-stick fails and how to build progress systems. For habit-forming product loops, see hooked-ux. For retention behavior design, see improve-retention.'
license: MIT
metadata:
  author: wondelai
  version: "1.4.0"
---

# Drive Motivation Framework

Design motivation systems for products, teams, and organizations using the science of intrinsic motivation.

## Core Principle

**The secret to high performance isn't rewards and punishment — it's the deeply human need to direct our own lives, learn and create new things, and do better for ourselves and our world.** For any task requiring even rudimentary cognitive effort, external rewards either don't work or actively worsen performance. Intrinsic motivation — Autonomy, Mastery, Purpose (AMP) — drives lasting engagement.

## Scoring

**Goal: 10/10.** Score any motivation system (product features, team incentives, gamification, engagement loops) against the [Quick Diagnostic](#quick-diagnostic): start at 5, add 1 for each of the first five rows answered "yes," then **subtract 2 if the sixth row is also "yes"** — an "if-then" reward doing the motivating crowds out the rest. Bands:

- **9-10** — autonomy, mastery, and purpose all present; no if-then crowding-out.
- **5-6** — one pillar carries the system; the other two are weak or extrinsic.
- **≤3** — relies on rewards, mandates, or controlling behaviors; intrinsic motivation absent.

Always state the current score, which diagnostic rows failed, and the specific fixes to reach 10/10.

## Motivation 1.0, 2.0, and 3.0

| Version | Core Assumption | Approach | Era |
|---------|----------------|----------|-----|
| **1.0** | Humans are biological | Survival drives | Pre-industrial |
| **2.0** | Humans respond to rewards/punishments | Carrot and stick | Industrial age |
| **3.0** | Humans seek autonomy, mastery, purpose | Intrinsic motivation | Knowledge economy |

### The Seven Deadly Flaws of Extrinsic Rewards

"If-then" rewards ("If you do X, then you get Y"):

| Flaw | Mechanism | Example |
|------|-----------|---------|
| **1. Extinguish intrinsic motivation** | Turns play into work | Kids paid to draw stopped drawing when payments stopped |
| **2. Diminish performance** | Narrow focus, reduce creativity | Candle problem: rewarded group performed worse |
| **3. Crush creativity** | Reward focus replaces exploration | Commissioned art rated less creative |
| **4. Crowd out good behavior** | Financial framing replaces moral framing | Day-care late fee: lateness increased (became a "service") |
| **5. Encourage cheating** | Goal fixation invites shortcuts | Wells Fargo fake accounts |
| **6. Become addictive** | Bigger rewards needed over time | Last year's bonus = this year's expectation |
| **7. Foster short-term thinking** | Optimize for the reward period | Quarterly bonuses → quarterly thinking |

**The boundary:** extrinsic rewards work only for routine, algorithmic tasks with no intrinsic interest. For creative work, complex problem-solving, or long-term engagement, they backfire.

See [references/extrinsic-rewards.md](references/extrinsic-rewards.md) when a reward or incentive scheme is backfiring — the named studies behind each flaw and a decision rule for when rewards are safe to use.

## The Three Pillars: Autonomy, Mastery, Purpose

### 1. Autonomy

**Core concept:** The desire to direct our own lives — choice over what, when, how, and with whom. Autonomy ≠ independence: people can act with choice while staying interdependent with a team.

**The Four T's of Autonomy:**

| Dimension | Question | Example |
|-----------|----------|---------|
| **Task** | What do I work on? | Google's 20% time, Atlassian ShipIt days |
| **Time** | When do I work? | Flexible hours, no mandatory meetings |
| **Technique** | How do I do it? | Choose tools, methods, approach |
| **Team** | Who do I work with? | Self-forming teams |

**Product applications:**

| Context | Autonomy Killer | Autonomy Enabler |
|---------|----------------|-------------------|
| **Onboarding** | Forced linear tutorial | Choose your path, skip steps |
| **Content** | Algorithm-only feed | User-controlled feeds, filters |
| **Workflow** | Rigid process, feature bloat | Custom automations, show/hide, progressive disclosure |

**Autonomy violations:** "You must complete X before Y", unskippable tutorials, mandatory notifications, and forced single paths through the experience.

See [references/autonomy.md](references/autonomy.md) when designing onboarding, feeds, or workflow controls — full Four T's patterns plus the autonomy audit checklist.

### 2. Mastery

**Core concept:** The desire to get better at something that matters. Mastery is a mindset, not a destination — it's asymptotic, and the joy is in the pursuit.

**Three laws of mastery:**

- **Mastery is a mindset** — ability is developed, not fixed (Dweck's growth mindset). Frame failures as learning, not judgment.
- **Mastery is a pain** — it demands effort and deliberate practice. Flow (Csikszentmihalyi) lives between boredom and anxiety, so calibrate challenge to skill level.
- **Mastery is asymptotic** — users never fully arrive. Always offer a next level, next challenge.

**Flow conditions:** clear goals, immediate feedback, challenge/skill balance, sense of control.

**Product applications:**

| Context | Mastery Design | Example |
|---------|---------------|---------|
| **Progress** | Visible skill development | GitHub contribution graph, Duolingo levels |
| **Difficulty** | Adaptive challenge | Games that adjust to player skill |
| **Feedback** | Immediate, clear signals | Grammarly real-time writing analysis |

**Mastery violations:** flat difficulty that never adapts, and failure that is punished rather than framed as learning.

See [references/mastery.md](references/mastery.md) when designing progress, difficulty, or feedback systems — flow-state calibration, deliberate practice, and the mastery audit checklist.

### 3. Purpose

**Core concept:** The yearning to act in service of something larger than ourselves. Purpose is the context for the other two pillars — without it, autonomy is directionless and mastery hollow.

**Three expressions of purpose:**

| Expression | How It Manifests | Example |
|-----------|-----------------|---------|
| **Goals** | Purpose-driven objectives | TOMS: every purchase helps a person in need |
| **Words** | Language of purpose, not profit | "Associates" not "employees", "community" not "users" |
| **Policies** | Actions that demonstrate purpose | Patagonia: "Don't Buy This Jacket" |

**Product applications:**

| Context | Purpose Design | Example |
|---------|---------------|---------|
| **Impact** | Show the user's contribution | Wikipedia edit counter, Kiva lending impact |
| **Community** | Connect to something bigger | Open source contributions, community goals |
| **Values** | Align product with beliefs | Ecosia: "Search the web to plant trees" |

**Purpose prescriptions:** show aggregate impact ("Together, our users have saved 1M hours"), connect individual actions to collective outcomes, and celebrate meaningful milestones over vanity metrics.

See [references/purpose.md](references/purpose.md) when wiring impact, community, or values features — Goals/Words/Policies patterns and the purpose audit checklist.

## AMP Applied: Product Design

### Gamification Done Right vs. Wrong

| Principle | Bad (Extrinsic) | Good (Intrinsic) |
|-----------|-----------------|-------------------|
| **Autonomy** | Forced challenges, mandatory participation | Opt-in, chosen challenges |
| **Mastery** | Points for everything, trivial badges | Skill-based progression, meaningful milestones |
| **Purpose** | Pointless competition, discouraging leaderboards | Community contribution, personal growth |

**Example — Duolingo:** autonomy (choose language, pace, topics), mastery (adaptive difficulty, skill levels), purpose ("learn a language to connect with people"). Caution: streaks can shift from intrinsic mastery to extrinsic loss aversion.

### Team Motivation

| Principle | Manager Action | Example |
|-----------|---------------|---------|
| **Autonomy** | Hand over task, time, technique, team | "Here's the goal. How you get there is up to you." |
| **Mastery** | Provide challenge, feedback, growth | Stretch assignments, mentorship, learning budget |
| **Purpose** | Connect work to mission | "Here's why this matters for our customers" |

### Compensation and Incentives

Pay people enough to take money off the table — fair, ideally above-market — then focus on AMP; beyond "enough," more money doesn't increase motivation. Prefer "now-that" rewards (unexpected recognition after the fact: "You hit target! Here's a bonus.") over "if-then" rewards ("If you hit target, you get a bonus"), which create pressure and short-term thinking.

See [references/applications.md](references/applications.md) when applying AMP to a concrete gamification, team-management, or compensation design — worked examples and escalation tables.

## Type I vs. Type X Behavior

| Type X (Extrinsic) | Type I (Intrinsic) |
|--------------------|---------------------|
| Fueled by external rewards | Fueled by autonomy, mastery, purpose |
| Seeks external recognition | Seeks inherent satisfaction |
| Short-term focus, fixed mindset | Long-term focus, growth mindset |

Design products and teams that cultivate Type I behavior: it's made, not born; it doesn't disdain money or recognition; it's renewable; and it promotes well-being.

See [references/type-i.md](references/type-i.md) when shifting a team or user base from Type X to Type I — the full behavioral contrast and conversion tactics. For real-world AMP programs (Atlassian ShipIt, 3M, ROWE, Duolingo, Wikipedia), see [references/case-studies.md](references/case-studies.md).

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Points for everything** | Crowds out intrinsic motivation | Reserve rewards for meaningful milestones |
| **Mandatory participation** | Kills autonomy | Make engagement opt-in |
| **Same challenge for everyone** | No flow — boredom or anxiety | Adaptive difficulty matching |
| **No visible progress** | Mastery is invisible | Progress indicators, skill tracking |
| **Missing "why"** | Actions feel meaningless | Connect every feature to purpose |
| **If-then bonuses** | Short-term thinking, gaming | Pay fairly; use "now-that" rewards; focus on AMP |

## Quick Diagnostic

Audit any motivation system:

| Question | If No | Action |
|----------|-------|--------|
| Can users choose what/when/how? | Autonomy violation | Add choices, flexibility, customization |
| Can users see their progress? | No mastery signal | Add progress tracking, skill levels |
| Is challenge matched to skill? | Boredom or anxiety | Implement adaptive difficulty |
| Is there immediate feedback? | Can't improve | Add real-time response to actions |
| Does the user know WHY this matters? | No purpose | Connect to mission, show impact |
| Are we using "if-then" rewards? | Extrinsic crowding-out | Switch to "now-that" or intrinsic design |

## Further Reading

Based on Daniel Pink's research on motivation science:

- [*"Drive: The Surprising Truth About What Motivates Us"*](https://www.amazon.com/Drive-Surprising-Truth-About-Motivates/dp/1594484805?tag=wondelai00-20) by Daniel H. Pink
- [*"To Sell Is Human"*](https://www.amazon.com/Sell-Human-Surprising-Moving-Others/dp/1594631905?tag=wondelai00-20) by Daniel H. Pink (applying motivation to sales and persuasion)

## About the Author

**Daniel H. Pink** is the author of seven books, including four New York Times bestsellers. *Drive*, translated into 40+ languages, changed how organizations think about motivation, and his TED Talk on motivation science is among the most-viewed of all time. He was previously chief speechwriter for Vice President Al Gore.
