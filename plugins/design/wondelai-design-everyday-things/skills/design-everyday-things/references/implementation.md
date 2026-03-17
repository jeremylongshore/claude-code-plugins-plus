# Design of Everyday Things - Implementation Guide

Step-by-step methodology for applying Norman's foundational design principles to create products that are discoverable, understandable, and fault-tolerant.

## The Six Fundamental Design Concepts

Before auditing or designing, internalize these six concepts:

| Concept | Definition | Design Question |
|---------|-----------|----------------|
| Affordances | Properties that signal possible actions | "What does this element invite users to do?" |
| Signifiers | Visible cues that communicate where to act | "How does the user know where to interact?" |
| Constraints | Limits that prevent wrong actions | "How does the design prevent this error?" |
| Feedback | Communication of results of actions | "How does the user know their action worked?" |
| Conceptual Model | User's mental model of how the system works | "Does the user understand what will happen?" |
| Mapping | Relationship between controls and outcomes | "Is the control near or similar to what it affects?" |

## Step 1: The Discoverability Audit

A discoverable interface = users can figure out what to do without instructions.

**1a. Run the "first 30 seconds" test**
- Show someone the UI for 30 seconds (no verbal instructions)
- Ask: "What can you do here? What would you click first?"
- Count: how many correct actions are taken vs. how many wrong attempts

**1b. Signifier audit**
- Walk through every interactive element: button, link, input, toggle, drag handle
- For each, ask: "Is it obvious this can be interacted with?"
- Common failures:
  - Flat design removing affordance cues (things that look like buttons aren't clickable)
  - Text that looks like a link but isn't
  - Invisible scrollable areas
  - Controls with no hover or active state

**1c. Mapping audit**
- Are controls located near or visually connected to what they affect?
- Classic failure: a form's "clear" button placed next to "submit" — wrong mapping, catastrophic results
- Good mapping: volume slider directly below the speaker icon it controls

## Step 2: Evaluate Conceptual Models

Users form a mental model of how your system works. If their model doesn't match your actual system, errors are inevitable.

**2a. The "how does this work?" test**
- Ask users to describe in their own words how the system works
- Listen for: correct models (good design), incorrect but logical models (mismatch to fix), and blank stares (fundamental clarity problem)

**2b. Systems image vs. designer's model**
- Designer's model = how you (the designer) think the system works
- System's image = what the product actually communicates through its design
- User's model = what the user believes based on the system's image
- Mismatches between these cause every "why did the user do that?!" moment

**2c. Common conceptual model failures:**
- Cloud sync that doesn't explain its sync status (users think changes are lost)
- "Archive" vs "Delete" when users don't understand the difference
- Multi-step forms without a visible progress indicator (users don't know where they are)
- Undo that only undoes the last action (users believe it undoes everything recent)

## Step 3: Apply the Gulf Framework

Norman's "gulfs" explain why users fail:
- **Gulf of Execution**: the gap between what the user wants to do and available actions ("I don't know how to do this")
- **Gulf of Evaluation**: the gap between system state and user's interpretation ("I don't know if it worked")

**3a. Close the Gulf of Execution**
- Reduce the steps required to accomplish common goals
- Every additional step is a potential point of abandonment
- Use progressive disclosure: show only what's needed now; reveal advanced options when needed
- Pre-fill forms with intelligent defaults based on context

**3b. Close the Gulf of Evaluation**
- Every action must have visible feedback:
  - Immediate feedback (< 100ms): visual state change on click/tap
  - Short-term feedback (< 1s): loading indicator
  - Completion feedback: success state with clear confirmation of what happened
  - Error feedback: specific, non-blaming, recovery-focused error messages

**3c. Feedback design principles:**
- Be specific: "Email sent to sarah@example.com" not "Success"
- Be actionable: "File size too large (8MB). Maximum is 5MB. Try compressing the image." not "Upload failed"
- Be immediate: if feedback is delayed, show a progress indicator within 100ms of the action

## Step 4: Design for Error Prevention and Recovery

Good design prevents errors. Great design also makes recovery from errors easy and blame-free.

**4a. Error prevention hierarchy (from Norman)**
1. Eliminate the possibility of error (best)
2. Make the error visible before it's committed (second best)
3. Make the error immediately reversible (good)
4. Make the error easy to recover from (acceptable)
5. Show a helpful error message (last resort)

**4b. Constraint types to implement:**
- Physical constraints: disable buttons/inputs that aren't applicable in the current state
- Cultural constraints: use familiar conventions (red = danger, checkmark = complete)
- Logical constraints: ordering steps so earlier steps naturally prevent later mistakes
- Semantic constraints: label options so their meaning prevents wrong selection

**4c. Design for "slips" vs. "mistakes"**
- Slips: correct intention, wrong execution (fat-finger, wrong button location)
  - Fix: confirmation dialogs for destructive actions; undo for all significant actions
- Mistakes: incorrect intention (user doesn't understand the system)
  - Fix: improve conceptual model clarity; better onboarding

## Step 5: Audit for the Seven Stages of Action

Norman's model of how humans act on systems: goal → plan → specify → perform → perceive → interpret → compare.

**Use this as a diagnostic checklist for any failed user flow:**

| Stage | Question | Common Failure |
|-------|----------|---------------|
| Goal formation | Is the user's goal served by this product? | Wrong audience or wrong product |
| Plan | Can the user find a plan to reach the goal? | Navigation failure; confusing IA |
| Specification | Can the user identify specific actions? | Unclear affordances/signifiers |
| Execution | Can the user perform the action? | Physical or interaction friction |
| Perception | Can the user see the system's response? | Missing feedback |
| Interpretation | Can the user understand what happened? | Unclear feedback messages |
| Comparison | Does the result match their goal? | Partial success, wrong outcome |

## Step 6: Apply the Human-Centered Design Process

**6a. Observation (not just asking)**
- Watch people use your product; don't ask "what do you want?" (people can't tell you)
- Note: what do they do, not what they say they do
- Track workarounds: if users consistently work around a feature, the design is wrong

**6b. Ideation constrained by principles**
- For each identified problem, generate 3+ solutions
- Evaluate each solution against: discoverability, feedback, conceptual model clarity, error prevention
- Select the solution that best scores across all criteria

**6c. Rapid prototyping**
- Test conceptual model first (before visual design)
- Wireframe the interaction, not the aesthetics
- 5 user tests will reveal 80% of fundamental design problems

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Removing affordances for visual cleanliness | Users can't figure out what's interactive | Add signifiers: hover states, icon + label, visual weight |
| Clever design that requires learning | Users blame themselves when confused | Use familiar conventions; be clear, not clever |
| Destructive actions without confirmation | Data loss, user frustration | Add confirmation dialogs + undo for all reversible actions |
| Error messages that blame the user | User abandonment, frustration | Rewrite errors: what happened + why + how to fix |
| Beautiful but unresponsive interactions | Users think their action failed | Every action needs feedback within 100ms |

## Quick-Start Checklist

- [ ] First-30-seconds discoverability test run with 3 users
- [ ] Signifier audit: every interactive element has a clear affordance
- [ ] Mapping audit: controls are adjacent to what they affect
- [ ] Conceptual model test: 3 users can explain how the system works
- [ ] Gulf of Execution: primary goal achievable in fewer than 5 steps
- [ ] Gulf of Evaluation: every action has immediate + completion feedback
- [ ] Destructive actions have confirmation + undo
- [ ] All error messages rewritten: specific, actionable, blame-free
- [ ] Seven-stage audit run on most-failed user flow
