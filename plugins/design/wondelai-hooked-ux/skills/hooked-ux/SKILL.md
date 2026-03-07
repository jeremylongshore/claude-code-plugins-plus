---
name: hooked-ux
description: 'Design habit-forming product loops using the Hook Model (Trigger, Action, Variable Reward, Investment). Use when the user mentions "users aren''t coming back", "engagement loops", "habit formation", "push notifications", or "variable rewards". Covers ethics evaluation and onboarding for habits. For friction reduction and B=MAP, see improve-retention. For viral sharing, see contagious.'
license: MIT
metadata:
  author: wondelai
  version: "1.1.1"
---

# Hook Model Framework

Framework for building habit-forming products. Based on a fundamental truth: habits are not created—they are built through successive cycles through the Hook.

## Core Principle

**The Hook Model** = a four-phase process that connects the user's problem to your solution frequently enough to form a habit.

```
Trigger → Action → Variable Reward → Investment
    ↑                                      │
    └──────────────────────────────────────┘
```

**Habit Zone:** Products enter the "habit zone" when used frequently enough and with enough perceived value. The goal is to move users from deliberate usage to automatic, habitual behavior.

## Scoring

**Goal: 10/10.** When reviewing or creating product engagement mechanics, rate them 0-10 based on adherence to the principles below. A 10/10 means full alignment with all guidelines; lower scores indicate gaps to address. Always provide the current score and specific improvements needed to reach 10/10.

## The Four Phases

### 1. Trigger

**Core concept:** The actuator of behavior. What prompts the user to take action? Triggers come in two forms: external (environment-driven) and internal (emotion-driven). The ultimate goal is to move users from external triggers to internal triggers.

**Why it works:** Every habit starts with a cue. Without a trigger, there is no behavior. External triggers get users started, but internal triggers — emotions like boredom, loneliness, uncertainty, or fear of missing out — are what drive unprompted, habitual usage. When your product becomes the automatic response to an internal trigger, you have a habit.

**Key insights:**
- External triggers (push notifications, emails, buttons, ads, word of mouth) initiate behavior early on
- Internal triggers (emotions, routines, situations) are the ultimate goal — users prompt themselves
- The goal is to move users from external triggers to internal triggers over time
- Map your product to the specific negative emotion it resolves (boredom, loneliness, confusion, FOMO)
- Effective external triggers must be well-timed, actionable, and lead to the simplest possible next action

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Onboarding** | Use external triggers to establish first loop | Welcome email with one clear action to take |
| **Retention** | Map product to internal emotional trigger | Instagram resolves boredom; Google resolves confusion |
| **Re-engagement** | External triggers bridge gaps until habit forms | Push notification: "Your friend just posted a photo" |
| **Emotion mapping** | Identify which negative emotion your product addresses | Loneliness → Facebook; Uncertainty → Twitter/News apps |
| **Trigger audit** | Evaluate if users still need external prompts | If yes after 30 days, internal trigger hasn't formed |

**Copy patterns:**
- "You might be wondering about..." (hooks into uncertainty)
- "Don't miss what happened while you were away" (FOMO trigger)
- "Your friend just..." (social/external trigger bridging to internal)
- "Pick up where you left off" (routine trigger)
- Notification copy should name the emotion: "Curious what's new?"

**Ethical boundary:** Never exploit vulnerable emotional states (depression, addiction, grief) as triggers. Triggers should connect users to genuine value, not manufacture anxiety to drive opens.

See: [references/triggers.md](references/triggers.md) for detailed trigger design, emotion mapping, and external-to-internal transition strategies.

### 2. Action

**Core concept:** The simplest behavior done in anticipation of a reward. Guided by the Fogg Behavior Model: B = MAT (Behavior = Motivation + Ability + Trigger). All three must converge at the same moment for action to occur.

**Why it works:** Increasing motivation is hard and unreliable. Reducing friction (increasing ability) is easier and often more effective. The key insight is that making the action simpler is almost always a better strategy than trying to increase motivation. Every extra step, field, or decision is a point where users drop off.

**Key insights:**
- Fogg Behavior Model: Behavior = Motivation x Ability x Trigger — all three must be present simultaneously
- Six elements of simplicity (ability): time, money, physical effort, brain cycles, social deviance, non-routine
- Increasing ability (reducing friction) is almost always more effective than increasing motivation
- The action should be the simplest behavior in anticipation of the reward — not the full task
- Hick's Law: more choices = slower decisions; reduce options to increase action rate

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Signup flow** | Minimize fields and steps to reduce friction | One-click Google/Apple sign-in instead of form |
| **Core action** | Make the key behavior completable in seconds | Twitter: type 280 characters and post (vs. write a blog) |
| **Simplicity audit** | Evaluate each of the six ability factors | Can user complete core action in under 60 seconds? |
| **Progressive disclosure** | Ask for more only after initial reward | Duolingo: play first, create account later |
| **Friction removal** | Identify and eliminate unnecessary steps | Autocomplete, defaults, skip options, smart prefills |

**Copy patterns:**
- "Just one tap to..." (emphasizes simplicity)
- "Takes less than 60 seconds" (time simplicity)
- "No credit card required" (money/risk simplicity)
- "We've set up defaults for you" (brain cycle simplicity)
- Buttons should be verbs: "Post", "Save", "Share" — not "Submit" or "Continue"

**Ethical boundary:** Reducing friction should make genuinely valuable actions easier — not trick users into actions they'd regret. Dark patterns that hide costs or consequences behind simple actions are unethical.

See: [references/triggers.md](references/triggers.md) for how triggers connect to the action phase, and [references/product-applications.md](references/product-applications.md) for action design across product types.

### 3. Variable Reward

**Core concept:** The phase that keeps users coming back. The anticipation of reward — not the reward itself — creates dopamine. Critically, rewards must be variable (unpredictable) to maintain engagement. Predictable rewards lose their power over time.

**Why it works:** The brain's dopamine system responds most strongly to the anticipation of uncertain rewards, not to the rewards themselves. This is the slot machine effect: variable reinforcement schedules are far more engaging than fixed ones. Three types of variable rewards — tribe (social), hunt (resources), and self (mastery) — tap into fundamental human drives.

**Key insights:**
- Dopamine spikes during anticipation of uncertain reward, not upon receiving it
- Three types: Tribe (social validation), Hunt (search for resources/information), Self (personal mastery)
- Predictable rewards lose power; variability is what sustains engagement
- The "slot machine effect": uncertainty is what makes rewards compelling
- Autonomy is critical — users must feel in control; forced engagement backfires
- Finite variability (limited content) eventually becomes predictable; aim for infinite variability

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Social features (Tribe)** | Variable social validation from others | Instagram likes, Reddit upvotes — you never know how many |
| **Content feeds (Hunt)** | Unpredictable stream of resources/information | Infinite scroll with algorithmically varied content |
| **Gamification (Self)** | Personal accomplishment with variable difficulty | Duolingo streaks + surprise bonus challenges |
| **Notifications** | Variable content in each notification | "3 people liked your post" vs. "Sarah commented something surprising" |
| **Search/Discovery** | The hunt for the next great find | Pinterest: scroll to find the perfect pin; eBay: hunt for deals |

**Copy patterns:**
- "See what's new" (implies variability — you don't know what you'll find)
- "You won't believe what happened next" (curiosity + variable reward)
- "3 people responded to your post" (tribe reward, variable quantity)
- "You've unlocked a new achievement!" (self reward, unexpected)
- "Trending now..." (hunt reward — the feed changes every time)

**Ethical boundary:** Variable rewards should deliver genuine value, not exploit compulsive behavior. If users consistently feel worse after engaging (regret, time loss, anxiety), the reward system is extractive, not valuable. Avoid infinite scroll without natural stopping points for vulnerable users.

See: [references/rewards.md](references/rewards.md) for reward design patterns, reinforcement schedules, and reward timing.

### 4. Investment

**Core concept:** The phase that increases the likelihood of another pass through the Hook. Users invest something — time, data, effort, social capital, or money — that improves the product for next use and raises switching costs. Investment loads the next trigger.

**Why it works:** People value what they put effort into (the IKEA effect). Investment creates stored value that makes the product better with use and harder to leave. Critically, investment is not about immediate reward — it's about improving the next cycle. Each investment loads the next trigger, creating a self-reinforcing loop.

**Key insights:**
- IKEA effect: users value what they invest effort into, even irrationally
- Investment creates switching costs (data, content, reputation, skill, social connections)
- Investment should come after reward, not before — users invest when they feel good
- Each investment should load the next trigger (creating content triggers notifications when someone responds)
- Small investments compound: preferences lead to better recommendations lead to more usage
- Stored value increases over time, making the product harder to leave

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Data investment** | Preferences, history, uploads improve personalization | Spotify: the more you listen, the better recommendations get |
| **Content investment** | User-created content they don't want to lose | Instagram posts, Notion documents, Slack message history |
| **Reputation investment** | Reviews, ratings, followers create social capital | Airbnb host ratings, Stack Overflow reputation points |
| **Skill investment** | Learning the interface creates switching cost | Photoshop expertise, Vim muscle memory |
| **Social investment** | Connections and groups that exist only on platform | LinkedIn network, Discord communities, Slack workspaces |

**Copy patterns:**
- "Personalize your experience" (inviting data investment)
- "Complete your profile to get better matches" (investment → future value)
- "Invite your team to collaborate" (social investment)
- "The more you use it, the smarter it gets" (compound investment)
- "Your history, preferences, and connections — all in one place" (switching cost reminder)

**Ethical boundary:** Investment should genuinely improve the user's experience. Don't make data export impossible or trap users with artificial switching costs. Ethical products let users leave with their data while making staying the better choice through real value.

See: [references/product-applications.md](references/product-applications.md) for investment patterns across B2B SaaS, e-commerce, health apps, and productivity tools.

## The Habit Zone

Two axes determine if a product can become a habit:

| | Low Frequency | High Frequency |
|--|---------------|----------------|
| **High Perceived Value** | Viable product (needs ads/marketing) | **HABIT ZONE** |
| **Low Perceived Value** | Failure | Failure |

**Questions:**
- How often do users need to engage? (Daily, weekly, monthly?)
- What's the perceived value of each engagement?
- Is frequency high enough to form automatic behavior?

## Habit Testing

The 5% rule: A product has formed a habit when at least 5% of users show unprompted, habitual usage.

**Three questions for habit testing:**

1. **Who are the habitual users?**
   - Which users engage most frequently?
   - What do they have in common?

2. **What are they doing?**
   - What's the "Habit Path" (common sequence of actions)?
   - What differentiates power users from casual users?

3. **Why are they doing it?**
   - What internal trigger drives the behavior?
   - What emotion precedes usage?

See: [references/habit-testing.md](references/habit-testing.md) for testing methodology.

## The Manipulation Matrix

Framework for evaluating the ethics of habit-forming products.

|  | **Maker Uses Product** | **Maker Doesn't Use** |
|--|------------------------|----------------------|
| **Materially Improves User's Life** | **Facilitator** | **Peddler** |
| **Doesn't Improve Life** | **Entertainer** | **Dealer** |

**Questions to ask:**
1. Would I use this product myself?
2. Does it genuinely help users achieve their goals?
3. Am I exploiting vulnerabilities or serving needs?

### When NOT to Use the Hook Model

The Hook Model is inappropriate when:
- Your product doesn't genuinely improve lives
- You're targeting vulnerable populations (children, addiction-prone users)
- Business model depends on user regret
- Engagement conflicts with user wellbeing

See: [references/ethical-boundaries.md](references/ethical-boundaries.md) for comprehensive ethics guidance.

### Regulatory Context

Be aware of emerging regulations around:
- **Children's apps:** COPPA, GDPR-K restrictions
- **Dark patterns:** FTC enforcement increasing
- **Notification practices:** Some jurisdictions regulating "addictive" features
- **Loot boxes:** Gaming regulations expanding

## Onboarding Audit Checklist

Optimizing onboarding for habit formation:

### First Trigger
- [ ] Is the first action obvious and easy?
- [ ] Is the value proposition clear before asking for investment?
- [ ] Are we using the right external trigger for this user?

### First Action
- [ ] Can the user complete the core action in under 60 seconds?
- [ ] Have we removed all unnecessary friction?
- [ ] Is the UI familiar (not requiring new learning)?

### First Reward
- [ ] Does the user get immediate feedback?
- [ ] Is there a variable element (surprise, delight)?
- [ ] Does the reward connect to an internal trigger?

### First Investment
- [ ] Do we ask for investment after reward (not before)?
- [ ] Is the investment small but meaningful?
- [ ] Does the investment load the next trigger?

### Loop Completion
- [ ] Is there a clear path back to the trigger?
- [ ] Do we send external triggers at appropriate times?
- [ ] Are we measuring progression through the Hook?

## Quick Diagnostic

Audit any product feature:

| Question | If No | Action |
|----------|-------|--------|
| What's the internal trigger? | Users need reminders to use it | Research user emotions |
| Is the action dead simple? | Users start but don't complete | Remove friction |
| Is the reward variable? | Users get bored | Add unpredictability |
| Does investment load next trigger? | Users don't return | Connect investment to triggers |

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Relying on external triggers indefinitely** | Users never form internal triggers; you're renting attention, not building habits | Map product to a specific emotion; transition from external to internal triggers within 30 days |
| **Making the core action too complex** | Users drop off before reaching the reward phase | Simplify to the minimum viable action; apply Fogg's six ability factors |
| **Using predictable rewards** | Engagement drops after novelty wears off; dopamine response fades | Introduce variability across tribe, hunt, and self reward types |
| **Asking for investment before reward** | Users haven't received value yet and resist investing effort | Always sequence: trigger, action, reward, THEN investment |
| **Ignoring the ethics of your hook** | User regret, backlash, regulatory risk, brand damage | Use the Manipulation Matrix; aim to be a Facilitator, not a Dealer |

## Reference Files

- [triggers.md](references/triggers.md): External and internal trigger design, emotion mapping
- [rewards.md](references/rewards.md): Variable reward types, reinforcement schedules, reward timing
- [habit-testing.md](references/habit-testing.md): Testing methodology, habit zone identification
- [case-studies.md](references/case-studies.md): Instagram, Slack, Duolingo, Pinterest, and failed products analysis
- [ethical-boundaries.md](references/ethical-boundaries.md): Dark patterns vs. ethical engagement, protecting vulnerable users
- [neuroscience-foundations.md](references/neuroscience-foundations.md): Dopamine, variable reinforcement schedules, habit loop neuroscience
- [product-applications.md](references/product-applications.md): B2B SaaS, e-commerce, health apps, productivity tools patterns

## Further Reading

This skill is based on the Hook Model developed by Nir Eyal. For the complete methodology, research, and case studies:

- [*"Hooked: How to Build Habit-Forming Products"*](https://www.amazon.com/Hooked-How-Build-Habit-Forming-Products/dp/1591847788?tag=wondelai00-20) by Nir Eyal
- [*"Indistractable: How to Control Your Attention and Choose Your Life"*](https://www.amazon.com/Indistractable-Control-Your-Attention-Choose/dp/194883653X?tag=wondelai00-20) by Nir Eyal (companion: resisting unwanted habits and building focus)

## About the Author

**Nir Eyal** is an author, lecturer, and investor who has taught at Stanford Graduate School of Business and the Hasso Plattner Institute of Design at Stanford. He previously worked in the gaming and advertising industries, where he gained firsthand experience with the psychology of habit-forming products. *Hooked* distills years of research and consulting into a practical framework used by product teams at startups and Fortune 500 companies worldwide. His follow-up book, *Indistractable*, addresses the other side of the equation — helping individuals manage the same behavioral triggers that make products habit-forming. Eyal writes extensively about the intersection of psychology, technology, and business at NirAndFar.com.
