---
name: design-everyday-things
description: 'Apply foundational design principles: affordances, signifiers, constraints, feedback, and conceptual models. Use when the user mentions "why is this confusing", "affordance", "error prevention", "discoverability", "human-centered design", "mental model", "mapping", "seven stages of action", "users keep making mistakes", "this is unintuitive", or "people cant figure out how to use it". Also trigger when diagnosing why users err, reducing product complexity, or improving error messages and feedback. Covers the gulfs of execution and evaluation. For usability scoring, see ux-heuristics. For iOS-specific patterns, see ios-hig-design.'
license: MIT
metadata:
  author: wondelai
  version: "1.3.0"
---

# Design of Everyday Things Framework

Foundational design principles for creating products that are intuitive, discoverable, and understandable. The "bible of UX" — applicable to physical products, software, and any human-designed system.

## Core Principle

**Good design is actually a lot harder to notice than poor design, in part because good designs fit our needs so well that the design is invisible.** When something fails, users blame themselves — but the fault is almost always in the design. Great design bridges the gap between what people want to do and what the product allows: it is discoverable (you can figure out what to do) and understandable (you can figure out what happened).

## Scoring

**Goal: 10/10.** Rate any design 0-10 on discoverability, understandability, and error prevention. A 10/10 means users figure out what to do without instructions, understand what happened, and recover from errors easily. Report the current score and the improvements needed to reach 10/10.

## The Two Gulfs

Every interaction with a product requires bridging two gulfs:

```
USER                                    PRODUCT
  │                                        │
  ├──── Gulf of Execution ────────────────→│
  │     "How do I do what I want?"         │
  │                                        │
  │←──── Gulf of Evaluation ──────────────┤
  │     "What happened? Did it work?"      │
```

### Gulf of Execution

**The gap between what users want to do and what the product lets them do.** Users ask: What can I do here? Which control do I use?

**Bridge with:** clear signifiers, natural mappings, constraints, familiar conceptual models.

### Gulf of Evaluation

**The gap between what the product did and what users understand happened.** Users ask: What happened? Did it work? What state is the system in?

**Bridge with:** immediate visible feedback, clear system-state indicators, meaningful error messages, progress indicators.

**Design goal:** Make both gulfs as narrow as possible — action and understanding should be immediate.

See: [references/two-gulfs.md](references/two-gulfs.md) for gulf analysis exercises.

## Seven Fundamental Design Principles

### 1. Discoverability

**Definition:** Can users figure out what actions are possible and how to perform them? Its five components — affordances, signifiers, constraints, mappings, feedback — are detailed below.

**Test:** Put a new user in front of your product. If they can't figure out what to do within 10 seconds, discoverability is broken.

**Anti-pattern:** "The user manual explains it." If users need a manual, the design failed.

### 2. Affordances

**Definition:** The relationship between an object's properties and a user's capabilities that determines how the object could be used.

**Key insight:** Affordances exist whether or not they are perceived — what matters for design is *perceived* affordance.

| Type | Definition | Example |
|------|------------|---------|
| **Real** | Physical capability exists | A button affords pressing |
| **Perceived** | User believes capability exists | A raised area looks clickable |
| **Hidden** | Exists but isn't obvious | Right-click context menu |
| **False** | Appears to afford action but doesn't | Decorative element that looks clickable |
| **Anti-affordance** | Prevents action | A barrier that blocks movement |

**Digital applications:**

| Element | Affordance | How to Signal |
|---------|------------|---------------|
| **Button** | Clicking/tapping | Raised, colored, shadow, hover state |
| **Text field** | Text input | Border, placeholder text, label |
| **Scroll area** | Scrolling | Scroll bar, fade at edge, partial content |

**Common failures:** flat design erasing perceived affordances (button or label?), too-small touch targets, interactive and decorative elements that look identical.

See: [references/affordances.md](references/affordances.md) for affordance design patterns.

### 3. Signifiers

**Definition:** Signals that communicate where the action should take place. **Affordances determine what you CAN do; signifiers show you WHERE and HOW.**

| Type | Definition | Example |
|------|------------|---------|
| **Deliberate** | Designed to communicate | "Push" label on door, placeholder text |
| **Accidental** | Unintentional but informative | Worn path in grass (people walk here) |
| **Social** | Other people's behavior | Line of people indicates entrance |

**Digital signifiers:**

| Signifier | What It Communicates | Example |
|-----------|---------------------|---------|
| **Cursor change + hover state** | This is interactive | Pointer → hand on links; button color change |
| **Icons + labels** | Function of the element | Magnifying glass = search; "Submit", "Cancel" |
| **Color + position** | Status, category, hierarchy | Red = error, green = success; close button top-right |

**Design rule:** When in doubt, add a signifier — better to over-communicate than leave users guessing.

See: [references/signifiers.md](references/signifiers.md) for signifier patterns and examples.

### 4. Mappings

**Definition:** The relationship between controls and their effects. **Natural mapping** means the spatial layout of controls matches the layout of what they control.

| Mapping Quality | Example | Why It Works/Fails |
|-----------------|---------|-------------------|
| **Natural** | Volume slider (up = louder) | Matches mental model |
| **Poor** | Light switch panel | No spatial correspondence to lights |
| **Poor** | Stovetop knobs in a row | Layout doesn't match burner positions |

**Digital principles:** controls near what they affect, layout mirroring content, direction matching expectation (scroll down = content moves up), related controls grouped.

| Technique | How It Works | Example |
|-----------|-------------|---------|
| **Proximity** | Control near target | Edit button next to content |
| **Spatial** | Layout mirrors real world | Map controls match compass directions |
| **Cultural** | Follows conventions | Red = stop/danger, green = go/safe |
| **Sequential** | Follows natural order | Steps 1, 2, 3 left to right (or top to bottom) |

See: [references/mappings.md](references/mappings.md) for mapping analysis exercises.

### 5. Constraints

**Definition:** Limiting the possible actions to prevent errors.

| Type | Mechanism | Example |
|------|-----------|---------|
| **Physical** | Shape/size prevents wrong action | USB plug only fits one way |
| **Cultural** | Social norms guide behavior | Red means stop, green means go |
| **Semantic** | Meaning restricts options | A rearview mirror only makes sense facing backward |
| **Logical** | Logic limits choices | Only one hole left for the last screw |

**Digital constraints:**

| Constraint | Implementation | Example |
|------------|---------------|---------|
| **Input validation** | Restrict what can be entered | Date picker vs. free text |
| **Disabled states** | Gray out unavailable options | "Submit" disabled until form valid |
| **Forced sequence + undo** | Steps in order; allow reversal | Wizard with locked steps; Gmail "Undo send" |

**Design rule:** Every constraint you add is one less error the user can make — make wrong actions impossible rather than punishing them.

See: [references/constraints.md](references/constraints.md) for constraint design patterns.

### 6. Feedback

**Definition:** Communicating the results of an action back to the user. Feedback must be immediate (within 0.1s for direct manipulation), informative, appropriately dosed, and non-intrusive.

| Type | When to Use | Example |
|------|-------------|---------|
| **Visual** | Most actions | Button press animation, color change, checkmark |
| **Auditory** | Important events, confirmations | Success chime, error sound |
| **Haptic** | Touch devices, confirmation | Vibration on key press |
| **Progress** | Long operations | Progress bar, spinner, skeleton screen |

**Digital feedback patterns:**

| Situation | Feedback Needed | Example |
|-----------|----------------|---------|
| **Form submission** | Success/error message | "Saved!" toast or inline error |
| **Loading** | Progress indicator | Spinner, skeleton screen, percentage |
| **Error** | What went wrong + how to fix | "Invalid email. Please check format." |

**Response times:** 0.1s feels instantaneous; 1s is a noticeable delay (change cursor); 10s loses attention (show progress bar); over 10s users leave (show percentage, allow backgrounding).

**Common failures:** no feedback (did my click register?), delayed feedback (feels broken), unclear feedback, alert overload.

See: [references/feedback.md](references/feedback.md) for feedback design patterns.

### 7. Conceptual Models

**Definition:** The user's mental model of how a product works.

| Model | Held By | Description |
|-------|---------|-------------|
| **Design model** | Designer | How the designer thinks it works |
| **User's model** | User | How the user thinks it works |
| **System image** | Product | What the product actually communicates |

**Goal:** The user's model should match the design model; the system image is the only bridge. Matching models let users predict outcomes and recover from errors; mismatches breed confusion, self-blame, and support calls.

**Example (thermostat):** design model — set a temperature, the system maintains it; common user model — higher setting heats faster (wrong), so users crank it to 90°F.

**Build correct models with:** familiar metaphors (desktop, trash), visible system state, clear feedback, consistent behavior, progressive disclosure.

See: [references/conceptual-models.md](references/conceptual-models.md) for model design frameworks.

## Human Error

**Norman's key insight: there is no such thing as "human error" — only bad design.** When someone errs, look for the design flaw, not the person's flaw.

### Types of Errors

**Slips** — correct intention, wrong action:

| Slip Type | Cause | Example | Design Fix |
|-----------|-------|---------|------------|
| **Action slip** | Wrong action on right target | Click "Delete" instead of "Edit" | Separate destructive actions |
| **Memory lapse** | Forget step in sequence | Forget attachment after writing "attached" | Gmail's attachment reminder |
| **Mode error** | Right action, wrong mode | Type in caps lock | Show mode state clearly |
| **Capture error** | Habit overrides intention | Drive to old office on autopilot | Interrupt at decision points |

**Mistakes** — wrong intention, executed correctly:

| Mistake Type | Cause | Example | Design Fix |
|-------------|-------|---------|------------|
| **Rule-based** | Apply wrong rule | Use formula for wrong situation | Provide context, confirm |
| **Knowledge-based** | Incomplete/wrong mental model | Misunderstand how system works | Better conceptual model |
| **Memory lapse** | Forget goal or plan | Forget why you opened the fridge | Reminders, history |

### Design for Error

**Prevent:** constraints that make errors impossible, undo/redo everywhere, confirmation for destructive actions, sensible defaults, forgiving input.
**Recover:** clear error messages, never erase the user's work, partial saves, easy reset to a known good state.

**Error message checklist:**
- [ ] Says what went wrong (in human language)
- [ ] Says how to fix it
- [ ] Doesn't blame the user
- [ ] Preserves user's work
- [ ] Provides alternative path

See: [references/human-error.md](references/human-error.md) for error prevention patterns.

## The Seven Stages of Action

**Norman's model for how humans interact with products:**

```
1. GOAL      → "I want to adjust the temperature"
2. PLAN      → "I'll use the thermostat"
3. SPECIFY   → "I'll press the up arrow"
4. PERFORM   → (presses button)
   ─── Gulf of Execution ───
5. PERCEIVE  → (sees display change)
6. INTERPRET → "The number went up"
7. COMPARE   → "Is this what I wanted?"
   ─── Gulf of Evaluation ───
```

**Design implications:** support stages 1-3 with signifiers, mappings, and constraints; stage 4 with good affordances; stages 5-7 with feedback and visible state. Walk any interaction through each stage to find where users get stuck.

See: [references/seven-stages.md](references/seven-stages.md) for stage-by-stage analysis.

## Human-Centered Design (HCD) Process

```
Observation → Idea Generation → Prototyping → Testing → (iterate)
```

### 1. Observation

Watch real users in real contexts. Don't ask what they want (they don't know) — look for workarounds, frustrations, and adaptations across whole activities.

### 2. Idea Generation

Generate many ideas before converging; defer judgment and build on others' ideas.

### 3. Prototyping

Quick, cheap, disposable — test concepts, not polish. Paper for early ideas, interactive for validation.

### 4. Testing

Test with real users, not designers: 5 users reveal 85% of problems. Observe behavior, not just opinions, then iterate.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **No signifiers** | Users can't find features | Add visual cues for every interactive element |
| **No feedback** | Users don't know if action worked | Respond to every action within 0.1s |
| **Blaming users** | Ignores design flaws | Look for design cause of every "user error" |
| **Feature creep** | Complexity overwhelms | Apply constraints, progressive disclosure |
| **Inconsistency** | Breaks conceptual model | Same action = same result everywhere |
| **Ignoring context** | Designed for ideal conditions | Observe real usage environments |

## Quick Diagnostic

Audit any design:

| Question | If No | Action |
|----------|-------|--------|
| Can users figure out what to do? | Poor discoverability | Add signifiers, improve affordances |
| Do users understand what happened? | Gulf of evaluation too wide | Add feedback, show system state |
| Can users recover from errors? | No error tolerance | Add undo, confirmation, clear messages |
| Does the control layout match the output? | Poor mapping | Reorganize controls to match spatial layout |
| Are impossible/irrelevant options hidden? | Missing constraints | Disable, hide, or remove invalid options |

## Reference Files

- [two-gulfs.md](references/two-gulfs.md): Gulf analysis exercises, bridging strategies
- [affordances.md](references/affordances.md): Affordance types, design patterns
- [signifiers.md](references/signifiers.md): Signifier patterns, examples, best practices
- [mappings.md](references/mappings.md): Natural mapping analysis, spatial layout
- [constraints.md](references/constraints.md): Constraint types, digital implementations
- [feedback.md](references/feedback.md): Feedback patterns, timing, modality
- [conceptual-models.md](references/conceptual-models.md): Model design, metaphors, mental models
- [human-error.md](references/human-error.md): Error types, prevention, recovery
- [seven-stages.md](references/seven-stages.md): Stage analysis, evaluation tool
- [case-studies.md](references/case-studies.md): Door handles, thermostats, digital products

## Further Reading

For the complete framework:

- [*"The Design of Everyday Things"*](https://www.amazon.com/Design-Everyday-Things-Revised-Expanded/dp/0465050654?tag=wondelai00-20) by Don Norman (Revised & Expanded Edition, 2013)
- [*"Emotional Design"*](https://www.amazon.com/Emotional-Design-Love-Everyday-Things/dp/0465051367?tag=wondelai00-20) by Don Norman (design and emotion)

## About the Author

**Don Norman, PhD** is co-founder of the Nielsen Norman Group, director of The Design Lab at UC San Diego, and a former VP of Advanced Technology at Apple, where he coined the term "user experience." *The Design of Everyday Things* (1988, revised 2013) is widely considered the most influential design book ever written and is required reading in design programs worldwide.
