---
name: drive-motivation
description: 'Design motivation systems using Autonomy, Mastery, and Purpose (AMP) for products and teams. Use when the user mentions "intrinsic motivation", "gamification isnt working", "team incentives", "autonomy", "mastery", "purpose-driven", "employee engagement", or "reward systems". Also trigger when designing onboarding progression systems, fixing broken gamification, or building team structures that sustain high performance. Covers why carrot-and-stick fails and how to build progress systems. For habit-forming product loops, see hooked-ux. For retention behavior design, see improve-retention.'
license: MIT
metadata:
  author: wondelai
  version: "1.1.0"
---

# Drive Motivation Framework

Framework for designing motivation systems in products, teams, and organizations based on the science of what actually motivates humans. Replaces outdated carrot-and-stick thinking with intrinsic motivation.

## Core Principle

**The secret to high performance isn't rewards and punishment — it's the deeply human need to direct our own lives, learn and create new things, and do better for ourselves and our world.**

**The foundation:** For any task requiring even rudimentary cognitive effort, external rewards (bonuses, prizes, punishments) either don't work or actively make performance worse. Intrinsic motivation — Autonomy, Mastery, Purpose — drives lasting engagement.

## Scoring

**Goal: 10/10.** When evaluating motivation systems (product features, team incentives, gamification, engagement loops), rate 0-10 based on AMP principles. A 10/10 means the system supports autonomy, enables mastery, and connects to purpose; lower scores indicate reliance on extrinsic rewards or controlling behaviors. Always provide current score and improvements to reach 10/10.

## Motivation 1.0, 2.0, and 3.0

| Version | Core Assumption | Approach | Era |
|---------|----------------|----------|-----|
| **1.0** | Humans are biological beings | Survival drives (food, shelter, safety) | Pre-industrial |
| **2.0** | Humans respond to rewards/punishments | Carrot and stick (bonuses, penalties) | Industrial age |
| **3.0** | Humans seek autonomy, mastery, purpose | Intrinsic motivation | Knowledge economy |

**The problem with Motivation 2.0 (carrot and stick):**

Most organizations still run on Motivation 2.0, but it's fundamentally broken for modern work.

### The Seven Deadly Flaws of Extrinsic Rewards

External rewards ("if-then" rewards: "If you do X, then you get Y"):

| Flaw | Mechanism | Example |
|------|-----------|---------|
| **1. Extinguish intrinsic motivation** | Turns play into work | Kids who were paid to draw stopped drawing when payments stopped |
| **2. Diminish performance** | Narrow focus, reduce creativity | Candle problem: reward group performed worse |
| **3. Crush creativity** | Focus on reward, not exploration | Artists creating commissioned work are less creative |
| **4. Crowd out good behavior** | Financial framing replaces moral framing | Day care late-pickup fee: lateness increased (became a "service") |
| **5. Encourage cheating** | Goal fixation leads to shortcuts | Wells Fargo fake accounts scandal |
| **6. Become addictive** | Need bigger rewards over time | Bonus escalation: last year's bonus = this year's expectation |
| **7. Foster short-term thinking** | Optimize for reward period | Quarterly bonuses → quarterly thinking |

**When extrinsic rewards DO work:**
- Routine, algorithmic tasks (assembly line, data entry)
- Tasks requiring no creativity or judgment
- When the task is genuinely boring and no intrinsic motivation exists

**When extrinsic rewards DON'T work (and hurt):**
- Creative work
- Complex problem-solving
- Any task requiring cognitive effort
- Long-term engagement

See: [references/extrinsic-rewards.md](references/extrinsic-rewards.md) for the science behind reward failures.

## The Three Pillars: Autonomy, Mastery, Purpose

### 1. Autonomy

**Definition:** The desire to direct our own lives — to have choice over what we do, when we do it, how we do it, and who we do it with.

**Autonomy ≠ independence.** Autonomy means acting with choice. You can be autonomous while being interdependent with a team.

**The Four T's of Autonomy:**

| Dimension | Question | Example |
|-----------|----------|---------|
| **Task** | What do I work on? | Google's 20% time, Atlassian ShipIt days |
| **Time** | When do I work? | Flexible hours, no mandatory meetings |
| **Technique** | How do I do it? | Choose your own tools, methods, approach |
| **Team** | Who do I work with? | Self-forming teams, choose collaborators |

**Product applications:**

| Context | Autonomy Killer | Autonomy Enabler |
|---------|----------------|-------------------|
| **Onboarding** | Forced linear tutorial | Choose your own path, skip steps |
| **Customization** | One-size-fits-all | Themes, layouts, preferences |
| **Content** | Algorithm-only feed | User-controlled feeds, filters |
| **Communication** | Forced notifications | Notification preferences, DND |
| **Workflow** | Rigid process | Flexible workflow, custom automations |
| **Features** | Feature bloat (all visible) | Show/hide features, progressive disclosure |

**Autonomy audit questions:**
- Can users choose WHAT to do in the product?
- Can users choose WHEN to engage?
- Can users choose HOW to complete tasks?
- Can users choose their own path through the experience?

**Warning signs of autonomy violation:**
- "You must complete X before Y"
- Forced tutorials with no skip option
- Mandatory notifications
- No customization options
- Rigid workflows with no flexibility

See: [references/autonomy.md](references/autonomy.md) for autonomy design patterns.

### 2. Mastery

**Definition:** The desire to get better at something that matters — to continually improve and grow.

**Mastery is a mindset, not a destination.** It's asymptotic — you can approach it but never fully reach it. The joy is in the pursuit.

**Three laws of mastery:**

**Law 1: Mastery is a Mindset**
- Growth mindset (Carol Dweck): Ability is developed, not fixed
- People with growth mindset seek challenges and learn from failure
- Fixed mindset people avoid challenges (might reveal inadequacy)
- **Design implication:** Frame failures as learning, not judgment

**Law 2: Mastery is a Pain**
- Requires effort, deliberate practice, and grit
- Flow (Csikszentmihalyi): Optimal state between boredom and anxiety
- Challenge must match skill level — too easy = boring, too hard = anxious
- **Design implication:** Calibrate difficulty to user's level

**Law 3: Mastery is Asymptotic**
- You can approach mastery but never fully arrive
- The pursuit itself is the reward
- **Design implication:** Always have next level, next challenge

**The Flow Channel:**

```
                ANXIETY
               /
              /
    FLOW ←──────────── Optimal challenge zone
              \
               \
                BOREDOM

    Low Skill ──────────────── High Skill
```

**Flow conditions:**
- Clear goals
- Immediate feedback
- Challenge/skill balance
- Sense of control
- Deep concentration

**Product applications:**

| Context | Mastery Design | Example |
|---------|---------------|---------|
| **Progress** | Visible skill development | GitHub contribution graph, Duolingo levels |
| **Difficulty** | Adaptive challenge | Games that adjust to player skill |
| **Feedback** | Immediate, clear signals | Real-time writing analysis (Grammarly) |
| **Goals** | Clear, achievable milestones | LinkedIn profile strength meter |
| **Learning** | Skill trees, structured paths | Codecademy learning paths |
| **Streaks** | Consistency tracking | Duolingo streaks (careful: can become extrinsic) |

**Mastery audit questions:**
- Can users see their progress over time?
- Does the product adapt to skill level?
- Is there immediate, meaningful feedback?
- Are there clear next steps for improvement?
- Does the challenge increase as skill increases?

**Warning signs of mastery violation:**
- No way to see improvement
- Same difficulty regardless of skill
- Delayed or absent feedback
- No clear path forward
- Punishing failures instead of teaching

See: [references/mastery.md](references/mastery.md) for mastery design patterns and flow state principles.

### 3. Purpose

**Definition:** The yearning to do what we do in the service of something larger than ourselves.

**Purpose is the context for autonomy and mastery.** Without purpose, autonomy is directionless and mastery is hollow.

**Three expressions of purpose:**

| Expression | How It Manifests | Example |
|-----------|-----------------|---------|
| **Goals** | Purpose-driven objectives | TOMS: "With every product you purchase, TOMS will help a person in need" |
| **Words** | Language of purpose, not profit | "Associates" not "employees", "community" not "users" |
| **Policies** | Actions that demonstrate purpose | Patagonia: "Don't Buy This Jacket" campaign |

**Product applications:**

| Context | Purpose Design | Example |
|---------|---------------|---------|
| **Mission** | Clear, inspiring why | "Organize the world's information" (Google) |
| **Impact** | Show user's contribution | Wikipedia edit counter, Kiva lending impact |
| **Community** | Connect to something bigger | Open source contribution, community goals |
| **Transparency** | Show how product helps | Charity: Water shows exact well location |
| **Values** | Align product with beliefs | Ecosia: "Search the web to plant trees" |

**Purpose audit questions:**
- Does the user understand WHY this product/feature exists?
- Can users see their impact on something bigger?
- Does the product connect to values the user cares about?
- Is there a mission beyond profit?

**Purpose in product design:**
- Show aggregate impact ("Together, our users have saved 1M hours")
- Connect individual actions to collective outcomes
- Frame features in terms of why, not just what
- Celebrate meaningful milestones, not vanity metrics

See: [references/purpose.md](references/purpose.md) for purpose-driven design patterns.

## AMP Applied: Product Design

### Gamification Done Right vs. Wrong

**Wrong gamification (extrinsic, Motivation 2.0):**
- Points for every action (becomes meaningless)
- Badges for trivial achievements
- Leaderboards that discourage (I'll never catch up)
- Rewards that replace intrinsic motivation

**Right gamification (intrinsic, Motivation 3.0):**

| Principle | Bad (Extrinsic) | Good (Intrinsic) |
|-----------|-----------------|-------------------|
| **Autonomy** | Forced challenges, mandatory participation | Choose challenges, opt-in |
| **Mastery** | Points for everything | Skill-based progression, meaningful milestones |
| **Purpose** | Pointless competition | Contribute to community, personal growth |

**Example: Duolingo**
- **Autonomy:** Choose language, pace, topics
- **Mastery:** Adaptive difficulty, progress tracking, skill levels
- **Purpose:** "Learn a language to connect with people"
- **Caution:** Streaks can shift from mastery (intrinsic) to loss aversion (extrinsic)

### Team Motivation

**How to apply AMP to team management:**

| Principle | Manager Action | Example |
|-----------|---------------|---------|
| **Autonomy** | Give control over task, time, technique, team | "Here's the goal. How you get there is up to you." |
| **Mastery** | Provide challenge, feedback, growth | Stretch assignments, mentorship, skill development budget |
| **Purpose** | Connect work to mission | "Here's why this matters for our customers" |

**"If-then" vs. "Now that" rewards:**
- **Bad:** "If you hit target, you get bonus" (if-then, creates pressure)
- **Better:** "You hit target! Here's a bonus." (now-that, unexpected recognition)
- **Best:** "Let's talk about what you want to work on next." (intrinsic)

### Compensation and Incentives

**Pink's recommendations:**
1. Pay people enough to take money off the table
2. Then focus on autonomy, mastery, purpose
3. Use "now-that" rewards (unexpected), not "if-then" rewards (contingent)

**The baseline:**
- Fair compensation eliminates distraction
- Above-market pay signals respect
- But beyond "enough," more money doesn't increase motivation
- Once baseline is met, AMP drives engagement

See: [references/applications.md](references/applications.md) for product and team applications.

## Type I vs. Type X Behavior

| Type X (Extrinsic) | Type I (Intrinsic) |
|--------------------|---------------------|
| Fueled by external rewards | Fueled by autonomy, mastery, purpose |
| Concerned with external recognition | Concerned with inherent satisfaction |
| Short-term focused | Long-term focused |
| Sees effort as burden | Sees effort as path to mastery |
| Fixed mindset tendencies | Growth mindset tendencies |

**Goal:** Design products and teams that cultivate Type I behavior.

**Type I behavior:**
- Is made, not born (anyone can develop it)
- Doesn't disdain money or recognition
- Is a renewable resource (doesn't deplete)
- Promotes greater physical and mental well-being

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Points for everything** | Crowds out intrinsic motivation | Reserve rewards for meaningful milestones |
| **Mandatory participation** | Kills autonomy | Make engagement opt-in |
| **Same challenge for everyone** | No flow state (bored or anxious) | Adaptive difficulty matching |
| **No visible progress** | Can't see mastery | Progress indicators, skill tracking |
| **Missing "why"** | Actions feel meaningless | Connect every feature to purpose |
| **If-then bonuses** | Creates short-term thinking | Pay fairly, focus on AMP |

## Quick Diagnostic

Audit any motivation system:

| Question | If No | Action |
|----------|-------|--------|
| Can users choose what/when/how? | Autonomy violation | Add choices, flexibility, customization |
| Can users see their progress? | No mastery signal | Add progress tracking, skill levels |
| Is the challenge matched to skill? | Boredom or anxiety | Implement adaptive difficulty |
| Is there immediate feedback? | Can't improve | Add real-time response to actions |
| Does the user know WHY this matters? | No purpose | Connect to mission, show impact |
| Are we using "if-then" rewards? | Extrinsic motivation | Switch to "now-that" or intrinsic design |

## Reference Files

- [extrinsic-rewards.md](references/extrinsic-rewards.md): The seven flaws, when rewards work and don't
- [autonomy.md](references/autonomy.md): Four T's, product and team autonomy design
- [mastery.md](references/mastery.md): Flow state, growth mindset, deliberate practice
- [purpose.md](references/purpose.md): Purpose-driven design, mission alignment
- [applications.md](references/applications.md): Product gamification, team management, compensation
- [type-i.md](references/type-i.md): Type I vs. Type X, cultivating intrinsic motivation
- [case-studies.md](references/case-studies.md): Atlassian, 3M, Duolingo, ROWE, Wikipedia

## Further Reading

This skill is based on Daniel Pink's research on motivation science. For the complete framework:

- [*"Drive: The Surprising Truth About What Motivates Us"*](https://www.amazon.com/Drive-Surprising-Truth-About-Motivates/dp/1594484805?tag=wondelai00-20) by Daniel H. Pink
- [*"To Sell Is Human"*](https://www.amazon.com/Sell-Human-Surprising-Moving-Others/dp/1594631905?tag=wondelai00-20) by Daniel H. Pink (applying motivation to sales and persuasion)

## About the Author

**Daniel H. Pink** is the author of seven books including four New York Times bestsellers. *Drive* has been translated into over 40 languages and fundamentally changed how organizations think about motivation. Pink's TED Talk on the science of motivation is one of the most-viewed of all time (45M+ views). He has advised companies, governments, and nonprofits worldwide on motivation, creativity, and human performance. Pink was previously a speechwriter for Vice President Al Gore and has written for The New York Times, Harvard Business Review, and Wired.
