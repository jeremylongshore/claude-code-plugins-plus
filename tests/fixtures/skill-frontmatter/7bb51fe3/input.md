---
name: sitrep
description: |
  On-demand situational assessment — reviews current work direction, scope,
  code quality, and progress at any point in the workflow. Provides an honest,
  opinionated evaluation of whether the current approach is on track, over-engineered,
  under-engineered, or drifting from the original goal.
  Trigger with "/sitrep", "status check", "am I on track", "scope check".
allowed-tools: 'Read,Grep,Glob,Bash(git:*),AskUserQuestion'
metadata:
  author: 'Jeremy Longshore <jeremy@intentsolutions.io>'
  version: '1.0.0'
  tier: enterprise
  category: workflow
---

# Situational Assessment (SITREP)

Universal mid-workflow assessment. Run at any point — mid-implementation,
mid-debugging, mid-refactor — to get an honest, opinionated evaluation of
direction, scope, quality, and risks.

## Engineering Philosophy

These principles guide every assessment:

- **DRY** — flag repetition aggressively
- **Well-tested is non-negotiable** — missing tests are always flagged
- **Engineered enough** — not over, not under
- **Handle more edge cases, not fewer** — defensive beats optimistic
- **Explicit over clever** — readable wins
- **Minimal diff** — fewest new abstractions and files touched
- **ASCII diagrams liberally** — for complex flows, draw them
- **Opinionated recommendations** — give a call, not a menu

## Instructions

Execute all six steps sequentially. Do NOT ask for user input until Step 6.

### Step 1: Orient

Figure out what is happening right now. Gather context silently.

1. Run `git status` to see working tree state
2. Run `git diff --stat` to see what files changed and how much
3. Run `git diff --cached --stat` to see staged changes
4. Run `git log --oneline -10` to see recent commit history
5. Read any active plan file if one exists (check for `plan.md`, `PLAN.md`, or similar in the working directory)
6. Review the conversation context to identify: the current task, the original goal, and what has been done so far

Produce a brief internal summary (do not output yet). Identify:

- **What** is being worked on
- **Why** (the original goal/request)
- **How far** along the work is
- **What files** have been touched

### Step 2: Scope Check

Evaluate whether the work is appropriately scoped.

1. Count files touched (modified + new). Flag if 8+ files modified.
2. Count new files/classes/modules created. Flag if 2+ new abstractions introduced.
3. Check if any existing code already solves part of the problem — use Grep/Glob to search for related utilities, helpers, or patterns that could be reused instead of rebuilt.
4. Identify the minimum set of changes needed to hit the original goal.
5. Flag any work that goes beyond the original request (scope creep).
6. Flag any premature abstractions — helpers or utilities created for a single use.

### Step 3: Direction Check

Assess whether the current approach is heading in the right direction.

1. Compare current work against the original goal. Does it still align?
2. Check for drift — solving a different problem than originally intended.
3. Check for over-engineering signs:
   - Premature abstraction (generalizing before the second use case)
   - Unnecessary indirection layers
   - Configuration where hardcoding suffices
   - Feature flags or backwards-compatibility shims when the code could just change
4. Check for under-engineering signs:
   - Fragile assumptions (hardcoded values that should be configurable)
   - Missing validation at system boundaries
   - Silent failures where errors should surface
   - Copy-paste instead of extracting shared logic (after 3+ copies)
5. Produce an opinionated recommendation: **stay course**, **adjust**, or **stop and rethink**

### Step 4: Quality Snapshot

Review the quality of work produced so far.

1. **DRY violations**: Scan changed files for duplicated logic or repeated patterns (3+ similar blocks).
2. **Error handling gaps**: Check new codepaths for missing error handling at system boundaries (user input, external APIs, file I/O, network calls).
3. **Test coverage**: Check if new codepaths have corresponding tests. Flag any new public function, API endpoint, or significant logic branch without a test.
4. **Data flow clarity**: If the change involves complex data flow or state management, produce an ASCII diagram showing the flow.
5. **Stale artifacts**: Check if touched files contain outdated comments, TODO markers, or diagrams that no longer reflect the current state.

### Step 5: Risks and Gaps

Identify failure modes and untested paths.

1. **Failure modes**: For each new codepath, consider: timeout, nil/null, race condition, stale data, partial failure, resource exhaustion.
2. **Untested paths**: List error branches, edge cases, and fallback paths that lack test coverage.
3. **Critical gaps**: Flag any combination of: no test + no error handling + silent failure. These are the highest-priority items.
4. **Security surface**: If changes touch auth, input parsing, SQL, or file paths — flag for review.

### Step 6: Verdict

Produce the summary card and ask for direction.

Format the assessment as:

```
SITREP SUMMARY
─────────────────────────────────────
Goal:           [original objective in one line]
Progress:       [X of Y done / percentage / phase description]
Direction:      On track | Drifting | Off course
Scope:          Tight | Creeping | Bloated
Quality:        Solid | Concerns | Issues
Risks:          [count] flagged, [count] critical
─────────────────────────────────────
Recommendation: [one-line opinionated call]
```

Below the card, list the top 3 findings (most important issues or observations).

Then use AskUserQuestion with these options:

- **Stay course** — current direction is good, keep going
- **Adjust scope** — trim or refocus based on findings
- **Pause and rethink** — significant concerns warrant replanning

## Examples

**Example 1: Mid-implementation check**
User runs `/sitrep` while adding a new API endpoint.
Assessment finds 4 files touched (reasonable), tests exist for happy path but not error cases, one DRY violation in validation logic. Verdict: "On track, adjust" — add error-path tests and extract shared validation.

**Example 2: Scope creep detection**
User runs `/sitrep` while fixing a bug. Assessment finds 12 files modified, 3 new utility classes, and a config system that did not exist before. Verdict: "Off course, pause" — the bug fix turned into a refactor. Recommend fixing the bug minimally, then planning the refactor separately.

**Example 3: Clean bill of health**
User runs `/sitrep` after completing a feature. Assessment finds all tests passing, scope matches the plan, no DRY violations, error handling present. Verdict: "On track, stay course" — ship it.

## Error Handling

- **No git repository**: Skip git-based checks. Assess based on conversation context and file reads only.
- **No active plan**: Note that no plan file was found. Infer the goal from conversation context.
- **No changes yet**: Report that no work has been done yet. Offer to help define the approach instead.
- **Large diff (50+ files)**: Focus assessment on the most-changed files. Note that a full review at this scale needs a dedicated code review, not a sitrep.
