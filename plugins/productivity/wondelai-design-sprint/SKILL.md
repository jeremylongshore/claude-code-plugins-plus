---
name: design-sprint
description: 'Run a structured 5-day process to prototype, test, and validate product ideas with real users. Use when the user mentions "design sprint", "validate before we build", "rapid prototype", "test with users", or "should we build this". Also trigger when a team is stuck in endless debate over a high-stakes product decision, or wants to de-risk a costly idea before investing in development. Covers mapping, sketching, deciding, prototyping, and testing across Monday-Friday. For ongoing experimentation and MVPs, see lean-startup. For customer job analysis, see jobs-to-be-done. For non-leading user interviews, see mom-test.'
license: MIT
metadata:
  author: wondelai
  version: "1.4.0"
---

# Design Sprint Framework

A five-day process for answering critical business questions through design, prototyping, and testing ideas with customers. Developed at Google Ventures and used by Google, Slack, Airbnb, and hundreds of startups.

## Core Principle

**Compress months of debate, design, and testing into one week — and test with real users before writing any production code.** The sprint replaces endless discussion with a fixed Monday-to-Friday spine, hard time-boxes, and a single Decider, so a high-stakes product question gets a real answer in five days instead of five months.

## Scoring

**Goal: 10/10.** Score a sprint plan or execution by awarding 1 point for each item present and correct (10 total). Report the score and the missing items needed to reach 10/10.

1. Decider committed for the full week; one Sprint Master facilitating.
2. Monday produces a target customer and moment (not a vague "test the product").
3. Hard time-boxes used (Crazy 8s in 8 min, 10am-5pm days, no open-ended sessions).
4. Solution sketches done alone and anonymous — no group brainstorming.
5. Wednesday ends with a single Decider Supervote, not consensus.
6. Storyboard specified before any prototype is built.
7. Prototype is a Goldilocks-fidelity facade, testable in 5-15 min, with a trial run done.
8. Exactly 5 target users recruited via screener (6 scheduled to absorb a no-show).
9. Friday uses the Five-Act Interview; users interpret the prototype unexplained.
10. End-of-sprint debrief converts the +/-/~ pattern grid into a decision on next steps.

A plan missing the Decider, real users, or a same-day prototype caps at 6 — those are the failure modes the sprint exists to prevent.

## The 5-Day Sprint Process

```
Monday → Tuesday → Wednesday → Thursday → Friday
  Map      Sketch     Decide      Prototype    Test
```

**Prerequisites:** a big challenge worth a week's focus; the right team (Decider plus 4-7 people with diverse expertise); five full days (10am-5pm) with no interruptions; a dedicated room with whiteboards. One **Sprint Master** facilitates, keeps time, and manages energy.

See [references/facilitation.md](references/facilitation.md) when you are the Sprint Master — it has the full facilitation guide, time-boxing tactics, and energy-management moves for keeping a stuck or low-energy room productive.

## Monday: Map

**Goal:** Understand the problem and choose a target for the week.

### Morning: Start at the End

- **Long-term goal:** Write the optimistic answer to "What do we want to be true in 2 years?" — e.g., "Customers use our product daily."
- **Sprint questions:** List obstacles and unknowns as questions on the whiteboard, whole team contributing — e.g., "Will customers trust us with payment info?"

### Afternoon: Map the Challenge

- **Customer journey map:** List the actors (customer types), then draw the journey left to right in 5-15 steps: "Hears about product → Visits site → Signs up → First use → Regular user."
- **Ask the Experts:** Interview teammates with specialized knowledge (CEO, design, engineering, support, sales); capture notes on the whiteboard.
- **How Might We (HMW):** Rephrase problems as opportunities — "Customers don't understand pricing" → "HMW make pricing immediately clear?" One per sticky note; vote and organize the best on the map.

### End of Day: Pick a Target

Choose which customer and moment on the map to focus on — the biggest risk or opportunity (e.g., "the first 10 minutes after signup"). The **Decider** (person with authority) makes the final call.

**Monday output:** long-term goal, sprint questions, journey map, expert insights, organized HMW notes, target customer and moment.

See [references/monday.md](references/monday.md) while facilitating Monday — step-by-step exercise scripts, HMW examples, and the target-selection method.

## Tuesday: Sketch

**Goal:** Generate solutions — each person sketches a detailed solution.

### Morning: Lightning Demos

- **Find inspiration:** 3-minute demos of competitors and analogous products ("Here's what I found, here's why it's interesting"); capture good ideas on the whiteboard. Borrow from any industry.
- **Divide or swarm:** Split the map between people if it has multiple parts; otherwise everyone tackles the same critical problem (most sprints swarm).

### Afternoon: The Four-Step Sketch

Everyone sketches alone — **no group brainstorming**. Individual work produces better, more diverse ideas.

1. **Notes (20 min):** Silently walk the room reviewing the map, HMWs, and inspiration.
2. **Ideas (20 min):** Rough doodles, mind maps, stick figures — quantity over quality.
3. **Crazy 8s (8 min):** Fold paper into 8 panels and sketch 8 variations in 8 minutes — forces you past your first idea.
4. **Solution Sketch (30-90 min):** A 3-panel storyboard of the customer experience (beginning, middle, end). Make it self-explanatory, give it a catchy title, and keep it **anonymous**.

**Tuesday output:** one detailed, anonymous, self-explanatory solution sketch per person.

See [references/tuesday.md](references/tuesday.md) before the Four-Step Sketch — Crazy 8s and solution-sketch templates plus worked examples to show the team.

## Wednesday: Decide

**Goal:** Critique solutions and choose the best one to prototype and test.

### Morning: Sticky Decision

- **Art museum:** Tape sketches to the wall; review silently (no talking) and mark interesting parts with dot stickers.
- **Heat map review:** Discuss each sketch for 3 minutes — the facilitator narrates while the anonymous sketcher stays silent; a scribe captures standout ideas on the whiteboard.
- **Straw poll:** Each person votes for one solution with one sentence of rationale (non-binding).
- **Supervote:** The Decider gets three large dots; their decision wins.

### Afternoon: Rumble or All-in-One

If multiple sketches win, choose: **Rumble** (competing prototypes testing different approaches) or **All-in-One** (combine the best ideas into one prototype — simpler, and what most sprints do).

- **Storyboard:** Draw a 10-15 panel comic of the test experience: opening scene (how the customer discovers you) → your solution in action → successful outcome. Keep it simple — stick figures, words, arrows — but get specific about the UI. Include just enough detail for Thursday's prototype.

**Wednesday output:** winning solution(s) and a detailed storyboard ready to prototype.

See [references/wednesday.md](references/wednesday.md) when running the Sticky Decision and storyboard — facilitation steps for the vote and a panel-by-panel storyboard template.

## Thursday: Prototype

**Goal:** Build a realistic facade in one day — you need something to test on Friday.

**Mindset:** Fake it; prototype only what you'll test. Aim for Goldilocks fidelity — sketches are too low for honest reactions, working code wastes time. It should look real without working for real (facades, click-throughs, video).

### Assign Roles

| Role | Responsibility |
|------|----------------|
| **Makers** (2+) | Build the prototype pieces (design, assets) |
| **Stitcher** (1) | Combines pieces into the final prototype (Keynote, Figma) |
| **Writer** (1) | All copy: headlines, button labels, descriptions |
| **Collector** (1-2) | Gathers photos, icons, competitor screenshots |
| **Interviewer** (1) | Writes and rehearses Friday's interview script |
| **Sprint Master** | Helps where needed, keeps energy up |

### Build the Prototype

**Tools:** Figma, Keynote, or PowerPoint linked slides for web/apps; video walkthrough or 3D-printed mockup for physical products; role-play video or scripted interaction for services.

Morning: divide the storyboard into scenes and assign them to makers. Afternoon: stitch together, review against the storyboard, rehearse the full flow, and run a trial with someone outside the sprint team.

**Prototype checklist:**
- [ ] Follows storyboard exactly
- [ ] Looks real enough to get honest reactions
- [ ] Can walk through in 5-15 minutes
- [ ] Interviewer knows how to present it
- [ ] Trial run completed

**Thursday output:** realistic prototype, interview script, prepared interview room.

See [references/thursday.md](references/thursday.md) while building the prototype — tool-by-tool techniques (Keynote/Figma facades, video, mockups) for hitting Goldilocks fidelity in a day.

## Friday: Test

**Goal:** Interview 5 customers; learn what works and what doesn't.

### Setup

Interview room: quiet space, laptop with the prototype, camera recording screen and customer's face. Observation room: live video feed where the whole team watches and takes notes on a whiteboard. One **Interviewer** conducts all five interviews.

### The Five-Act Interview

About 45 minutes per customer (the five acts run ~35 min plus setup and transitions), with 30-minute breaks between to discuss observations and adjust questions. See references/friday.md for the full 9am-5pm schedule.

| Act | Time | What to Do |
|-----|------|------------|
| **1. Friendly welcome** | 5 min | Greet warmly; explain you're testing the prototype, not them; get recording permission; encourage thinking aloud |
| **2. Context questions** | 5 min | "Tell me about how you currently handle [problem]" — understand mindset and current behavior |
| **3. Introduce prototype** | 5 min | "What's this? What do you think it's for?" Don't explain — let them interpret |
| **4. Tasks and nudges** | 15 min | Open-ended exploration, then storyboard tasks. When stuck: "What would you do next?", "What's going through your mind?" Don't help — watch them struggle |
| **5. Debrief** | 5 min | "What did you think overall?", "Who is this for?", "What worked? What was confusing?" |

### Five Is the Magic Number

Patterns emerge after 3-5 people and returns diminish after 5 — and five interview-plus-break slots fit one day (see references/friday.md). Recruit target customers via a screener survey and offer an incentive ($100-$200 B2B, $50-$100 B2C).

See [references/recruiting.md](references/recruiting.md) two weeks before the sprint — it has screener-survey questions, recruiting channels, scheduling logistics, and incentive guidance for locking in five on-target users.

### Take Notes: Pattern Recognition

Capture observations in a grid, one column per customer:

| Customer 1 | Customer 2 | Customer 3 | Customer 4 | Customer 5 |
|------------|------------|------------|------------|------------|
| notes | notes | notes | notes | notes |

Mark each observation **✓** (positive, success), **✗** (negative, failure), or **~** (neutral/mixed). After all five interviews, count marks per row and look for patterns — did all 5 struggle with the same thing?

### End-of-Sprint Debrief

Organize findings: **✓ what worked** (flows everyone understood, messaging that resonated), **✗ what failed** (confusing terminology, missing steps, wrong assumptions), **~ mixed** (some got it, some didn't). Then decide next steps:

- **Core concept validated:** build it, or run the next sprint on details
- **Major issues:** pivot, or sprint again on the problems
- **Total failure:** back to the drawing board — you just saved months

**Friday output:** interview recordings, pattern notes, a clear list of what works and what doesn't, decision on next steps.

See [references/friday.md](references/friday.md) before interviewing — verbatim Five-Act scripts, note-taking templates, the fuller next-steps decision table, and the common Friday mistakes to avoid.

## When to Run a Design Sprint

**Run when:** the decision is high-stakes, there's no time to build and test normally, the team is stuck in endless debate, multiple solutions compete, it's a new product/feature/major redesign, or you need to de-risk before investing.

**Don't run when:** the problem and solution are obvious and you just need to execute, the team isn't bought in, or you can't get the Decider for the full week.

See [references/case-studies.md](references/case-studies.md) for worked sprint walk-throughs (Slack, Blue Bottle Coffee, Savioke and more) when you need a concrete precedent for how a sprint played out in a domain like yours.

## Variations

- **4-Day Sprint:** Day 1 Map + Sketch (compressed), Day 2 Decide, Day 3 Prototype, Day 4 Test.
- **Remote Sprint:** Same schedule with Miro/FigJam whiteboards and Zoom. See [references/remote-sprints.md](references/remote-sprints.md) when the team is distributed — it adapts each exercise to digital whiteboards, sets remote time-boxes, and handles video-based prototype testing.
- **Multi-Sprint:** Sprint 1 chooses direction on a broad problem, Sprint 2 deep-dives the chosen solution, Sprint 3 refines details.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Skip prototyping** | Nothing to test | Always prototype, even if simple |
| **Over-engineer prototype** | Waste time on details that don't matter | Facade only, not working code |
| **Test with wrong users** | Invalid feedback | Screen for target customers |
| **Explain prototype to users** | Defeats the test; confusion is the data | Run Acts 3-4 as written — they interpret and struggle unaided |
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

## Further Reading

For the complete methodology, exercises, and case studies:

- [*"Sprint: How to Solve Big Problems and Test New Ideas in Just Five Days"*](https://www.amazon.com/Sprint-Solve-Problems-Test-Ideas/dp/150112174X?tag=wondelai00-20) by Jake Knapp, John Zeratsky, Braden Kowitz

## About the Author

**Jake Knapp** created the Design Sprint at Google, where he ran sprints on Gmail, Chrome, and Google X, then refined the process across 100+ startup sprints as a design partner at Google Ventures. The sprint is now used at Google, Slack, Airbnb, LEGO, and thousands of companies worldwide. He is also the author of *Make Time*.
