# The Seven Deadly Flaws of Extrinsic Rewards

Extrinsic rewards -- bonuses, prizes, commissions, points, badges -- are the default tool organizations reach for when they want to change behavior. The research is clear: for any work requiring cognitive effort, creativity, or judgment, extrinsic "if-then" rewards either fail to improve performance or actively make it worse. This reference provides a deep dive into the seven mechanisms by which rewards backfire, when they do work, and how to design reward systems that minimize damage.

## Flaw 1: Extinguish Intrinsic Motivation

When people already find a task interesting, adding an external reward reduces their desire to do it once the reward disappears.

### The Research

**Deci (1969):** College students solved Soma puzzles. Group A was paid in session two; Group B was never paid. In session three (no payment for either), Group A spent significantly less free time on the puzzles. Payment had turned play into work.

**Lepper, Greene, & Nisbel (1973):** Preschoolers who already liked drawing were divided into three groups. The "expected reward" group was told they'd get a certificate for drawing. Two weeks later, these children drew 50% less than children who received no reward or an unexpected reward. The expected reward had undermined what was previously spontaneous enjoyment.

**Meta-analysis by Deci, Koestner, & Ryan (1999):** Reviewed 128 studies and found that tangible, expected, contingent rewards significantly undermine intrinsic motivation for interesting tasks. The effect is robust across ages, settings, and cultures.

### Mechanism

The cognitive shift is called the **overjustification effect**. When an external reason is added to an activity that already has an internal reason, the brain recategorizes the activity: "I must be doing this for the reward, not because I enjoy it." Remove the reward and the internal reason has been weakened.

### Product Implications

| Scenario | What Happens | Example |
|----------|-------------|---------|
| Paying users to write reviews | Users stop writing reviews without payment | Early Amazon Vine program churn |
| Points for every login | Users login for points, not value | Engagement drops when points system changes |
| Bonuses for feature usage | Feature becomes "work" | Enterprise software with mandatory adoption bonuses |

## Flaw 2: Diminish Performance

External rewards narrow focus, which helps for simple tasks but hurts for tasks requiring creative problem-solving.

### The Candle Problem (Glucksberg, 1962)

Participants were given a candle, a box of thumbtacks, and matches. The goal: attach the candle to the wall so wax doesn't drip on the table. The solution requires creative insight -- empty the box, tack it to the wall, place the candle inside.

- **Group offered cash rewards** for fast solving: took **3.5 minutes longer** on average
- Rewards narrowed their focus; they couldn't see the box as anything other than a container for tacks
- When the tacks were presented **outside** the box (making the solution obvious/algorithmic), the rewarded group solved faster

This is the core finding: rewards help with algorithmic tasks (clear path to solution) and hurt with heuristic tasks (requiring exploration and insight).

### The London School of Economics Review (2009)

An analysis of 51 studies of corporate pay-for-performance plans found that "financial incentives can result in a negative impact on overall performance." The pattern held across industries and compensation structures.

### Product Implications

- Reward systems that create urgency (countdown timers, limited-time bonuses) narrow user focus and reduce exploration
- Competition-based features (leaderboards with prizes) reduce the creative solutions users discover
- Gamification that rewards speed over quality drives shallow engagement

## Flaw 3: Crush Creativity

Rewards constrain the mental space needed for creative work by directing attention toward the reward and away from open exploration.

### The Research

**Amabile (1985):** Artists who created commissioned (rewarded) work were rated by expert panels as significantly less creative than when the same artists created non-commissioned work. The quality of execution was equivalent; only creativity suffered.

**McGraw & McCullers (1979):** Participants rewarded for solving problems continued to use rote strategies even after the problems changed and required new approaches. The reward locked them into existing patterns.

### Why This Matters for Product Design

- Feature bounties and hackathon prizes can reduce the creativity of submissions
- "Fastest to complete" challenges in learning products discourage experimentation
- Reward-driven A/B testing (rewarding teams for wins) can reduce willingness to run bold experiments

## Flaw 4: Crowd Out Good Behavior

When you attach a financial value to a behavior that was previously governed by social or moral norms, people shift from a social framework to a market framework.

### The Daycare Study (Gneezy & Rustichelli, 2000)

A daycare in Haifa, Israel, introduced a fine for parents who picked up children late. The result: **late pickups doubled**. Parents reframed lateness from a moral failing ("I'm inconveniencing the teacher") to a market transaction ("I'm paying for extra time"). When the fine was later removed, late pickups stayed high -- the social norm had been permanently damaged.

### The Blood Donation Effect (Titmuss, 1970; Mellstrom & Johannesson, 2008)

When blood donors were offered small payments, donation rates dropped -- especially among women. Payment crowded out the altruistic motivation. The act shifted from "generous contribution" to "low-paying job."

### Product Implications

| Good Behavior | Reward Introduced | Result |
|--------------|-------------------|--------|
| Community help (forums) | Points per answer | Quantity up, quality down; helpful users leave |
| User referrals (organic) | Cash per referral | Spam referrals replace genuine recommendations |
| Content creation (passion) | Pay per post | Clickbait replaces thoughtful content |

## Flaw 5: Encourage Cheating, Shortcuts, and Unethical Behavior

When rewards are tied to specific outcomes, people optimize for the metric -- even through dishonest means.

### Case Studies

**Wells Fargo (2016):** Employees were given aggressive sales targets with bonuses. They responded by opening over 3.5 million fake accounts without customer consent. The reward system didn't create bad people; it created an environment where good people did bad things.

**Sears Auto Centers (1992):** Mechanics were given minimum repair quotas. They began recommending unnecessary repairs. California's Department of Consumer Affairs found systematic overcharging driven entirely by the incentive structure.

**Atlanta Public Schools (2009):** Teachers and administrators altered standardized test scores after bonuses were tied to test performance. 178 educators were implicated. The reward system made cheating the rational economic choice.

### The Pattern

```
Specific metric target + Reward for hitting it = Optimized metric (by any means)
```

### Product Implications

- Rewarding users for "completing" profiles leads to fake data entry
- Paying for app reviews leads to fake reviews
- Rewarding content volume leads to AI-generated spam
- Referral bonuses lead to self-referral fraud

## Flaw 6: Become Addictive

Extrinsic rewards follow the same habituation curve as other stimuli: the same reward produces diminishing satisfaction over time, requiring escalation.

### The Hedonic Treadmill in Compensation

Last year's bonus becomes this year's expectation. Research by Kahneman and Deaton (2010) showed that while emotional well-being rises with income up to approximately $75,000/year (adjusted for inflation), it plateaus beyond that. Yet bonus expectations continue to escalate.

### The Escalation Pattern

| Year | Bonus | Satisfaction | Expectation for Next Year |
|------|-------|-------------|--------------------------|
| 1 | $5,000 | High | $5,000+ |
| 2 | $5,000 | Neutral | $7,000+ |
| 3 | $5,000 | Negative | $10,000+ |
| 4 | $7,000 | Moderate | $10,000+ |

The same dynamic applies in products: a daily login reward that excited users in month one becomes an expectation by month three and a grievance if removed by month six.

### Product Implications

- Points systems require inflation management (users expect more points over time)
- Discount-based engagement (coupons, sales) trains users to wait for deals
- Streak rewards lose motivational power and become anxiety-driven obligations

## Flaw 7: Foster Short-Term Thinking

Rewards orient behavior toward the reward period and away from long-term value creation.

### The Research

**Laverty (1996):** Quarterly earnings incentives drive executives to sacrifice long-term R&D for short-term results. Companies with heavy short-term incentives invest less in innovation, employee development, and infrastructure.

**Thaler et al. (1997):** People given frequent performance feedback (analogous to frequent reward cycles) take fewer risks and make worse long-term decisions than those given infrequent feedback. This is called **myopic loss aversion**.

### Product Implications

| Short-Term Incentive | Short-Term Behavior | Long-Term Cost |
|---------------------|---------------------|----------------|
| Daily login rewards | Users login but don't engage | No habit formation; users leave when rewards stop |
| Flash sale urgency | Users buy impulsively | Increased returns; reduced brand trust |
| Monthly usage targets | Users binge at month-end | No sustainable workflow adoption |

## When Extrinsic Rewards DO Work

Rewards are not universally harmful. They work well for **algorithmic tasks** -- tasks with a clear set of steps and a known solution.

### Algorithmic vs. Heuristic Tasks

| Task Type | Description | Reward Effect | Examples |
|-----------|-------------|---------------|----------|
| **Algorithmic** | Clear steps, known solution | Rewards improve speed and output | Data entry, assembly, form filling |
| **Heuristic** | No clear path, requires exploration | Rewards hurt performance | Design, strategy, writing, coding |

### Conditions Where Rewards Help

- The task is genuinely boring and has no intrinsic motivation
- The task requires no creative thinking
- The reward acknowledges that the task is dull ("I know this isn't exciting, but...")
- There is no existing intrinsic motivation to undermine

## "If-Then" vs. "Now-That" Rewards

This distinction is the most actionable takeaway for reward design.

### Comparison

| Dimension | "If-Then" Reward | "Now-That" Reward |
|-----------|-----------------|-------------------|
| **Timing** | Announced before the task | Given after the task |
| **Expectation** | Expected, contingent | Unexpected, non-contingent |
| **Framing** | "If you do X, you get Y" | "Now that you did X, here's Y" |
| **Motivation impact** | Undermines intrinsic motivation | Minimal impact on intrinsic motivation |
| **Example (product)** | "Complete 5 lessons to earn a badge" | "You completed 5 lessons! Here's something special." |
| **Example (team)** | "Hit quota, get bonus" | "Your work this quarter was outstanding -- here's a bonus" |

### Why "Now-That" Works Better

- No prior expectation means no cognitive reframing of the task
- The reward feels like recognition, not payment
- The person doesn't optimize for the reward during the task
- Caution: if "now-that" rewards become predictable, they convert to "if-then" rewards

## Reward Design Guidelines

When rewards are genuinely necessary, follow these principles to minimize damage.

### Checklist for Necessary Reward Systems

- [ ] The task is primarily algorithmic (clear steps, little creativity required)
- [ ] There is minimal existing intrinsic motivation to undermine
- [ ] The reward acknowledges the routine nature of the task
- [ ] The reward is offered with maximum autonomy in how to complete the task
- [ ] The reward is non-controlling (no surveillance or micromanagement attached)
- [ ] The reward provides useful information about competence (feedback, not just payment)
- [ ] The reward is fair relative to the effort (unfair rewards are worse than no reward)
- [ ] "Now-that" is preferred over "if-then" wherever possible
- [ ] The reward doesn't create a single metric that invites gaming

### Reward Escalation Prevention

| Strategy | How It Works |
|----------|-------------|
| Vary reward type | Alternate between recognition, autonomy grants, learning opportunities |
| Keep rewards unexpected | Surprise recognition prevents entitlement cycles |
| Tie rewards to effort, not outcome | "You worked hard on this" vs. "You hit the number" |
| Use non-tangible rewards | Autonomy, choice, praise, and feedback resist habituation |
| Cap reward frequency | Monthly or quarterly instead of daily prevents rapid escalation |

## Common Reward System Mistakes in Products and Teams

### Product Mistakes

| Mistake | Why It Fails | Better Approach |
|---------|-------------|-----------------|
| Points for every action | Devalues meaningful progress | Reserve recognition for genuine milestones |
| Leaderboards showing top 10 | Discourages 99% of users | Show personal progress or nearby peers |
| Time-limited rewards | Creates anxiety, not engagement | Celebrate completion regardless of timing |
| Removing earned rewards | Feels punishing, erodes trust | Rewards once earned should persist |
| Identical rewards for all | No autonomy, no personal meaning | Let users choose their reward type |

### Team Mistakes

| Mistake | Why It Fails | Better Approach |
|---------|-------------|-----------------|
| Stack-ranking with bonuses | Pits team members against each other | Team-based recognition |
| Individual commissions only | Discourages collaboration | Mix individual and team incentives |
| Surprise metric changes | Destroys trust in the system | Stable, transparent criteria |
| Paying for hours, not output | Rewards presence over productivity | Focus on outcomes and autonomy |
| Annual reviews tied to ratings | Once-a-year feedback cycle | Continuous, informal feedback |

### Self-Assessment: Is Your Reward System Helping or Hurting?

| Question | Yes = Risk | Action |
|----------|-----------|--------|
| Do users/employees work only when rewarded? | Intrinsic motivation is gone | Rebuild intrinsic drivers before adding rewards |
| Are people gaming the metrics? | Reward is misaligned | Redesign metrics or remove contingent rewards |
| Do people expect bigger rewards each cycle? | Addiction pattern | Shift to non-tangible, variable recognition |
| Did engagement drop after changing rewards? | Reward dependency | Gradually transition to intrinsic motivation design |
| Are people doing the minimum to qualify? | No intrinsic interest | The task may need redesign, not better rewards |
