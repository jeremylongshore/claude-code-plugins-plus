---
name: hyperflow-trace
description: Hyperflow debugging. Use for bugs, test failures, runtime errors, broken builds, or "this doesn't work" reports — verbs like debug, "fix it", solve, "why is X failing", "Y is broken", or a pasted stack trace. Systematic root-cause analysis before any patch — never blind-patch symptoms.
---

# hyperflow-trace — root-cause phase (Antigravity single-agent)

Find the root cause before changing anything. Follow the `hyperflow` doctrine.

## Steps

1. **Reproduce / locate.** Read the error, stack trace, or failing test. Identify the exact failing line and the observed-vs-expected behavior.
2. **5 Whys.** Trace the causal chain backward — keep asking "why" until you reach the true cause, not a symptom.
3. **Hypotheses.** List the 2-4 most plausible causes. For each, state a cheap test (read a file, add a log, run one test) that confirms or rules it out. Test them — narrow to the real cause.
4. **Confirm** the root cause with evidence (a failing assertion, a value print, a reproduced path). Do not patch on a guess.
5. **Fix** the root cause minimally. Add or update a test that would have caught it (characterization test before behavior change).
6. **Verify**: re-run the failing case + the surrounding suite. Self-review the diff (L1-L3). Commit as `fix(<scope>): <root cause>` (conventional, lowercase).

## Rules

- Never blind-patch a symptom to make an error message disappear.
- No behavior change beyond the fix unless asked.
- If the root cause is unclear after hypothesis testing, surface what you found and what's still unknown — don't ship a speculative patch.
