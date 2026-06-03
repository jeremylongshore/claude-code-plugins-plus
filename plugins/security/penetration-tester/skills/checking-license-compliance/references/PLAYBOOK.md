# PLAYBOOK — Policy Templates and Remediation

## Default policy templates

### Proprietary product (most common)

```json
{
  "allow": ["MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "0BSD", "Unlicense", "CC0-1.0"],
  "deny": ["GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later", "AGPL-3.0-only", "AGPL-3.0-or-later"],
  "review": ["LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only", "LGPL-3.0-or-later", "MPL-2.0", "EPL-2.0", "CDDL-1.0"],
  "project_license": "MIT"
}
```

Strict: no GPL family. LGPL/MPL require dynamic-linking review.

### Internal-only tool (no distribution)

```json
{
  "allow": ["MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "MPL-2.0", "EPL-2.0", "LGPL-3.0-or-later"],
  "deny": ["AGPL-3.0-only", "AGPL-3.0-or-later"],
  "review": ["GPL-2.0-only", "GPL-3.0-only"],
  "project_license": "PROPRIETARY"
}
```

Internal tools don't distribute, so GPL contamination is lower-risk
(only AGPL still poses a service-use issue if the internal tool
becomes externally accessible). GPL goes to review, not deny, so
the team is alerted but not blocked.

### OSS library (you publish under permissive license)

```json
{
  "allow": ["MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "0BSD"],
  "deny": ["GPL-2.0-only", "GPL-3.0-only", "AGPL-3.0-only", "LGPL-2.1-only", "LGPL-3.0-only", "MPL-2.0", "EPL-2.0", "CDDL-1.0"],
  "review": [],
  "project_license": "Apache-2.0"
}
```

Strictest — anything that could force a license change on downstream
users is denied. Better to refuse a dep than to push an Apache-2.0
license into a sea of new copyleft obligations.

### SaaS service (AGPL-aware)

```json
{
  "allow": ["MIT", "BSD-3-Clause", "Apache-2.0", "ISC", "MPL-2.0", "LGPL-3.0-or-later"],
  "deny": ["AGPL-3.0-only", "AGPL-3.0-or-later"],
  "review": ["GPL-2.0-only", "GPL-3.0-only"],
  "project_license": "PROPRIETARY"
}
```

AGPL is the categorical no for SaaS. GPL is review-only because
SaaS distribution doesn't trigger GPL obligation (you're not
distributing the binary).

## Replacing copyleft deps with permissive alternatives

| Copyleft package | Permissive alternative | License |
|---|---|---|
| `node-readline` (GPL-2.0) | `readline-sync` | MIT |
| `aspell` bindings (GPL-3.0) | `hunspell` (LGPL with binary linking exception) or `spellchecker` (MIT) | varies |
| `MySQL Connector/J` (GPL-2.0 with FOSS exception) | `MariaDB JDBC` (LGPL-2.1) | LGPL |
| `qt-py` (LGPL/GPL) | `PySide` (LGPL) or `PyQt` (GPL — same family) | LGPL preferred |
| `iText 7` (AGPL) | `Apache PDFBox` | Apache-2.0 |
| `ghostscript` (AGPL) | `MuPDF` (AGPL too — limited alternatives) | n/a; needs commercial license |

When no permissive alternative exists, options are:

1. **Buy a commercial license** from the upstream maintainer.
2. **Re-implement** the needed functionality.
3. **Vendor + relicense** if upstream is willing to dual-license.
4. **Architectural separation** — isolate the copyleft component
   into a separate service / process / binary that's distributed
   independently with its own source-availability commitment.

## Auto-generated NOTICE file

```bash
python3 ./scripts/check_licenses.py . --emit-attribution
# Produces ./NOTICE.md listing every permissively-licensed dep
```

Include `NOTICE.md` in your release artifacts:

- npm: add it to `files` array in `package.json` so it's published
  with the package.
- Python: add it to `MANIFEST.in` or `pyproject.toml`'s
  `package_data` so it's included in the sdist + wheel.
- Docker images: `COPY NOTICE.md /usr/share/doc/<your-app>/NOTICE`
- Mobile / desktop apps: include in the about / credits screen.

## Legal-counsel handoff template

When escalating a finding to legal counsel, provide:

```
PACKAGE:           <name>@<version>
ECOSYSTEM:         npm | pypi
DECLARED LICENSE:  <license>
CLASSIFICATION:    permissive | weak_copyleft | strong_copyleft | custom | unknown
USE CONTEXT:       (a) build-time only / (b) ships in binary / (c) ships in service
DEPENDENCY DEPTH:  direct | transitive (via <parent>)
PROJECT LICENSE:   <license>
REMEDIATION COST:  (estimate hours + alternative-package availability)
RISK IF UNRESOLVED: (compliance / contractual / brand)
```

This gives legal the minimum facts to advise. Don't ask "is this
OK?" — provide the facts and ask "given these facts, what's our
posture?" Counsel-advised exceptions go into the security register
with a re-evaluation date.

## Pre-release legal gate (CI)

```yaml
- name: License compliance gate
  run: |
    python3 plugins/security/penetration-tester/skills/checking-license-compliance/scripts/check_licenses.py \
        . --min-severity high --format json --output license-audit.json
    jq -e '. == []' license-audit.json || {
      echo "::error::License finding requires legal review before release"
      exit 1
    }
```

## M&A due diligence playbook

When auditing an acquisition target:

1. Run the scanner against `target-codebase/` with `--include-dev`.
2. Cross-reference findings against the target's representation-and-
   warranty schedule from the SPA (Stock Purchase Agreement).
3. For any finding NOT disclosed in the schedule, escalate to the
   M&A legal team.
4. Re-run after the target's response to your due-diligence
   questions — they may have local exceptions / commercial licenses
   that resolve flagged findings.

## Quarterly review cadence

License findings have a longer remediation window than CVEs (no
active exploitation pressure), but the obligation doesn't go away.
Schedule quarterly:

- Re-run audit against the current main branch.
- Review the previous quarter's exceptions; promote / demote /
  remove.
- Update `.license-policy.json` if the project's posture changed
  (e.g. open-sourcing a previously-proprietary module).

Document the quarterly review in your security register; SOC2 and
ISO 27001 auditors look for evidence of ongoing license posture
management.
