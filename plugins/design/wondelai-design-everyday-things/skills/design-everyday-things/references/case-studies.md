# Case Studies: Design Analysis Using Norman's Principles

This collection of case studies applies Don Norman's design principles to real products, both physical and digital. Each case follows the same structure: the product, the design problem, the principle violated, a detailed analysis, the fix, and the broader lesson. These cases demonstrate that the same small set of principles explains why products are intuitive or infuriating.

---

## Case Study 1: The Norman Door

### Product

Commercial building doors with flat push-plates on both sides, or handles on a door that requires pushing.

### Design Problem

People push when they should pull, and pull when they should push. This happens millions of times daily in buildings around the world. The problem is so pervasive that doors requiring a "Push" or "Pull" sign have become known as "Norman Doors."

### Principles Violated

**Affordances**, **Signifiers**, **Constraints**

### Analysis

A flat plate affords pushing. A handle affords pulling (and pushing, but the grip shape invites pulling). When a door has a handle on the side that requires pushing, the affordance (graspable handle) contradicts the required action (push). The user perceives a pull affordance, attempts to pull, fails, and then pushes. The "Push" sign is a signifier band-aid for a broken affordance.

The deeper failure is a missing constraint. If the door only opens one way, the hardware should make the wrong action impossible. A flat plate on the push side and a handle on the pull side creates a physical constraint: you cannot pull a flat plate.

### Fix

- **Push side**: Flat plate (no handle). Affords only pushing.
- **Pull side**: Vertical handle. Affords pulling.
- **Automatic doors**: Eliminate the push/pull decision entirely.

### Lesson

When users consistently do the wrong thing, the design is wrong, not the users. The cheapest fix (a sign) is also the weakest. The best fix changes the physical design so the correct action is the only possible action.

---

## Case Study 2: The Thermostat Mental Model

### Product

Home thermostats (traditional and digital).

### Design Problem

Users set the thermostat to an extreme temperature (90 degrees) believing it will heat the room faster. It does not. The heating system operates at a constant rate regardless of the target temperature. Setting it to 90 just means it runs longer, overshoots the comfortable temperature, and wastes energy.

### Principle Violated

**Conceptual Models**

### Analysis

Users apply a "valve" mental model: more = faster, like a faucet where turning the handle further produces more water flow. The thermostat actually works as a "goal-seeking" system: it turns heating on/off to reach and maintain a target temperature. The rate of heating is fixed.

The system image fails because traditional thermostats show only the target number. They do not show the current temperature, the heating state (on/off), or the rate of change. Without this information, users cannot build the correct conceptual model.

### Fix

- Show current temperature AND target temperature side by side.
- Show "Heating to 72..." with an animated indicator.
- Show estimated time to reach target: "~15 minutes."
- Nest smart thermostats (like Nest) show all of this and learned the pattern early.

### Lesson

When users consistently misuse a product, the product's system image is failing to communicate its conceptual model. The fix is to make the internal mechanism visible, not to educate users through manuals.

---

## Case Study 3: Stovetop Burner Mapping

### Product

Gas and electric stoves with four burners in a 2x2 grid and four control knobs in a 1x4 row.

### Design Problem

Users turn the wrong knob for the burner they want to use. They must look at labels (often small and hard to read) to determine which knob controls which burner because the linear arrangement of knobs does not correspond to the grid arrangement of burners.

### Principle Violated

**Mappings**

### Analysis

The four burners are arranged in a square:

```
[FL] [FR]
[BL] [BR]
```

The four knobs are arranged in a line:

```
[K1] [K2] [K3] [K4]
```

There is no natural spatial mapping between the linear knobs and the grid of burners. The relationship is arbitrary and must be memorized or read from a label. Even after years of use, many people occasionally turn the wrong knob.

### Fix

Arrange the knobs in a 2x2 grid matching the burner layout:

```
[FL] [FR]     [KFL] [KFR]
[BL] [BR]     [KBL] [KBR]
```

Or place each knob directly adjacent to its burner. Some modern stove designs use a staggered or offset knob layout that better matches the burner positions.

### Lesson

Natural spatial mapping eliminates the need for labels, memorization, and guesswork. When the control layout matches the output layout, the relationship is self-evident.

---

## Case Study 4: Airplane Cockpit Mode Errors

### Product

Commercial aircraft autopilot and flight management systems.

### Design Problem

Pilots perform the correct action for the wrong mode, or fail to notice a mode change, leading to altitude deviations, speed errors, or in extreme cases, accidents. The 1994 Nagoya A300 crash and the 2009 Air France 447 disaster both involved mode confusion.

### Principles Violated

**Feedback**, **Signifiers**, **Conceptual Models**

### Analysis

Modern autopilot systems have dozens of modes: altitude hold, vertical speed, flight level change, approach, go-around, autothrottle, and many more. Mode transitions can be triggered by the pilot, by the automation, or by the system responding to conditions (e.g., reaching a target altitude).

The problems are compounded:
1. **Mode annunciations are small**: A tiny text label on the Primary Flight Display changes from "ALT HOLD" to "V/S" but may not attract attention.
2. **Automation acts silently**: The system transitions modes without alerting the pilot. A critical mode change (like autothrottle disconnection) may be signaled by a brief tone that is missed in a noisy cockpit.
3. **Model complexity**: Pilots must maintain a mental model of multiple interacting automation modes. The combinations are too numerous to track reliably.

### Fix

- **Prominent mode annunciations**: Large, color-coded mode displays that change distinctly when the mode changes.
- **Mode change alerts**: Auditory and visual alerts when the automation changes mode, especially uncommanded changes.
- **Simplified mode structure**: Reduce the number of modes. Combine similar modes. Make transitions predictable.
- **Consistent behavior**: Same pilot action should produce the same result regardless of mode.

### Lesson

When systems have modes, those modes must be visible, and mode changes must be unmissable. The more modes a system has, the more likely users are to lose track of the current state. Simplify modes wherever possible, and make remaining modes impossible to overlook.

---

## Case Study 5: Hospital Medication Errors

### Product

Electronic health record (EHR) systems and medication ordering interfaces.

### Design Problem

Physicians and nurses select the wrong medication, wrong dose, or wrong route of administration when ordering or administering medications. The Institute of Medicine estimates that medication errors harm at least 1.5 million Americans annually.

### Principles Violated

**Constraints**, **Signifiers**, **Feedback**, **Mappings**

### Analysis

Multiple design failures contribute:

| Failure | Principle | Description |
|---------|-----------|-------------|
| Drug name confusion | Signifiers | "Hydroxyzine" vs. "Hydralazine" look similar in dropdown lists |
| Dose entry as free text | Constraints | No range validation; a tenfold error (1.0mg vs 10mg) is not caught |
| Units not locked | Constraints | User can type "mg" when "mcg" is required |
| Alert fatigue | Feedback | So many alerts fire that clinicians override 90%+ of them, including real dangers |
| Display density | Mappings | Medication lists show 50+ items in a flat list with no grouping or hierarchy |

### Fix

- **Tall Man Lettering**: hydrOXYzine vs. hydrALAzine (capitalize distinguishing letters).
- **Dose range validation**: Flag doses outside the normal range for the selected drug: "10mg is 10x the typical adult dose. Confirm or adjust."
- **Pre-set dose options**: Dropdown of standard doses for each drug instead of free-text entry.
- **Tiered alerts**: Reserve modal alerts for true contraindications. Use inline warnings for less critical issues. Reduce alert volume by 80% so the remaining alerts are respected.
- **Visual grouping**: Group medications by category (cardiac, analgesic, antibiotic) with visual separation.

### Lesson

In high-stakes environments, constraints are the most important design tool. Preventing errors is always better than detecting them. Alert fatigue is a failure of the feedback system: when everything is flagged as important, nothing is.

---

## Case Study 6: ATM Interface Evolution

**Product**: Automated teller machines (1980s to present). **Principles Violated** (early ATMs): Signifiers, Feedback, Conceptual Models, Mappings.

Early ATMs had unlabeled buttons beside cryptic text screens. The mapping between button position and screen menu item was arbitrary and fragile. Users made frequent errors and needed staff assistance.

| Era | Interface | Mapping | Feedback | Errors |
|-----|-----------|---------|----------|--------|
| 1980s | Unlabeled buttons + text menu | Arbitrary | Minimal; cryptic messages | High |
| 1990s | Labeled buttons + graphical menu | Improved (labels adjacent to items) | Better; clearer messages | Moderate |
| 2010s | Touchscreen | Direct (tap the option itself) | Good; progress bars, animations | Low |

### Lesson

Direct manipulation (touching the thing itself) produces the best mapping possible. ATM evolution is a 40-year demonstration of mapping improvement through progressively more natural interaction.

---

## Case Study 7: Smartphone Unlock Evolution

**Product**: Smartphone lock screens (2007 to present). **Principles Applied**: Affordances, Constraints, Feedback.

Securing a device accessed 80-150 times daily requires balancing security against usability. Each generation reduced friction while maintaining or improving security.

| Method | Era | Signifier | Feedback | Error Recovery |
|--------|-----|-----------|----------|---------------|
| **Slide to unlock** | 2007 | Arrow and track | Slider follows finger | Springs back on failure |
| **PIN** | 2007+ | Familiar keypad | Dots fill, shake on error | Escalating delays |
| **Pattern** | 2008+ | Grid of dots | Line follows finger | Shake, timeout |
| **Fingerprint** | 2013+ | Sensor position | Haptic pulse | Falls back to PIN |
| **Face unlock** | 2017+ | None (ambient) | Padlock icon animation | Falls back to PIN |

### Lesson

The best interface is no interface. Each evolution reduced the Gulf of Execution while keeping evaluation clear. As technology improves, constraints can be maintained while affordances become invisible.

---

## Case Study 8: Smart Home Light Controls

**Product**: Smart home lighting (Philips Hue, LIFX, smart switches, voice assistants). **Principles Violated**: Conceptual Models, Mappings, Affordances.

A simple task (turn on the kitchen light) now involves choosing between a wall switch, app, voice command, hub, or automation. Users often cannot turn on their own lights because the conceptual model is fragmented.

### Analysis

| Problem | Principle | Description |
|---------|-----------|-------------|
| Wall switch kills smart bulb power | Conceptual model conflict | User's model: switch controls light. Reality: switch cuts power to the smart bulb, making it unresponsive to the app. |
| Multiple control points | Mapping confusion | The light can be controlled from 4+ places. Which one is "current"? |
| State ambiguity | Feedback failure | Is the light off because the switch is off, the app is off, the schedule turned it off, or the bulb has no power? |
| Voice command variability | Specification difficulty | "Turn on the kitchen light" vs "Turn on kitchen" vs "Lights on in the kitchen." Which works? |
| Automation surprises | Unexpected behavior | Lights turn on at 6 AM because of an automation the user forgot they set up. |

### Fix

- **Single source of truth**: All control methods feed into one system reflecting true state.
- **Switches send commands, not power**: Smart switches send commands to the hub rather than cutting electrical power to the bulb.
- **State always visible**: App and wall display always show current state.
- **Fallback to simple**: If the smart system fails, the physical switch still works.

### Lesson

Adding "smart" capabilities to simple products undermines the original simplicity. Every new control point must integrate with the existing model, not create a parallel one.

---

## Cross-Cutting Patterns: What Makes Designs Intuitive vs. Confusing

Across all eight case studies, the same patterns emerge repeatedly.

### What Makes Designs Intuitive

| Pattern | How It Works | Seen In |
|---------|-------------|---------|
| **Direct manipulation** | Act on the thing itself, not through an intermediary | Touchscreen ATM, smartphone unlock, WYSIWYG editors |
| **Spatial correspondence** | Control layout matches output layout | Stove fix, car seat adjusters, elevator buttons |
| **Visible system state** | Users always know what mode, state, or phase the system is in | Thermostat fix, airplane mode annunciation, smart home state |
| **Physical constraint** | Wrong action is impossible | Norman Door fix, USB-C, medication dose validation |
| **Immediate feedback** | Every action produces a perceivable result | Smartphone unlock haptics, ATM animations, inline validation |
| **Familiar metaphors** | New products map to known mental models | Trash can, folders, shopping cart |

### What Makes Designs Confusing

| Pattern | How It Fails | Seen In |
|---------|-------------|---------|
| **Hidden modes** | Users perform correct action in wrong mode | Airplane autopilot, caps lock, smart home automations |
| **Arbitrary mapping** | Controls have no logical connection to outcomes | Stove knobs, early ATM buttons, light switch panels |
| **Silent failures** | Errors produce no feedback | Form submissions, background sync, medication order processing |
| **Conflicting affordances** | Hardware suggests one action, system requires another | Norman Door, smart home wall switch |
| **Broken metaphors** | Product looks like something familiar but behaves differently | Thermostat as valve, cloud as physical location |
| **Alert fatigue** | Too many warnings cause all warnings to be ignored | Hospital medication alerts, confirmation dialogs |

### The Universal Fix

Every confusing design can be improved by asking six questions:

1. **Can the user see what actions are possible?** (Affordances, Signifiers)
2. **Can the user tell which control affects which outcome?** (Mappings)
3. **Can the user avoid making errors?** (Constraints)
4. **Can the user see what happened?** (Feedback)
5. **Does the user understand how the system works?** (Conceptual Model)
6. **Can the user recover from mistakes?** (Error Tolerance)

If the answer to any question is "no," the corresponding principle identifies both the problem and the category of solution.
