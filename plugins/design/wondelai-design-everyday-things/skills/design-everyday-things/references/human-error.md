# Human Error: Designing for Mistakes

There is no such thing as human error. There is only bad design. When a person makes an error, the cause is almost always a design flaw: poor feedback, misleading signifiers, bad mappings, missing constraints, or a broken conceptual model. Blaming users for errors is the designer's greatest failure. Instead, design systems that prevent errors, tolerate errors, and make recovery easy.

## Slips vs. Mistakes: The Fundamental Taxonomy

Don Norman divides errors into two categories based on where the failure occurs in the action cycle.

| | Slips | Mistakes |
|---|-------|---------|
| **Definition** | Correct intention, wrong action | Wrong intention, correctly executed |
| **Cause** | Attention failure, motor error, habit | Incorrect mental model, wrong rule, faulty reasoning |
| **Awareness** | User often notices immediately | User may not realize error until consequences appear |
| **Example** | Clicking "Delete" when reaching for "Edit" | Using the wrong formula in a spreadsheet because the user misunderstands the data |
| **Fix approach** | Make actions distinct and recoverable | Build correct conceptual models and provide better information |

---

## Slip Types

### Action-Based Slips

The user intends to perform one action but accidentally performs a similar or adjacent one.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Adjacent target** | Clicking the wrong button because it is too close | Tapping "Delete" instead of "Edit" on mobile | Separate destructive actions from constructive ones by distance and visual style |
| **Similar action** | Performing a habitual action instead of the intended one | Typing your old password after changing it | Provide clear feedback when the old credential is rejected and guide to the new one |
| **Description similarity** | Confusing two objects that look alike | Grabbing the wrong file from a list of similar names | Make distinguishing information prominent (dates, sizes, thumbnails) |

### Memory-Lapse Slips

The user forgets a step in a familiar sequence.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Omitted step** | Skipping a step in a multi-step task | Forgetting to attach a file after writing "see attached" | Detect the omission (Gmail attachment reminder) |
| **Lost place** | Forgetting which step they are on | Returning to a form after an interruption and re-entering data | Persist form state; show progress indicators |
| **Forgotten intention** | Walking to a room and forgetting why | Opening a settings page and forgetting which setting to change | Provide search within settings; show recently changed items |

### Mode Errors

The user performs the correct action for one mode while the system is in a different mode.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Invisible mode** | The current mode is not visually indicated | Typing in all caps because caps lock is on with no indicator | Always show the current mode visually (caps lock indicator, edit/view mode badge) |
| **Unexpected mode change** | The system changed modes without the user noticing | Airplane auto-throttle disengages silently | Announce mode changes with prominent feedback |
| **Cross-application mode** | Different behavior in different apps for the same action | Ctrl+S saves in one app, does something else in another | Follow platform conventions; never repurpose standard shortcuts |

### Capture Errors

A frequently performed action "captures" and overrides the intended less-frequent action.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Habit capture** | Habitual sequence overrides intended deviation | Driving to old workplace instead of new one on autopilot | Insert interruptions at decision points in habitual sequences |
| **Routine capture** | A daily routine overrides a one-time variation | Opening email client instead of the report you intended to work on | Use reminders, task lists, and calendar blocks to interrupt routines |

---

## Mistake Types

### Rule-Based Mistakes

The user applies a correct rule in the wrong situation, or applies a wrong rule that seems correct.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Wrong rule** | Applying a rule from a different context | Using "Reply All" when only "Reply" was appropriate because the user follows a "always reply all" rule | Show recipient count prominently, warn on large recipient lists |
| **Misclassified situation** | Correctly following a rule, but for the wrong problem type | Using the standard password reset flow when the account is actually locked (different issue, different fix) | Diagnose the situation for the user before presenting solutions |
| **Outdated rule** | Following a rule that used to be correct | A nurse giving a medication dose based on an old protocol | Version and timestamp all rules, policies, and procedures visible in the interface |

### Knowledge-Based Mistakes

The user lacks the knowledge or has an incorrect mental model to handle a novel situation.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Incomplete model** | The user's understanding of the system is partial | A user deletes a shared file not knowing it affects other users | Show sharing indicators and warn about impact |
| **Incorrect model** | The user's understanding is actively wrong | User believes setting thermostat to 90 heats the room faster | Redesign system image to teach correct model (show heating rate) |
| **Analogy failure** | Applying a model from one system to a different system | Expecting "undo" to work like a timeline when it actually works as a stack | Make the undo model explicit: show action history |

### Memory-Lapse Mistakes

The user forgets their goal, plan, or evaluation criteria.

| Subtype | Mechanism | Example | Design Prevention |
|---------|-----------|---------|-------------------|
| **Forgotten goal** | Losing track of what they set out to do | Opening the phone to set a timer but getting distracted by notifications | Provide reminders: "You opened Settings. Looking for something?" |
| **Forgotten plan** | Losing track of multi-step plan | Forgetting the third item in a three-item to-do after completing the first two | Show task lists, checklists, and recently started workflows |
| **Forgotten evaluation** | Forgetting what "success" looks like | Adjusting a photo but forgetting the original state to compare against | Provide before/after toggle, history, or comparison view |

---

## Error Prevention Strategies by Type

### Preventing Slips

| Strategy | Implementation | Prevents |
|----------|---------------|----------|
| **Increase target distance** | Separate destructive actions from routine actions by space and visual grouping | Adjacent target slips |
| **Distinctive appearance** | Make destructive buttons red, routine buttons blue | Description similarity slips |
| **Confirmation for irreversible actions** | "Delete this account? This cannot be undone." | Action slips with permanent consequences |
| **Mode indicators** | Always-visible badge showing current mode | Mode errors |
| **Interrupts at decision points** | "You're about to send to 500 people. Continue?" | Capture errors, memory-lapse slips |
| **Auto-detection** | Detect likely omissions and prompt | Memory-lapse slips (Gmail attachment warning) |
| **Constraints** | Disable invalid actions, enforce sequences | Multiple slip types |

### Preventing Mistakes

| Strategy | Implementation | Prevents |
|----------|---------------|----------|
| **Clear conceptual models** | Make system behavior visible and predictable | Knowledge-based mistakes |
| **Contextual information** | Show relevant data at the point of decision | Rule-based mistakes |
| **Undo and exploration** | Let users try things safely | Fear-based inaction (a form of mistake) |
| **Wizards and guides** | Step-by-step assistance for complex tasks | Knowledge-based and rule-based mistakes |
| **Default values** | Pre-fill with the most common or safest option | All mistake types |
| **Checklists** | Visible task lists for multi-step processes | Memory-lapse mistakes |
| **Comparisons** | Show before/after, show alternatives side-by-side | Forgotten-evaluation mistakes |

---

## Error Recovery Patterns

### Undo

| Pattern | Scope | Implementation |
|---------|-------|---------------|
| **Single undo** | Most recent action | Ctrl+Z, "Undo" button |
| **Multi-level undo** | Multiple recent actions | Undo stack with history list |
| **Undo toast** | Time-limited reversal | "Action completed. Undo (5s)" |
| **Version history** | All changes over time | Named versions, autosave snapshots |
| **Soft delete** | Deletion recovery | Trash bin with 30-day retention |

### Confirmation Dialogs

Use confirmation dialogs sparingly and only for high-consequence, irreversible actions.

| Effective Confirmation | Ineffective Confirmation |
|-----------------------|------------------------|
| "Delete 47 files permanently? This cannot be undone." | "Are you sure you want to save?" |
| "Send this email to 1,200 subscribers?" | "Are you sure you want to close this tab?" |
| "Downgrade your account? You will lose access to premium features." | "Are you sure you want to log out?" |

**The confirmation dialog trap**: If you show confirmations for routine actions, users develop "dialog blindness" and click "Yes" without reading. Then the one time the confirmation matters, they click "Yes" again out of habit.

### Autosave

| Feature | Purpose |
|---------|---------|
| Continuous autosave | No work is ever lost due to crash, timeout, or accidental navigation |
| Visible save indicator | "All changes saved" or "Saving..." shows the user the system is working |
| Named save points | Users can create explicit save points for comparison |
| Conflict resolution | When two versions exist, show both and let the user choose |

### Clear Error Messages

**The error message formula**:

```
1. What happened (in plain language)
2. Why it happened (if helpful)
3. How to fix it (specific actionable steps)
4. Alternative path (if available)
```

**Good example**:
```
We couldn't save your changes.
Your internet connection was interrupted.
Check your connection and try again, or download a copy of your work.
[Retry] [Download Copy]
```

**Bad example**:
```
Error 500: Internal Server Error
```

---

## Error Message Design Checklist

### Content

- [ ] Message describes what happened in human language (no error codes as the primary message).
- [ ] Message explains how to fix the problem or what to try next.
- [ ] Message does not blame the user ("We couldn't process" not "You entered incorrectly").
- [ ] Message provides an alternative path when possible.
- [ ] Technical details are available but not prominent (expandable section).

### Presentation

- [ ] Error appears near the source of the error (inline for form fields).
- [ ] Error is visually distinct (red border, error icon) but not alarming (avoid all-caps, exclamation marks).
- [ ] Error does not erase the user's work (form fields retain their values).
- [ ] Error is announced to screen readers (role="alert" or aria-live="assertive").
- [ ] Error is persistent until the user fixes the issue (does not auto-dismiss).

### Recovery

- [ ] A clear action is provided (button, link, or instruction).
- [ ] The user can retry without re-entering information.
- [ ] If the error is systemic (server down), communicate expected resolution time.
- [ ] If the error requires support, provide a direct path to contact support with the error context pre-filled.

---

## Designing for Error Tolerance

Error-tolerant systems assume users will make errors and minimize their consequences.

### Principles of Error Tolerance

| Principle | Implementation |
|-----------|---------------|
| **Reversibility** | Every action can be undone. Deletion is soft. Edits are versioned. |
| **Low cost of experimentation** | Users can try things without fear. Preview modes, sandbox environments, and undo reduce the risk of exploration. |
| **Graduated consequences** | Minor actions have minor consequences. Major consequences require major confirmation. |
| **Data preservation** | The system never discards user data without explicit, confirmed intent. Form data survives errors, navigation, and session timeouts. |
| **Graceful degradation** | When something breaks, the system continues working at reduced capacity rather than failing completely. |

---

## The Swiss Cheese Model of Errors

James Reason's Swiss Cheese Model explains how errors lead to disasters. Each layer of defense has holes (like Swiss cheese). An error becomes a disaster only when the holes in multiple layers align and the error passes through all defenses.

### Layers of Defense in Digital Products

| Layer | Defense | Example |
|-------|---------|---------|
| **Layer 1: UI Constraints** | Prevent the action from being possible | Disabled button, input validation, type-safe inputs |
| **Layer 2: Warnings** | Alert the user before they proceed | "This will delete 47 files. Are you sure?" |
| **Layer 3: Immediate Feedback** | Show the result so the user can catch the error | File count changes, visual confirmation |
| **Layer 4: Undo / Reversal** | Allow the user to reverse the action | "Undo" toast, trash bin, version history |
| **Layer 5: Recovery** | Restore from backup or contact support | 30-day trash retention, admin recovery tools |

For every critical action, ensure at least 3 layers of defense. If any single layer fails, the others catch the error.

---

## Case Studies of Error-Prone Designs and Fixes

| Case | Error | Root Cause | Fix |
|------|-------|-----------|-----|
| **Reply vs Reply All** | Private comment sent to entire organization | Buttons adjacent, identical, equally prominent | Make "Reply" default; show recipient count before sending |
| **Unsaved form on navigation** | User loses form data by clicking a link | No autosave, no navigation warning | Autosave to local storage; warn on navigation; restore on return |
| **Wrong file overwrite** | New file silently replaces existing file | No collision warning, no version history | Detect collision and warn; keep version history |
| **Medication dosage** | Nurse enters 10mg instead of 1.0mg | Free-text input, no range validation, small targets | Pre-set dose dropdown; range validation; large targets |

---

## Error Audit Checklist

### Prevention

- [ ] Destructive actions are visually separated from routine actions.
- [ ] Destructive actions require confirmation (for irreversible actions only).
- [ ] Input constraints prevent invalid data entry (type, range, format).
- [ ] The system detects likely omissions and prompts the user (attachment reminders, required fields).
- [ ] Mode indicators are always visible when modes exist.
- [ ] Default values are set to the safest or most common option.

### Detection

- [ ] Every action produces visible feedback within 100ms.
- [ ] Error messages appear inline near the source of the error.
- [ ] Error messages describe what happened, why, and how to fix it.
- [ ] Error messages do not blame the user.
- [ ] System state is visible at all times (saved/unsaved, connected/disconnected).

### Recovery

- [ ] Undo is available for all non-destructive actions.
- [ ] Deleted items go to a recoverable trash/archive.
- [ ] Form data is preserved on error (fields are not cleared).
- [ ] Autosave prevents data loss from crashes and timeouts.
- [ ] Version history allows reverting to previous states.
- [ ] Session recovery restores work after accidental closure.

### Systemic

- [ ] Errors are logged and analyzed for design improvement (not user blame).
- [ ] The most common user errors are tracked and addressed in design iterations.
- [ ] New features are tested for common slip and mistake patterns before launch.
- [ ] Error rate is a tracked product metric alongside task completion and satisfaction.
