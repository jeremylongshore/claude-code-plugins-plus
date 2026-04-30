---
name: contagious
description: |
  Engineer word-of-mouth and virality using the STEPPS framework (Social Currency, Triggers, Emotion, Public, Practical Value, Stories). Use when the user mentions "go viral", "word of mouth", "shareable content", "social currency", or "why people share". Covers environmental triggers and high-arousal emotional content. For sticky messaging, see made-to-stick. For persuasion tactics, see influence-psychology. Trigger with 'contagious'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [business, contagious]
---
# Word-of-Mouth & Virality Framework

A framework for engineering word-of-mouth and making products, ideas, and content contagious. Based on Jonah Berger's research into why certain things catch on while others languish in obscurity — and how to systematically tip the odds in your favor.

## Core Principle

**Virality is not born — it is engineered.** Products don't go viral by luck or by simply being great. They spread because they were designed — consciously or unconsciously — to be shared.

**The foundation:** Contrary to popular belief, only 7% of word-of-mouth happens online. The remaining 93% happens offline, in everyday conversations. This means virality isn't just about social media — it's about understanding the psychology of why people talk about and share certain things. Sharing follows predictable psychological patterns, and these patterns can be engineered into any product, idea, or piece of content using the STEPPS framework.

## Scoring

**Goal: 10/10.** When reviewing or creating products, campaigns, content, or features for shareability, rate 0-10 based on adherence to the STEPPS principles below. A 10/10 means the offering activates all six STEPPS drivers; lower scores indicate untapped viral potential. Always provide the current score and specific improvements needed to reach 10/10.

## STEPPS Overview

Six principles that make things contagious:

```
set -euo pipefail
S - Social Currency     → Does sharing it make people look good?
T - Triggers            → Is there an environmental cue that reminds people of it?
E - Emotion             → Does it evoke high-arousal feelings?
P - Public              → Is it visible when people use or consume it?
P - Practical Value     → Is it genuinely useful information people want to pass along?
S - Stories             → Is it wrapped in a narrative people want to tell?
```

**Not a checklist — a multiplier.** Each principle independently increases the likelihood of sharing. The most contagious ideas activate multiple STEPPS simultaneously. But even activating one or two well can dramatically increase word-of-mouth.

| Principle | Core Question | Sharing Driver |
|-----------|--------------|----------------|
| **Social Currency** | Does it make people look good to share? | Self-enhancement |
| **Triggers** | What in the environment reminds people of it? | Top-of-mind accessibility |
| **Emotion** | Does it fire up high-arousal feelings? | Physiological arousal |
| **Public** | Can others see people using/engaging with it? | Observational learning |
| **Practical Value** | Is it useful enough to pass along? | Altruism and helpfulness |
| **Stories** | Is the brand embedded in a narrative? | Entertainment and identity |

## The STEPPS Framework

### 1. Social Currency

**Core concept:** People share things that make them look good — smart, cool, in-the-know. If your product or idea makes people feel like insiders, they'll spread it to boost their own image.

**Why it works:** We use brands and information as social signals. Sharing remarkable facts, exclusive access, or high-status products is a form of self-enhancement. People don't just share what they think — they share what makes them look good for thinking it.

**Key insights:**
- **Remarkability** — things that are surprising, novel, or extreme get shared because they make the sharer seem interesting. "Did you know...?" is one of the most powerful sharing triggers
- **Game mechanics** — leaderboards, badges, status tiers, and achievement systems create visible markers of accomplishment that people want to display and talk about
- **Exclusivity and scarcity** — secret menus, invite-only access, members-only content — making people feel like insiders gives them social currency when they share "insider knowledge" with their circle
- **Inner remarkability** — even mundane products can find their remarkable angle. The key is framing, not the product itself

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| SaaS onboarding | Achievement milestones users can share | "I just hit 1,000 tasks completed on Todoist" |
| E-commerce | Exclusive early access for loyal customers | Amazon Prime early deals |
| Content platform | Insider statistics or year-in-review | Spotify Wrapped |
| B2B product | Industry benchmarking data users want to cite | HubSpot State of Marketing report |
| Mobile app | Shareable accomplishment cards | Duolingo streak badges |
| Community | Tiered status with visible badges | Stack Overflow reputation system |

**Copy patterns:**
- "Most people don't know that..."
- "You're one of the first to try..."
- "Only available to [exclusive group]..."
- "Here's what [X] insiders know..."
- "You've unlocked [achievement]..."
- "Share your [impressive metric]..."

**Ethical boundary:** Social currency should make people genuinely feel good, not manipulate through false scarcity or manufactured exclusivity that breeds toxicity. Create real insider value, not artificial gatekeeping.

See: [references/social-currency.md](references/social-currency.md) for remarkability exercises and game mechanics design.

### 2. Triggers

**Core concept:** Top-of-mind means tip-of-tongue. Environmental cues — sights, sounds, smells, times of day, routines — can trigger people to think about and talk about your product. The more frequently people encounter your trigger, the more they'll talk about you.

**Why it works:** Most word-of-mouth is not driven by excitement about the product itself but by whatever happens to be top-of-mind at the moment of conversation. If your product is linked to a frequent environmental cue, it gets mentioned more often — not because it's more exciting, but because it's more accessible in memory.

**Key insights:**
- **Frequency beats strength** — a trigger encountered daily (like coffee) is more valuable than a powerful but rare trigger (like a holiday). Kit Kat linked itself to coffee breaks, which happen multiple times per day
- **Habitat matters** — where and when do people encounter environments related to your product? Those are your trigger opportunities
- **Competitive triggers** — you can link competitor moments to your own brand. When people think of [competitor's context], they think of you instead
- **Ongoing vs. temporary** — triggers that persist in the environment (a desk item, a daily routine) generate sustained word-of-mouth, while event-based triggers create spikes
- **Context linking** — pair your product with an existing, frequent behavior or environment

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Food/Beverage | Link to daily routine or habit | Kit Kat + coffee break |
| Productivity tool | Tie to a recurring workflow moment | "Every Monday standup..." |
| Health app | Connect to a physiological cue | "When you feel stressed..." |
| Financial product | Link to payday or spending moment | "Every time you get paid..." |
| Content/Media | Tie to a day of the week | "Taco Tuesday" driving taco talk |
| E-commerce | Connect to seasonal or weather triggers | "When it rains..." campaigns |

**Copy patterns:**
- "Every time you [frequent activity], think of..."
- "Next time you [daily habit]..."
- "When you see [environmental cue]..."
- "It's [day/time] — time for..."
- "Whenever you [routine behavior]..."

**Ethical boundary:** Triggers should create genuine, helpful associations. Hijacking sensitive contexts (grief, health scares) as triggers is manipulative and will backfire.

See: [references/triggers.md](references/triggers.md) for habitat analysis and trigger design frameworks.

### 3. Emotion

**Core concept:** When we care, we share. High-arousal emotions — both positive (awe, excitement, amusement) and negative (anger, anxiety) — drive sharing. Low-arousal emotions (sadness, contentment) suppress it.

**Why it works:** Physiological arousal — the racing heart, the tightened muscles, the activated state — creates a need to share. It's not about positivity vs. negativity; it's about activation vs. deactivation. Content that fires people up gets shared; content that brings people down gets ignored.

**Key insights:**
- **High-arousal positive:** awe, excitement, amusement, humor, inspiration — all drive sharing
- **High-arousal negative:** anger, anxiety, outrage, fear — also drive sharing (controversies spread fast)
- **Low-arousal positive:** contentment, relaxation, satisfaction — suppress sharing (people feel no urgency to act)
- **Low-arousal negative:** sadness, melancholy, disappointment — suppress sharing (people withdraw)
- **Awe is the most powerful sharing emotion** — content that makes people feel small in the face of something vast, beautiful, or surprising spreads the furthest
- **Emotional framing** — the same information can be framed to evoke different arousal levels. Facts inform; emotional framing motivates sharing

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Launch content | Engineer awe through unexpected scale or beauty | Apple keynote reveals |
| Social campaigns | Tap righteous anger at an injustice | Dove "Real Beauty" challenging beauty standards |
| Product demos | Create amusement through unexpected use cases | Blendtec "Will It Blend?" |
| User milestones | Spark excitement at personal achievement | Fitness apps celebrating PRs |
| Brand storytelling | Inspire through human triumph narratives | Nike "Just Do It" athlete stories |
| Feature announcements | Generate curiosity and anticipation | "Something big is coming..." teasers |

**Copy patterns:**
- "This will change how you think about..."
- "I can't believe [surprising fact]..."
- "Watch what happens when..."
- "This is why we fight for..."
- "You won't believe what [person] did..."
- "[Powerful statistic] — here's what we're doing about it"

**Ethical boundary:** Anger and outrage are high-arousal and highly shareable, but engineering outrage for clicks corrodes trust. Use high-arousal negative emotion sparingly and only when the underlying cause genuinely warrants it.

See: [references/emotion.md](references/emotion.md) for emotional arousal mapping and content audit tools.

### 4. Public

**Core concept:** Built to show, built to grow. If people can see others using your product, they're more likely to adopt it themselves. Make the private public — design for observability.

**Why it works:** People imitate what they can see. If your product usage is invisible, you lose the most powerful adoption channel: social proof through observation. The phrase "monkey see, monkey do" exists because observational learning is one of the deepest human instincts.

**Key insights:**
- **Behavioral residue** — design products that leave visible traces after use. A bumper sticker outlasts the rally. A Livestrong wristband is worn long after the donation
- **Self-advertising products** — every Hotmail email included "Get your free email at Hotmail" in the signature. The product advertised itself through use
- **Observable consumption** — Apple deliberately designed the MacBook logo to face outward (toward observers) rather than toward the user. Every open laptop became a billboard
- **Private behaviors stay private** — if no one can see you using the product, you can't benefit from social proof. Find ways to make invisible usage visible
- **Public = imitable** — people can only copy what they can observe. Making your product publicly visible makes it easier for others to adopt

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Email/Messaging | Branded signatures or footers | "Sent from my iPhone" |
| Physical products | Visible branding during use | Apple logo on laptops, Beats headphones |
| Digital products | Shareable output with branding | Canva designs with watermark, Spotify "Now Playing" |
| Communities | Wearable or displayable membership signals | Livestrong wristbands, conference badges |
| SaaS tools | Public-facing outputs that credit the tool | "Powered by [tool]" on websites |
| Content platforms | Share cards with platform branding | Twitter/X quote cards, Instagram story frames |

**Copy patterns:**
- "Show the world you [achievement/identity]..."
- "Let others know you..."
- "Wear your [accomplishment]..."
- "Share your [output] — powered by [brand]..."
- "Join [number] others who..."

**Ethical boundary:** Public visibility should empower users, not shame them. Never make private information (failures, health data, financial struggles) involuntarily public. The user should always control what is visible.

See: [references/public-visibility.md](references/public-visibility.md) for observability design and behavioral residue strategies.

### 5. Practical Value

**Core concept:** People share useful information to help others. News you can use spreads — especially when it's packaged in a way that's easy to pass along and clearly valuable.

**Why it works:** Sharing practical value is driven by altruism — people genuinely want to help their friends and family. If your content or product saves people time, money, or effort, they'll share it as a favor to their network.

**Key insights:**
- **Prospect Theory** — people evaluate deals relative to a reference point, not in absolute terms. A $10 discount on a $20 item feels better than a $10 discount on a $1,000 item, even though the savings are identical
- **Rule of 100** — for products under $100, use percentage discounts (50% off a $30 item sounds better than $15 off). For products over $100, use dollar amounts ($200 off sounds better than 10% off a $2,000 item)
- **Diminishing sensitivity** — the difference between $5 and $10 feels bigger than the difference between $495 and $500. Frame savings relative to small reference points
- **Knowledge packaging** — useful information needs to be packaged for easy sharing. Lists, how-tos, infographics, and tip collections are inherently more shareable than long-form essays
- **Narrow audience = wider sharing** — counterintuitively, content targeting a specific niche gets shared more because people forward it to "the person who needs this"

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Pricing/Promotions | Frame deals using Rule of 100 | "Save 40%" (under $100) vs. "Save $500" (over $100) |
| Content marketing | Package expertise as numbered lists | "7 ways to reduce your electricity bill" |
| Product features | Build in shareable utility outputs | Calorie tracker generating weekly health summaries |
| Email campaigns | Include "forward-worthy" tips | Useful tips the recipient would forward to a friend |
| B2B content | Create industry benchmarks and tools | Free ROI calculator with shareable results |
| Customer success | Package how-to guides for common tasks | Quick-start guides users share with teammates |

**Copy patterns:**
- "Save [amount] with this one trick..."
- "The [number]-step guide to..."
- "Here's something you'll want to send to [specific person]..."
- "[Number] things I wish I knew about..."
- "Quick tip: [immediately useful advice]..."
- "Share this with someone who needs to hear it"

**Ethical boundary:** Practical value must be genuine. Fake savings (inflated "original" prices), misleading tips, or clickbait "life hacks" that don't actually work will destroy trust faster than they generate shares.

See: [references/practical-value.md](references/practical-value.md) for Prospect Theory applications and knowledge packaging formats.

### 6. Stories

**Core concept:** People don't just share information — they tell stories. The best way to spread your idea is to embed it inside a narrative so engaging that people retell it, and your brand comes along for the ride. This is the Trojan Horse approach.

**Why it works:** Stories are how humans naturally process and transmit information. We think in narratives, not bullet points. A well-crafted story carries your brand message inside it like a Trojan Horse — the listener absorbs the message while being entertained by the story.

**Key insights:**
- **The Trojan Horse test** — can someone retell the story without mentioning your brand? If yes, the story fails. Your brand must be so integral to the narrative that removing it makes the story collapse
- **Stories carry morals** — people extract lessons from narratives. The lesson should naturally lead to your value proposition
- **Narrative transportation** — when people are absorbed in a story, their critical defenses drop. They accept the embedded message more readily than a direct pitch
- **Retellability** — the story must be simple enough to retell in a conversation. If it requires a 10-minute setup, it won't spread
- **Valuable virality** — the story must not just be shareable but must carry the brand message. A hilarious ad that people can't remember the brand of is a failure

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Brand marketing | Create a narrative inseparable from the product | Blendtec "Will It Blend?" (can't retell without mentioning Blendtec) |
| Product launch | Build origin story around a customer problem | "We built this because our founder couldn't find..." |
| Content marketing | Wrap data and insights inside human stories | Customer success stories as narratives, not testimonials |
| PR/Earned media | Create stunts that are inherently story-worthy | Barclay Prime's $100 cheesesteak |
| User onboarding | Frame the user as the hero of a journey | "Your story starts here..." |
| Customer advocacy | Give customers a story to tell about their experience | "You won't believe what happened when I called support..." |

**Copy patterns:**
- "Here's the story of how..."
- "It all started when [founder/customer] realized..."
- "Nobody believed [audacious claim] — until..."
- "What would you do if [relatable dilemma]?"
- "The [person/company] who [did something remarkable]..."

**Ethical boundary:** Stories must be true or clearly fictional. Fabricating testimonials, inventing origin stories, or creating misleading narratives will eventually be exposed, destroying the brand's credibility and making future word-of-mouth toxic.

See: [references/stories-trojan-horse.md](references/stories-trojan-horse.md) for narrative templates and the Trojan Horse integration test.

## Engineering Word of Mouth

The STEPPS principles are most powerful when combined. Here are applied combinations for common scenarios:

### Product Launch

| Phase | STEPPS Combination | Tactics |
|-------|-------------------|---------|
| Pre-launch | Social Currency + Public | Invite-only beta with visible waitlist counters |
| Launch day | Emotion + Stories | Founder narrative + awe-inducing demo |
| First week | Triggers + Practical Value | Tie product to daily workflow + "share to unlock" features |
| Sustained growth | Public + Social Currency | Visible usage signals + achievement sharing |

### Content Strategy

| Content Type | Primary STEPPS | Secondary STEPPS | Example |
|-------------|---------------|-----------------|---------|
| Thought leadership | Social Currency | Stories | Insider knowledge wrapped in narrative |
| How-to guides | Practical Value | Triggers | Useful tips tied to recurring situations |
| Brand films | Emotion | Stories | Awe-inspiring narrative with brand at center |
| Interactive tools | Practical Value | Public | Calculator/quiz with shareable results |
| User spotlights | Stories | Social Currency | Customer heroes whose stories feature your product |

### Feature Design

| Feature Goal | STEPPS to Apply | Implementation |
|-------------|----------------|----------------|
| Drive referrals | Social Currency + Public | Shareable achievement cards with branding |
| Increase retention | Triggers + Practical Value | Daily-routine integrations with useful outputs |
| Build community | Public + Social Currency | Visible membership tiers and contribution badges |
| Launch virally | Emotion + Stories | Remarkable origin story + emotionally charged demo |

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Focusing only on online sharing | 93% of WOM is offline — you're ignoring the dominant channel | Design for conversation triggers, not just social media shares |
| Making content shareable but not brand-linked | People share the joke but forget who made it | Apply the Trojan Horse test — brand must be integral to the story |
| Using low-arousal emotions | Sadness and contentment don't activate sharing behavior | Reframe content for high-arousal emotions: awe, excitement, amusement, anger |
| Making product usage invisible | No one can imitate what they can't see | Add behavioral residue and observable usage signals |
| Relying on product quality alone | Great products with no STEPPS integration spread slowly | Deliberately engineer at least 2-3 STEPPS into the product experience |
| Creating rare, powerful triggers | A strong but infrequent trigger generates less WOM than a weak but daily one | Prioritize frequency over strength when selecting environmental triggers |

## Quick Diagnostic

Run this diagnostic on any product, campaign, or content piece:

| Question | If No... | Action |
|----------|----------|--------|
| Does sharing this make people look good? | No social currency | Add remarkability, exclusivity, or achievement mechanics |
| Is there an everyday cue that triggers thoughts of it? | No trigger | Link product to a frequent environmental cue or daily routine |
| Does it evoke high-arousal emotion? | Low emotional activation | Reframe for awe, excitement, humor, or righteous anger |
| Can others see people using or engaging with it? | Invisible usage | Add observable signals, branded outputs, or public indicators |
| Is the information useful enough to forward? | Low practical value | Package insights as tips, lists, or tools people would send to a friend |
| Is the brand embedded in a retellable story? | No narrative vehicle | Create a Trojan Horse story that requires your brand to retell |

## Reference Files

- [references/social-currency.md](references/social-currency.md) — Remarkability techniques, game mechanics, exclusivity design, and identity signaling strategies
- [references/triggers.md](references/triggers.md) — Habitat analysis, trigger frequency matrix, competitive triggers, and the Kit Kat case study
- [references/emotion.md](references/emotion.md) — High-arousal vs. low-arousal emotion mapping, awe engineering, humor design, and emotional audit tools
- [references/public-visibility.md](references/public-visibility.md) — Behavioral residue, observable consumption design, self-advertising products, and the Apple logo story
- [references/practical-value.md](references/practical-value.md) — Prospect Theory for marketers, Rule of 100, knowledge packaging formats, and deal framing
- [references/stories-trojan-horse.md](references/stories-trojan-horse.md) — Trojan Horse narrative design, brand integration testing, and story templates
- [references/word-of-mouth.md](references/word-of-mouth.md) — Offline vs. online WOM, conversation triggers, measurement approaches, and WOM audit
- [references/viral-content-patterns.md](references/viral-content-patterns.md) — Content formats that spread, platform-specific patterns, viral coefficient, and shareability audit
- [references/case-studies.md](references/case-studies.md) — Detailed breakdowns of Blendtec, Barclay Prime, Kit Kat, Livestrong, Dove, and Hotmail

## Further Reading

- [Contagious: Why Things Catch On](https://www.amazon.com/Contagious-Things-Catch-Jonah-Berger/dp/1451686579?tag=wondelai00-20) by Jonah Berger
- [The Catalyst: How to Change Anyone's Mind](https://www.amazon.com/Catalyst-How-Change-Anyones-Mind/dp/1982108606?tag=wondelai00-20) by Jonah Berger

## About the Author

**Jonah Berger** is a marketing professor at the Wharton School at the University of Pennsylvania. His research focuses on social influence, word-of-mouth, and why products, ideas, and behaviors catch on. He has published dozens of articles in top-tier academic journals and his work has been featured in the New York Times, Wall Street Journal, and Harvard Business Review. "Contagious" distills his years of research into a practical framework for understanding and engineering virality. He has also authored "Invisible Influence" (on how hidden forces shape behavior) and "The Catalyst" (on how to change minds), and consults with companies ranging from startups to Fortune 500 firms on how to make their products and ideas spread.

## Overview

Engineer word-of-mouth and virality using the STEPPS framework (Social Currency, Triggers, Emotion, Public, Practical Value, Stories).

## Prerequisites

- Access to the Go environment or API
- Required CLI tools installed and authenticated
- Familiarity with Go concepts and terminology

## Instructions

1. Assess the current state of the Go configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [Go implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Go |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply contagious to a standard project setup with default configuration options.

**Advanced scenario**: Customize contagious for production environments with multiple constraints and team-specific requirements.

## Resources

- Official Go documentation
- Community best practices and patterns
- Related skills in this plugin pack
