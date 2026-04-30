---
name: design-everyday-things
description: |
  Analyze and apply foundational design principles: affordances, signifiers, constraints, feedback, and conceptual models. Use when the user mentions "why is this confusing", "affordance", "error prevention", "discoverability", "human-centered design", or "fault tolerance". Covers the gulfs of execution and evaluation. For usability scoring, see ux-heuristics. For iOS-specific patterns, see ios-hig-design. Trigger with 'design', 'everyday', 'things'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [design, design-everyday]
---
# Design of Everyday Things Framework

Foundational design principles for creating products that are intuitive, discoverable, and understandable. The "bible of UX" — applicable to physical products, software, and any human-designed system.

## Core Principle

**Good design is actually a lot harder to notice than poor design, in part because good designs fit our needs so well that the design is invisible.** When something works well, we take it for granted. When it fails, we blame ourselves — but the fault is almost always in the design.

**The foundation:** Design must bridge the gap between what people want to do and what the product allows them to do. The best designs are discoverable (users figure out what to do) and understandable (users figure out what happened).

## Scoring

**Goal: 10/10.** When reviewing or creating designs, rate 0-10 based on discoverability, understandability, and error prevention. A 10/10 means users can figure out what to do without instructions, understand what happened, and recover from errors easily. Always provide current score and improvements to reach 10/10.

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

**The gap between what users want to do and what the product lets them do.**

**Questions users ask:**
- What can I do here?
- How do I do it?
- Which control do I use?
- How do I operate this control?

**Bridging strategies:**
- Clear signifiers showing what's possible
- Natural mappings between controls and outcomes
- Constraints preventing wrong actions
- Familiar conceptual models

### Gulf of Evaluation

**The gap between what the product did and what users understand happened.**

**Questions users ask:**
- What happened?
- Did it work?
- Is this what I wanted?
- What state is the system in now?

**Bridging strategies:**
- Immediate, visible feedback
- Clear system state indicators
- Meaningful error messages
- Progress indicators

**Design goal:** Make both gulfs as narrow as possible. The ideal design requires zero bridging — action and understanding are immediate.

See: [references/two-gulfs.md](references/two-gulfs.md) for gulf analysis exercises.

## Seven Fundamental Design Principles

### 1. Discoverability

**Definition:** Can users figure out what actions are possible and how to perform them?

**Five components of discoverability:**
- Affordances
- Signifiers
- Constraints
- Mappings
- Feedback

(Each detailed below)

**Test:** Put a new user in front of your product. Can they figure out what to do within 10 seconds? If not, discoverability is broken.

**Anti-pattern:** "The user manual explains it." If users need a manual, the design failed.

### 2. Affordances

**Definition:** The relationship between the properties of an object and the capabilities of the agent (user) that determine how the object could be used.

**Key insight:** Affordances exist whether or not they are perceived. A door affords pushing whether or not you know to push it. What matters is *perceived* affordance.

**Types:**

| Type | Definition | Example |
|------|------------|---------|
| **Real affordance** | Physical capability exists | A button affords pressing |
| **Perceived affordance** | User believes capability exists | A raised area looks clickable |
| **Hidden affordance** | Capability exists but isn't obvious | Right-click context menu |
| **False affordance** | Appears to afford action but doesn't | A decorative element that looks clickable |
| **Anti-affordance** | Prevents action | A barrier that blocks movement |

**Digital applications:**

| Element | Affordance | How to Signal |
|---------|------------|---------------|
| **Button** | Affords clicking/tapping | Raised, colored, shadow, hover state |
| **Text field** | Affords text input | Border, hint text, label |
| **Link** | Affords navigation | Color, underline, cursor change |
| **Slider** | Affords dragging | Handle, track, visual range |
| **Scroll area** | Affords scrolling | Scroll bar, fade at edge, partial content |

**Common failures:**
- Flat design removes perceived affordances (is it a button or a label?)
- Touch targets that are too small (fat finger problem)
- No visual distinction between interactive and decorative elements

See: [references/affordances.md](references/affordances.md) for affordance design patterns.

### 3. Signifiers

**Definition:** Signals that communicate where the action should take place.

**Key insight:** Affordances determine what's possible. Signifiers communicate where and how.

**Affordances define what CAN be done; signifiers show HOW to do it.**

**Types:**

| Type | Definition | Example |
|------|------------|---------|
| **Deliberate signifier** | Designed to communicate | "Push" label on door, input hint text |
| **Accidental signifier** | Unintentional but informative | Worn path in grass (people walk here) |
| **Social signifier** | Other people's behavior | Line of people indicates entrance |

**Digital signifiers:**

| Signifier | What It Communicates | Example |
|-----------|---------------------|---------|
| **Cursor change** | This is interactive | Pointer → hand on links |
| **Hover state** | This responds to interaction | Button color change on hover |
| **Input hint text** | What to type here | "Enter your email..." |
| **Icons** | Function of the element | Magnifying glass = search |
| **Labels** | What this control does | "Submit", "Cancel", "Next" |
| **Color** | Status or category | Red = error, green = success |
| **Position** | Relationship and hierarchy | Close button in top-right corner |

**Design rule:** When in doubt, add a signifier. It's better to over-communicate than to leave users guessing.

See: [references/signifiers.md](references/signifiers.md) for signifier patterns and examples.

### 4. Mappings

**Definition:** The relationship between controls and their effects.

**Natural mapping:** When the spatial layout of controls matches the layout of the thing being controlled.

**Examples:**

| Mapping Quality | Example | Why It Works/Fails |
|-----------------|---------|-------------------|
| **Natural** | Steering wheel turns car direction | Direct spatial correspondence |
| **Natural** | Volume slider (up = louder) | Matches mental model |
| **Poor** | Light switch panel (which switch = which light?) | No spatial correspondence |
| **Poor** | Stovetop controls in a row (which knob = which burner?) | Layout doesn't match |

**Digital mapping principles:**
- Controls should be near what they affect
- Layout of controls should mirror layout of content
- Direction of action should match expectation (scroll down = content moves up)
- Grouping related controls together

**Mapping techniques:**

| Technique | How It Works | Example |
|-----------|-------------|---------|
| **Proximity** | Control near target | Edit button next to content |
| **Spatial** | Layout mirrors real world | Map controls match compass directions |
| **Cultural** | Follows conventions | Red = stop/danger, green = go/safe |
| **Sequential** | Follows natural order | Steps 1, 2, 3 from left to right (or top to bottom) |

See: [references/mappings.md](references/mappings.md) for mapping analysis exercises.

### 5. Constraints

**Definition:** Limiting the possible actions to prevent errors.

**Four types of constraints:**

| Type | Mechanism | Example |
|------|-----------|---------|
| **Physical** | Shape/size prevents wrong action | USB plug only fits one way (USB-C both ways) |
| **Cultural** | Social norms guide behavior | Red means stop, green means go |
| **Semantic** | Meaning restricts options | A rearview mirror only makes sense facing backward |
| **Logical** | Logic limits choices | Only one hole left for last screw (process of elimination) |

**Digital constraints:**

| Constraint Type | Implementation | Example |
|-----------------|---------------|---------|
| **Input validation** | Restrict what can be entered | Date picker vs. free text |
| **Disabled states** | Gray out unavailable options | "Submit" disabled until form valid |
| **Progressive disclosure** | Show options only when relevant | Payment fields after selecting "Buy" |
| **Forced sequence** | Steps must be completed in order | Wizard/stepper with locked steps |
| **Undo/redo** | Allow reversal | Gmail "Undo send" |

**The power of constraints:** Every constraint you add is one less error the user can make.

**Design rule:** Make it impossible to do the wrong thing, rather than punishing users for doing the wrong thing.

See: [references/constraints.md](references/constraints.md) for constraint design patterns.

### 6. Feedback

**Definition:** Communicating the results of an action back to the user.

**Feedback must be:**
- **Immediate:** Within 0.1 seconds for direct manipulation
- **Informative:** Tells user what happened and current state
- **Appropriate:** Not too much (annoying) or too little (confusing)
- **Non-intrusive:** Doesn't block the user's workflow

**Types of feedback:**

| Type | When to Use | Example |
|------|-------------|---------|
| **Visual** | Most actions | Button press animation, color change, checkmark |
| **Auditory** | Important events, confirmations | Success chime, error sound, notification |
| **Haptic** | Touch devices, confirmation | Vibration on key press, force feedback |
| **Progress** | Long operations | Progress bar, spinner, skeleton screen |

**Digital feedback patterns:**

| Situation | Feedback Needed | Example |
|-----------|----------------|---------|
| **Button click** | Visual state change | Button depresses, color changes |
| **Form submission** | Success/error message | "Saved!" toast or inline error |
| **Loading** | Progress indicator | Spinner, skeleton screen, percentage |
| **Error** | What went wrong + how to fix | "Invalid email. Please check format." |
| **Hover** | Interactive element indicator | Background color change, underline |
| **Drag** | Object follows cursor | Element moves with mouse |

**Common failures:**
- No feedback at all (did my click register?)
- Delayed feedback (makes system feel broken)
- Unclear feedback (something happened but what?)
- Too much feedback (every action triggers alert)

**Response time guidelines:**
- 0.1s: Feels instantaneous (direct manipulation)
- 1.0s: Noticeable delay (show cursor change)
- 10s: Attention wanders (show progress bar)
- >10s: User leaves (show percentage, allow background)

See: [references/feedback.md](references/feedback.md) for feedback design patterns.

### 7. Conceptual Models

**Definition:** The user's mental model of how a product works.

**Three models:**

| Model | Held By | Description |
|-------|---------|-------------|
| **Design model** | Designer | How the designer thinks it works |
| **User's model** | User | How the user thinks it works |
| **System image** | Product | What the product actually communicates |

**Goal:** User's model should match the design model. The system image is the bridge.

**When models match:**
- Users predict outcomes correctly
- Users recover from errors easily
- Users feel confident and in control

**When models mismatch:**
- Users are confused and frustrated
- Users blame themselves
- Users give up or call support

**Example: Thermostat**
- **Design model:** Set temperature, system maintains it
- **Common user model:** Higher setting = faster heating (wrong!)
- **Result:** Users crank thermostat to 90°F hoping for faster warmth

**Building correct conceptual models:**
- Use familiar metaphors (desktop, folder, trash)
- Make system state visible
- Provide clear feedback
- Use consistent behavior (same action = same result)
- Progressive disclosure (simple model first, details available)

See: [references/conceptual-models.md](references/conceptual-models.md) for model design frameworks.

## Human Error

**Norman's key insight: There is no such thing as "human error." There is only bad design.**

**When someone makes an error, look for the design flaw, not the person's flaw.**

### Types of Errors

**Slips:** Correct intention, wrong action

| Slip Type | Cause | Example | Design Fix |
|-----------|-------|---------|------------|
| **Action slip** | Wrong action on right target | Click "Delete" instead of "Edit" | Separate destructive actions |
| **Memory lapse** | Forget step in sequence | Forget attachment after writing "attached" | Gmail's attachment reminder |
| **Mode error** | Right action, wrong mode | Type in caps lock | Show mode state clearly |
| **Capture error** | Familiar action overrides intended | Drive to old office on autopilot | Interruptions at decision points |

**Mistakes:** Wrong intention, executed correctly

| Mistake Type | Cause | Example | Design Fix |
|-------------|-------|---------|------------|
| **Rule-based** | Apply wrong rule | Use formula for wrong situation | Provide context, confirm |
| **Knowledge-based** | Incomplete/wrong mental model | Misunderstand how system works | Better conceptual model |
| **Memory lapse** | Forget goal or plan | Forget why you opened the fridge | Provide reminders, history |

### Design for Error

**Error prevention:**
- Constraints that make errors impossible
- Undo/redo for all actions
- Confirmation for destructive actions
- Sensible defaults
- Forgiving input (accept variations)

**Error recovery:**
- Clear error messages (what happened + how to fix)
- Don't erase user's work on error
- Allow partial saves
- Easy reset to known good state

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

**Design implications:**
- Stages 1-3 (execution): Support with clear signifiers, mappings, constraints
- Stage 4 (action): Support with good affordances
- Stages 5-7 (evaluation): Support with clear feedback, system state

**Use as evaluation tool:** Walk through each stage for any interaction. Where does the user get stuck?

See: [references/seven-stages.md](references/seven-stages.md) for stage-by-stage analysis.

## Human-Centered Design (HCD) Process

**Norman's design process:**

```
Observation → Idea Generation → Prototyping → Testing → (iterate)
```

### 1. Observation
- Watch real users in real contexts
- Don't ask what they want (they don't know)
- Look for workarounds, frustrations, adaptations
- Focus on activities, not individual tasks

### 2. Idea Generation
- Generate many ideas (diverge before converge)
- Don't criticize during ideation
- Build on others' ideas
- Defer judgment

### 3. Prototyping
- Quick, cheap, disposable
- Test concepts, not polish
- Paper prototypes for early ideas
- Interactive prototypes for validation

### 4. Testing
- Test with real users (not designers)
- 5 users reveal 85% of problems
- Observe behavior, not just opinions
- Iterate based on findings

**Key principle:** The design process is iterative. You'll go through multiple cycles, each time refining the design based on what you learn.

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

This skill is based on Don Norman's foundational design principles. For the complete framework:

- [*"The Design of Everyday Things"*](https://www.amazon.com/Design-Everyday-Things-Revised-Expanded/dp/0465050654?tag=wondelai00-20) by Don Norman (Revised & Expanded Edition, 2013)
- [*"Emotional Design"*](https://www.amazon.com/Emotional-Design-Love-Everyday-Things/dp/0465051367?tag=wondelai00-20) by Don Norman (design and emotion)

## About the Author

**Don Norman, PhD** is co-founder of the Nielsen Norman Group and director of The Design Lab at UC San Diego. He coined the term "user experience" while at Apple in the 1990s. *The Design of Everyday Things* (originally published in 1988 as "The Psychology of Everyday Things") is considered the most influential design book ever written and is required reading in virtually every design program worldwide. Norman has served as VP of Advanced Technology at Apple and has been a professor at Northwestern, UC San Diego, and KAIST (Korea).

## Overview

Apply foundational design principles: affordances, signifiers, constraints, feedback, and conceptual models.

## Prerequisites

- Access to the design environment or API
- Required CLI tools installed and authenticated
- Familiarity with design concepts and terminology

## Instructions

1. Assess the current state of the design configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [design implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with design |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply design everyday things to a standard project setup with default configuration options.

**Advanced scenario**: Customize design everyday things for production environments with multiple constraints and team-specific requirements.

## Resources

- Official design documentation
- Community best practices and patterns
- Related skills in this plugin pack
