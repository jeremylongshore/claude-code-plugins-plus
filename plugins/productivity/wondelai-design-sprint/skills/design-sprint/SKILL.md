---
name: design-sprint
description: |
  Run a structured 5-day process to prototype, test, and validate product ideas with real users. Use when the user mentions "design sprint", "validate in a week", "rapid prototype", "test with users", or "de-risk before building". Covers mapping, sketching, deciding, prototyping, and testing. For ongoing experimentation, see lean-startup. For customer job analysis, see jobs-to-be-done. Trigger with 'design', 'sprint'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [productivity, testing, design-sprint]
---
# Design Sprint Framework

A five-day process for answering critical business questions through design, prototyping, and testing ideas with customers. Developed at Google Ventures and used by Google, Slack, Airbnb, and hundreds of startups.

## Core Principle

**Great solutions require both deep work and fast iteration.** The Design Sprint compresses months of debate, design, and testing into a single week, creating focus and urgency that eliminates endless discussion.

**The foundation:** Traditional product development wastes months building the wrong thing. Design Sprints de-risk product decisions by testing with real users before writing production code.

## Scoring

**Goal: 10/10.** When planning or executing a Design Sprint, rate it 0-10 based on adherence to the principles below. A 10/10 means proper structure, time-boxing, prototyping, and user testing; lower scores indicate skipping steps or insufficient testing. Always provide the current score and specific improvements needed to reach 10/10.

## The 5-Day Sprint Process

```
Monday → Tuesday → Wednesday → Thursday → Friday
  Map      Sketch     Decide      Prototype    Test
```

**Prerequisites:**
- **Big challenge:** Important problem worth a week's focus
- **Right team:** Decision maker + 4-7 people with diverse expertise
- **Time commitment:** 5 full days (10am-5pm), no interruptions
- **Space:** Dedicated room with whiteboards

**Sprint Master:** One person facilitates, keeps time, manages energy.

## Monday: Map

**Goal:** Understand the problem and choose a target for the week.

### Morning: Start at the End

**Exercise: Long-term goal**
- Write the sprint question: "What do we want to be true in 2 years?"
- Example: "Customers use our product daily" or "We've captured 20% market share"

**Exercise: Sprint questions**
- List obstacles and unknowns as questions
- Example: "Will customers trust us with payment info?" or "Can first-time users figure out the interface?"

**Format:** Write on whiteboard, entire team contributes

### Afternoon: Map the Challenge

**Exercise: Map the customer journey**
1. List actors (different types of customers/users)
2. Draw the journey from start to finish (left to right on whiteboard)
3. Keep it simple: 5-15 steps max
4. Example: "Hears about product → Visits site → Signs up → First use → Becomes regular user"

**Exercise: Ask the Experts**
- Interview team members with specialized knowledge
- CEO, designer, engineer, customer support, sales
- Take detailed notes on whiteboard
- Capture "How Might We" notes (HMW)

**Exercise: How Might We (HMW) notes**
- Rephrase problems as opportunities
- "Customers don't understand pricing" → HMW make pricing immediately clear?
- Write each HMW on a sticky note
- Vote on best HMWs, organize on map

### End of Day: Pick a Target

**Exercise: Choose the target**
- Which part of the map (customer journey) will you focus on?
- Where's the biggest risk or opportunity?
- Example: "We'll focus on the first 10 minutes after signup"

**Decider:** The person with authority makes the final call.

**Monday output:**
- Long-term goal
- Sprint questions
- Customer journey map
- Expert insights
- HMW notes organized
- Target customer and moment

See: [references/monday.md](references/monday.md) for detailed Monday exercises and facilitation.

## Tuesday: Sketch

**Goal:** Generate solutions. Each person sketches a detailed solution.

### Morning: Lightning Demos

**Exercise: Find inspiration**
- Look at competitors and analogous products
- 3-minute demos: "Here's what I found, here's why it's interesting"
- Capture good ideas on whiteboard
- Don't limit to your industry—borrow from anywhere

**Exercise: Divide or swarm**
- Divide: If map has multiple parts, different people tackle different sections
- Swarm: If one critical problem, everyone tackles the same thing
- Most sprints = swarm

### Afternoon: The Four-Step Sketch

**Goal:** Everyone individually sketches a detailed solution (not as a group!)

**Step 1: Notes (20 minutes)**
- Walk around room, review map, HMWs, inspiration
- Take notes silently

**Step 2: Ideas (20 minutes)**
- Rough doodles, mind maps, stick figures
- Quantity over quality
- Still working alone

**Step 3: Crazy 8s (8 minutes)**
- Fold paper into 8 sections
- Sketch 8 variations in 8 minutes (1 minute each)
- Forces you past first idea
- Can be 8 variations on one idea or 8 different ideas

**Step 4: Solution Sketch (30-90 minutes)**
- 3-panel storyboard showing customer experience
- Step 1 → Step 2 → Step 3 (beginning, middle, end)
- Make it self-explanatory (someone should understand without you explaining)
- Use text, arrows, simple drawings
- Give it a catchy title
- **Anonymous:** Don't put your name on it

**Critical:** No group brainstorming. Individual work produces better, more diverse ideas.

**Tuesday output:**
- Each person has a detailed solution sketch
- Sketches are anonymous and self-explanatory

See: [references/tuesday.md](references/tuesday.md) for sketching templates and examples.

## Wednesday: Decide

**Goal:** Critique solutions and choose the best one to prototype and test.

### Morning: Sticky Decision

**Exercise: Art museum**
- Tape solution sketches to wall
- Give everyone dot stickers
- Silently review sketches (no talking!)
- Put dots next to interesting parts

**Exercise: Heat map review**
- Discuss each sketch for 3 minutes
- Facilitator narrates: "Here they see X, then click Y..."
- Sketcher stays silent (don't reveal yourself yet)
- Team calls out interesting parts
- Scribe captures standout ideas on whiteboard

**Exercise: Straw poll**
- Each person votes for one solution (put one large dot)
- Explain your vote in 1 sentence
- This is non-binding, just to see preferences

**Decider:** Person with authority gets three large dots (supervote). Their decision wins.

### Afternoon: Rumble or All-in-One

**If multiple winners:**
- **Rumble:** Competing prototypes (test different approaches)
- **All-in-One:** Combine best ideas into one prototype

**Most sprints:** All-in-one (simpler to prototype and test)

**Exercise: Storyboard**
- Draw 10-15 panel storyboard (comic book style)
- Each panel = one screen or step
- Opening scene: How customer discovers you
- Middle: Your solution in action
- Ending: Successful outcome
- Include just enough detail for Friday's prototype

**Storyboard rules:**
- Keep it simple
- Use stick figures
- Words and arrows okay
- Get specific about UI
- 10-15 panels max

**Wednesday output:**
- Winning solution(s) chosen
- Detailed storyboard ready to prototype

See: [references/wednesday.md](references/wednesday.md) for decision exercises and storyboard templates.

## Thursday: Prototype

**Goal:** Build a realistic facade. You need something to test on Friday.

**Prototype mindset:**
- Fake it
- Prototype only what you'll test
- Goldilocks quality: not too high, not too low (realistic enough to get honest reactions)
- One day only

**Prototype fidelity:**
- **Too low:** Sketches, wireframes (customers can't react realistically)
- **Too high:** Working code, pixel-perfect design (wastes time)
- **Just right:** Looks real, doesn't work real (facades, click-through, video)

### Assign Roles

**Makers** (2+ people):
- Designer, writer, asset collector (images, icons)
- Build the prototype

**Stitcher** (1 person):
- Combines pieces into final prototype
- Usually in Keynote, Figma, or prototyping tool

**Writer** (1 person):
- Writes all copy
- Headlines, button labels, descriptions

**Collector** (1-2 people):
- Gathers assets (photos, icons, competitor screenshots)
- Provides raw materials

**Interviewer** (1 person):
- Writes interview script for Friday
- Practices interviewing

**Sprint Master:**
- Helps where needed
- Keeps energy up

### Build the Prototype

**Tools:**
- **Web/App:** Figma, Keynote, PowerPoint (linked slides)
- **Physical Product:** Video walkthrough, 3D-printed mockup
- **Service:** Role-play video, scripted interaction

**Thursday morning:**
- Divide storyboard into scenes
- Assign scenes to makers
- Start building

**Thursday afternoon:**
- Stitch together
- Review as team (does it match storyboard?)
- Rehearse for Friday (run through entire flow)
- Trial run (test with someone not on sprint team)

**Prototype checklist:**
- [ ] Follows storyboard exactly
- [ ] Looks real enough to get honest reactions
- [ ] Can walk through in 5-15 minutes
- [ ] Interviewer knows how to present it
- [ ] Trial run completed

**Thursday output:**
- Realistic prototype ready to test
- Interview script written
- Interview room prepared

See: [references/thursday.md](references/thursday.md) for prototyping tools and techniques.

## Friday: Test

**Goal:** Interview 5 customers, learn what works and what doesn't.

### Setup

**Interview room:**
- Quiet space with table, 2 chairs
- Laptop with prototype
- Camera recording screen and customer face

**Observation room:**
- Separate room with live video feed
- Team watches together
- Whiteboard for notes

**Roles:**
- **Interviewer:** Conducts all 5 interviews
- **Team:** Watches, takes notes

### The Five-Act Interview

**Act 1: Friendly Welcome (5 min)**
- Greet warmly
- Explain you're testing prototype, not them
- Ask permission to record
- Encourage thinking aloud

**Act 2: Context Questions (5 min)**
- Ask about their background
- Example: "Tell me about how you currently handle [problem]"
- Goal: Understand their mindset and current behavior

**Act 3: Introduce the Prototype (5 min)**
- Show landing page or entry point
- "What's this? What do you think it's for?"
- Don't explain—let them interpret
- Note: Do they get it?

**Act 4: Tasks and Nudges (15 min)**
- Give open-ended task: "Go ahead and explore"
- Follow with specific tasks from storyboard: "Try to [complete action]"
- Use nudges when stuck: "What would you do next?" or "What's going through your mind?"
- Don't help—watch them struggle
- Encourage thinking aloud

**Act 5: Debrief (5 min)**
- "What did you think overall?"
- "Who is this for?"
- "What worked? What was confusing?"
- Ask about specific parts you're uncertain about

**Interview length:** ~30 minutes per customer

**Between interviews:**
- 30-minute break
- Team discusses observations
- Update questions if needed

### Five Is the Magic Number

**Why 5 customers?**
- Patterns emerge after 3-5 people
- Diminishing returns after 5
- Doable in one day (5 × 1 hour = 5 hours with breaks)

**Who to recruit:**
- Target customers (match your personas)
- Screener survey to qualify
- Incentive ($100-$200 for B2B, $50-$100 for B2C)
- Schedule 6 (expect 1 no-show)

### Take Notes: Pattern Recognition

**While watching interviews, team captures:**

| Column 1 | Column 2 | Column 3 | Column 4 | Column 5 |
|----------|----------|----------|----------|----------|
| Customer 1 notes | Customer 2 notes | Customer 3 notes | Customer 4 notes | Customer 5 notes |

**Mark with ✓, ✗, or ~:**
- ✓ Positive reaction, success
- ✗ Negative reaction, failure
- ~ Neutral or mixed

**After all 5 interviews:**
- Look for patterns (did all 5 struggle with the same thing?)
- Count ✓ ✗ ~ per row
- Identify what worked and what failed

### End-of-Sprint Debrief

**Organize findings:**

**✓ What worked:**
- Features/flows that all customers understood
- Messaging that resonated
- Design that felt intuitive

**✗ What failed:**
- Confusing terminology
- Missing steps
- Wrong assumptions

**~ Mixed results:**
- Some got it, some didn't
- Unclear if it matters

**Next steps:**
- **If core concept validated:** Build it (or next sprint on details)
- **If major issues:** Pivot or next sprint to solve problems
- **If totally failed:** Back to drawing board (but you saved months!)

**Friday output:**
- Interview videos
- Pattern notes
- Clear list of what works, what doesn't
- Decision on next steps

See: [references/friday.md](references/friday.md) for interview scripts and note-taking templates.

## When to Run a Design Sprint

**Run a sprint when:**
- High-stakes decision
- Not enough time to build and test normally
- Team is stuck in endless debate
- Multiple solutions possible
- New product, feature, or major redesign
- Need to de-risk before investing

**Don't run a sprint when:**
- Problem is clear and solution is obvious
- You just need to execute
- Team isn't bought in
- Can't get decision maker for full week

## Variations

**4-Day Sprint:**
- Day 1: Map + Sketch (compressed)
- Day 2: Decide
- Day 3: Prototype
- Day 4: Test

**Remote Sprint:**
- Use Miro/FigJam for whiteboarding
- Zoom for meetings
- Same schedule, digital tools

**Multi-Sprint:**
- Sprint 1: Broad problem, choose direction
- Sprint 2: Deep dive on chosen solution
- Sprint 3: Refine details

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Skip prototyping** | Nothing to test | Always prototype, even if simple |
| **Over-engineer prototype** | Waste time on details that don't matter | Facade only, not working code |
| **Test with wrong users** | Invalid feedback | Screen for target customers |
| **Explain prototype to users** | Defeats the test | Let them struggle, observe confusion |
| **No decision maker** | Can't commit to decision | Get Decider for full week or don't sprint |
| **Interruptions** | Breaks focus | Protect the week, no meetings/emails |

## Quick Diagnostic

Audit any sprint plan:

| Question | If No | Action |
|----------|-------|--------|
| Do we have a Decider for full week? | Sprint will fail | Get commitment or postpone |
| Is the problem important enough? | Waste of time | Only sprint on big challenges |
| Can we prototype in 1 day? | Wrong problem for sprint | Choose more concrete problem |
| Can we recruit 5 target users? | Can't test properly | Start recruiting now (2 weeks ahead) |
| Will team commit to no interruptions? | Won't maintain focus | Get buy-in from leadership |

## Overview

A five-day process for answering critical business questions through design, prototyping, and testing with real customers, developed at Google Ventures.

## Prerequisites

- A clearly defined challenge worth a week of focused effort
- A decision maker plus 4-7 team members committed for the full 5 days
- Dedicated room with whiteboards and a way to recruit 5 target customers for Friday testing

## Instructions

1. Follow the 5-day structure: Map (Monday), Sketch (Tuesday), Decide (Wednesday), Prototype (Thursday), Test (Friday)
2. Use the Quick Diagnostic table to verify readiness before starting
3. Refer to the day-specific reference files for detailed exercises and facilitation guides

## Output

- **Monday**: Long-term goal, sprint questions, customer journey map, target selection
- **Wednesday**: Winning solution chosen, detailed storyboard ready to prototype
- **Friday**: Interview recordings, pattern notes, validated/invalidated hypotheses, next steps decision

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No decision maker available | Key stakeholder absent | Postpone sprint until Decider can commit the full week |
| Cannot recruit 5 users | Insufficient lead time or wrong audience | Start recruiting 2 weeks ahead; broaden screener criteria |
| Prototype too complex for one day | Storyboard scope too large | Cut to the single riskiest assumption and prototype only that flow |

## Examples

- **New product validation**: A SaaS startup runs a sprint to test onboarding flow with 5 target users before writing production code.
- **Feature prioritization**: A product team with 3 competing feature proposals uses Wednesday's decision process to choose one, prototypes Thursday, and tests Friday.

## Resources

- [references/monday.md](references/monday.md) through [references/friday.md](references/friday.md) — daily exercises and facilitation
- [references/case-studies.md](references/case-studies.md) — Slack, Blue Bottle Coffee, Savioke, and more
- [references/remote-sprints.md](references/remote-sprints.md) — adapting sprints for distributed teams
- [*"Sprint"*](https://www.amazon.com/Sprint-Solve-Problems-Test-Ideas/dp/150112174X?tag=wondelai00-20) by Jake Knapp — the complete methodology

