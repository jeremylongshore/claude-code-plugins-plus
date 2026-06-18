---
name: hooked-ux
description: 'Design habit-forming product loops using the Hook Model (Trigger, Action, Variable Reward, Investment). Use when the user mentions "users arent coming back", "engagement loops", "habit formation", "push notifications", "variable rewards", "daily active users", "habit zone", or "user retention loops". Also trigger when designing notification strategies, building streaks or progress systems, or analyzing why users stop using a product after initial signup. Covers ethics evaluation and onboarding for habits. For friction reduction and B=MAP, see improve-retention. For viral sharing, see contagious.'
license: MIT
metadata:
  author: wondelai
  version: "1.3.0"
---

# Hook Model Framework

Framework for building habit-forming products. Habits are not created — they are built through successive cycles through the Hook.

## Core Principle

**The Hook Model** = a four-phase loop that connects the user's problem to your solution frequently enough to form a habit, moving usage from deliberate to automatic.

```
Trigger → Action → Variable Reward → Investment
    ↑                                      │
    └──────────────────────────────────────┘
```

## Scoring

**Goal: 10/10.** When reviewing or creating product engagement mechanics, rate them 0-10 based on adherence to the principles below. A 10/10 means full alignment with all guidelines; lower scores indicate gaps to address. Always provide the current score and specific improvements needed to reach 10/10.

## The Four Phases

### 1. Trigger

**Core concept:** The actuator of behavior. Triggers are external (environment-driven: notifications, emails, ads) or internal (emotion-driven) — and the goal is to migrate users from external to internal triggers.

**Why it works:** Every habit starts with a cue. External triggers get users started, but internal triggers — boredom, loneliness, uncertainty, FOMO — drive unprompted usage; when your product becomes the automatic response to an emotion, you have a habit.

**Key insights:**
- Map your product to the specific negative emotion it resolves (boredom, loneliness, confusion, FOMO)
- Effective external triggers are well-timed, actionable, and lead to the simplest possible next action
- If users still need external prompts after ~30 days, no internal trigger has formed

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Onboarding** | External triggers establish the first loop | Welcome email with one clear action |
| **Retention** | Map product to internal emotional trigger | Instagram resolves boredom; Google resolves confusion |
| **Re-engagement** | External triggers bridge gaps until habit forms | Push: "Your friend just posted a photo" |

**Copy patterns:**
- "Don't miss what happened while you were away" (FOMO trigger)
- "Your friend just..." (social trigger bridging to internal)
- "Pick up where you left off" (routine trigger)

**Ethical boundary:** Never exploit vulnerable emotional states (depression, addiction, grief) — triggers should connect users to genuine value, not manufacture anxiety to drive opens.

See: [references/triggers.md](references/triggers.md) for trigger design, emotion mapping, and external-to-internal transition strategies.

### 2. Action

**Core concept:** The simplest behavior done in anticipation of a reward, guided by the Fogg Behavior Model: Behavior = Motivation + Ability + Trigger, all converging at the same moment.

**Why it works:** Increasing motivation is hard and unreliable; reducing friction (increasing ability) is easier and more effective. Every extra step, field, or decision is a drop-off point.

**Key insights:**
- Six elements of simplicity: time, money, physical effort, brain cycles, social deviance, non-routine
- The action is the simplest behavior in anticipation of reward — not the full task
- Hick's Law: more choices = slower decisions; reduce options to increase action rate

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Signup flow** | Minimize fields and steps | One-click Google/Apple sign-in |
| **Core action** | Completable in seconds | Twitter: type 280 characters and post |
| **Progressive disclosure** | Ask for more only after initial reward | Duolingo: play first, create account later |

**Copy patterns:**
- "Just one tap to..." (emphasizes simplicity)
- "No credit card required" (money/risk simplicity)
- Buttons should be verbs: "Post", "Save", "Share" — not "Submit" or "Continue"

**Ethical boundary:** Reduce friction on genuinely valuable actions only — dark patterns that hide costs or consequences behind simple actions are unethical.

See: [references/product-applications.md](references/product-applications.md) for action and investment design across product types.

### 3. Variable Reward

**Core concept:** The phase that keeps users coming back. Anticipation of reward — not the reward itself — creates dopamine, and rewards must be variable (unpredictable) to sustain engagement.

**Why it works:** The brain's dopamine system responds most strongly to anticipation of uncertain rewards — the slot machine effect. Three reward types — tribe (social), hunt (resources), self (mastery) — tap fundamental human drives.

**Key insights:**
- Tribe = social validation; Hunt = search for resources/information; Self = personal mastery
- Predictable rewards lose power; finite variability eventually becomes predictable — aim for infinite variability
- Autonomy is critical: users must feel in control; forced engagement backfires

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Social features (Tribe)** | Variable social validation | Instagram likes — you never know how many |
| **Content feeds (Hunt)** | Unpredictable resource stream | Infinite scroll with algorithmically varied content |
| **Gamification (Self)** | Accomplishment with variable difficulty | Duolingo streaks + surprise bonus challenges |

**Copy patterns:**
- "See what's new" (implies variability)
- "3 people responded to your post" (tribe reward, variable quantity)
- "You've unlocked a new achievement!" (self reward, unexpected)

**Ethical boundary:** If users consistently feel worse after engaging (regret, time loss, anxiety), the reward system is extractive — avoid infinite scroll without natural stopping points.

See: [references/rewards.md](references/rewards.md) for reward design patterns, reinforcement schedules, and reward timing.

### 4. Investment

**Core concept:** Users invest something — time, data, effort, social capital, money — that improves the product for next use, raises switching costs, and loads the next trigger.

**Why it works:** People value what they put effort into (the IKEA effect). Investment is not about immediate reward — it improves the next cycle, creating a self-reinforcing loop.

**Key insights:**
- Investment should come after reward, not before — users invest when they feel good
- Each investment should load the next trigger (posting content triggers reply notifications)
- Small investments compound: preferences → better recommendations → more usage; stored value grows over time

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Data investment** | History improves personalization | Spotify: more listening = better recommendations |
| **Content investment** | User-created content they won't abandon | Instagram posts, Notion documents |
| **Reputation/social investment** | Social capital that exists only on-platform | Airbnb host ratings, LinkedIn network |

**Copy patterns:**
- "Complete your profile to get better matches" (investment → future value)
- "The more you use it, the smarter it gets" (compound investment)
- "Invite your team to collaborate" (social investment)

**Ethical boundary:** Investment should genuinely improve the experience — never trap users with artificial switching costs or impossible data export; make staying the better choice through real value.

## The Habit Zone

Two axes determine if a product can become a habit:

| | Low Frequency | High Frequency |
|--|---------------|----------------|
| **High Perceived Value** | Viable product (needs ads/marketing) | **HABIT ZONE** |
| **Low Perceived Value** | Failure | Failure |

Ask: how often do users need to engage, what's the perceived value of each engagement, and is frequency high enough to form automatic behavior?

## Habit Testing

The 5% rule: a habit has formed when at least 5% of users show unprompted, habitual usage.

**Three questions:**
1. **Who are the habitual users?** Which users engage most frequently, and what do they share?
2. **What are they doing?** Identify the "Habit Path" — the action sequence that separates power users from casual users.
3. **Why are they doing it?** What internal trigger and emotion precede usage?

See: [references/habit-testing.md](references/habit-testing.md) for testing methodology.

## The Manipulation Matrix

Framework for evaluating the ethics of habit-forming products:

|  | **Maker Uses Product** | **Maker Doesn't Use** |
|--|------------------------|----------------------|
| **Materially Improves User's Life** | **Facilitator** | **Peddler** |
| **Doesn't Improve Life** | **Entertainer** | **Dealer** |

Ask: would I use this myself? Does it genuinely help users achieve their goals? Am I exploiting vulnerabilities or serving needs?

### When NOT to Use the Hook Model

- Your product doesn't genuinely improve lives
- You're targeting vulnerable populations (children, addiction-prone users)
- The business model depends on user regret
- Engagement conflicts with user wellbeing

See: [references/ethical-boundaries.md](references/ethical-boundaries.md) for comprehensive ethics guidance.

### Regulatory Context

Watch emerging regulation: children's apps (COPPA, GDPR-K), dark patterns (rising FTC enforcement), "addictive" notification practices, and loot boxes (expanding gaming rules).

## Onboarding Audit Checklist

Optimizing onboarding for habit formation:

### First Trigger
- [ ] First action obvious and easy; right external trigger for this user
- [ ] Value proposition clear before asking for investment

### First Action
- [ ] Core action completable in under 60 seconds, friction removed
- [ ] UI familiar (no new learning required)

### First Reward
- [ ] Immediate feedback with a variable element (surprise, delight)
- [ ] Reward connects to an internal trigger

### First Investment
- [ ] Investment asked after reward (not before), small but meaningful
- [ ] Investment loads the next trigger

### Loop Completion
- [ ] Clear path back to the trigger; external triggers sent at appropriate times
- [ ] Progression through the Hook is measured

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Relying on external triggers indefinitely** | You're renting attention, not building habits | Map product to an emotion; transition to internal triggers within 30 days |
| **Making the core action too complex** | Users drop off before the reward | Simplify to minimum viable action; apply the six ability factors |
| **Using predictable rewards** | Dopamine response fades with novelty | Add variability across tribe, hunt, and self rewards |
| **Asking for investment before reward** | Users haven't received value yet | Sequence: trigger, action, reward, THEN investment |
| **Ignoring the ethics of your hook** | User regret, backlash, regulatory risk | Use the Manipulation Matrix; be a Facilitator, not a Dealer |

## Quick Diagnostic

Audit any product feature:

| Question | If No | Action |
|----------|-------|--------|
| What's the internal trigger? | Users need reminders to use it | Research user emotions |
| Is the action dead simple? | Users start but don't complete | Remove friction |
| Is the reward variable? | Users get bored | Add unpredictability |
| Does investment load next trigger? | Users don't return | Connect investment to triggers |

## Reference Files

- [triggers.md](references/triggers.md): External and internal trigger design, emotion mapping
- [rewards.md](references/rewards.md): Variable reward types, reinforcement schedules, reward timing
- [habit-testing.md](references/habit-testing.md): Testing methodology, habit zone identification
- [case-studies.md](references/case-studies.md): Instagram, Slack, Duolingo, Pinterest, and failed products analysis
- [ethical-boundaries.md](references/ethical-boundaries.md): Dark patterns vs. ethical engagement, protecting vulnerable users
- [neuroscience-foundations.md](references/neuroscience-foundations.md): Dopamine, variable reinforcement schedules, habit loop neuroscience
- [product-applications.md](references/product-applications.md): B2B SaaS, e-commerce, health apps, productivity tools patterns

## Further Reading

Based on the Hook Model developed by Nir Eyal:

- [*"Hooked: How to Build Habit-Forming Products"*](https://www.amazon.com/Hooked-How-Build-Habit-Forming-Products/dp/1591847788?tag=wondelai00-20) by Nir Eyal
- [*"Indistractable: How to Control Your Attention and Choose Your Life"*](https://www.amazon.com/Indistractable-Control-Your-Attention-Choose/dp/194883653X?tag=wondelai00-20) by Nir Eyal (companion: resisting unwanted habits and building focus)

## About the Author

**Nir Eyal** taught at Stanford Graduate School of Business and the Hasso Plattner Institute of Design, after working in the gaming and advertising industries where he saw habit psychology firsthand. *Hooked* distills that research into a framework used by product teams from startups to Fortune 500s; his follow-up *Indistractable* addresses resisting the same triggers.
