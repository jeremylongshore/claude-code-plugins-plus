---
title: "Self-Expiring Report-Only CI Gates: From Advisory to Enforced"
description: "How a meta-gate enforces deadline-driven CI hardening without freezing contributors — one logical concern per PR, permanent blocking by design."
date: "2026-05-23"
tags: ["ci", "devops", "github-actions", "linting", "code-quality"]
featured: false
---
Advisory CI gates are where good intentions go to die. A team adds a linter "in warning mode for now," and "for now" becomes forever. The violations scroll past in PR reviews, nobody cleans them, the gate never goes blocking. Six months later the warnings are archaeological noise.

The pattern that breaks this cycle is simple but mechanical: every report-only gate carries a self-expiring deadline marker — `REPORT-ONLY-UNTIL: <date>` — and a meta-gate script fails the build if any gate outlives its deadline. Advisory mode becomes temporary by construction. The second part: organize around one logical concern per PR, bulk-cleaning all violations for that concern in the same commit. Tightly-coupled tools — like eslint and prettier, or ruff and ruff-format — flip together because they share a single run step and a single class of violation. Unrelated gates never share a PR. This keeps each change reviewable and the blame surface small.

## What Is a Self-Expiring Report-Only CI Gate?

A self-expiring report-only CI gate is a quality check that runs in advisory mode — violations are warnings, not build failures — but carries an explicit deadline date. A meta-gate fails the build once that deadline passes, forcing the team to either clean the violations and flip the gate to blocking, or remove it. This prevents advisory gates from quietly becoming permanent technical debt.

## The Meta-Gate: Enforced Deadlines

The enforcement script is small but decisive. It lives in the workflow as a step that runs before any code cleanup and fails the build if any gate is past its deadline:

```yaml
- name: Check CI deadline compliance
  run: |
    python scripts/check-ci-deadlines.py
  env:
    GITHUB_REF: ${{ github.ref }}
```

The script (~150 lines) scans workflow files for `REPORT-ONLY-UNTIL: <date>` markers and compares them against `datetime.now()`:

```python
import re
import datetime
import sys

def check_deadlines(workflow_file):
    with open(workflow_file) as f:
        content = f.read()
    
    # Match: REPORT-ONLY-UNTIL: YYYY-MM-DD
    pattern = r'REPORT-ONLY-UNTIL:\s*(\d{4}-\d{2}-\d{2})'
    matches = re.finditer(pattern, content)
    
    today = datetime.date.today()
    expired = []
    
    for match in matches:
        deadline_str = match.group(1)
        deadline = datetime.date.fromisoformat(deadline_str)
        
        if today > deadline:
            expired.append((deadline_str, match.group(0)))
    
    return expired

if expired_gates := check_deadlines('.github/workflows/validate-plugins.yml'):
    print("FATAL: report-only gates past deadline:")
    for deadline, marker in expired_gates:
        print(f"  {marker} (expired {deadline})")
    sys.exit(1)
```

The hardcoded workflow path can be swapped for any project (or glob all workflow files in `.github/workflows/`).

The marker lives as a comment in the workflow, immediately preceding the gate it guards:

```yaml
- name: Run ESLint
  # REPORT-ONLY-UNTIL: 2026-06-20
  run: npm run lint:js || true
```

When the deadline arrives, the meta-gate blocks the build. To flip the gate to blocking, you remove the marker AND remove the `|| true` in the same commit:

```diff
  - name: Run ESLint
-   # REPORT-ONLY-UNTIL: 2026-06-20
-   run: npm run lint:js || true
+   run: npm run lint:js
```

This forces a deliberate choice: keep the gate advisory (extend the deadline or remove the marker entirely to soft-delete it), or flip it to blocking (bulk-clean the violations first, then remove both markers in one PR).

## The Campaign: Nine PRs, Zero Rot

Claude-code-plugins is a 2000+ GitHub star monorepo with ~10,468 markdown files and plugins written in Python, TypeScript, shell, and markdown. The groundwork — the deadline meta-gate and one chastening moment where a freshly-blocking gate was flipped back to report-only after it caught a real failure on its first run — landed 2026-05-21. The campaign proper ran across 2026-05-22 and 2026-05-23, organized as nine sequential PRs (A through I), each addressing one logical concern.

### PR A (#764): ESLint + Prettier

ESLint and Prettier flipped to blocking gates together. No backlog of violations; the gates were added with cleanup already done, so the flip was immediate. These tools are tightly-coupled (same run step, same class of violations).

### PR B (#765): Ruff + ruff-format

Ruff (Python linter) and ruff-format flipped to blocking gates together. Bulk cleanup across ~180 Python files, then flip. This PR established the template: bulk cleanup + immediate gate, no deadline crutch. Again, tightly-coupled tools (same step, same violation class).

### PR C (#767): Markdownlint (report-only)

Markdownlint added as a report-only gate. Added with a `REPORT-ONLY-UNTIL: 2026-06-20` deadline because the backlog was large (80 violations across 10,468 files). This was deliberate: the gate exists, enforcement is temporary, and the deadline is explicit.

### PR D (#766): Root directory hygiene

Root directory cleanup (removed stale license files, dead symlinks, misplaced config fragments). No gate change, just hygiene.

### PR E (#768): Shellcheck — where the pattern earned its keep

Shellcheck cleanup and flip to blocking. This PR surfaced the real value of the pattern.

Shellcheck flagged 223 violations across 47 shell script files. These weren't nitpicks a reviewer would catch — they were silent runtime failures that report-only mode had been hiding for months. Flipping the gate to blocking forced them into the light.

First detail: 47 of the .sh files were actually Python scripts with a `#!/usr/bin/env python3` shebang but `.sh` extension. Shellcheck flagged them as SC1071 (unknown shell dialect). The fix was `git mv` to rename them `.py`, which also correctly moved them under ruff's scope (discovered later in PR G when the widened-test-loop caught new Python lint).

The real bugs shellcheck surfaced:

**SC2064 – trap expansion time.** A cleanup handler was written as:

```bash
trap "rm -rf $temp_dir" EXIT
```

The issue: `$temp_dir` expands when the trap is SET (at script start), not when it FIRES (at exit). If the script changed the variable later, the trap deleted the wrong directory (or nothing at all). The fix:

```bash
trap 'rm -rf "$temp_dir"' EXIT
```

Single quotes defer expansion to fire-time. Shellcheck flags this by default; it's a real gotcha.

**Unquoted redirection operator.** A dependency pinning line read:

```bash
pip install some-package[extra]>=1.0
```

The `>=1.0` is unquoted, so bash interprets `>` as file redirection. The script silently created a file named `=1.0` instead of pinning the version. Quoting the entire argument:

```bash
pip install 'some-package[extra]>=1.0'
```

fixes it. Shellcheck flags the unquoted redirection.

**SC2166 – POSIX `-o` operator.** The script used:

```bash
[ -f "$file1" -o -f "$file2" ]
```

The `-o` operator (logical OR in `[ ]` test) is not well-defined in POSIX and can misparse in edge cases. The portable form:

```bash
[ -f "$file1" ] || [ -f "$file2" ]
```

is safer and clearer.

Other notable finds: SC2188 (no-command redirect — fix: `: > "$LOG_FILE"`), SC2213/SC2214 (getopts with duplicate option letters and unreachable case branches).

After cleanup, PR E added a `.shellcheckrc` file with project-wide disables for checks that were genuinely incompatible with the codebase style:

```ini
disable=SC1090,SC1091,SC2155,SC2034
severity=warning
```

These are set in the config, NOT in the workflow step. A gotcha: `.shellcheckrc` does not have a `severity=` directive (it only recognizes `disable=`). The severity policy is set at runtime in the CI step, so the workflow must include `--severity=warning` in the `run:` command.

### PR F (#769): TypeScript coverage + codeblock syntax

TypeScript coverage audit and code-block syntax linting flipped to blocking together. These tools are tightly-coupled (both operate on codeblock content in TypeScript/SKILL.md).

### PR G (#770): Widened test loop

Widened test loop (a 15-minute timeout gate that runs the full plugin suite). Flipped to blocking.

### PR H (#771): Codeblock syntax cleanup

Codeblock syntax cleanup (SKILL.md and README fenced-code fence fixes across plugins) flipped to blocking.

### PR I (#772): Markdownlint — the last gate flips

Markdownlint, the last report-only gate. 80 violations reduced to zero across 10,468 files. The largest categories were:

- MD051 (broken anchor links): 33 violations. TOC link targets regenerated to match GitHub's auto-slug format.
- MD056 (table column mismatch): 20 violations. Notable: 8 were a literal `|` inside a backtick code span that needed escaping to `\|`, and 12 were genuine header/row count mismatches.
- MD001 (improper heading increment): 7 violations.
- MD045 (missing alt text on shield badges): 3 violations.

The remaining ~17 violations were distributed across smaller categories (MD046 indented-code, MD003 setext-style, MD031 fence blank-line) and cascading --fix resolutions.

After PR I merged: **10 blocking required gates, zero report-only.** The gates: eslint, prettier, ruff, ruff-format, shellcheck-skills, skill-codeblock-syntax, typescript-coverage-audit, widened-test-loop, markdownlint, and the base validate step.

## The Proof: External Contributions Now Bind

The same day PR I merged (2026-05-23), a community-contributed plugin (agency-os, PR #709) landed. This PR had been open for review since before the campaign; when the 10 gates went blocking on 2026-05-23, the still-open PR's CI started failing, forcing a restructure. Its SKILL.md was 863 lines of auto-generated cruft. The marketplace-tier required fields (name, description, allowed-tools, version, author, license, compatibility, tags) were missing.

The CI ran. All 10 gates failed. The contributor restructured the SKILL.md from 863 lines to 168 and added the 6 missing marketplace fields. No human reviewer had to enforce the standard in the PR thread — the CI did. This is the payoff: the gates now bind external contributions automatically, without a human argument happening in the thread.

## How to Adopt This

1. **Add the meta-gate script** (`check-ci-deadlines.py`) to `scripts/`. Swap the hardcoded workflow path (or glob all workflow files) and any project can adopt it.
2. **Mark each report-only gate with a deadline comment** before the run step. Use format `# REPORT-ONLY-UNTIL: YYYY-MM-DD`. Choose a date 4–6 weeks out.
3. **Add the meta-gate to your workflow** as an early step. It fails fast if any gate is past deadline.
4. **When you're ready to flip a gate or tool-pair to blocking:** bulk-clean all violations in one commit, then remove the deadline marker AND the `|| true` in the same PR. One logical concern per PR (tightly-coupled tools flip together).
5. **Never extend a deadline without a written plan.** If the backlog is too large, the deadline was too aggressive; next time, choose 8–12 weeks instead. The discipline is in the deliberate choice, not in the calendar date.

The system ensures that advisory gates cannot quietly rot into permanent technical debt. They expire, they get re-evaluated, or they go blocking. Technical governance becomes automatic.
