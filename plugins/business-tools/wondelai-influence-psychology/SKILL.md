---
name: influence-psychology
description: 'Apply the seven principles of ethical persuasion (reciprocity, commitment, social proof, authority, liking, scarcity, unity) to product design, copy, and sales. Use when the user mentions "social proof", "persuasive copy", "why users dont convert", "ethical persuasion", "reciprocity", "scarcity tactics", "commitment and consistency", "shared identity", "in-group", "make my copy more persuasive", "increase trust", or "get more people to say yes". Also trigger when designing testimonial sections, crafting urgency messaging, or improving trust signals on landing pages. Covers the principles, when each applies, and ethical limits. For deal negotiation tactics, see negotiation. For viral word-of-mouth, see contagious.'
license: MIT
metadata:
  author: wondelai
  version: "1.4.1"
---

# Influence Psychology Framework

Apply six decades of persuasion science — Cialdini's research into why people say "yes" — to product, copy, and sales, ethically.

## Core Principle

**People don't make decisions rationally — they use mental shortcuts (heuristics) that can be triggered to influence behavior.** These shortcuts evolved because they're usually reliable, but they can also be exploited. Understanding them lets you design products, messaging, and experiences that align with how people actually decide.

## Scoring

**Goal: 10/10.** When reviewing or creating persuasive elements (features, copy, flows, campaigns), run the Quick Diagnostic, then score against the bands below and apply the ethics gate. Always report the current score and the specific change needed to reach 10/10.

- **9-10** — Multiple principles deliberately layered; every claim truthful; users can reverse the decision; passes the transparency test (still works if the user knows the strategy); safe for vulnerable users.
- **7-8** — Principles deliberately layered and honest, but one gap (e.g. weak reversibility, or a single principle where layering was possible).
- **5-6** — One principle present but generic, or leverage left on the table.
- **<=3** — No principle deliberately designed (relying on luck), OR any tactic is deceptive/coercive. Any fabricated proof, fake scarcity, or hidden-cost dark pattern caps the score at 3 regardless of other strengths.

## The Seven Principles of Influence

### 1. Reciprocity

**Core concept:** People feel obligated to give back to those who have given to them first.

**Why it works:** Humans are wired to avoid being indebted — the obligation to repay can overpower personal preference, and the return favor often exceeds the original gift.

**Key insights:**
- The gift must come first (before the request)
- Unexpected, personalized gifts beat expected, generic ones
- Even small gifts create obligation

**Product applications:**

| Context | Reciprocity Trigger | Example |
|---------|---------------------|---------|
| **Free trials** | Full access first, then ask to pay | Spotify Premium trial → subscription |
| **Content marketing** | Value upfront (guides, tools) | HubSpot free CRM → paid tools |
| **Referral programs** | Reward both referrer and referee | Dropbox: both get extra storage |

**Copy patterns:**
- "Here's a gift for you..." (before asking)
- "As a thank you for signing up..."
- "We noticed you needed help with X, so we..."

See [references/reciprocity.md](references/reciprocity.md) when building free trials, lead magnets, or referral rewards — gift tiers, email templates, day-by-day reciprocity-stacking, and A/B variables.

### 2. Commitment & Consistency

**Core concept:** People want to be consistent with their past statements, beliefs, and actions.

**Why it works:** Inconsistency is psychologically uncomfortable; once we take a stand, personal and interpersonal pressure pushes us to behave consistently with it.

**Key insights:**
- Small initial commitments lead to larger ones (foot-in-the-door)
- Public > private; written > verbal; active (user-generated) > passive
- Self-perception: we infer our attitudes from our behavior

**Product applications:**

| Context | Commitment Trigger | Example |
|---------|-------------------|---------|
| **Onboarding** | Easy yes, then larger asks | Duolingo: "Can you commit to 5 min/day?" |
| **Goal setting** | User publicly states a goal | Strava: "I want to run 50km this month" |
| **Habit formation** | Track streaks publicly | Snapchat streaks, GitHub contributions |

**Copy patterns:**
- "What's your biggest challenge with X?" (commitment to a problem)
- "How much would you like to save per month?" (numerical commitment)
- "You said you wanted to achieve X. Let's start with..."

**Onboarding sequence:** micro-commitment ("What brings you here?") → small action (click, choice) → public/written commitment (goal) → reinforce ("Based on what you told us...").

**Ethical boundary:** Make every commitment freely chosen and easily reversible — no trick opt-ins or locked-in defaults the user can't undo.

See [references/commitment-consistency.md](references/commitment-consistency.md) when designing onboarding or goal-setting flows — foot-in-the-door sequences and public-commitment tactics.

### 3. Social Proof

**Core concept:** People determine what's correct by finding out what others think is correct.

**Why it works:** When uncertain, we use others' behavior as a guide — "if everyone's doing it, it must be right."

**Key insights:**
- Most powerful when observers are uncertain; similar others = stronger proof
- Negative social proof backfires ("9 out of 10 don't...")
- Specific numbers beat vague claims ("2,347 users" > "thousands")

**Types of social proof:**

| Type | Definition | Example |
|------|------------|---------|
| **Wisdom of crowds** | Many people use/buy | "Join 50,000+ marketers" |
| **Wisdom of friends** | People you know use it | "3 of your friends use Notion" |
| **Expert** | Authorities endorse | "Recommended by Y Combinator" |
| **Celebrity** | Famous people use it | "Used by Elon Musk" |
| **Certification** | Third-party validation | "SOC 2 compliant", "App of the Year" |
| **User** | Similar people succeeded | "Startups like yours grew 10x" |

**Product applications:**

| Context | Social Proof Implementation | Example |
|---------|----------------------------|---------|
| **Landing pages** | User count, reviews, logos | "Trusted by 10,000+ companies" |
| **Signup flow** | Live signups, popular plans | "23 people signed up in the last hour" |
| **Feature adoption** | Show usage by others | "85% of teams use this feature" |

**Copy patterns:**
- "[X number] of [similar people] are already..."
- "[Name/Company] increased [metric] by [%]"
- "Don't take our word for it. Here's what [users] say..."

**Ethical boundary:** Disclose when proof is curated or cherry-picked (e.g. "selected reviews") rather than presenting it as representative.

See [references/social-proof.md](references/social-proof.md) when building testimonial sections or trust bars — proof types and implementation patterns.

### 4. Authority

**Core concept:** People follow the lead of credible, knowledgeable experts.

**Why it works:** Obedience to authority is deeply ingrained — following experts is an efficient shortcut when we lack expertise ourselves.

**Key insights:**
- Titles, credentials, even symbols (lab coats, official-looking design) trigger automatic compliance
- Admitting a weakness paradoxically increases authority (trustworthiness) — lead with it before strengths
- Expertise doesn't transfer across domains, but people assume it does

**Sources of authority:**

| Type | Signal | Example |
|------|--------|---------|
| **Credentials** | Degrees, certifications | "Built by Stanford PhDs" |
| **Experience** | Years in field, track record | "20 years in cybersecurity" |
| **Association** | Trusted partners, investors | "Backed by Y Combinator" |
| **Content** | Thought leadership, research | "Based on research with 10,000 users" |
| **Transparency** | Honest about limitations | "Works best for teams of 10-50" |

**Product applications:**

| Context | Authority Trigger | Example |
|---------|------------------|---------|
| **About page** | Founder and team expertise | "Built by ex-Google engineers" |
| **Content** | Original research, citations | "State of [Industry] 2026 Report" |
| **Partnerships** | Security certs, integration badges | "SOC 2 Type II", "GDPR compliant" |

**Copy patterns:**
- "Trusted by [authority figure/company]"
- "Research shows that [cite source]..."
- "Our team includes [credentials]"

See [references/authority.md](references/authority.md) when writing About pages, bylines, or trust badges — credential framing and thought-leadership strategies.

### 5. Liking

**Core concept:** People prefer to say yes to those they like.

**Why it works:** Each liking factor (similarity, compliments, cooperation) is a separate lever that independently lowers a person's resistance to a request — they stack.

**Factors that increase liking:**

| Factor | Mechanism | Example |
|--------|-----------|---------|
| **Attractiveness** | Halo effect: attractive = good | Professional headshots, polished design |
| **Similarity** | We like people like us | "I'm a founder just like you" |
| **Compliments** | Flattery works (even when obvious) | "You have great taste in tools" |
| **Cooperation** | Working toward shared goals | "Let's build this together" |
| **Familiarity** | Repeated exposure increases liking | Consistent brand, retargeting |
| **Association** | Linked to positive things | Placement with aspirational lifestyles |

**Product applications:**

| Context | Liking Trigger | Example |
|---------|---------------|---------|
| **Brand voice** | Friendly, conversational, human | Mailchimp's playful copy |
| **Team pages** | Real people, personality | Personal bios, hobbies, photos |
| **Support** | Warm, empathetic responses | "I totally understand that frustration..." |

**Copy patterns:**
- "We're [similar trait] just like you"
- "We built this because we were frustrated with..."
- Casual, warm language ("Hey", "Awesome!", "We got you")

See [references/liking.md](references/liking.md) when setting brand voice or writing support replies — liking factors and tone guidelines. For ready-to-adapt persuasive copy across all seven principles, see [references/copywriting.md](references/copywriting.md).

### 6. Scarcity

**Core concept:** People want more of what they can't have or what's running out.

**Why it works:** Loss aversion is stronger than gain seeking — FOMO triggers urgency, and psychological reactance makes us want what threatens to become unavailable.

**Key insights:**
- Scarcity of time > scarcity of quantity; newly scarce > always scarce (loss framing)
- Competition increases value — if others want it, I want it
- Exclusive access is more valuable than open access

**Types of scarcity:**

| Type | Mechanism | Example |
|------|-----------|---------|
| **Limited quantity** | Finite supply | "Only 5 seats left" |
| **Limited time** | Deadline pressure | "Offer ends Friday" |
| **Exclusive access** | Not everyone can have it | "Invite-only beta" |
| **Competition** | Others competing for it | "12 people viewing this" |

**Product applications:**

| Context | Scarcity Trigger | Example |
|---------|-----------------|---------|
| **Pricing** | Limited-time discount | "Early bird pricing ends in 3 days" |
| **Features** | Beta access, waitlist | "Join 5,000 on the waitlist" |
| **Inventory** | Stock levels | "2 left in stock" |

**Copy patterns:**
- "Limited to the first [X] customers"
- "Offer expires [specific date]"
- "[X] people are viewing this right now"

**Ethical boundary:** Ethical scarcity reflects real constraints (true inventory counts, genuine deadlines, legitimate capacity limits). Unethical: invented limits, countdown timers that reset, "Only 2 left!" shown daily, pressuring vulnerable users.

See [references/scarcity.md](references/scarcity.md) when adding urgency or waitlists — five scarcity types, each with an "ethical when" line and the dark patterns to avoid.

### 7. Unity

**Core concept:** People say yes to those they consider part of "us" (shared identity).

**Why it works:** Tribal identity is fundamental — we make sacrifices for in-group members we wouldn't make for strangers.

**Unity vs. Liking:** Liking = "this person is like me" (similarity); Unity = "this person is me" (shared identity).

**Sources of unity:**

| Type | Mechanism | Example |
|------|-----------|---------|
| **Place** | Hometown, region, nationality | "Built in San Francisco, for founders" |
| **Experience** | Shared hardship or triumph | "We've all struggled with bad CRMs" |
| **Values** | Deep beliefs, mission alignment | "For people who value privacy" |
| **Tribe** | Co-creation, movement | "Join the indie maker community" |

**Product applications:**

| Context | Unity Trigger | Example |
|---------|--------------|---------|
| **Brand positioning** | Define the tribe | "For remote-first teams" |
| **Messaging** | "We" language, shared struggle | "We believe work should be flexible" |
| **Community** | Facilitate co-creation | User-generated content, forums |

**Copy patterns:**
- "For [identity group]" ("For designers", "For bootstrappers")
- "Join [X] others who believe..."
- "We're building this together"

**Ethical boundary:** Build the in-group by what it stands for, not by vilifying an out-group — define "us" without manufacturing a "them" to resent.

See [references/unity.md](references/unity.md) when defining a brand tribe or community — identity-marketing and co-creation strategies.

## Combining Principles

The most powerful persuasion layers multiple principles:

**SaaS landing page:** authority ("Built by ex-Stripe engineers") + social proof ("Trusted by 5,000+ companies") + liking (warm copy) + scarcity ("Join the beta—limited spots") + reciprocity ("Start free, no credit card") + unity ("For founders who move fast").

**Referral program:** reciprocity (reward both parties) + social proof ("X friends already joined") + unity ("Invite your team") + commitment (ask after a good experience).

See [references/case-studies.md](references/case-studies.md) for full worked teardowns of multi-principle stacks across industries.

## The Ethical Line

**Persuasion helps people see value they'd appreciate anyway; manipulation tricks people into choices against their interests.** The deciding tests are in the Quick Diagnostic below — run every persuasive element through them before shipping.

See [references/ethics.md](references/ethics.md) when a tactic feels borderline or you ship to vulnerable users — the persuasion-vs-manipulation decision tree, the regulatory landscape (FTC, GDPR, DSA, dark-patterns law), vulnerable-population safeguards, and audit templates.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Fake social proof** | Destroys trust when discovered | Use real data or don't use it |
| **Overuse of scarcity** | Becomes noise, loses power | Reserve for genuine urgency |
| **Inconsistent authority** | Undermines credibility | Don't claim expertise you lack |
| **Forced reciprocity** | Feels transactional, not genuine | Give without immediate ask |
| **Generic unity** | "Everyone" is not a tribe | Define specific shared identity |

## Quick Diagnostic

Audit any persuasive element:

| Question | If No | Action |
|----------|-------|--------|
| Which principle(s) am I using? | You're relying on luck | Explicitly design for influence |
| Am I combining principles? | Missing leverage | Layer multiple principles |
| Is this claim/tactic truthful? | You're manipulating | Remove or replace with truth |
| Does it help the user (not just convert)? | You're exploiting, not persuading | Realign the tactic with the user's goal |
| Would it still work if the user knew the strategy? | The tactic relies on deception | Replace with a transparent version |
| Can users easily reverse the decision? | Ethical concern | Add clear opt-outs |
| Safe for vulnerable users (children, elderly, distressed)? | Heightened-harm risk | Apply ethics.md safeguards or exclude them |

## Further Reading

Based on Robert Cialdini's research and books:

- [*"Influence: The Psychology of Persuasion"*](https://www.amazon.com/Influence-Psychology-Persuasion-Robert-Cialdini/dp/006124189X?tag=wondelai00-20) by Robert B. Cialdini (Original + Expanded Edition with Unity principle)
- [*"Pre-Suasion: A Revolutionary Way to Influence and Persuade"*](https://www.amazon.com/Pre-Suasion-Revolutionary-Way-Influence-Persuade/dp/1501109790?tag=wondelai00-20) by Robert B. Cialdini (Advanced: creating privileged moments for influence)

## About the Author

**Robert B. Cialdini, PhD** is Regents' Professor Emeritus of Psychology and Marketing at Arizona State University. *Influence*, the foundational text on persuasion science, has sold over 5 million copies worldwide, and he has consulted for Fortune 500 companies, government agencies, and nonprofits on ethical influence.
