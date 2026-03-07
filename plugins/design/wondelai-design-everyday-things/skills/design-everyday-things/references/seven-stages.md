# The Seven Stages of Action

Don Norman's Seven Stages of Action is a model of how humans interact with products. Every interaction, from flipping a light switch to completing an online checkout, follows the same seven-stage cycle. Understanding these stages lets designers identify exactly where users get stuck and apply targeted fixes. The model divides neatly into two sides: execution (stages 1-4, bridging the Gulf of Execution) and evaluation (stages 5-7, bridging the Gulf of Evaluation).

## The Seven Stages in Detail

```
                        1. GOAL
                     "What do I want?"
                          |
              +-----------+-----------+
              |     EXECUTION         |     EVALUATION
              |                       |
         2. PLAN                 7. COMPARE
    "How can I do it?"      "Is this what I wanted?"
              |                       |
         3. SPECIFY              6. INTERPRET
    "What specific action?"  "What does this mean?"
              |                       |
         4. PERFORM              5. PERCEIVE
    "Do the action"          "What happened?"
              |                       |
              +--- THE WORLD / SYSTEM +
```

---

## Stage 1: Goal Formation

**Question the user asks**: "What do I want to accomplish?"

The user forms a high-level intention. Goals can be precise ("Set the alarm for 7:00 AM") or vague ("Make this presentation look better").

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| Goal is vague | "I want to fix this document" | The system does not help refine or clarify goals |
| Goal conflicts with system capabilities | "I want to merge these two accounts" (not supported) | Feature does not exist or is not discoverable |
| Goal is forgotten mid-task | User opens settings, forgets which setting they wanted | Complex navigation, many distractions |

### Design Solutions for Stage 1

| Solution | Implementation |
|----------|---------------|
| **Suggest goals** | Home screen with common tasks: "Create a document", "Schedule a meeting" |
| **Make capabilities visible** | Dashboard showing all available features at a glance |
| **Support vague goals** | Search that accepts natural language: "make text bigger" |
| **Maintain goal context** | Show breadcrumbs, page titles, and task descriptions that remind users why they are here |

---

## Stage 2: Plan Formation

**Question the user asks**: "How can I do this? What approach should I take?"

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| No obvious path | "How do I share this?" (no share button visible) | Missing signifiers, hidden features |
| Multiple possible paths, unclear which is correct | "Should I use Export, Save As, or Download?" | Overlapping features with unclear distinctions |
| Plan requires knowledge the user lacks | "I need to configure the API webhook" (what is a webhook?) | Technical jargon, no progressive disclosure |

### Design Solutions for Stage 2

| Solution | Implementation |
|----------|---------------|
| **Clear signifiers** | Visible labels for every available action |
| **Guided workflows** | Step-by-step wizards for complex tasks |
| **Reduce choices** | Offer the most common path prominently; hide alternatives |
| **Contextual help** | "How do I...?" link that opens task-specific guidance |
| **Templates and presets** | Pre-configured starting points that skip planning |

---

## Stage 3: Specification of Action

**Question the user asks**: "What specific action do I need to perform?"

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| Cannot find the control | "Where is the save button?" | Poor visual hierarchy, inconsistent placement |
| Cannot identify the correct control | "Is this the right dropdown?" | Ambiguous labels, icon-only controls |
| Action requires non-obvious sequence | "Click here, then hold Shift, then click there" | Complex interaction that is not signified |

### Design Solutions for Stage 3

| Solution | Implementation |
|----------|---------------|
| **Consistent placement** | Primary actions always in the same location across screens |
| **Clear labels** | Every control has a text label (not just an icon) |
| **Affordances** | Interactive elements look interactive (buttons look clickable) |
| **Keyboard shortcuts visible** | Show shortcut in tooltip or menu alongside the action name |
| **Command palette** | Searchable list of all actions for users who know what they want |

---

## Stage 4: Execution (Perform)

**Question the user asks**: "I'm doing it. Is this working?"

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| Click does not register | Tap target too small on mobile | Touch target below 44pt minimum |
| Action is physically difficult | Precise drag-and-drop on a touchscreen | Interaction not optimized for input device |
| Accidental action | Tapping the wrong button because targets overlap | Insufficient spacing between targets |
| Action is slow or tedious | Selecting 50 items one by one | No bulk selection or "Select All" option |

### Design Solutions for Stage 4

| Solution | Implementation |
|----------|---------------|
| **Adequate target sizes** | Minimum 44x44pt touch targets, 24x24px desktop |
| **Input optimization** | Match interaction to device (tap on mobile, click on desktop) |
| **Spacing** | Sufficient distance between interactive targets |
| **Shortcuts** | Bulk actions, keyboard shortcuts, gesture shortcuts |
| **Forgiveness** | Undo for accidental actions, confirmation for destructive ones |

---

## Stage 5: Perception

**Question the user asks**: "What happened? What changed?"

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| No visible change | Click a button and nothing happens | No feedback implemented |
| Change is too subtle | A small number changed in a corner of the screen | Low visual prominence of the feedback |
| Change is too fast | A toast message appeared and disappeared in 1 second | Insufficient display duration |
| Change is off-screen | The effect happened below the fold | No scroll-to or highlight behavior |

### Design Solutions for Stage 5

| Solution | Implementation |
|----------|---------------|
| **Immediate feedback** | Every action produces visible response within 100ms |
| **Prominent changes** | Use animation, color, and position to draw attention to what changed |
| **Sufficient duration** | Toast messages visible for 4-8 seconds with manual dismiss option |
| **Scroll to change** | Automatically scroll to or highlight the part of the interface that changed |
| **Multi-channel feedback** | Combine visual + auditory + haptic for important events |

---

## Stage 6: Interpretation

**Question the user asks**: "What does this mean?"

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| Feedback is ambiguous | A number changed from 3 to 4 but user does not know what it represents | Unclear labels or missing context |
| Feedback uses jargon | "Error: ECONNREFUSED" | Technical language not translated to human language |
| Feedback is misleading | Green checkmark appears but the action actually failed partially | Incorrect or premature success signal |
| Multiple changes at once | Several parts of the screen update simultaneously | No visual hierarchy to guide attention |

### Design Solutions for Stage 6

| Solution | Implementation |
|----------|---------------|
| **Plain language** | All feedback in human-readable terms with no jargon |
| **Context** | Include enough information to interpret the feedback ("3 items deleted" not just "Done") |
| **Accurate status** | Only show success when the action truly succeeded end-to-end |
| **Single focus** | Sequence changes or highlight the most important one |
| **Error explanations** | Describe what happened, why, and how to fix it |

---

## Stage 7: Comparison

**Question the user asks**: "Is this what I wanted? Did I achieve my goal?"

The user compares the interpreted result against their original goal from Stage 1.

### Where Users Get Stuck

| Problem | Example | Design Cause |
|---------|---------|-------------|
| Cannot confirm goal was achieved | "Did my email actually send?" | No explicit confirmation |
| Goal partially achieved | Three of four settings were saved but one failed silently | Partial success not communicated |
| Unexpected side effects | "I changed my username but now my old links are broken" | Consequences not explained before action |
| Cannot compare before and after | "Did the color actually change?" | No reference point for comparison |

### Design Solutions for Stage 7

| Solution | Implementation |
|----------|---------------|
| **Explicit confirmation** | "Your email has been sent to alice@example.com" |
| **Complete status reporting** | "3 of 4 settings saved. 'Display name' could not be updated because..." |
| **Consequence preview** | "Changing your username will break existing links. Continue?" |
| **Before/after comparison** | Toggle or side-by-side view showing previous and current state |
| **Summary screens** | After multi-step processes, show a summary of everything that was done |

---

## Using the Seven Stages as an Evaluation Tool

The Seven Stages of Action is one of the most practical evaluation tools available. For any user task, walk through each stage and ask: "What could go wrong here?"

### Walkthrough Template

For each task you want to evaluate, fill in this table.

| Stage | Question | Current Design Support | Gap / Problem | Severity (H/M/L) | Proposed Fix |
|:-----:|----------|----------------------|--------------|:-----------------:|-------------|
| 1. Goal | Can the user form a clear goal? | | | | |
| 2. Plan | Can the user figure out an approach? | | | | |
| 3. Specify | Can the user identify the right control? | | | | |
| 4. Perform | Can the user execute the action easily? | | | | |
| 5. Perceive | Can the user see what happened? | | | | |
| 6. Interpret | Can the user understand what it means? | | | | |
| 7. Compare | Can the user confirm the goal was achieved? | | | | |

Attempt the task as a new user. At each stage, note what supports and what hinders. Rate severity (H/M/L) and propose a fix.

---

## Worked Examples

### Example 1: Booking a Flight

| Stage | User Experience | Design Analysis |
|:-----:|----------------|-----------------|
| 1. Goal | "I want to fly from New York to London on March 15" | Goal is clear and specific |
| 2. Plan | "I'll search for flights on this booking site" | Plan is straightforward |
| 3. Specify | User must find origin, destination, date, and passenger fields | Fields are labeled and use autocomplete for cities: good |
| 4. Perform | User types "New York", selects from dropdown, picks date from calendar | Autocomplete and date picker reduce errors: good |
| 5. Perceive | Search results appear below | Results load with skeleton screens: good |
| 6. Interpret | User sees prices, times, airlines, and stops | Information is well-organized but "1 stop" does not say where or how long: gap |
| 7. Compare | User compares results to find the best option | Sort and filter available, but no "best value" indicator: minor gap |

**Key fixes**: Show layover details (city, duration) inline. Add a "Best value" tag for flights that balance price and convenience.

### Example 2: Using a Thermostat

| Stage | User Experience | Design Analysis |
|:-----:|----------------|-----------------|
| 1. Goal | "I want the room to be warmer" | Goal is vague: how much warmer? |
| 2. Plan | "I'll turn up the thermostat" | Simple plan |
| 3. Specify | User looks for the up arrow or dial | Control is visible: adequate |
| 4. Perform | User presses up repeatedly or turns dial to a high number | User sets to 85 hoping for faster heating: conceptual model failure |
| 5. Perceive | Display shows "85" | Number changed: perceived |
| 6. Interpret | User believes the house will now heat faster | Interpretation is wrong because the system image does not explain the on/off mechanism |
| 7. Compare | Room is not noticeably warmer after 5 minutes | User is frustrated, may turn it up further |

**Key fixes**: Show current temperature AND target. Show "Heating..." indicator. Show estimated time to reach target. Explain that the heating rate is constant regardless of the target setting.

### Example 3: Completing an E-Commerce Checkout

| Stage | User Experience | Design Analysis |
|:-----:|----------------|-----------------|
| 1. Goal | "I want to buy this item" | Clear goal |
| 2. Plan | "I'll go through checkout" | User expects a standard flow |
| 3. Specify | User must find "Checkout" or "Buy Now" button | Button is prominent and well-labeled: good |
| 4. Perform | User clicks the button | Proceeds to checkout: good |
| 5. Perceive | Checkout page loads with shipping, payment, and review sections | Clear step indicator "Step 1 of 3": good |
| 6. Interpret | User understands they must fill in shipping first | Labels are clear, fields are ordered logically: good |
| 7. Compare | After placing order, user sees confirmation with order number and expected delivery date | Explicit confirmation with all details: excellent |

**Key observation**: E-commerce checkout is one of the most optimized seven-stage flows because conversion directly impacts revenue.

---

## Seven Stages Audit Worksheet

Rate each stage 1-5 (1 = users consistently fail, 5 = zero friction).

| Stage | Rating (1-5) | What Works | What Fails | Priority Fix |
|:-----:|:------------:|-----------|-----------|-------------|
| 1. Goal | | | | |
| 2. Plan | | | | |
| 3. Specify | | | | |
| 4. Perform | | | | |
| 5. Perceive | | | | |
| 6. Interpret | | | | |
| 7. Compare | | | | |

### Summary

- **Weakest stage**: ___
- **Side with more issues**: Execution (stages 1-4) / Evaluation (stages 5-7)
- **Total issues found**: ___
- **Top 3 fixes by impact**:
  1. ___
  2. ___
  3. ___

### Follow-Up Actions

- [ ] Design and prototype fixes for top-priority issues
- [ ] Test with 3-5 users using a think-aloud protocol
- [ ] Re-score each stage after implementing fixes
- [ ] Track improvement in task completion rate and time
