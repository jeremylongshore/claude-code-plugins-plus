# Hook Model - Implementation Guide

Step-by-step methodology for building habit-forming product loops using Nir Eyal's four-phase Hook Model.

## The Hook Model Overview

```
Trigger → Action → Variable Reward → Investment → (repeat)
```

Each pass through the loop:
- Requires less external motivation to initiate
- Creates stronger internal triggers
- Increases the investment in the product (harder to leave)

A product becomes habitual when users reach the point where an internal trigger (an emotion, a feeling, a routine) automatically prompts use — before any external trigger is needed.

## Step 1: Identify and Design Triggers

Triggers prompt action. They are either external (a notification, an email, an ad) or internal (a feeling, a routine, a thought).

**1a. External triggers (getting started)**

| Type | Description | Examples |
|------|-------------|---------|
| Paid | Ads and promotions | Facebook ad, Google search ad |
| Earned | PR, viral content | Press mention, shared content |
| Relationship | Word-of-mouth | Friend referral, team invite |
| Owned | In-product notifications | Push notification, email, badge |

Owned triggers are the most valuable at scale: once the user installs the app or subscribes to email, you can trigger for free.

**1b. Internal triggers (the goal)**
- Internal triggers are emotions or thoughts that prompt product use
- Map the emotion your target user feels immediately before they could open your product
- Examples:
  - Boredom → social media
  - Loneliness → messaging apps
  - Uncertainty → Google/search
  - FOMO → news or social feeds
  - Stress about a task → productivity tool

**1c. Identify the right internal trigger**
Ask "Why?" five times about your user's behavior until you reach an emotion:
- "Why would they open the app?" → "To catch up on messages"
- "Why do they need to catch up?" → "They feel anxious about missing something"
- "Why does that make them anxious?" → "They worry about being left out of conversations that matter"
- Internal trigger: **fear of missing out / social anxiety**

## Step 2: Simplify the Action

Action = the simplest behavior done in anticipation of a reward.

The key principle: the simpler the action, the more likely it will happen. Reduce friction until the action requires almost no conscious effort.

**2a. Fogg's B=MAP formula**
```
Behavior = Motivation + Ability + Prompt
```
- If motivation is low, ability must be very high (make it effortless)
- If ability is low (high friction), motivation must be very high (rare)
- Design to increase ability: reduce steps, reduce thinking, reduce decisions

**2b. Six elements of simplicity (Fogg)**
- Time: how long does the action take?
- Money: does it cost anything (directly or in mental accounting)?
- Physical effort: how much physical work is involved?
- Brain cycles: how much thinking does it require?
- Social deviance: how different is this from what others do?
- Non-routine: how much does it disrupt established patterns?

**2c. Action audit**
- Map the exact steps from trigger to action completion
- Count every tap, scroll, decision, and form field
- Reduce: every eliminated step increases completion rate

**2d. Heuristic defaults**
- Pre-fill forms with intelligent defaults
- One-tap actions wherever possible (one-click purchase, quick reply)
- Don't make users think: provide the obvious, correct choice in the UI

## Step 3: Design Variable Rewards

Variable rewards are the engine of habit formation. The brain craves the anticipation of reward more than the reward itself.

**3a. Three types of variable rewards**

| Type | Definition | Examples |
|------|-----------|---------|
| Tribe | Social validation, connection, acceptance | Likes, comments, follower counts, multiplayer outcomes |
| Hunt | Search for information, resources, or outcomes | Social feed, email inbox, product search results, news |
| Self | Achievement, mastery, completion | Game progress, task completion, streaks, personal bests |

**3b. Variability is key**
- A slot machine pays out randomly — the uncertainty is what makes it compelling
- Variable reward mechanisms: algorithmic feeds (you don't know what you'll see), inbox (you don't know what's waiting), social validation (you don't know if people will respond)
- Predictable rewards are boring: a "good job!" every single time becomes meaningless

**3c. Reward the user's effort, not just the outcome**
- Rewards that are connected to effort feel earned and reinforce the habit
- Empty rewards (notifications for completing a form) feel hollow
- Design rewards that validate the user's identity or progress

**3d. Scratch the itch**
- The reward must scratch the internal trigger itch that started the cycle
- If the trigger is boredom, the reward must be stimulating content
- If the trigger is loneliness, the reward must be genuine connection
- Mismatch between trigger and reward = low retention

## Step 4: Design the Investment Phase

Investment = an action that increases the likelihood of the user returning to the next trigger. Unlike actions (which deliver immediate rewards), investments increase the value of the product over time.

**4a. Types of investments**

| Type | Description | Example |
|------|-------------|---------|
| Stored value | User adds data that makes the product smarter | Playlist curation, photos, contacts |
| Content | User creates content that others engage with | Posts, reviews, comments |
| Followers/Connections | Building a social graph | Following people who then follow back |
| Reputation | Building status that exists only in the product | Points, levels, badges |
| Skills learned | Skill that is harder to transfer than to continue | Learning a new interface, tool proficiency |
| Preferences | Customizations that personalize the product | Dark mode, notification settings, saved filters |

**4b. The investment phase loads the next trigger**
- Investments should make the next external trigger more likely or create the internal trigger directly
- After a user writes a post (investment), they return to see the likes (tribe reward) → the anticipation of seeing those likes IS the next internal trigger

**4c. Investment timing**
- The investment must come AFTER the reward, not before
- Asking for investment before delivering value kills the loop
- Onboarding that starts with "set up your profile, invite friends, import data" before showing any value fails here

## Step 5: Ethics Assessment

Before deploying habit-forming mechanics, run the Hook Model Ethics Test:

**5a. The Hooked Quadrant**

| Outcome | Habit-forming? | Result |
|---------|---------------|--------|
| Improves users' lives | Yes | Facilitator (ideal) |
| Improves users' lives | No | Peddler (neutral) |
| Harms users | Yes | Dealer (dangerous) |
| Harms users | No | Entertainer (acceptable) |

**5b. Questions to ask:**
- Would I use this product myself?
- Does using this product leave users better or worse off?
- Does this product exploit psychological weaknesses or genuinely serve user goals?
- Could I publicly explain the psychological mechanics behind this design?

Manipulative designs (deliberately exploiting cognitive biases to override user intent) create short-term engagement but long-term backlash and churn.

## Step 6: Map Your Product's Hook

Build the Hook Canvas for your product:

```
INTERNAL TRIGGER: What emotion prompts use?
  → ___________________________

EXTERNAL TRIGGER: What notification/cue starts the cycle?
  → ___________________________

ACTION: What is the simplest behavior before the reward?
  Current steps: ___ (target: 2 or fewer)
  Biggest friction: _______________

VARIABLE REWARD: What type? (Tribe / Hunt / Self)
  Reward mechanism: ______________
  Variability source: _____________

INVESTMENT: What does the user add to the product?
  Investment type: ________________
  How it loads the next trigger: ___
```

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| External triggers that feel intrusive | Users disable notifications → loop broken | Ensure trigger feels helpful, not annoying |
| Too many steps before reward | Users drop off in the action phase | Audit and reduce steps; test 1-tap actions |
| Predictable, non-variable rewards | Reward becomes expected → loses power | Introduce genuine variability in content or outcome |
| Investment before value | Users never invest because they haven't been rewarded yet | Deliver reward first; invest after |
| Habit-forming without purpose | High engagement, high churn when something better arrives | Ensure the habit serves the user's actual goals |

## Quick-Start Checklist

- [ ] Internal trigger identified (the emotion, verified with 5 Whys)
- [ ] External trigger designed: notification, email, or social cue
- [ ] Action mapped with step count; target 2 or fewer steps to first reward
- [ ] Variable reward type selected: Tribe, Hunt, or Self
- [ ] Variability mechanism identified (how are rewards unpredictable?)
- [ ] Investment phase identified: what does the user add?
- [ ] Investment leads to next trigger (complete the loop)
- [ ] Ethics assessment passed: Facilitator or Entertainer quadrant
- [ ] Hook Canvas fully documented
