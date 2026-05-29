---
title: "CI gap: shellcheck + ruff caught 4 findings"
description: "Plugin scripts had zero lint coverage. Added shellcheck + ruff to CI; caught four issues on first run. Behavior tests missed them."
date: "2026-05-26"
tags: ["ci-cd", "shellcheck", "ruff", "testing", "static-analysis"]
featured: false
---
The CI matrix ran lint-staged and the main workflow against TS/JS/JSON/MD/YAML. Good coverage there. But `plugin/skills/**/*.{sh,py}` — the shell and Python scripts inside plugin archetypes and skill scaffolding — got behavior tests (`test_run_sh.sh`, `test_verify.py`, `test_bank.py`) but nothing ran shellcheck or ruff on them. A quoting bug, an unused import, or a quote-injection footgun could land without signal.

I didn't see the gap until bead `nwh` forced the look.

Added `plugin-scripts-lint` job to `.github/workflows/ci.yml`. Two steps: shellcheck on `plugin/skills/**/*.sh`, ruff on `plugin/skills/**/*.py`. Each step does `shopt -s globstar nullglob`, expands the glob into a bash array, and `exit 0`s with a "no files" message when the array is empty — explicit guard, not "trust the glob":

```yaml
- name: shellcheck
  run: |
    shopt -s globstar nullglob
    files=(plugin/skills/**/*.sh)
    if [ ${#files[@]} -eq 0 ]; then
      echo "no .sh files under plugin/skills — skipping"
      exit 0
    fi
    shellcheck "${files[@]}"
```

The reason for the explicit `${#files[@]}` check rather than relying on shellcheck's behavior: shellcheck exits 3 ("no files specified") when invoked with zero arguments. Without the guard, an empty match would fail the build. The array form means the glob expands once, in bash, in a known mode.

First run caught four real findings on files that had shipped with behavior tests passing:

**SC2015** in `plugin/skills/ico-your-internals/scripts/run.sh` — the classic `[ -n A ] && [ -n B ] || usage` footgun. People read it as "if both non-empty, do nothing; else show usage." The actual semantics: `||` fires when *anything* on its left side returns non-zero. If B is empty (the intended trigger), `usage` runs — fine. But if both are non-empty and the next command in the chain (or a later expansion of the pattern) ever fails, `usage` fires spuriously on the success path. The pattern can't distinguish "validation failed" from "validation passed but a downstream step errored." Rewrote as `if [ -z A ] || [ -z B ]; then usage; fi` — explicit branch, no false trigger:

```bash
# before — SC2015
[ -n "$INPUT_FILE" ] && [ -n "$OUTPUT_DIR" ] || usage

# after
if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_DIR" ]; then
  usage
fi
```

**SC2016** (twice) in `tests/test_run_sh.sh` — single-quoted `$VAR` in grep patterns. Shellcheck flags this because single-quotes usually mean "you forgot to expand the variable." In grep patterns it's correct (literal text match), but the rule can't infer intent. Switched to `grep "\\$VAR"` — same literal match, rule satisfied.

**SC2028** in `tests/test_run_sh.sh` — `echo` with escaped backslashes. The bash builtin honors `\n` only with `-e`; `/bin/echo` on some distros honors it by default, on others it doesn't; dash's builtin behaves differently again. A test that writes `echo "line1\nline2"` to a fixture file gets a one-liner with a literal `\n` on Ubuntu's `/bin/sh` and a two-line file under bash on macOS. Replaced with `printf "line1\nline2\n"` — explicit format string, no environment ambiguity.

**F401 (ruff)** in `tests/test_verify.py` — unused imports (`os`, `shutil`). Auto-fixed by `ruff check --fix`. No behavior change.

The same day also fixed `stryker.config.json` → `stryker.config.js`. The audit-harness hash-pinning patterns recognized the legacy `.json` name and the modern `.js` form but not the intermediate Stryker default. Renamed to `.js` ESM export, re-init pinned the hash. Mutation test on the crypto module: 3/4 killed, 75% — identical to before.

Both findings share a pattern: gates that *thought* they covered their scope but didn't. The CI matrix "ran static analysis" — just not on that surface. The audit-harness "pinned the stryker config" — just didn't recognize that filename. The gaps aren't in the enforcement; they're in the scope assumptions.

v1.6.0 shipped the same day. Bead cycle closed with 11 P3 deferrals and three epics resolved.
