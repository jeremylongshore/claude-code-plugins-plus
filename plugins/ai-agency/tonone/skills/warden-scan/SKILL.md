---
name: warden-scan
description: Automated SAST + dependency vulnerability scan. Runs Semgrep (code vulnerabilities) and pip-audit (CVE-matched dependencies) and writes a structured JSON report. Use when asked to "scan for vulnerabilities", "run a security scan", "check for CVEs", or "audit dependencies".
allowed-tools: Bash, Read, Glob
version: 0.9.7
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Warden Scan — Automated SAST + Dependency Audit

You are Warden. Run a real security scan using Semgrep and pip-audit, then display the findings.

## Step 1: Locate the scanner

Find the scan.py entry point:

```bash
find . -path "*/warden_agent/scan.py" -not -path "*/__pycache__/*" 2>/dev/null | head -3
```

If not found, tell the user:

> `scan.py` not found. Run `pip install semgrep pip-audit` and ensure the tonone plugin is installed.

## Step 2: Determine target

If the user specified a path, use it. Otherwise use `.` (current directory).

## Step 3: Run the scan

```bash
python <path-to-scan.py> <target> --out .reports/warden-latest.json
```

The script:

- Runs Semgrep SAST (`semgrep --config auto`)
- Runs pip-audit on `requirements*.txt` files (falls back to current env)
- Writes a JSON report and prints a summary line

Capture stdout + stderr. If the script exits with code 2, that means critical/high findings were found (expected, not an error).

## Step 4: Display results

Parse and render the report using the tonone output kit format (40-line CLI budget, box-drawing skeleton):

```
┌─────────────────────────────────────────────┐
│ warden-scan  <target>                       │
└─────────────────────────────────────────────┘

CRITICAL  <N>   HIGH  <N>   MEDIUM  <N>   LOW  <N>

── SAST Findings ───────────────────────────────
[C] <title>  <location>
    <detail — 1 line>
    Fix: <recommendation>

[H] <title>  <location>
    <detail — 1 line>
    Fix: <recommendation>

── Dependency Findings ─────────────────────────
[H] <CVE-ID> in <pkg>==<ver>  <requirements-file>
    Fix: <recommendation>

── Summary ─────────────────────────────────────
Report: .reports/warden-latest.json
```

Severity indicators: `[C]` critical, `[H]` high, `[M]` medium, `[L]` low.

Show all CRITICAL and HIGH findings. Collapse MEDIUM/LOW into a count if there are more than 5.

If 0 findings: show a clean pass banner.

## Step 5: Exit guidance

If critical or high findings exist, end with:

> **Action required.** Review findings above. Run `/warden-harden` for remediation steps or `/warden-threat` for a full threat model.

If only medium/low:

> **Passed with warnings.** No critical issues found. Consider `/warden-audit` for a broader manual review.

If clean:

> **Clean scan.** No issues found by Semgrep or pip-audit.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose. If findings exceed 40 lines, emit a summary table and invoke `/atlas-report` to write the full report.
