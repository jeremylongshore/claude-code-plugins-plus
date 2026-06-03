# THEORY — Why Python Dependency Audits Matter

## The Python install model

`pip install <package>` does three things in sequence:

1. Resolves a transitive dependency graph from PyPI metadata.
2. Downloads each resolved package as a wheel (`.whl`) or sdist
   (`.tar.gz`).
3. For sdists, executes the package's `setup.py` (which is arbitrary
   Python) at install time. For wheels, runs any post-install hooks.

The `setup.py` execution step is the load-bearing detail. A
compromised PyPI package can read environment variables, write to
the user's home directory, exfiltrate data, and pivot to other
systems — all on `pip install`, before the package is ever imported.

## PyPI supply-chain incidents that drove audit adoption

| Year | Event | Mechanism |
|---|---|---|
| 2017 | Typosquat wave (PyTorch, RoboGirl, ...) | Names one character off from popular packages. Some shipped credential-stealing setup.py. |
| 2022 | `ctx` | Maintainer account compromise. Replaced legitimate package with a credential exfiltrator. ~22k weekly downloads. |
| 2022 | `request-toolbelt` (typosquat of `requests-toolbelt`) | Same week, same actor, similar tactics. |
| 2023 | `tornado` typosquats | Multiple variants targeting Tornado web framework users. |
| 2024 | `ultralytics` 8.3.42 / 8.3.43 | YOLO ML library hijacked through GitHub Actions cache poisoning. Crypto miner in the wheel. |
| 2025 | `requests-darwin-lite` | Targeted macOS users; trojanized binary inside an otherwise innocent wheel. |

Each case relied on either (a) someone installing the malicious
package by name without checking, or (b) a transitive dep updating
to a malicious version that an existing project pulled in
automatically.

## OSV, PyPA, and the audit data sources

`pip-audit` queries the Open Source Vulnerabilities (OSV) database
(osv.dev), maintained by Google as an aggregator of ecosystem-specific
advisory feeds. For Python, OSV ingests the PyPA Advisory Database
(github.com/pypa/advisory-database), which is the upstream of record
for Python-specific vulnerabilities.

Why OSV and not NVD?

- **OSV is ecosystem-aware.** A finding tagged "PyPI" affects exactly
  the packages installed via pip. NVD's CVE list is package-agnostic
  and requires manual mapping to ecosystem.
- **PyPA records often pre-date CVE assignment.** A vulnerability
  in a Python package can be published in PyPA's database before
  NIST assigns a CVE number. Tools that only query NVD miss the
  early window.
- **Severity bands are normalized.** OSV maps CVSS scores to a
  consistent severity vocabulary across ecosystems.

The skill consumes pip-audit's output (which already does the OSV
query) rather than querying OSV directly. Reasons: pip-audit's
parser is mature, handles edge cases (yanked releases, retracted
advisories), and integrates with PEP 621 / poetry / pipenv project
layouts natively.

## Python-specific install-time risks

Two install-time behaviors make Python uniquely vulnerable:

### setup.py execution

Sdists run `setup.py` to build. `setup.py` is arbitrary Python.
A malicious sdist can do anything Python can do at install time,
including:

- Read `~/.aws/credentials`, `~/.ssh/id_*`, `.env` files.
- Open a reverse shell via socket.
- Modify other installed packages in site-packages.

`pip install <package> --only-binary :all:` refuses sdists,
forcing wheels — but most published packages still publish sdists
alongside wheels.

### Eager dependency resolution

Pre-pip 20.3, pip's resolver was first-match-wins, leading to
inconsistent dependency trees across environments. Pip's modern
resolver (PEP 517 + 2020-resolver) is consistent but slower; some
CI pipelines disable it for speed, reintroducing the inconsistency.

Inconsistent resolution = the audit on your laptop may show
different packages than the audit in CI. Locking via `pip-tools`,
`poetry`, or `uv` is the only durable fix.

## pip-audit vs Safety vs Snyk

Three audit tools compete in the Python space.

| Tool | Backed by | Strengths | Weaknesses |
|---|---|---|---|
| pip-audit | PyPA | Official; consumes the PyPA advisory DB directly; supports requirements/poetry/pipenv | Severity normalization is sometimes coarser than CVSS |
| Safety | safetycli.com | Commercial advisory DB with curated severity; web UI | Free tier rate-limited; relies on a third-party DB |
| Snyk | Snyk Inc. | Commercial advisory DB; rich vulnerability metadata; web UI | Auth required; commercial pricing for production use |

The skill standardizes on pip-audit because it's PyPA-blessed,
zero-cost, and ships with the data quality SOC2 auditors expect to
see in evidence packages.

## Why severity normalization matters

OSV emits severity as free-text strings or CVSS vectors. NVD emits
CVSS scores. GitHub uses 4 levels. PyPA uses ecosystem-specific
labels. The penetration-tester `Severity` enum (`lib/finding.py`)
is the canonical mapping target so downstream consumers (executive
reports, SOC2 evidence collection, dashboards) see one vocabulary
across every tool.

## When "no fix" is itself a finding

A vulnerability with no `fix_versions` is not less severe — it's
MORE remediation-bound. You can't `pip install -U` your way out of
it. The skill bumps such findings to at-least HIGH severity to make
this visible in the report. Operator options are limited:

1. Pin to an older safe version (if one exists pre-vulnerability).
2. Vendor the package locally and patch it in-tree.
3. Replace the package with an alternative.
4. Accept the risk with an explicit security-register exception.
