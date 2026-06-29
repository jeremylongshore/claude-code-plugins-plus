---
name: design-sprint
description: 'Run a structured 5-day process to prototype, test, and validate product ideas with real users. Use when the user mentions "design sprint", "validate in a week", "rapid prototype", "test with users", "de-risk before building", "GV sprint", "prototype testing", "design workshop", "should we build this", "validate an idea fast", or "test before we build". Also trigger when a team must make a critical product decision quickly, resolve stakeholder disagreements, or test a risky idea before investing in development. Covers mapping, sketching, deciding, prototyping, and testing. For ongoing experimentation, see lean-startup. For customer job analysis, see jobs-to-be-done.'
license: MIT
metadata:
  author: wondelai
  version: "1.3.0"
---

# Design Sprint Framework

A five-day process for answering critical business questions through design, prototyping, and testing ideas with customers. Developed at Google Ventures and used by Google, Slack, Airbnb, and hundreds of startups.

## Core Principle

**Great solutions require both deep work and fast iteration.** The Design Sprint compresses months of debate, design, and testing into one week, replacing endless discussion with focus and urgency. It de-risks product decisions by testing with real users before any production code is written.

## Scoring

**Goal: 10/10.** Rate any sprint plan or execution 0-10 against the principles below: proper structure, time-boxing, prototyping, and user testing. Lower scores mean skipped steps or insufficient testing. Report the current score and the improvements needed to reach 10/10.

## The 5-Day Sprint Process

```
Monday → Tuesday → Wednesday → Thursday → Friday
  Map      Sketch     Decide      Prototype    Test
```

**Prerequisites:** a big challenge worth a week's focus; the right team (Decider plus 4-7 people with diverse expertise); five full days (10am-5pm) with no interruptions; a dedicated room with whiteboards. One **Sprint Master** facilitates, keeps time, and manages energy.

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

See: [references/monday.md](references/monday.md) for detailed Monday exercises and facilitation.

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

See: [references/tuesday.md](references/tuesday.md) for sketching templates and examples.

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

See: [references/wednesday.md](references/wednesday.md) for decision exercises and storyboard templates.

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

See: [references/thursday.md](references/thursday.md) for prototyping tools and techniques.

## Friday: Test

**Goal:** Interview 5 customers; learn what works and what doesn't.

### Setup

Interview room: quiet space, laptop with the prototype, camera recording screen and customer's face. Observation room: live video feed where the whole team watches and takes notes on a whiteboard. One **Interviewer** conducts all five interviews.

### The Five-Act Interview

About 30 minutes per customer, with 30-minute breaks between to discuss observations and adjust questions.

| Act | Time | What to Do |
|-----|------|------------|
| **1. Friendly welcome** | 5 min | Greet warmly; explain you're testing the prototype, not them; get recording permission; encourage thinking aloud |
| **2. Context questions** | 5 min | "Tell me about how you currently handle [problem]" — understand mindset and current behavior |
| **3. Introduce prototype** | 5 min | "What's this? What do you think it's for?" Don't explain — let them interpret |
| **4. Tasks and nudges** | 15 min | Open-ended exploration, then storyboard tasks. When stuck: "What would you do next?", "What's going through your mind?" Don't help — watch them struggle |
| **5. Debrief** | 5 min | "What did you think overall?", "Who is this for?", "What worked? What was confusing?" |

### Five Is the Magic Number

Patterns emerge after 3-5 people and returns diminish after 5 — and five 1-hour slots fit one day. Recruit target customers via a screener survey, offer an incentive ($100-$200 B2B, $50-$100 B2C), and schedule 6 to absorb a no-show.

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

See: [references/friday.md](references/friday.md) for interview scripts and note-taking templates.

## When to Run a Design Sprint

**Run when:** the decision is high-stakes, there's no time to build and test normally, the team is stuck in endless debate, multiple solutions compete, it's a new product/feature/major redesign, or you need to de-risk before investing.

**Don't run when:** the problem and solution are obvious and you just need to execute, the team isn't bought in, or you can't get the Decider for the full week.

## Variations

- **4-Day Sprint:** Day 1 Map + Sketch (compressed), Day 2 Decide, Day 3 Prototype, Day 4 Test.
- **Remote Sprint:** Same schedule with Miro/FigJam whiteboards and Zoom.
- **Multi-Sprint:** Sprint 1 chooses direction on a broad problem, Sprint 2 deep-dives the chosen solution, Sprint 3 refines details.

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

## Reference Files

- [monday.md](references/monday.md): Map exercises, HMW notes, target selection
- [tuesday.md](references/tuesday.md): Sketching templates, Crazy 8s, solution sketches
- [wednesday.md](references/wednesday.md): Decision exercises, storyboard templates
- [thursday.md](references/thursday.md): Prototyping tools, techniques, checklists
- [friday.md](references/friday.md): Interview scripts, note-taking, pattern analysis
- [facilitation.md](references/facilitation.md): Sprint Master guide, time-boxing, energy management
- [recruiting.md](references/recruiting.md): User recruitment, screener surveys, scheduling
- [case-studies.md](references/case-studies.md): Slack, Blue Bottle Coffee, Savioke, and more
- [remote-sprints.md](references/remote-sprints.md): Adapting sprint for distributed teams

## Further Reading

For the complete methodology, exercises, and case studies:

- [*"Sprint: How to Solve Big Problems and Test New Ideas in Just Five Days"*](https://www.amazon.com/Sprint-Solve-Problems-Test-Ideas/dp/150112174X?tag=wondelai00-20) by Jake Knapp, John Zeratsky, Braden Kowitz

## About the Author

**Jake Knapp** created the Design Sprint at Google, where he ran sprints on Gmail, Chrome, and Google X, then refined the process across 100+ startup sprints as a design partner at Google Ventures. The sprint is now used at Google, Slack, Airbnb, LEGO, and thousands of companies worldwide. He is also the author of *Make Time*.
