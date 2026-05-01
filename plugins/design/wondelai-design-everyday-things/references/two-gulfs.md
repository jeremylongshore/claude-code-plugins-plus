# The Two Gulfs: Execution and Evaluation

Every human-product interaction involves crossing two psychological chasms. The Gulf of Execution separates what the user wants to do from the actions the product requires. The Gulf of Evaluation separates what the product did from the user's understanding of what happened. Narrowing these gulfs is the central challenge of interaction design.

## Gulf of Execution: The Gap Between Intent and Action

The Gulf of Execution exists whenever a user has a goal but cannot figure out how to achieve it. The wider the gulf, the more effort users must expend translating their intentions into physical actions.

### What Makes the Gulf Wide

| Factor | Description | Example |
|--------|-------------|---------|
| Hidden controls | Actions exist but users cannot find them | Swipe gestures with no visual indicator |
| Unfamiliar vocabulary | Labels use jargon or internal terminology | "Reconcile ledger" instead of "Match payments" |
| Non-obvious sequences | Multiple steps required with no guidance | Configuring a router through 7 unlabeled screens |
| Mismatched mappings | Controls don't correspond to outcomes | A row of identical switches controlling different zones |
| Missing affordances | Interactive elements look static | A clickable text block with no hover state, underline, or color |

### What Narrows the Gulf

| Strategy | How It Works | Example |
|----------|-------------|---------|
| Clear signifiers | Visual cues reveal available actions | Placeholder text reading "Search by name or email..." |
| Natural mappings | Controls spatially match outputs | Volume slider oriented vertically, up means louder |
| Constraints | Only valid actions are possible | Date picker prevents invalid date entry |
| Familiar patterns | Use conventions users already know | Shopping cart icon in the top-right corner |
| Progressive disclosure | Show relevant options at the right time | Payment fields appear only after "Checkout" is clicked |

### Gulf of Execution in Web Applications

Web apps frequently widen the Gulf of Execution by burying functionality. Common offenders:

- **Hamburger menus on desktop**: Users cannot see what actions are available without clicking an icon that many people do not recognize.
- **Icon-only toolbars**: Without labels, users must guess what each icon does. A floppy disk icon means "save" only to users who have seen floppy disks.
- **Right-click dependent actions**: Any action that requires right-clicking is invisible to most users.
- **Keyboard-shortcut-only features**: Power users love them, but they are undiscoverable without signifiers.

### Gulf of Execution in Mobile Apps

- **Gesture-only navigation**: Swipe-to-delete, pull-to-refresh, and pinch-to-zoom all have wide execution gulfs for new users.
- **Hidden bottom sheets**: Content tucked behind a drag handle that looks decorative.
- **Long-press menus**: No visual indicator that holding down on an element reveals additional options.

### Gulf of Execution in Physical Products

- **Flat push-plates on doors that need to be pulled**: The plate affords pushing, but the door requires pulling.
- **Stove knobs in a row**: Four knobs in a line controlling burners in a 2x2 grid. Users cannot tell which knob maps to which burner.
- **Shower controls with unmarked handles**: Hot, cold, and diverter valves with no labels or color coding.

---

## Gulf of Evaluation: The Gap Between System State and Understanding

The Gulf of Evaluation exists whenever a user has performed an action but cannot determine what happened, whether it worked, or what state the system is now in.

### What Makes the Gulf Wide

| Factor | Description | Example |
|--------|-------------|---------|
| No feedback | Action produces no visible response | Clicking a button with no loading indicator or confirmation |
| Delayed feedback | Response comes seconds or minutes later | Email sent with no confirmation; user wonders if it went |
| Ambiguous feedback | Something changed but meaning is unclear | A number changed from 3 to 4 with no explanation |
| Hidden state | System state is not visible | Background sync happening with no indicator |
| Technical error messages | Error text is not human-readable | "Error 0x80070005: Access denied" |

### What Narrows the Gulf

| Strategy | How It Works | Example |
|----------|-------------|---------|
| Immediate feedback | Visual response within 100ms | Button depresses and changes color on click |
| State indicators | Persistent display of current state | "Draft" / "Published" badge on documents |
| Progress communication | Show advancement toward goal | "Step 3 of 5" with a progress bar |
| Clear error messages | Explain what happened and how to fix it | "That email is already registered. Try logging in instead." |
| Meaningful transitions | Animations that explain change | A deleted item sliding off-screen to the trash |

### Gulf of Evaluation in Web Applications

- **Silent saves**: Auto-save is excellent, but without a "Saved" indicator, users repeatedly click save.
- **Pagination with no count**: Users cannot tell how much content exists or where they are in the set.
- **Background processing**: File uploads, exports, or calculations with no progress indicator.
- **Form submission without redirect or toast**: Users click "Submit" and nothing visibly changes.

### Gulf of Evaluation in Kiosks and Public Terminals

- **Airport check-in kiosks**: Users scan their passport but receive no confirmation for 3-5 seconds. Many scan again, causing errors.
- **Parking meters**: Payment accepted but the display returns to the default screen before the user reads the confirmation.
- **Self-checkout machines**: Weight sensor errors display cryptic messages, and the machine locks until an attendant arrives.

---

## Gulf Analysis Exercise Template

Use this template to analyze any interface by examining both gulfs for a specific user task.

### Step 1: Define the Task

| Field | Entry |
|-------|-------|
| **Product / Interface** | |
| **User goal** | |
| **Target user profile** | |
| **Context of use** | |

### Step 2: Analyze the Gulf of Execution

| Question | Assessment (1-5) | Notes |
|----------|:-----------------:|-------|
| Can the user identify what actions are available? | | |
| Are the correct controls visible and discoverable? | | |
| Do the controls use familiar patterns and vocabulary? | | |
| Is the mapping between controls and outcomes clear? | | |
| Are impossible or irrelevant actions constrained? | | |
| Is the required sequence of steps obvious? | | |
| **Execution Gulf Score (average)** | | |

### Step 3: Analyze the Gulf of Evaluation

| Question | Assessment (1-5) | Notes |
|----------|:-----------------:|-------|
| Does the system provide immediate feedback on actions? | | |
| Can the user determine the current system state? | | |
| Is the feedback informative and understandable? | | |
| Are error states clearly communicated with recovery steps? | | |
| Can the user confirm the goal was achieved? | | |
| Are transitions and state changes visible? | | |
| **Evaluation Gulf Score (average)** | | |

### Step 4: Identify Improvements

| Gulf | Problem Found | Severity (H/M/L) | Proposed Fix |
|------|--------------|:-----------------:|-------------|
| Execution | | | |
| Execution | | | |
| Evaluation | | | |
| Evaluation | | | |

---

## Measuring Gulf Width: A Heuristic Evaluation Approach

Gulf width is not a single number. It varies by user expertise, context, and task. Use these heuristics to estimate relative width.

### Execution Gulf Width Indicators

| Width | Characteristics |
|-------|----------------|
| **Narrow** | User completes the action on first attempt without hesitation. Controls are visible, labeled, and follow conventions. |
| **Medium** | User pauses, scans the interface, then finds the correct action. Minor exploration required. |
| **Wide** | User tries incorrect actions before finding the right one, or gives up and seeks help. |
| **Very wide** | User cannot complete the task without external instruction (manual, tutorial, another person). |

### Evaluation Gulf Width Indicators

| Width | Characteristics |
|-------|----------------|
| **Narrow** | User immediately understands what happened and confirms the result. No uncertainty. |
| **Medium** | User notices a change but takes a moment to interpret it. Brief confusion, then clarity. |
| **Wide** | User is unsure whether the action succeeded. May repeat the action or navigate away to verify. |
| **Very wide** | User has no idea what the system did. Cannot determine current state. Abandons or calls support. |

---

## Design Patterns That Widen Each Gulf

### Patterns That Widen the Execution Gulf

- **Mystery meat navigation**: Links or icons with no labels that reveal their purpose only on hover or click.
- **Modes without indicators**: The interface behaves differently depending on an invisible mode (edit mode vs. view mode with no visual distinction).
- **Nested menus beyond two levels**: Users must remember a path through multiple levels to reach a function.
- **Inconsistent action locations**: "Save" is in the toolbar on one screen, in the footer on another, and in a menu on a third.
- **Custom scrollbars that hide**: Disappearing scrollbars on content that is not obviously scrollable.

### Patterns That Widen the Evaluation Gulf

- **Toasts that disappear too quickly**: Success or error messages that vanish in under 2 seconds before users read them.
- **Silent failures**: An action fails but the interface shows no error, giving the impression of success.
- **Optimistic UI without correction**: The interface shows success immediately but never corrects if the server rejects the action.
- **Identical states**: A toggle switch where "on" and "off" look nearly the same.
- **Aggregate indicators**: A single status badge that combines multiple states (e.g., "3 issues" with no breakdown).

---

## Patterns That Narrow Each Gulf

### Patterns That Narrow the Execution Gulf

- **Visible toolbars with text labels**: Every action is one click away with a clear label.
- **Contextual actions**: Relevant actions appear near the content they affect (inline edit buttons, contextual menus on selection).
- **Command palettes**: A searchable list of all available actions, bridging the gap for users who know what they want but not where it is.
- **Onboarding spotlights**: First-time highlights that point out key controls.
- **Consistent layout grids**: Users learn where to look for actions because they are always in the same place.

### Patterns That Narrow the Evaluation Gulf

- **Persistent status bars**: Always-visible indicators of system state (connection status, save status, user role).
- **Inline validation**: Real-time feedback on form fields as the user types.
- **Undo toasts with timers**: "Message sent. Undo (5s)" gives confirmation and a recovery window simultaneously.
- **State-change animations**: Smooth transitions that show how the old state became the new state.
- **Confirmation screens**: A summary of what was just done with the option to modify.

---

## Worksheet: Analyze Any Interface Through the Two Gulfs

Use this quick-reference worksheet for a 15-minute audit of any product or feature.

### Instructions

1. Choose a specific task the user wants to accomplish.
2. Attempt the task yourself as if you were a new user.
3. At each moment of hesitation, note which gulf is too wide.
4. Fill in the table below.

| Step | What I Wanted to Do | What I Actually Did | Gulf Issue (Execution / Evaluation) | Severity | Fix |
|:----:|---------------------|--------------------|------------------------------------|:--------:|-----|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

### Summary

- **Total execution issues found**: ___
- **Total evaluation issues found**: ___
- **Widest gulf moment**: ___
- **Highest-priority fix**: ___
- **Overall gulf assessment**: The [execution / evaluation] gulf is the bigger problem for this task.

### Follow-Up Actions

- [ ] Prioritize fixes by severity
- [ ] Sketch improved designs for the widest gulf moments
- [ ] Test improved designs with 3-5 users
- [ ] Re-evaluate gulf width after changes
