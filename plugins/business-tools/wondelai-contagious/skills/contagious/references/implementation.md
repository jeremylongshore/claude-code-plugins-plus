# Contagious - Implementation Guide

Step-by-step methodology for engineering word-of-mouth and virality using the STEPPS framework from Jonah Berger's research.

## Step 1: Audit Current Virality

Before applying STEPPS, score each principle for your current product or content (0-10 per principle):

| Principle | Question | Score (0-10) |
|-----------|----------|--------------|
| Social Currency | Does sharing make the sharer look good? | ? |
| Triggers | Is there an environmental cue linked to the product? | ? |
| Emotion | Does it evoke high-arousal feelings (awe, anger, excitement)? | ? |
| Public | Is usage or consumption visible to others? | ? |
| Practical Value | Is the information useful enough to pass along? | ? |
| Stories | Is the brand embedded in a story people want to retell? | ? |

A total below 30 = significant untapped viral potential. Prioritize the lowest-scoring principles first.

## Step 2: Apply Social Currency

Goal: Make sharing the product a form of self-expression or status signaling.

**2a. Find the remarkable angle**
- Ask: "What is genuinely surprising, counterintuitive, or extreme about this?"
- Example: Blendtec "Will It Blend?" — industrial blender blending iPhones. Not remarkable product → remarkable demonstration.
- Reframe mundane facts: "Our app processes 10,000 data points per second" → "We process more data in a day than all the emails you'll send in your lifetime."

**2b. Add game mechanics**
- Map user progression to visible milestones (streaks, levels, cumulative stats)
- Make milestones share-worthy: design a "1,000th task" moment the same way you'd design a confetti moment
- Concrete implementation: add `onMilestoneReached(userId, milestone)` → generate shareable card with user's stat + product branding

**2c. Create exclusivity**
- Invite-only launches, beta programs, or early access tiers give joiners something to tell: "I'm on the waitlist"
- Secret features, easter eggs, or undocumented commands create insider knowledge worth sharing
- Example copy: "You're one of 500 people with access to [feature]. Here's what it does..."

## Step 3: Engineer Triggers

Goal: Link the product to a frequent environmental cue so people are reminded of it throughout their day.

**3a. Identify high-frequency contexts**
- When do your users already think or talk about the problem your product solves?
- Example: Kit Kat linked "have a break" to coffee breaks — the trigger fires multiple times per day
- Map the user's day: morning commute, post-standup, after a stressful meeting

**3b. Own a word or phrase**
- Pick one evocative trigger word that is already high-frequency in your target environment
- SaaS example: "ship" (developers ship code daily → tool that helps them ship faster gets triggered every deploy)

**3c. Use top-of-mind timing**
- Schedule marketing touchpoints at peak trigger moments: Monday morning for productivity tools, Friday afternoon for social tools
- For products solving recurring problems (e.g., meeting scheduling), send a touchpoint right after the trigger event (post-meeting follow-up)

## Step 4: Activate High-Arousal Emotion

Goal: Evoke feelings that increase physiological arousal — awe, excitement, anxiety, amusement, or anger. Avoid low-arousal states (sadness, contentment).

**4a. Identify the emotional core**
- Map your content on the arousal/valence grid:
  - High arousal + positive: awe, excitement, humor → share-worthy
  - High arousal + negative: anger, anxiety → share-worthy (use carefully)
  - Low arousal: sadness, contentment → suppresses sharing

**4b. Design for awe**
- Awe = vastness + accommodation (mind has to expand to comprehend)
- Show the scale of what the product does: "You saved 37 hours this month — that's a full work week"
- Visualize aggregate impact: "Together, our users have saved 2.3 million hours"

**4c. Use humor strategically**
- Unexpected juxtapositions, absurdist premises, or relatable frustrations are shareable
- Example: Mailchimp's playful pre-send microcopy reduces anxiety with humor → users screenshot and share

## Step 5: Make It Public (Observable)

Goal: Design visible behavioral residue that shows others the product is being used.

**5a. Build public artifacts**
- Every use of the product should leave a trace others can see
- Examples: Hotmail "Sent from Hotmail" footer, Livestrong bracelets, LinkedIn profile views
- Implementation: add optional "Made with [product]" watermark to exports, reports, or shared assets

**5b. Social proof at point of decision**
- Show real-time or aggregate usage when someone is deciding whether to try the product
- "127 teams signed up this week" on the pricing page
- "Your colleague Sarah also uses this" (with permission)

**5c. Design behavioral imitation triggers**
- Make the desired behavior visible so others copy it
- Example: Apple's white earbuds made iPod ownership visible in a crowd
- SaaS equivalent: public activity feeds, contributor graphs (GitHub), or shared dashboards

## Step 6: Amplify Practical Value

Goal: Give people genuinely useful information or features they'll share because sharing helps others.

**6a. Identify the shareable insight**
- What does your product know that would be valuable to someone else?
- Data products: share industry benchmarks, personalized insights, or aggregated statistics
- Educational products: create condensed summaries, checklists, or decision frameworks

**6b. Package for effortless sharing**
- Reduce friction to zero: one-click share, pre-written caption, or automatically generated summary
- Format for the medium: tweet-sized insight for social, PDF for email, embeddable widget for blogs
- Example: Spotify Wrapped generates a shareable story with no editing required

**6c. News hijacking and timeliness**
- Tie practical value to current events or trending topics to amplify sharing
- Template: "[Current event] + [Your product's relevant insight]" → newsworthy and shareable

## Step 7: Embed in a Story

Goal: Make the brand or product an inseparable part of a narrative people want to retell.

**7a. Identify the host story**
- What stories do your users already tell? (Success stories, transformation narratives, "this changed how I work" moments)
- Your product should be the sword in the hero's journey, not the hero itself

**7b. Design the Trojan Horse narrative**
- Create a story so compelling it travels on its own — and your product is required to understand it
- Frame case studies as transformation narratives: "[Customer] was drowning in [problem]. Then they discovered [product]. Today, [remarkable outcome]."

**7c. Give users a story to tell**
- Design "tell your friends" moments: unexpected delight, surprising results, or meaningful milestones
- Example: Zappos overnight delivery — the story retells itself because of the emotional impact

## Step 8: Prioritize and Roadmap

After scoring all six principles:

1. Fix the biggest gap first (score < 4 = critical)
2. Double down on your highest score (score 8+ = amplify what's working)
3. Build a "virality experiment" into each sprint: one STEPPS test per quarter

**Tracking word-of-mouth:**
- Measure referral source in onboarding: "How did you hear about us?"
- Track share events, embed mentions, branded hashtag volume
- Use NPS as proxy: promoters are your STEPPS activators

## Common Pitfalls

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Building viral loops without emotional resonance | Mechanics without feeling → ignored | Attach game mechanic to genuine user achievement |
| Relying solely on social media | 93% of WOM is offline | Design offline conversation triggers |
| Making the brand the hero | Self-promotion → ignored | Make the user's transformation the story |
| Adding sharing buttons | Friction is not the bottleneck — motivation is | Fix motivation first, then reduce friction |
| Copying competitors' viral features | Context-dependent → same feature may not transfer | Apply STEPPS from scratch in your context |

## Quick-Start Checklist

- [ ] STEPPS audit complete with scores per principle
- [ ] Lowest-scoring principle has at least one concrete experiment planned
- [ ] Shareable artifact designed (Wrapped-style report, achievement card, or embed)
- [ ] Trigger word or context identified and mapped to product touchpoints
- [ ] One "remarkable angle" articulated in 10 words or fewer
- [ ] Share friction measured: how many taps/clicks from insight to post?
