# PLAYBOOK — Trace-Driven Remediation

## End-to-end triage flow

```
                +-------------------------+
                | Initial audit (noisy)   |
                +------------+------------+
                             |
                             v
                +-------------------------+
                | Trace via this skill    |
                +------------+------------+
                             |
            +----------------+----------------+
            |                |                |
     leverage report    deep-transitive   unreachable
            |                |                |
            v                v                v
       bump highest-     consider          add override
       leverage parent   override          OR vendor+patch
            |                |                |
            v                v                v
                  Re-run trace (post-fix)
                             |
                             v
                  (loop until clean OR
                   remaining findings are
                   all overrides/vendor)
```

## SBOM generation patterns (cyclonedx, syft, anchore)

The skill builds an in-memory graph. For long-term SBOM hygiene
you want a persisted SBOM file. Tools that generate one from a
project:

### npm — `@cyclonedx/cyclonedx-npm`

```bash
npm install -g @cyclonedx/cyclonedx-npm
cyclonedx-npm --output-file sbom.json
```

Produces CycloneDX JSON. Includes per-package license, version,
hash, and dependency edges. Can be fed to `grype` or `trivy` for
CVE scanning of the SBOM itself.

### Python — `cyclonedx-bom`

```bash
pip install cyclonedx-bom
cyclonedx-py environment -o sbom.json     # from active venv
cyclonedx-py requirements requirements.txt -o sbom.json
```

### Multi-language — `syft`

```bash
syft <directory> -o cyclonedx-json=sbom.json
```

Syft auto-detects ecosystem and produces a unified SBOM across
languages.

### Vulnerability scanning the SBOM — `grype`

```bash
grype sbom:./sbom.json -o json > vulns.json
```

This skill consumes audit JSON from the per-language skills
(`auditing-npm-dependencies` / `auditing-python-dependencies`). The
SBOM path is parallel — both can coexist; the SBOM is more useful
for long-term tracking, while the audit JSON is more useful for
PR-time gating.

## When to override vs vendor-patch

| Decision factor | Override wins | Vendor-patch wins |
|---|---|---|
| Fix-version available | YES → override | n/a |
| Maintainer accepting PRs | YES → override + upstream PR | n/a |
| Maintainer unresponsive | n/a | YES |
| Override produces resolution conflicts | n/a | YES |
| Multiple direct deps converge on the vulnerable transitive | YES → single override clears all | n/a |
| The vulnerability is in a function YOU need patched, not just upgraded | n/a | YES |
| Maintenance is a concern (small team) | YES → override is cheap | n/a |
| Maintenance is not a concern (security team has bandwidth) | n/a | acceptable |

## Per-runtime override mechanics

### npm overrides (npm 8.3+)

```json
{
  "overrides": {
    "lodash": "^4.17.21"
  }
}
```

After editing, run `npm install` to refresh the lockfile. The
override applies to every transitive consumer.

### npm overrides — nested form

```json
{
  "overrides": {
    "express": {
      "qs": "^6.10.3"
    }
  }
}
```

Forces `qs@^6.10.3` only when reached via `express`. Use when the
flat override breaks unrelated consumers.

### pnpm overrides

```json
{
  "pnpm": {
    "overrides": {
      "lodash": "^4.17.21"
    }
  }
}
```

Same semantics, different config block.

### Yarn resolutions

```json
{
  "resolutions": {
    "lodash": "^4.17.21"
  }
}
```

Yarn's equivalent. Predates npm overrides; works in Yarn 1, 2, 3, 4.

### Python — pin in requirements

```
boto3==1.34.0
urllib3>=2.0.2     # transitive pin, overrides boto3's loose pin
```

Python doesn't have a first-class override; pinning the transitive
as a direct dep is the pattern.

### Python — poetry constraints

```toml
[tool.poetry.dependencies]
urllib3 = "^2.0.2"
```

Adding the transitive as a direct dep with a constraint accomplishes
the override.

## Trace re-run cadence

After applying any override or parent-bump:

1. Re-run the per-language audit skill to refresh the finding list.
2. Re-run this trace skill against the new audit output.
3. Confirm the previously-flagged paths are gone.
4. Repeat until the residual is overrides + vendor work only.

A clean trace run (zero deep-transitive findings, zero unreachable
findings) is the gate for merging the dependency-refresh PR.

## Multi-finding direct-dep upgrade workflow

When the leverage report identifies a direct dep that's the
ancestor for ≥3 CVEs, plan the upgrade as a single PR:

1. Identify the direct dep + bump target.
2. Read its changelog from the previous-pinned to the target
   version. Note any documented breaking changes.
3. Run your full test suite against the bumped version (don't merge
   on green-CI alone for a 3+ CVE bump — local validation matters).
4. If the parent's API changed, update YOUR call sites in the same
   PR.
5. Commit the dep bump + call-site updates + lockfile in one PR.
6. After merge, re-run the trace and confirm CVE clearance.

## When to give up on a CVE

A finding with NO fix in ANY reachable version, where the package
has no maintainer response and no available replacement, sometimes
just sits. Document the exception with:

- Date of last upstream maintainer activity (`npm view <pkg> time`)
- Vulnerability detail (CVE / GHSA)
- Reachability assessment (is the vulnerable function actually called
  in your code path?)
- Mitigation in place (WAF rule, input sanitization upstream, etc.)
- Re-evaluation date (typically 90 days)

This is the security-register equivalent of an `# noqa` comment.
It's not pretty, but it's honest. The skill's "unreachable" finding
class is the surface where this kind of exception arises.

## Integration with auditing-* skills

This skill is intended to be run AFTER the per-language audit:

```bash
# Pipeline
python3 .../auditing-npm-dependencies/scripts/audit_npm.py . \
    --format json --output /tmp/npm-audit.json
python3 .../tracing-transitive-vulnerabilities/scripts/trace_vulns.py . \
    --audit-input /tmp/npm-audit.json --format markdown --output trace.md
```

For a polyglot project, run both per-language audits and merge:

```bash
python3 .../auditing-npm-dependencies/scripts/audit_npm.py . \
    --format json --output /tmp/npm-audit.json
python3 .../auditing-python-dependencies/scripts/audit_python.py . \
    --format json --output /tmp/py-audit.json
jq -s 'add' /tmp/npm-audit.json /tmp/py-audit.json > /tmp/all-audit.json
python3 .../tracing-transitive-vulnerabilities/scripts/trace_vulns.py . \
    --audit-input /tmp/all-audit.json --format markdown --output trace.md
```
