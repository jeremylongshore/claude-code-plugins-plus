# UX Heuristics - Implementation Guide

Step-by-step methodology for evaluating and improving interface usability using Nielsen's 10 heuristics with severity ratings.

## The Evaluation Process

A heuristic evaluation is NOT a user test. It is an expert review of an interface against established usability principles. Run it before user testing to eliminate obvious problems.

**Who runs it:** 3-5 evaluators independently review the interface. The same evaluator spots only ~35% of problems — multiple reviewers catch ~75%.

**What you need:** The interface (live, prototype, or screenshots), a task list covering primary user flows, and this heuristic guide.

## The 10 Heuristics

### H1: Visibility of System Status

The system should always keep users informed about what is going on.

**Check for:**
- Loading states: does every async operation show a progress indicator?
- Confirmation: after completing a form or action, does the user see clear confirmation?
- Current location: can the user always tell where they are? (breadcrumbs, active nav, page titles)
- Background operations: are long-running tasks visible even after the user navigates away?

**Common failures:** No loading spinner, no success message after form submit, no active state in navigation

### H2: Match Between System and the Real World

The system should speak the users' language, use concepts familiar from the real world.

**Check for:**
- Jargon: are there technical, internal, or domain-specific terms that new users won't understand?
- Metaphors: do icons and UI metaphors map to physical-world equivalents?
- Mental model alignment: does the system behavior match users' expectations based on their life experience?

**Common failures:** Database error messages surfaced to users, "null" or "undefined" in UI, technical abbreviations without explanation

### H3: User Control and Freedom

Users often choose system functions by mistake and need a clearly marked "emergency exit."

**Check for:**
- Undo: is there undo for all significant actions?
- Cancel: can the user cancel any in-progress operation?
- Close/dismiss: can the user exit any modal, dialog, or flow?
- Confirmation for destructive actions: are delete/remove actions reversible or at least confirmed?

**Common failures:** No undo after accidental deletion, no back button in multi-step forms, modals with no way to close

### H4: Consistency and Standards

Users should not have to wonder whether different words, situations, or actions mean the same thing.

**Check for:**
- Terminology: is the same concept called the same thing everywhere?
- Visual consistency: do similar elements look and behave the same way across the product?
- Platform conventions: does the UI follow OS and browser standards? (right-click, keyboard shortcuts)

**Common failures:** "Save" in one place, "Submit" in another; same action in different colors; buttons that look different across pages

### H5: Error Prevention

Better than good error messages is careful design that prevents problems from occurring in the first place.

**Check for:**
- Form validation: inline, before submission
- Dangerous actions: confirmation dialogs with explicit consequences ("Delete 47 files permanently?")
- Input constraints: does the UI prevent invalid input? (disable buttons until form is complete, reject non-numeric in number fields)
- Confirmation before irreversible actions

**Common failures:** No inline validation (all errors shown after submit), destructive actions with no confirmation, no way to undo permanent deletions

### H6: Recognition Rather Than Recall

Minimize the user's memory load by making objects, actions, and options visible.

**Check for:**
- Recent items/history: does the user see their previous choices where relevant?
- Context always visible: do users need to remember information from a previous step?
- Command discoverability: are available actions visible rather than requiring memorized commands?
- Search and suggestion: does the system help users find things rather than requiring exact recall?

**Common failures:** Multi-step forms that don't show previous answers, search requiring exact syntax, no autocomplete

### H7: Flexibility and Efficiency of Use

Accelerators — unseen by novice users — may speed up interaction for experts.

**Check for:**
- Keyboard shortcuts: are primary actions accessible via keyboard?
- Bulk actions: can expert users perform repetitive tasks in bulk?
- Default settings that serve most users while allowing customization
- Power features: do advanced users have access to more efficient paths?

**Common failures:** No keyboard shortcuts for common operations, no batch selection in lists, settings reset on every visit

### H8: Aesthetic and Minimalist Design

Dialogues should not contain irrelevant or rarely needed information.

**Check for:**
- Information density: is every element on screen necessary?
- Competing elements: is there one clear primary action per screen/section?
- Copy: is all text necessary? (every word that survives should earn its place)
- Visual noise: decorative elements that don't communicate anything

**Common failures:** Too many CTAs, dense information panels with no hierarchy, promotional content interrupting primary flow

### H9: Help Users Recognize, Diagnose, and Recover from Errors

Error messages should be expressed in plain language, precisely indicate the problem, and constructively suggest a solution.

**Check for:**
- Plain language: no technical codes or jargon in error messages
- Specific: does the message tell the user exactly what went wrong?
- Actionable: does the message tell the user what to do?
- Blame-free: does the message avoid blaming the user?

**Error message formula:** "[What happened]. [Why it happened, if useful]. [What to do now]."
- Bad: "Error 400: Bad Request"
- Good: "Your password must be at least 8 characters. Please try again."

### H10: Help and Documentation

Even though it is better if the system can be used without documentation, sometimes help is necessary.

**Check for:**
- Inline help: are complex fields or interactions documented at point of use (not in a separate FAQ)?
- Onboarding: is there guidance for new users completing their first task?
- Search-able help: can users find answers to specific questions quickly?
- Progressive disclosure: is documentation available but not intrusive?

**Common failures:** No tooltips on complex fields, help documentation in a separate tab/window, no onboarding for first-time users

## Severity Rating Scale

Rate each finding on a 0-4 scale:

| Severity | Rating | Definition |
|----------|--------|-----------|
| Not a usability problem | 0 | No impact on usability |
| Cosmetic | 1 | Only fix if time permits |
| Minor | 2 | Low priority, fix in next release |
| Major | 3 | High priority, fix soon |
| Catastrophic | 4 | Must fix before launch |

**Severity factors:**
- Frequency: how often does this occur?
- Impact: how severely does this affect users when it occurs?
- Persistence: is this a one-time issue or does it affect users repeatedly?

## Evaluation Process

**Phase 1: Familiarization (15 min)**
- Review the product without evaluating
- Understand the intended use case and target user

**Phase 2: Individual evaluation (60-90 min)**
- Complete a predefined set of tasks while evaluating each heuristic
- Note every problem: what heuristic it violates, where it occurs, severity rating

**Phase 3: Aggregation**
- Combine all evaluator findings into a master list
- Merge duplicates, average severity scores across evaluators

**Phase 4: Prioritization**
- Sort by severity (4s first)
- Group by category (navigation, forms, feedback, etc.)
- Create a prioritized fix list with owner assignments

## Common Patterns by Component Type

**Forms:**
- H1: Show field-level validation feedback immediately (not on blur, not on submit-only)
- H5: Disable the submit button until required fields are complete
- H3: Allow editing previous steps without losing later step data
- H9: All field errors in plain language with specific fix instructions

**Navigation:**
- H1: Active state clearly shows current page/section
- H4: Navigation labels are consistent across pages
- H2: Labels use user vocabulary, not internal product terminology

**Data tables/lists:**
- H7: Bulk select + bulk actions for repetitive operations
- H3: Undo for bulk operations
- H8: Show only the columns users need by default; hide advanced columns

**Modals/dialogs:**
- H3: Always closable via X button AND escape key
- H5: Destructive actions show exact consequences
- H8: Modals contain only what the task requires — not the full feature

## Quick-Start Checklist

- [ ] Evaluation team of 3-5 evaluators assembled
- [ ] Task list covering primary user flows documented
- [ ] Each evaluator reviews independently (no group think)
- [ ] All findings recorded with: heuristic number, location, severity (0-4)
- [ ] Findings aggregated into master list
- [ ] Severity 4 items fixed before any other work
- [ ] Severity 3 items on the next sprint backlog
- [ ] Error messages audited: plain language, specific, actionable
- [ ] Undo/cancel/close available for all significant actions
- [ ] Navigation has visible active states on all pages
