# Design Sprint - Implementation Guide

Step-by-step methodology for running a 5-day structured sprint to prototype, test, and validate product ideas with real users.

## Why Design Sprints Work

Traditional product development wastes months building the wrong thing. Design Sprints de-risk decisions by testing ideas with real users before writing production code. The compressed timeline creates urgency that eliminates endless meetings and forces decisions.

A Design Sprint answers: "Should we build this, and if so, what version should we build first?"

## Pre-Sprint Preparation (1-2 weeks before)

**Team composition (5-7 people maximum)**
- Decider: the person with final say on product decisions (PM, CEO, or founder)
- Facilitator: runs the process (can be external or internal)
- Designer: visual and interaction design
- Engineer: technical feasibility assessment
- Customer expert: someone who talks to customers regularly
- Marketing or sales: understands the customer's language
- Domain expert (optional): subject matter expert for the specific challenge

**Room and materials setup**
- Large wall space for sticky notes (or equivalent digital tool: FigJam, MIRO)
- Sticky notes (2-3 colors), markers, dot stickers (for voting)
- Timer visible to all participants
- No laptops during sprint sessions (phones permitted only for research tasks)

**Define the sprint question**
- Write the sprint question before Monday: "What big question do we want to answer this week?"
- Example: "Will busy parents use a meal planning tool integrated into their grocery app?"
- The sprint question determines what you prototype and what you test

## Day 1: Map (Monday)

**Goal:** Understand the problem space and agree on the focus for the week.

**Morning: Context setting (3 hours)**
- "How Might We" exercise (20 min): write every problem statement on sticky notes starting with "How Might We..."
- Sort and group HMWs on the wall
- Lightning demos (60 min): each team member shares inspiring examples (competitors, adjacent products, non-software solutions) — 3 minutes each, no more

**Afternoon: Long-term goal + sprint questions (2 hours)**
- Long-term goal: "In 2 years, [product] will be..." (optimistic, inspiring)
- Sprint questions (pessimistic): "What could go wrong? What would cause us to fail?"
- Sprint questions become the framework for user testing
- Map: draw a simple flow map from customer → key action → desired outcome (keep it high-level, 5-15 steps)
- Facilitate a vote (dot stickers) on the most important map area to focus the sprint

**Day 1 outputs:**
- Agreed sprint question
- Long-term goal
- Sprint questions (tests to answer)
- Focus area on the map
- "Target customer" and "target moment" selected

## Day 2: Sketch (Tuesday)

**Goal:** Generate diverse solution ideas independently before group discussion.

**Morning: Lightning demos and inspiration (90 min)**
- Each participant researches: 3 inspiring examples relevant to the sprint question
- Share and discuss (builds a shared inspiration library)

**Afternoon: Sketching (3 hours)**
- Four-step sketching sequence:
  1. **Notes** (20 min): walk the map, take notes on anything relevant
  2. **Ideas** (20 min): rough sketches of any ideas without editing
  3. **Crazy 8s** (8 min): fold paper into 8 panels, sketch 8 variations of one key idea in 1 min each
  4. **Solution sketch** (60-90 min): one detailed 3-panel storyboard of the best solution (no names on sketches)

**Day 2 outputs:**
- Solution sketches from every team member
- High diversity of approaches (no groupthink — sketches done independently)

## Day 3: Decide (Wednesday)

**Goal:** Choose the best ideas and create a storyboard for the prototype.

**Morning: Critique and vote (3 hours)**
- Sticky decision process:
  1. Gallery: hang all solution sketches on the wall
  2. Silent critique (15-20 min): everyone reads all sketches, places dot stickers on interesting elements
  3. Speed critique (3 min per sketch): facilitator narrates what each sketch says, team notes interesting elements
  4. Straw poll: everyone votes on their single favorite solution
  5. Decider makes the final call (overrides popular vote if needed — they have the most context)

**Afternoon: Storyboard (3 hours)**
- Create a 15-panel storyboard: the customer's complete experience with the prototype
- Begin the storyboard with an "opening scene" (where does the customer come from?)
- Each panel = one screen or step
- Be specific: write the actual copy, describe the actual UI elements
- Do not prototype what you don't need to test

**Day 3 outputs:**
- Winning solution selected
- 15-panel storyboard ready for prototype build

## Day 4: Prototype (Thursday)

**Goal:** Build a realistic-looking prototype that is testable on Friday.

**Prototyping principles**
- The prototype must look real enough that a user can react honestly
- The prototype does NOT need to work — it needs to look like it works
- Scope: build only the storyboard panels, nothing else
- Tool: Figma, Keynote, or any rapid prototyping tool

**Team roles on Prototype Day**
- Makers (2-3 people): build the prototype screens
- Writer: writes all copy (headlines, buttons, body text) in the customer's language
- Asset collector: gathers photos, icons, and content needed
- Stitcher: assembles all assets into a clickable prototype in the afternoon
- Interviewer: writes and rehearses the Friday interview script

**Quality bar:**
- User can complete the core task flow without explanation from the team
- Looks like a screenshot of a real product, not a wireframe
- The actual copy is written and used (not "Lorem Ipsum")

**Day 4 outputs:**
- Clickable prototype covering the storyboard flow
- Interview script for Friday

## Day 5: Test (Friday)

**Goal:** Learn from 5 real users whether the solution works.

**Recruiting users**
- Recruit 5 users matching the sprint's target customer profile
- 5 interviews reveal 80% of usability problems
- Schedule 60-min slots with 15-min breaks between each
- Compensate fairly ($50-150 depending on audience type)

**Interview structure (60 min)**
- Intro (5 min): "I'm testing the design, not you. There are no wrong answers. Think aloud."
- Warm-up questions (5 min): understand their current behavior related to the sprint question
- Context setup (5 min): set the scene without revealing your solution
- Prototype tasks (40 min): give them tasks, observe without helping
- Debrief (5 min): overall impressions, open questions

**Live note-taking (observation room)**
- Team watches via screen share or camera (not in the interview room)
- Each observer takes notes on sticky notes: green = positive reaction, red = confusion or frustration
- After each interview: 15-min debrief, stick notes on "learning wall"

**Friday afternoon: Pattern finding**
- After all 5 interviews, group the sticky notes by theme
- Look for patterns that appear in 3+ interviews (signal vs. noise)
- Create a summary: what worked, what didn't, what to do next

**Day 5 outputs:**
- Qualitative data from 5 real users
- Patterns of success and failure
- Decision: validated (build it), invalidated (change direction), or needs another sprint

## Post-Sprint Decisions

| Result | Signal | Action |
|--------|--------|--------|
| Strong positive (4-5/5 users succeed) | Validated | Move to production with confidence |
| Mixed (2-3/5 users succeed) | Partial validation | Identify what worked, sprint again on what didn't |
| Negative (0-1/5 users succeed) | Invalidated | Do not build this; return to problem definition |

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Including more than 7 people | Decision-making becomes impossible | Cap at 7; observers can watch but can't vote |
| Skipping user recruitment | No Friday testing → no learning | Recruit users BEFORE the sprint starts |
| Building too much on Thursday | Prototype takes 2 days, nothing gets tested | Prototype only what's in the storyboard |
| No Decider in the room | Decisions get postponed or appealed after the sprint | Decider must attend Monday and Wednesday |
| Testing on colleagues | Confirmation bias, no real learning | Only test with actual target users |

## Quick-Start Checklist

- [ ] Sprint question defined
- [ ] Team of 5-7 assembled with all roles covered
- [ ] Decider confirmed and committed to Monday and Wednesday
- [ ] 5 user interviews recruited before sprint starts
- [ ] Room and materials ready (or digital tool set up)
- [ ] No laptops policy communicated to team
- [ ] Interview script drafted by Wednesday
- [ ] Prototype complete and tested internally by Thursday 5pm
- [ ] Interview recorded for analysis (with permission)
- [ ] Pattern-finding session scheduled for Friday afternoon
